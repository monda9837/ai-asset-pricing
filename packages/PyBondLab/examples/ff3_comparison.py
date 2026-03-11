"""FF3 Factor Comparison: Official vs PBL Original vs PBL Aligned vs WRDS Method."""

import pandas as pd
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.tseries.offsets import MonthEnd, YearEnd
from scipy import stats
from pathlib import Path
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

# ---- Config ----
OUT_DIR = Path("results") / f"ff3_comparison_{datetime.now().strftime('%Y_%m_%d')}"
OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "figures").mkdir(exist_ok=True)
(OUT_DIR / "tables").mkdir(exist_ok=True)

# Colors
C_OFFICIAL = '#d62728'   # red
C_PBL_ORIG = '#1f77b4'   # blue
C_PBL_ALIGN = '#ff7f0e'  # orange
C_WRDS = '#2ca02c'       # green

METHODS_COLORS = [
    ('Official', C_OFFICIAL, '--', 1.5),
    ('PBL Original', C_PBL_ORIG, '-', 1.5),
    ('PBL Aligned', C_PBL_ALIGN, '-', 1.5),
    ('WRDS Method', C_WRDS, ':', 1.8),
]

# WRDS connection
if os.name == 'nt' and not os.environ.get('PGSERVICEFILE'):
    pg_service = os.path.expanduser('~/.pg_service.conf')
    if os.path.exists(pg_service):
        os.environ['PGSERVICEFILE'] = pg_service

# ============================================================
# Step 1: Load Official FF Factors
# ============================================================
print("Step 1: Loading official FF factors...")
conn = psycopg2.connect("service=wrds")
_ff = pd.read_sql("SELECT date, smb, hml FROM ff.factors_monthly", conn)
_ff['date'] = pd.to_datetime(_ff['date']) + MonthEnd(0)
_ff = _ff.set_index('date').astype(float)

# ============================================================
# Step 2: Load PyBondLab Factors — Original + Aligned
# ============================================================
print("Step 2: Loading PyBondLab factors...")
pbl_orig = pd.read_csv("results/ff3_equity_real_2x3_2026_03_10/tables/factor_returns.csv",
                        index_col='date', parse_dates=True)
pbl_orig.index = pbl_orig.index + MonthEnd(0)

pbl_aligned = pd.read_csv("results/ff3_equity_aligned_2026_03_10/tables/factor_returns.csv",
                           index_col='date', parse_dates=True)
pbl_aligned.index = pbl_aligned.index + MonthEnd(0)

# ============================================================
# Step 3: Run WRDS Method (Drechsler notebook, CIZ format)
# ============================================================
print("Step 3: Running WRDS method (CIZ format)...")

# --- Compustat ---
comp = pd.read_sql("""
    SELECT gvkey, datadate, at, pstkl, txditc, pstkrv, seq, pstk
    FROM comp.funda
    WHERE indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'
    AND datadate >= '1959-01-01'
""", conn)
comp['datadate'] = pd.to_datetime(comp['datadate'])
comp['year'] = comp['datadate'].dt.year
comp['ps'] = comp['pstkrv'].fillna(comp['pstkl']).fillna(comp['pstk']).fillna(0)
comp['txditc'] = comp['txditc'].fillna(0)
comp['be'] = comp['seq'] + comp['txditc'] - comp['ps']
comp.loc[comp['be'] <= 0, 'be'] = np.nan
comp = comp.dropna(subset=['be'])
comp = comp.sort_values(['gvkey', 'datadate'])
comp['count'] = comp.groupby('gvkey').cumcount()
comp = comp[['gvkey', 'datadate', 'year', 'be', 'count']]

