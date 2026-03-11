"""FF3 SMB + HML replication: WRDS-aligned data procedures fed into PyBondLab.

Matches the WRDS Drechsler notebook methodology:
  1. crsp.msf_v2 (CIZ format) — no manual delisting merge
  2. permco-level ME aggregation (sum across permno)
  3. December ME for book-to-market denominator
  4. 2+ years in Compustat requirement
  5. Dynamic monthly weights (buy-and-hold via dynamic_weights=True)

Then runs PBL DoubleSort to test whether data alignment improves correlation
with official Ken French factors.
"""

import pandas as pd
import numpy as np
import psycopg2
import PyBondLab as pbl
from PyBondLab.report import ResultsReporter
from pandas.tseries.offsets import MonthEnd, YearEnd
import os

SCRIPT = """FF3 WRDS-aligned: CIZ, permco ME, Dec ME for BtM, 2yr Compustat, dynamic weights"""

# ---- WRDS Connection ----
print("Connecting to WRDS...")
if os.name == 'nt' and not os.environ.get('PGSERVICEFILE'):
    pg_service = os.path.expanduser('~/.pg_service.conf')
    if os.path.exists(pg_service):
        os.environ['PGSERVICEFILE'] = pg_service
conn = psycopg2.connect("service=wrds")

# ---- Step 1: Official FF factors for comparison ----
print("Downloading official FF factors...")
_ff = pd.read_sql("SELECT date, smb, hml FROM ff.factors_monthly", conn)
_ff['date'] = pd.to_datetime(_ff['date']) + MonthEnd(0)

# ---- Step 2: Compustat ----
print("Downloading Compustat...")
comp = pd.read_sql("""
    SELECT gvkey, datadate, at, pstkl, txditc, pstkrv, seq, pstk
    FROM comp.funda
    WHERE indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'
    AND datadate >= '1959-01-01'
""", conn)
comp['datadate'] = pd.to_datetime(comp['datadate'])
comp['year'] = comp['datadate'].dt.year

# Preferred stock: pstkrv -> pstkl -> pstk -> 0
comp['ps'] = comp['pstkrv'].fillna(comp['pstkl']).fillna(comp['pstk']).fillna(0)
comp['txditc'] = comp['txditc'].fillna(0)
# Book equity
comp['be'] = comp['seq'] + comp['txditc'] - comp['ps']
comp.loc[comp['be'] <= 0, 'be'] = np.nan
comp = comp.dropna(subset=['be'])

# Years in Compustat (count >= 1 means 2+ years)
comp = comp.sort_values(['gvkey', 'datadate'])
comp['count'] = comp.groupby('gvkey').cumcount()
comp = comp[['gvkey', 'datadate', 'year', 'be', 'count']]
comp = comp.drop_duplicates(subset=['gvkey', 'year'], keep='last')

# ---- Step 3: CRSP (CIZ format — no manual delisting needed) ----
print("Downloading CRSP (CIZ format)...")
crsp_m = pd.read_sql("""
    SELECT a.permno, a.permco, a.mthcaldt,
           a.issuertype, a.securitytype, a.securitysubtype,
           a.sharetype, a.usincflg,
           a.primaryexch, a.conditionaltype, a.tradingstatusflg,
           a.mthret, a.mthretx, a.shrout, a.mthprc
    FROM crsp.msf_v2 AS a
    WHERE a.mthcaldt BETWEEN '1959-01-01' AND '2024-12-31'
""", conn)
crsp_m['mthcaldt'] = pd.to_datetime(crsp_m['mthcaldt'])
print(f"  CRSP raw: {len(crsp_m)} rows")

# Common stock filter (shrcd 10,11 equivalent)
crsp_m = crsp_m[
    (crsp_m['sharetype'] == 'NS') &
    (crsp_m['securitytype'] == 'EQTY') &
    (crsp_m['securitysubtype'] == 'COM') &
    (crsp_m['usincflg'] == 'Y') &
    (crsp_m['issuertype'].isin(['ACOR', 'CORP']))
]
# Exchange filter (NYSE/AMEX/NASDAQ, active trading)
crsp_m = crsp_m[
    (crsp_m['primaryexch'].isin(['N', 'A', 'Q'])) &
    (crsp_m['conditionaltype'] == 'RW') &
    (crsp_m['tradingstatusflg'] == 'A')
]
print(f"  CRSP filtered: {len(crsp_m)} rows")

crsp_m[['permco', 'permno']] = crsp_m[['permco', 'permno']].astype(int)
crsp_m['date'] = crsp_m['mthcaldt'] + MonthEnd(0)

# Fill missing returns
crsp_m['mthret'] = crsp_m['mthret'].fillna(0)
crsp_m['mthretx'] = crsp_m['mthretx'].fillna(0)

# ---- Step 4: Permco-level ME aggregation ----
print("Aggregating ME at permco level...")
crsp_m['me'] = np.abs(crsp_m['mthprc']) * crsp_m['shrout']  # in thousands
crsp_m = crsp_m.sort_values(['date', 'permco', 'me'])

