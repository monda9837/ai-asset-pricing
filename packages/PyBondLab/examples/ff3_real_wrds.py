"""Real FF3 SMB + HML replication with WRDS equity data."""

import pandas as pd
import numpy as np
import psycopg2
import PyBondLab as pbl
from PyBondLab.report import ResultsReporter
from pandas.tseries.offsets import MonthEnd
import os

SCRIPT = """Real FF3 SMB + HML replication with WRDS equity data"""

# ---- Step 1: Download data from WRDS ----
print("Connecting to WRDS via psycopg2...")
# On Windows, psycopg2 needs PGSERVICEFILE set explicitly
if os.name == 'nt' and not os.environ.get('PGSERVICEFILE'):
    pg_service = os.path.expanduser('~/.pg_service.conf')
    if os.path.exists(pg_service):
        os.environ['PGSERVICEFILE'] = pg_service
conn = psycopg2.connect("service=wrds")

# Download Fama-French factors for comparison
print("Downloading official FF factors...")
_ff = pd.read_sql("SELECT date, smb, hml FROM ff.factors_monthly", conn)
_ff['date'] = pd.to_datetime(_ff['date']) + MonthEnd(0)

# Download CRSP monthly data
print("Downloading CRSP monthly data (this takes a few minutes)...")
crsp_query = """
SELECT a.permno, a.date, a.ret, a.retx, a.shrout, a.prc,
       b.shrcd, b.exchcd,
       a.cfacpr, a.cfacshr
FROM crsp.msf AS a
JOIN crsp.msenames AS b ON a.permno = b.permno
    AND a.date >= b.namedt AND a.date <= b.nameendt
    AND b.exchcd BETWEEN 1 AND 3
    AND b.shrcd IN (10, 11)
WHERE a.date >= '1960-01-01' AND a.date <= '2024-12-31'
"""
crsp = pd.read_sql(crsp_query, conn)
print(f"CRSP: {len(crsp)} rows, {crsp['permno'].nunique()} permnos")

# Download delisting returns
print("Downloading delisting returns...")
dlret_query = """
SELECT permno, dlstdt, dlret, dlstcd
FROM crsp.msedelist
WHERE dlstdt >= '1960-01-01'
"""
dlret = pd.read_sql(dlret_query, conn)

# Download Compustat annual
print("Downloading Compustat annual fundamentals...")
comp_query = """
SELECT gvkey, datadate, at, pstkl, txditc, pstkrv, seq, pstk, ceq, lt
FROM comp.funda
WHERE indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'
AND datadate >= '1959-01-01'
"""
comp = pd.read_sql(comp_query, conn)

# Download CCM linking table
print("Downloading CCM link table...")
ccm_query = """
SELECT gvkey, lpermno AS permno, linkdt, linkenddt, linktype, linkprim
FROM crsp.ccmxpf_lnkhist
WHERE linktype IN ('LU', 'LC')
AND linkprim IN ('P', 'C')
"""
ccm = pd.read_sql(ccm_query, conn)

conn.close()
print("WRDS download complete.")

# ---- Step 2: Process CRSP ----
print("\nProcessing CRSP data...")
crsp['date'] = pd.to_datetime(crsp['date'])
crsp['date'] = crsp['date'] + MonthEnd(0)

# Market equity
crsp['me'] = np.abs(crsp['prc']) * crsp['shrout'] / 1000  # in millions

# Adjust for delistings
dlret['dlstdt'] = pd.to_datetime(dlret['dlstdt']) + MonthEnd(0)
dlret = dlret.rename(columns={'dlstdt': 'date'})
crsp = crsp.merge(dlret[['permno', 'date', 'dlret']], on=['permno', 'date'], how='left')
crsp['ret'] = crsp['ret'].fillna(0) + crsp['dlret'].fillna(0)

# Keep exchcd and shrcd for breakpoint filtering
crsp['EXCHCD'] = crsp['exchcd']
crsp['SHRCD'] = crsp['shrcd']

# Year-month identifiers
crsp['year'] = crsp['date'].dt.year
crsp['month'] = crsp['date'].dt.month

# June ME for size sorting
june = crsp[crsp['month'] == 6][['permno', 'year', 'me']].rename(columns={'me': 'ME_june'})
crsp = crsp.merge(june, on=['permno', 'year'], how='left')
# Forward fill June ME for July-May
crsp['ME_june'] = crsp.groupby('permno')['ME_june'].ffill()

print(f"CRSP processed: {len(crsp)} rows")

# ---- Step 3: Process Compustat ----
print("\nProcessing Compustat...")
comp['datadate'] = pd.to_datetime(comp['datadate'])
comp['year'] = comp['datadate'].dt.year