# --- CRSP CIZ ---
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
crsp_m = crsp_m[
    (crsp_m['sharetype'] == 'NS') & (crsp_m['securitytype'] == 'EQTY') &
    (crsp_m['securitysubtype'] == 'COM') & (crsp_m['usincflg'] == 'Y') &
    (crsp_m['issuertype'].isin(['ACOR', 'CORP']))
]
crsp_m = crsp_m[
    (crsp_m['primaryexch'].isin(['N', 'A', 'Q'])) &
    (crsp_m['conditionaltype'] == 'RW') & (crsp_m['tradingstatusflg'] == 'A')
]
crsp_m[['permco', 'permno']] = crsp_m[['permco', 'permno']].astype(int)
crsp_m['jdate'] = crsp_m['mthcaldt'] + MonthEnd(0)
crsp = crsp_m.copy()
crsp['mthret'] = crsp['mthret'].fillna(0)
crsp['mthretx'] = crsp['mthretx'].fillna(0)
crsp['me'] = crsp['mthprc'] * crsp['shrout']
crsp = crsp.sort_values(['jdate', 'permco', 'me'])

# Permco ME aggregation
crsp_summe = crsp.groupby(['jdate', 'permco'])['me'].sum().reset_index()
crsp_maxme = crsp.groupby(['jdate', 'permco'])['me'].max().reset_index()
crsp1 = crsp.merge(crsp_maxme, on=['jdate', 'permco', 'me'], how='inner')
crsp1 = crsp1.drop('me', axis=1)
crsp2 = crsp1.merge(crsp_summe, on=['jdate', 'permco'], how='inner')
crsp2 = crsp2.sort_values(['permno', 'jdate']).drop_duplicates()

crsp2['year'] = crsp2['jdate'].dt.year
crsp2['month'] = crsp2['jdate'].dt.month
decme = crsp2[crsp2['month'] == 12][['permno', 'me', 'year']].rename(columns={'me': 'dec_me'})

crsp2['ffdate'] = crsp2['jdate'] + MonthEnd(-6)
crsp2['ffyear'] = crsp2['ffdate'].dt.year
crsp2['ffmonth'] = crsp2['ffdate'].dt.month
crsp2['1+retx'] = 1 + crsp2['mthretx']
crsp2 = crsp2.sort_values(['permno', 'mthcaldt'])

crsp2['cumretx'] = crsp2.groupby(['permno', 'ffyear'])['1+retx'].cumprod()
crsp2['lcumretx'] = crsp2.groupby('permno')['cumretx'].shift(1)
crsp2['lme'] = crsp2.groupby('permno')['me'].shift(1)
crsp2['count'] = crsp2.groupby('permno').cumcount()
crsp2['lme'] = np.where(crsp2['count'] == 0, crsp2['me'] / crsp2['1+retx'], crsp2['lme'])

mebase = crsp2[crsp2['ffmonth'] == 1][['permno', 'ffyear', 'lme']].rename(columns={'lme': 'mebase'})
crsp3 = crsp2.merge(mebase, on=['permno', 'ffyear'], how='left')
crsp3['wt'] = np.where(crsp3['ffmonth'] == 1, crsp3['lme'], crsp3['mebase'] * crsp3['lcumretx'])

decme['year'] = decme['year'] + 1
crsp3_jun = crsp3[crsp3['month'] == 6]
crsp_jun = crsp3_jun.merge(decme, on=['permno', 'year'], how='inner')
crsp_jun = crsp_jun[['permno', 'mthcaldt', 'jdate', 'primaryexch',
                      'mthret', 'me', 'wt', 'cumretx', 'mebase', 'lme', 'dec_me']]
crsp_jun = crsp_jun.sort_values(['permno', 'jdate']).drop_duplicates()

# CCM
ccm = pd.read_sql("""
    SELECT gvkey, lpermno AS permno, linktype, linkprim, linkdt, linkenddt
    FROM crsp.ccmxpf_linktable
    WHERE substr(linktype,1,1)='L' AND (linkprim='C' OR linkprim='P')
""", conn)
ccm['linkdt'] = pd.to_datetime(ccm['linkdt'])
ccm['linkenddt'] = pd.to_datetime(ccm['linkenddt']).fillna(pd.Timestamp('today'))
conn.close()