# Sum ME across permno within same permco
crsp_summe = crsp_m.groupby(['date', 'permco'])['me'].sum().reset_index()
# Keep the permno with largest ME as representative
crsp_maxme = crsp_m.groupby(['date', 'permco'])['me'].max().reset_index()
crsp = crsp_m.merge(crsp_maxme, on=['date', 'permco', 'me'], how='inner')
crsp = crsp.drop('me', axis=1)
crsp = crsp.merge(crsp_summe, on=['date', 'permco'], how='inner')
crsp = crsp.sort_values(['permno', 'date']).drop_duplicates()

crsp['me'] = crsp['me'] / 1000  # Convert to millions for consistency

crsp['year'] = crsp['date'].dt.year
crsp['month'] = crsp['date'].dt.month

# ---- Step 5: December ME for BtM denominator ----
print("Using December ME for BtM...")
decme = crsp[crsp['month'] == 12][['permno', 'year', 'me']].rename(columns={'me': 'dec_me'})
decme['year'] = decme['year'] + 1  # Dec year t -> matched to July t+1 through June t+2

# June ME for size sorting (same as standard FF)
june_me = crsp[crsp['month'] == 6][['permno', 'year', 'me']].rename(columns={'me': 'ME_june'})
crsp = crsp.merge(june_me, on=['permno', 'year'], how='left')
crsp['ME_june'] = crsp.groupby('permno')['ME_june'].ffill()

# ---- Step 6: Dynamic weights (buy-and-hold) ----
# PBL's dynamic_weights=True handles this: uses VW from d-1 (previous month)
# We just need to pass current month's ME as VW, and PBL will lag it.
# Actually, the WRDS method uses mebase * lcumretx as weight.
# PBL dynamic_weights=True uses the previous period's ME, which is conceptually
# the same as buy-and-hold weighting.

# ---- Step 7: CCM Link ----
print("Downloading CCM...")
ccm = pd.read_sql("""
    SELECT gvkey, lpermno AS permno, linktype, linkprim, linkdt, linkenddt
    FROM crsp.ccmxpf_linktable
    WHERE substr(linktype,1,1)='L'
    AND (linkprim='C' OR linkprim='P')
""", conn)
ccm['linkdt'] = pd.to_datetime(ccm['linkdt'])
ccm['linkenddt'] = pd.to_datetime(ccm['linkenddt']).fillna(pd.Timestamp('2099-12-31'))

conn.close()
print("WRDS download complete.")

# ---- Step 8: Merge Compustat to CRSP via CCM ----
print("\nMerging CRSP-Compustat via CCM...")
comp_ccm = comp.merge(ccm, on='gvkey', how='inner')
comp_ccm = comp_ccm[
    (comp_ccm['datadate'] >= comp_ccm['linkdt']) &
    (comp_ccm['datadate'] <= comp_ccm['linkenddt'])
]

# FF timing: fiscal year t-1 Compustat matched to July t through June t+1
comp_ccm['jyear'] = comp_ccm['year'] + 1
crsp['jyear'] = crsp['year'].copy()
crsp.loc[crsp['month'] <= 6, 'jyear'] = crsp.loc[crsp['month'] <= 6, 'year'] - 1

merged = crsp.merge(
    comp_ccm[['permno', 'jyear', 'be', 'count']],
    on=['permno', 'jyear'], how='left'
)

# ---- Step 9: Apply 2+ years Compustat requirement ----
# count >= 1 means at least 2 fiscal years in Compustat
merged.loc[merged['count'] < 1, 'be'] = np.nan

# ---- Step 10: Book-to-Market using December ME ----
merged = merged.merge(decme, on=['permno', 'year'], how='left')
merged['BtM'] = merged['be'] / merged['dec_me']  # December ME denominator
merged.loc[merged['BtM'] <= 0, 'BtM'] = np.nan

# ---- Step 11: Final filters ----
merged = merged.dropna(subset=['mthret', 'me'])
merged = merged[merged['date'] >= '1963-07-01']

# Deduplicate (CCM can produce multiples)
merged = merged.sort_values(['permno', 'date', 'be'], ascending=[True, True, False])
merged = merged.drop_duplicates(subset=['permno', 'date'], keep='first')

# Convert nullable dtypes
for col in merged.select_dtypes(include=['Float64', 'Float32', 'Int64', 'Int32', 'Int16']).columns:
    merged[col] = merged[col].astype('float64')

# ---- Step 12: PyBondLab columns ----
merged['RATING_NUM'] = 1.0  # Dummy for equity
merged['VW'] = merged['me'].astype('float64')
merged['ME'] = merged['ME_june'].astype('float64')
merged['ret'] = merged['mthret'].astype('float64')
merged['BtM'] = merged['BtM'].astype('float64')

