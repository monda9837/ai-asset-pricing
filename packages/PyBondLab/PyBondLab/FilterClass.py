# -*- coding: utf-8 -*-
"""
FilterClass.py -- Return adjustment filters for data uncertainty analysis.

Applies trimming, winsorizing, price filtering, and bounce filtering to bond
returns. Each filter creates a ``ret_{adj}`` column (e.g. ``ret_trim``) with
adjusted values; the original ``ret`` column is never modified.

Entry points: Filter.apply_filters()
Internal: _trimming(), _pricefilter(), _bounce(), _winsorizing(), _winsorizing_ep()
Dependencies: numpy, pandas
Docs: docs/DataUncertaintyAnalysis_README.md

@authors: Giulio Rossetti & Alex Dickerson
"""
import numpy as np
import pandas as pd

# @entrypoint
# @see:docs/DataUncertaintyAnalysis_README.md
class Filter:
    """
    Filter class for applying various data filtering and adjustment techniques.
    
    Supports trimming, winsorizing, price filtering, and bounce filtering.
    
    Parameters
    ----------
    data : pd.DataFrame
        Input data containing at least 'ret', 'date', 'ID' columns
    adj : str
        Adjustment method: 'trim', 'wins', 'price', or 'bounce'
    w : Union[float, List[float]]
        Threshold parameter(s) for filtering
    loc : str
        Location parameter for winsorizing: 'both', 'left', or 'right'
    percentile_breakpoints : Optional[pd.DataFrame]
        Pre-calculated percentile breakpoints for winsorizing
    price_threshold : Optional[float]
        Reference threshold for price filtering
    """
    # @internal
    def __init__(self, data, adj, w, loc, percentile_breakpoints=None, price_threshold=None):
        self.data = data
        self.adj = adj
        self.w = w
        self.loc = loc
        self.percentile_breakpoints = percentile_breakpoints
        self.price_threshold = price_threshold

        # Build a unique suffix for the filter column name, e.g. "_trim_0.2" or "_wins_99_both"
        if isinstance(self.w, list) and len(self.w) == 2:
            lower_bound, upper_bound = w
            self.name_filt = f"_{self.adj}_{str(round(lower_bound,3))}_{str(round(upper_bound,3))}"
        else:
            self.name_filt = f"_{self.adj}_{str(round(self.w,3))}"

        if self.loc:
            self.name_filt += f"_{self.loc}"

    # @entrypoint
    def apply_filters(self):
        """Apply the configured filter and create a ``ret_{adj}`` column.

        Dispatches to the appropriate internal method based on ``self.adj``.
        For winsorizing, both ex-ante (``_winsorizing``, no look-ahead) and
        ex-post (``_winsorizing_ep``, global percentiles) are computed.

        Returns
        -------
        pd.DataFrame
            The input DataFrame with an added ``ret_{adj}`` column
            (e.g. ``ret_trim``, ``ret_price``, ``ret_bounce``, ``ret_wins``).
            Original ``ret`` column is never modified.
        """
        if self.adj == 'trim':
            self._trimming(self.w)
        elif self.adj == 'price':
            self._pricefilter(self.w)
        elif self.adj == 'wins':
            # Ex-post (global percentiles) computed first for reference
            self.data_winsorized_ex_post = self._winsorizing_ep(self.data.copy(),self.w)
            # Ex-ante (rolling historical percentiles) is the primary output
            self._winsorizing(self.w)
        elif self.adj == 'bounce':
            self._bounce(self.w)
        return self.data
    
    # @internal
    # @called-by:Filter._winsorizing
    def _ex_ante_wins_threshold(self, w):
        """Compute ex-ante (rolling historical) winsorization thresholds.

        For each date t, thresholds are computed from all returns BEFORE date t,
        avoiding look-ahead bias.  If ``percentile_breakpoints`` were pre-computed
        externally, those are used instead (faster for repeated calls).

        Parameters
        ----------
        w : float
            Percentile level (e.g. 99 for 99th percentile).

        Returns
        -------
        pd.DataFrame
            Columns: ``date``, upper bound (``w``), lower bound (``100 - w``).
        """
        if self.percentile_breakpoints is not None:
            df_d = self.percentile_breakpoints.loc[:, [str(round(w, 4)), str(round(100 - w, 4))]]
        else:
            data_w = self.data.copy()
            data_w.sort_values(by='date', inplace=True)
            df_d = pd.DataFrame(index=data_w['date'].unique(), columns=[w, 100 - w])
            for current_date in data_w['date'].unique():
                # Strictly historical: only returns before current_date (no look-ahead)
                pooled_data = data_w[data_w['date'] < current_date]['ret']
                lb = np.nanpercentile(pooled_data, 100 - w)
                ub = np.nanpercentile(pooled_data, w)
                df_d.loc[current_date, w] = ub
                df_d.loc[current_date, 100 - w] = lb
        df_d.reset_index(inplace=True)
        df_d.rename({'index': 'date'}, axis=1, inplace=True)
        self.winz_threshold_ex_ante = df_d
        return df_d

    # @internal
    # @called-by:Filter.apply_filters
    def _trimming(self, w):
        """Set extreme returns to NaN (trim filter).

        Parameters
        ----------
        w : float or list of [lower, upper]
            If float >= 0: trim right tail (ret > w -> NaN).
            If float < 0: trim left tail (ret < w -> NaN).
            If [lower, upper]: trim both tails.

        Side Effects
        ------------
        Creates ``self.data['ret_trim']`` column.
        """
        adj = 'trim'
        if isinstance(w, list) and len(w) == 2:
            lower_bound, upper_bound = w
            self.data[f"ret_{adj}"] = np.where((self.data['ret'] > upper_bound) | (self.data['ret'] < lower_bound), np.nan, self.data['ret'])
        elif w >= 0:
            self.data[f"ret_{adj}"] = np.where(self.data['ret'] > w, np.nan, self.data['ret'])
        else:
            self.data[f"ret_{adj}"] = np.where(self.data['ret'] < w, np.nan, self.data['ret'])
        self.data[f"ret_{adj}"] = pd.to_numeric(self.data[f"ret_{adj}"])

    # @internal
    # @called-by:Filter.apply_filters
    def _pricefilter(self, w):
        """Exclude bonds by price level (price filter).

        Uses the ``PRICE`` column to filter. Direction is inferred from
        ``self.price_threshold``: if w >= threshold, exclude high-priced bonds
        (right tail); if w < threshold, exclude low-priced bonds (left tail).

        Parameters
        ----------
        w : float or list of [lower, upper]
            If float >= price_threshold: exclude PRICE > w (right tail).
            If float < price_threshold: exclude PRICE < w (left tail).
            If [lower, upper]: exclude outside range.

        Side Effects
        ------------
        Creates ``self.data['ret_price']`` column. Returns are set to NaN
        for bonds whose PRICE falls outside the accepted range.
        """
        adj = 'price'
        if isinstance(w, list) and len(w) == 2:
            lower_bound, upper_bound = w
            self.data[f"ret_{adj}"] = np.where((self.data['PRICE'] > upper_bound) | (self.data['PRICE'] < lower_bound), np.nan, self.data['ret'])
        elif w >= self.price_threshold:
            self.data[f"ret_{adj}"] = np.where(self.data['PRICE'] > w, np.nan, self.data['ret'])
        else:
            self.data[f"ret_{adj}"] = np.where(self.data['PRICE'] < w, np.nan, self.data['ret'])

    # @internal
    # @called-by:Filter.apply_filters
    def _bounce(self, w):
        """Exclude return reversals / continuations (bounce filter).

        Computes ``bounce = ret_{t-1} * ret_t`` for each bond. Positive bounce
        means same-direction consecutive returns; negative means reversal.

        Parameters
        ----------
        w : float or list of [lower, upper]
            If float >= 0: exclude positive bounce > w (same-direction).
            If float < 0: exclude negative bounce < w (reversals).
            If [lower, upper]: exclude outside range.

        Side Effects
        ------------
        Creates ``self.data['ret_bounce']``, ``self.data['ret_LAG']``,
        and ``self.data['bounce']`` columns.
        """
        adj = 'bounce'
        self.data['ret_LAG'] = self.data.groupby("ID", observed=False)['ret'].shift(1)
        # bounce > 0 means consecutive same-sign returns (continuation)
        # bounce < 0 means sign reversal between months
        self.data['bounce'] = self.data['ret_LAG'] * self.data['ret']
        if isinstance(w, list) and len(w) == 2:
            lower_bound, upper_bound = w
            self.data[f"ret_{adj}"] = np.where((self.data['bounce'] > upper_bound) | (self.data['bounce'] < lower_bound), np.nan, self.data['ret'])
        elif w >= 0:
            self.data[f"ret_{adj}"] = np.where(self.data['bounce'] > w, np.nan, self.data['ret'])
        else:
            self.data[f"ret_{adj}"] = np.where(self.data['bounce'] < w, np.nan, self.data['ret'])

    # @internal
    # @called-by:Filter.apply_filters
    # @calls:Filter._ex_ante_wins_threshold
    def _winsorizing(self, w):
        """Clip extreme returns using ex-ante (rolling historical) thresholds.

        Thresholds at each date t are derived from returns strictly before t,
        preventing look-ahead bias.  NaN returns are preserved as-is (not clipped).

        Parameters
        ----------
        w : float
            Percentile level (e.g. 99). Upper bound = w-th percentile,
            lower bound = (100 - w)-th percentile.

        Side Effects
        ------------
        Creates ``self.data['ret_wins']`` column. Merges threshold columns
        onto ``self.data``.
        """
        adj = 'wins'

        thr_ts = self._ex_ante_wins_threshold(w)
        self.data = pd.merge(self.data, thr_ts, on='date', how='left')
        if self.percentile_breakpoints is not None:
            bound_u = str(w)
            bound_d = str(round(100 - w, 4))
        else:
            bound_u = w
            bound_d = 100 - w
        # Preserve NaN returns (first np.where gate); clip non-NaN to thresholds
        if self.loc == "both":
            self.data[f"ret_{adj}"] = np.where(
                pd.isna(self.data['ret']), self.data['ret'],
                np.where(
                    self.data['ret'] > self.data[bound_u], self.data[bound_u],
                    np.where(self.data['ret'] < self.data[bound_d], self.data[bound_d], self.data['ret'])
                )
            )
        elif self.loc == "right":
            self.data[f"ret_{adj}"] = np.where(
                pd.isna(self.data['ret']), self.data['ret'],
                np.where(self.data['ret'] > self.data[bound_u], self.data[bound_u], self.data['ret'])
            )
        elif self.loc == "left":
            self.data[f"ret_{adj}"] = np.where(
                pd.isna(self.data['ret']), self.data['ret'],
                np.where(self.data['ret'] < self.data[bound_d], self.data[bound_d], self.data['ret'])
            )
        self.data[f"ret_{adj}"] = pd.to_numeric(self.data[f"ret_{adj}"])
        
    # @internal
    # @called-by:Filter.apply_filters
    def _winsorizing_ep(self, df, w):
        """Clip extreme returns using ex-post (global) percentile thresholds.

        Unlike ``_winsorizing`` (ex-ante), this uses the ENTIRE sample to compute
        thresholds -- it is look-ahead biased by design. Used as a reference
        benchmark for the ex-ante version.

        Parameters
        ----------
        df : pd.DataFrame
            Copy of the data (to avoid mutating the original).
        w : float
            Percentile level (e.g. 99).

        Returns
        -------
        pd.DataFrame
            DataFrame with added ``ret_wins`` column clipped to global thresholds.

        Notes
        -----
        Sets ``self.lb_ep`` and ``self.ub_ep`` for external access to the
        global thresholds.
        """
        adj = 'wins'
        df1 = df.copy() # redundant
        # Global thresholds from the full sample (look-ahead biased)
        self.lb_ep = np.nanpercentile(df1['ret'], 100 - w)
        self.ub_ep = np.nanpercentile(df1['ret'], w)
        if self.loc == 'both':
            df1[f"ret_{adj}"] = np.where(df1['ret'] > self.ub_ep, self.ub_ep,
                                 np.where(df1['ret'] < self.lb_ep, self.lb_ep,
                                        df1['ret']))
        if self.loc == 'right':
            df1[f"ret_{adj}"] = np.where(df1['ret'] > self.ub_ep, self.ub_ep, df1['ret'])

        if self.loc == 'left':
            df1[f"ret_{adj}"] = np.where(df1['ret'] < self.lb_ep, self.lb_ep, df1['ret'])
        return df1
    