ccm1 = comp.merge(ccm, on='gvkey', how='left')
ccm1['yearend'] = ccm1['datadate'] + YearEnd(0)
ccm1['jdate'] = ccm1['yearend'] + MonthEnd(6)
ccm2 = ccm1[(ccm1['jdate'] >= ccm1['linkdt']) & (ccm1['jdate'] <= ccm1['linkenddt'])]
ccm2 = ccm2[['gvkey', 'permno', 'datadate', 'yearend', 'jdate', 'be', 'count']]

ccm_jun = crsp_jun.merge(ccm2, on=['permno', 'jdate'], how='inner')
ccm_jun['beme'] = ccm_jun['be'] * 1000 / ccm_jun['dec_me']

nyse = ccm_jun[(ccm_jun['primaryexch'] == 'N') & (ccm_jun['beme'] > 0) &
               (ccm_jun['me'] > 0) & (ccm_jun['count'] >= 1)]
nyse_sz = nyse.groupby('jdate')['me'].median().reset_index().rename(columns={'me': 'sizemedn'})
nyse_bm = nyse.groupby('jdate')['beme'].describe(percentiles=[0.3, 0.7]).reset_index()
nyse_bm = nyse_bm[['jdate', '30%', '70%']].rename(columns={'30%': 'bm30', '70%': 'bm70'})
nyse_breaks = nyse_sz.merge(nyse_bm, on='jdate')
ccm1_jun = ccm_jun.merge(nyse_breaks, on='jdate', how='left')

def sz_bucket(row):
    if pd.isna(row['me']) or pd.isna(row['sizemedn']):
        return ''
    return 'S' if row['me'] <= row['sizemedn'] else 'B'

def bm_bucket(row):
    if pd.isna(row['beme']) or row['beme'] <= 0:
        return ''
    if row['beme'] <= row['bm30']:
        return 'L'
    elif row['beme'] <= row['bm70']:
        return 'M'
    else:
        return 'H'

valid = (ccm1_jun['beme'] > 0) & (ccm1_jun['me'] > 0) & (ccm1_jun['count'] >= 1)
ccm1_jun['szport'] = np.where(valid, ccm1_jun.apply(sz_bucket, axis=1), '')
ccm1_jun['bmport'] = np.where(valid, ccm1_jun.apply(bm_bucket, axis=1), '')
ccm1_jun['nonmissport'] = (ccm1_jun['bmport'] != '').astype(int)
ccm1_jun['posbm'] = valid.astype(int)

june = ccm1_jun[['permno', 'jdate', 'bmport', 'szport', 'posbm', 'nonmissport']].copy()
june['ffyear'] = june['jdate'].dt.year

crsp3_cols = ['mthcaldt', 'permno', 'primaryexch', 'mthret', 'me', 'wt', 'cumretx', 'ffyear', 'jdate']
ccm3 = crsp3[crsp3_cols].merge(
    june[['permno', 'ffyear', 'szport', 'bmport', 'posbm', 'nonmissport']],
    on=['permno', 'ffyear'], how='left')
ccm4 = ccm3[(ccm3['wt'] > 0) & (ccm3['posbm'] == 1) & (ccm3['nonmissport'] == 1)]

def wavg(group, avg_name, weight_name):
    d, w = group[avg_name], group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return np.nan

vwret = ccm4.groupby(['jdate', 'szport', 'bmport']).apply(
    wavg, 'mthret', 'wt').to_frame().reset_index().rename(columns={0: 'vwret'})
vwret['sbport'] = vwret['szport'] + vwret['bmport']

ff_factors = vwret.pivot(index='jdate', columns='sbport', values='vwret').reset_index()
ff_factors['WSMB'] = (ff_factors['SL'] + ff_factors['SM'] + ff_factors['SH']) / 3 - \
                      (ff_factors['BL'] + ff_factors['BM'] + ff_factors['BH']) / 3
ff_factors['WHML'] = (ff_factors['BH'] + ff_factors['SH']) / 2 - \
                      (ff_factors['BL'] + ff_factors['SL']) / 2
ff_factors = ff_factors.rename(columns={'jdate': 'date'}).set_index('date')

print(f"  WRDS method: {len(ff_factors)} months")