# NYSE breakpoint mask (primaryexch == 'N' in CIZ format)
merged['NYSE'] = (
    (merged['primaryexch'] == 'N') &
    (merged['BtM'] > 0) &
    (merged['ME'] > 0)
).astype(float)

# Also require valid BtM and ME for sorting
merged = merged[merged['ME'].notna() & (merged['ME'] > 0)]

print(f"Final merged: {len(merged)} rows, {merged['permno'].nunique()} permnos")
print(f"Date range: {merged['date'].min()} to {merged['date'].max()}")
print(f"NYSE breakpoint universe: {merged['NYSE'].sum():.0f} obs ({merged['NYSE'].mean()*100:.1f}%)")

# ---- Step 13: Run PBL DoubleSort ----
print("\nRunning FF3 DoubleSort (WRDS-aligned)...")

def nyse_filter(df):
    return df['NYSE'] == 1.0

strategy = pbl.DoubleSort(
    holding_period=1,
    sort_var='ME', sort_var2='BtM',
    num_portfolios=2, num_portfolios2=3,
    breakpoints=[50], breakpoints2=[30, 70],
    how='unconditional',
    rebalance_frequency='annual', rebalance_month=7,
    breakpoint_universe_func=nyse_filter,
    breakpoint_universe_func2=nyse_filter,
)

result = pbl.StrategyFormation(
    merged, strategy=strategy,
    rating=None, dynamic_weights=True,  # <-- buy-and-hold weights like WRDS
    turnover=True, verbose=True,
    chars=['NYSE'],
).fit(IDvar='permno', RETvar='ret', VWvar='VW', RATINGvar='RATING_NUM')

# ---- Step 14: Extract factors ----
ew_ptf, vw_ptf = result.get_ptf()
print(f"\nPortfolio columns: {list(vw_ptf.columns)}")

small_cols = [c for c in vw_ptf.columns if c.startswith('ME1')]
big_cols = [c for c in vw_ptf.columns if c.startswith('ME2')]
ew_smb = ew_ptf[small_cols].mean(axis=1) - ew_ptf[big_cols].mean(axis=1)
vw_smb = vw_ptf[small_cols].mean(axis=1) - vw_ptf[big_cols].mean(axis=1)

high_cols = [c for c in vw_ptf.columns if 'BTM3' in c]
low_cols = [c for c in vw_ptf.columns if 'BTM1' in c]
ew_hml = ew_ptf[high_cols].mean(axis=1) - ew_ptf[low_cols].mean(axis=1)
vw_hml = vw_ptf[high_cols].mean(axis=1) - vw_ptf[low_cols].mean(axis=1)

print(f"\nSMB (VW): mean={vw_smb.mean()*1200:.2f}% ann, std={vw_smb.std()*np.sqrt(12)*100:.2f}%")
print(f"HML (VW): mean={vw_hml.mean()*1200:.2f}% ann, std={vw_hml.std()*np.sqrt(12)*100:.2f}%")

# ---- Step 15: Compare with official ----
smb_df = pd.DataFrame({'SMB_pbl': vw_smb}, index=vw_ptf.index)
smb_df.index = smb_df.index + MonthEnd(0)
hml_df = pd.DataFrame({'HML_pbl': vw_hml}, index=vw_ptf.index)
hml_df.index = hml_df.index + MonthEnd(0)

comp_smb = smb_df.join(_ff.set_index('date')['smb'], how='inner')
comp_hml = hml_df.join(_ff.set_index('date')['hml'], how='inner')

corr_smb = comp_smb['SMB_pbl'].corr(comp_smb['smb'].astype(float))
corr_hml = comp_hml['HML_pbl'].corr(comp_hml['hml'].astype(float))

print(f"\nSMB correlation with official: {corr_smb:.4f}")
print(f"HML correlation with official: {corr_hml:.4f}")

# Compare with previous (non-aligned) results
print("\n--- Improvement over baseline ---")
print(f"SMB: 0.9743 -> {corr_smb:.4f} ({'+'if corr_smb > 0.9743 else ''}{(corr_smb - 0.9743)*100:.2f}pp)")
print(f"HML: 0.9139 -> {corr_hml:.4f} ({'+'if corr_hml > 0.9139 else ''}{(corr_hml - 0.9139)*100:.2f}pp)")

# ---- Step 16: Save via ResultsReporter ----
custom_factors = {
    'SMB': (ew_smb, vw_smb),
    'HML': (ew_hml, vw_hml),
}
custom_factor_legs = {
    'SMB': (small_cols, big_cols),
    'HML': (high_cols, low_cols),
}
report_path = ResultsReporter(
    result, mnemonic='ff3_equity_aligned',
    script_path=os.path.abspath(__file__),
    labels={'ME': 'Size (ME)', 'BtM': 'Book-to-Market'},
    custom_factors=custom_factors,
    custom_factor_legs=custom_factor_legs,
).generate()
print(f"\nReport saved to: {report_path}")
print("\n=== DONE ===")