# Book equity = SEQ + TXDITC - PS (preferred stock)
comp['ps'] = comp['pstkrv'].fillna(comp['pstkl']).fillna(comp['pstk']).fillna(0)
comp['be'] = comp['seq'].fillna(comp['ceq'].fillna(comp['at'] - comp['lt'])) + comp['txditc'].fillna(0) - comp['ps']
comp = comp[comp['be'] > 0]  # Require positive book equity
comp = comp[['gvkey', 'datadate', 'year', 'be']]
comp = comp.sort_values(['gvkey', 'datadate']).drop_duplicates(subset=['gvkey', 'year'], keep='last')

# ---- Step 4: CCM merge ----
print("Merging CRSP-Compustat via CCM...")
ccm['linkdt'] = pd.to_datetime(ccm['linkdt'])
ccm['linkenddt'] = pd.to_datetime(ccm['linkenddt']).fillna(pd.Timestamp('2099-12-31'))

# Merge comp with CCM
comp_ccm = comp.merge(ccm, on='gvkey', how='inner')
comp_ccm = comp_ccm[(comp_ccm['datadate'] >= comp_ccm['linkdt']) & (comp_ccm['datadate'] <= comp_ccm['linkenddt'])]

# Add Compustat BE to CRSP (lagged: fiscal year t-1 matched to July t through June t+1)
comp_ccm['jyear'] = comp_ccm['year'] + 1  # lag by 1 year
crsp['jyear'] = crsp['year']
# For months July-Dec, use current year's jyear; for Jan-June, use previous year
crsp.loc[crsp['month'] <= 6, 'jyear'] = crsp.loc[crsp['month'] <= 6, 'year'] - 1

merged = crsp.merge(comp_ccm[['permno', 'jyear', 'be']], on=['permno', 'jyear'], how='left')

# Book-to-market
merged['BtM'] = merged['be'] / merged['ME_june']
merged.loc[merged['BtM'] <= 0, 'BtM'] = np.nan

# Final filters
merged = merged.dropna(subset=['ret', 'me'])
merged = merged[merged['date'] >= '1963-07-01']  # Standard FF start

# Deduplicate: keep one obs per permno-date (multiple matches from CCM)
merged = merged.sort_values(['permno', 'date', 'be'], ascending=[True, True, False])
merged = merged.drop_duplicates(subset=['permno', 'date'], keep='first')

# Convert all numeric columns to standard numpy dtypes (WRDS returns nullable types)
for col in merged.select_dtypes(include=['Float64', 'Float32', 'Int64', 'Int32', 'Int16']).columns:
    merged[col] = merged[col].astype('float64')

# PyBondLab requirements
merged['RATING_NUM'] = 1.0  # Dummy for equity (float64 for numba)
merged['VW'] = merged['me'].astype('float64')  # VW weights

# Copy ME for sorting (VWvar consumption!)
merged['ME'] = merged['ME_june'].astype('float64')
merged['ret'] = merged['ret'].astype('float64')
merged['BtM'] = merged['BtM'].astype('float64')

# Pre-compute NYSE breakpoint mask as a column (PyBondLab only carries required_cols)
merged['NYSE'] = (
    (merged['exchcd'] == 1) &
    (merged['BtM'] > 0) &
    (merged['ME'] > 0) &
    (merged['shrcd'].isin([10, 11]))
).astype(float)

print(f"Final merged: {len(merged)} rows, {merged['permno'].nunique()} permnos")
print(f"Date range: {merged['date'].min()} to {merged['date'].max()}")
print(f"NYSE breakpoint universe: {merged['NYSE'].sum():.0f} obs ({merged['NYSE'].mean()*100:.1f}%)")

# ---- Step 5: FF3 strategy ----
print("\nRunning FF3 DoubleSort...")

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
    rating=None, dynamic_weights=False, turnover=True, verbose=True,
    chars=['NYSE'],  # carry NYSE column through so breakpoint_universe_func can access it
).fit(IDvar='permno', RETvar='ret', VWvar='VW', RATINGvar='RATING_NUM')

# ---- Step 6: Extract and construct factors ----
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

# Compare with official FF (VW is the standard comparison)
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

# ---- Step 7: Save via ResultsReporter ----
custom_factors = {
    'SMB': (ew_smb, vw_smb),
    'HML': (ew_hml, vw_hml),
}
custom_factor_legs = {
    'SMB': (small_cols, big_cols),    # long small, short big
    'HML': (high_cols, low_cols),     # long high BtM, short low BtM
}
report_path = ResultsReporter(
    result, mnemonic='ff3_equity_real_2x3',
    script_path=os.path.abspath(__file__),
    labels={'ME': 'Size (ME)', 'BtM': 'Book-to-Market'},
    custom_factors=custom_factors,
    custom_factor_legs=custom_factor_legs,
).generate()
print(f"\nReport saved to: {report_path}")
print("\n=== DONE ===")