# ============================================================
# Step 4: Build Comparison DataFrame
# ============================================================
print("\nStep 4: Aligning dates...")
comp_df = pd.DataFrame({
    'SMB_official': _ff['smb'],
    'HML_official': _ff['hml'],
    'SMB_pbl_orig': pbl_orig['SMB_vw'],
    'HML_pbl_orig': pbl_orig['HML_vw'],
    'SMB_pbl_aligned': pbl_aligned['SMB_vw'],
    'HML_pbl_aligned': pbl_aligned['HML_vw'],
    'SMB_wrds': ff_factors['WSMB'],
    'HML_wrds': ff_factors['WHML'],
}).dropna()
print(f"  Common: {comp_df.index.min()} to {comp_df.index.max()}, {len(comp_df)} months")

# ============================================================
# NW t-stat helper
# ============================================================
def nw_tstat(series):
    T = len(series)
    if T < 2:
        return np.nan
    nw_lag = int(T ** 0.25)
    mean = series.mean()
    resid = series - mean
    gamma0 = (resid ** 2).sum() / T
    gamma = gamma0
    for j in range(1, nw_lag + 1):
        w = 1 - j / (nw_lag + 1)
        cov_j = (resid.iloc[j:].values * resid.iloc[:-j].values).sum() / T
        gamma += 2 * w * cov_j
    se = np.sqrt(gamma / T)
    return mean / se if se > 0 else np.nan

# ============================================================
# Step 5: Stats Table
# ============================================================
print("\nStep 5: Computing statistics...")

method_map = {
    'Official': {'SMB': 'SMB_official', 'HML': 'HML_official'},
    'PBL Original': {'SMB': 'SMB_pbl_orig', 'HML': 'HML_pbl_orig'},
    'PBL Aligned': {'SMB': 'SMB_pbl_aligned', 'HML': 'HML_pbl_aligned'},
    'WRDS Method': {'SMB': 'SMB_wrds', 'HML': 'HML_wrds'},
}

rows = []
for method, factors in method_map.items():
    for factor, col in factors.items():
        s = comp_df[col]
        ann_mean = s.mean() * 12 * 100
        t = nw_tstat(s)
        std = s.std() * np.sqrt(12) * 100
        sr = s.mean() / s.std() * np.sqrt(12) if s.std() > 0 else np.nan
        corr = s.corr(comp_df[f'{factor}_official'])
        rows.append({
            'Method': method, 'Factor': factor,
            'Mean(%)': round(ann_mean, 2), 't-stat(NW)': round(t, 2),
            'Std(%)': round(std, 2), 'SR': round(sr, 3),
            'Corr(Official)': round(corr, 4),
        })

stats_table = pd.DataFrame(rows)
stats_table.to_csv(OUT_DIR / "tables" / "comparison_stats.csv", index=False)
print(stats_table.to_string(index=False))

# Correlation matrix
all_cols = ['SMB_official', 'SMB_pbl_orig', 'SMB_pbl_aligned', 'SMB_wrds',
            'HML_official', 'HML_pbl_orig', 'HML_pbl_aligned', 'HML_wrds']
corr_matrix = comp_df[all_cols].corr()
corr_matrix.to_csv(OUT_DIR / "tables" / "correlation_matrix.csv")

# ============================================================
# Step 6: Figures
# ============================================================
print("\nStep 6: Generating figures...")
plt.rcParams.update({'font.size': 11, 'figure.facecolor': 'white'})

method_styles = {
    'official': (C_OFFICIAL, '--', 1.5, 'Ken French'),
    'pbl_orig': (C_PBL_ORIG, '-', 1.5, 'PBL Original'),
    'pbl_aligned': (C_PBL_ALIGN, '-', 1.5, 'PBL Aligned'),
    'wrds': (C_WRDS, ':', 1.8, 'WRDS Method'),
}

# --- 1. Cumulative Returns ---
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
for i, factor in enumerate(['SMB', 'HML']):
    ax = axes[i]
    for method, (color, style, lw, label) in method_styles.items():
        col = f'{factor}_{method}'
        cumret = np.log1p(comp_df[col]).cumsum()
        ax.plot(cumret.index, cumret.values, color=color, linestyle=style,
                linewidth=lw, label=label)
    ax.set_title(factor, fontsize=14, fontweight='bold')
    ax.set_ylabel('Cumulative Log Return')
    ax.legend(fontsize=9, loc='upper left')
    ax.axhline(0, color='black', linewidth=0.3)
    ax.grid(True, alpha=0.3)
axes[-1].xaxis.set_major_locator(mdates.YearLocator(10))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
fig.suptitle('Cumulative Returns: Official vs PBL (Original & Aligned) vs WRDS', fontsize=14, y=1.01)
fig.tight_layout()
fig.savefig(OUT_DIR / "figures" / "cumret_comparison.png", dpi=150, bbox_inches='tight')
plt.close()
print("  cumret_comparison.png")

# --- 2. Return Bars ---
fig, ax = plt.subplots(figsize=(12, 6))
bar_width = 0.2
x = np.arange(2)
for j, (method, factors) in enumerate(method_map.items()):
    color = [C_OFFICIAL, C_PBL_ORIG, C_PBL_ALIGN, C_WRDS][j]
    means, tstats = [], []
    for factor in ['SMB', 'HML']:
        row = stats_table[(stats_table['Method'] == method) & (stats_table['Factor'] == factor)].iloc[0]
        means.append(row['Mean(%)'])
        tstats.append(row['t-stat(NW)'])
    pos = x + (j - 1.5) * bar_width
    bars = ax.bar(pos, means, width=bar_width, color=color, alpha=0.85,
                  edgecolor='black', linewidth=0.5, label=method)
    for bar, t in zip(bars, tstats):
        y = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, y, f't={t:.2f}',
                ha='center', va='bottom', fontsize=8, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(['SMB', 'HML'], fontsize=13)
ax.set_ylabel('Annualized Mean Return (%)', fontsize=12)
ax.set_title('Annualized Mean Returns', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.axhline(0, color='black', linewidth=0.5, linestyle='--')
ax.grid(True, alpha=0.3, axis='y')
fig.tight_layout()
fig.savefig(OUT_DIR / "figures" / "return_bars.png", dpi=150, bbox_inches='tight')
plt.close()
print("  return_bars.png")

# --- 3. Sharpe Ratio Bars ---
fig, ax = plt.subplots(figsize=(12, 6))
for j, (method, factors) in enumerate(method_map.items()):
    color = [C_OFFICIAL, C_PBL_ORIG, C_PBL_ALIGN, C_WRDS][j]
    srs = []
    for factor in ['SMB', 'HML']:
        row = stats_table[(stats_table['Method'] == method) & (stats_table['Factor'] == factor)].iloc[0]
        srs.append(row['SR'])
    pos = x + (j - 1.5) * bar_width
    bars = ax.bar(pos, srs, width=bar_width, color=color, alpha=0.85,
                  edgecolor='black', linewidth=0.5, label=method)
    for bar, sr in zip(bars, srs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{sr:.3f}',
                ha='center', va='bottom', fontsize=8, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(['SMB', 'HML'], fontsize=13)
ax.set_ylabel('Sharpe Ratio', fontsize=12)
ax.set_title('Sharpe Ratio Comparison', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.axhline(0, color='black', linewidth=0.5, linestyle='--')
ax.grid(True, alpha=0.3, axis='y')
fig.tight_layout()
fig.savefig(OUT_DIR / "figures" / "sharpe_bars.png", dpi=150, bbox_inches='tight')
plt.close()
print("  sharpe_bars.png")

# --- 4 & 5. Scatter Plots ---
for factor in ['SMB', 'HML']:
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    official = comp_df[f'{factor}_official']
    for ax, (method, col, color, label) in zip(axes, [
        ('pbl_orig', f'{factor}_pbl_orig', C_PBL_ORIG, 'PBL Original'),
        ('pbl_aligned', f'{factor}_pbl_aligned', C_PBL_ALIGN, 'PBL Aligned'),
        ('wrds', f'{factor}_wrds', C_WRDS, 'WRDS Method'),
    ]):
        replica = comp_df[col]
        ax.scatter(official * 100, replica * 100, alpha=0.3, s=10, color=color)
        slope, intercept, r, p, se = stats.linregress(official, replica)
        x_line = np.linspace(official.min(), official.max(), 100)
        ax.plot(x_line * 100, (slope * x_line + intercept) * 100, 'k--', linewidth=1.2)
        lims = [min(official.min(), replica.min()) * 100,
                max(official.max(), replica.max()) * 100]
        ax.plot(lims, lims, color='gray', linewidth=0.6, linestyle=':')
        corr = official.corr(replica)
        ax.set_title(f'{label}\nCorr={corr:.4f}, R²={r**2:.4f}', fontsize=11)
        ax.set_xlabel(f'Official {factor} (%)')
        ax.set_ylabel(f'{label} {factor} (%)')
        ax.grid(True, alpha=0.3)
    fig.suptitle(f'{factor}: Scatter Comparison with Official', fontsize=14, fontweight='bold')
    fig.tight_layout()
    fig.savefig(OUT_DIR / "figures" / f"scatter_{factor.lower()}.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  scatter_{factor.lower()}.png")

# --- 6. Rolling Correlation ---
window = 60
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
for i, factor in enumerate(['SMB', 'HML']):
    ax = axes[i]
    official = comp_df[f'{factor}_official']
    for method, col, color, style, label in [
        ('pbl_orig', f'{factor}_pbl_orig', C_PBL_ORIG, '-', 'PBL Original'),
        ('pbl_aligned', f'{factor}_pbl_aligned', C_PBL_ALIGN, '-', 'PBL Aligned'),
        ('wrds', f'{factor}_wrds', C_WRDS, '--', 'WRDS Method'),
    ]:
        rc = official.rolling(window).corr(comp_df[col])
        ax.plot(rc.index, rc.values, color=color, linestyle=style, linewidth=1.2, label=label)
    ax.set_title(f'{factor}: {window}-Month Rolling Correlation with Official', fontsize=12, fontweight='bold')
    ax.set_ylabel('Correlation')
    ax.set_ylim(0.7, 1.02)
    ax.axhline(1.0, color='gray', linewidth=0.5, linestyle=':')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
axes[-1].xaxis.set_major_locator(mdates.YearLocator(10))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
fig.suptitle('Rolling Correlation with Official Ken French Factors', fontsize=14, y=1.01)
fig.tight_layout()
fig.savefig(OUT_DIR / "figures" / "rolling_corr.png", dpi=150, bbox_inches='tight')
plt.close()
print("  rolling_corr.png")

# --- 7. Correlation Bar Chart ---
fig, ax = plt.subplots(figsize=(10, 6))
methods_no_official = ['PBL Original', 'PBL Aligned', 'WRDS Method']
colors_no_official = [C_PBL_ORIG, C_PBL_ALIGN, C_WRDS]
bar_width = 0.25
x = np.arange(2)
for j, (method, color) in enumerate(zip(methods_no_official, colors_no_official)):
    corrs = []
    for factor in ['SMB', 'HML']:
        row = stats_table[(stats_table['Method'] == method) & (stats_table['Factor'] == factor)].iloc[0]
        corrs.append(row['Corr(Official)'])
    pos = x + (j - 1) * bar_width
    bars = ax.bar(pos, corrs, width=bar_width, color=color, alpha=0.85,
                  edgecolor='black', linewidth=0.5, label=method)
    for bar, c in zip(bars, corrs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{c:.4f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(['SMB', 'HML'], fontsize=13)
ax.set_ylabel('Correlation with Official', fontsize=12)
ax.set_title('Correlation with Official Ken French Factors', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.set_ylim(0.85, 1.01)
ax.grid(True, alpha=0.3, axis='y')
fig.tight_layout()
fig.savefig(OUT_DIR / "figures" / "correlation_bars.png", dpi=150, bbox_inches='tight')
plt.close()
print("  correlation_bars.png")

print(f"\n{'='*60}")
print(f"All outputs saved to: {OUT_DIR}")
print(f"{'='*60}")
