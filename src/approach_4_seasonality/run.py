import pandas as pd
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import WeekdayLocator, MO, WE, FR
from matplotlib.ticker import FuncFormatter
import os
import warnings

warnings.filterwarnings('ignore')

CANDIDATE_PERIODS = [7, 14, 30, 60, 91]
PERIOD_LABELS = {7: 'weekly', 14: 'biweekly', 30: 'monthly', 60: 'bimonthly', 91: 'quarterly'}
MIN_ACTIVE_DAYS = 30


def compute_acf(series, max_lag):
    """Normalized autocorrelation function via direct computation."""
    n = len(series)
    mean = series.mean()
    var = series.var()
    if var < 1e-10:
        return np.zeros(max_lag + 1)
    centered = series - mean
    full = np.correlate(centered, centered, mode='full')
    acf = full[n - 1:n + max_lag]
    acf /= var * n
    return acf


def seasonality_strength(ts_values):
    """
    Measure seasonality strength combining autocorrelation at known lags
    with spectral concentration from a periodogram.

    Returns dict with score, best period, per-lag ACF, and spectral ratio.
    """
    n = len(ts_values)
    if n < MIN_ACTIVE_DAYS or np.std(ts_values) < 1e-10:
        return dict(score=0.0, best_period=None, acf_at_lags={}, spectral_ratio=0.0)

    max_lag = min(n // 2, max(CANDIDATE_PERIODS) + 5)
    acf = compute_acf(ts_values, max_lag)

    acf_at_lags = {}
    for p in CANDIDATE_PERIODS:
        if p < max_lag:
            acf_at_lags[p] = float(acf[p])

    best_period = max(acf_at_lags, key=acf_at_lags.get) if acf_at_lags else None
    best_acf = acf_at_lags[best_period] if best_period else 0.0

    freqs, psd = signal.periodogram(ts_values - np.mean(ts_values))
    total_power = np.sum(psd)

    if total_power < 1e-10:
        return dict(score=0.0, best_period=best_period, acf_at_lags=acf_at_lags, spectral_ratio=0.0)

    best_spectral = 0.0
    window = max(1, len(freqs) // 100)
    for p in CANDIDATE_PERIODS:
        target_freq = 1.0 / p
        idx = np.argmin(np.abs(freqs - target_freq))
        lo, hi = max(0, idx - window), min(len(freqs), idx + window + 1)
        ratio = np.sum(psd[lo:hi]) / total_power
        best_spectral = max(best_spectral, ratio)

    score = 0.6 * max(best_acf, 0) + 0.4 * best_spectral
    return dict(score=score, best_period=best_period, acf_at_lags=acf_at_lags, spectral_ratio=best_spectral)


def main():
    print("Loading data...")
    merchants = pd.read_csv('../../data/dstakehome_merchants.csv')
    payments = pd.read_excel('../../data/dstakehome_payments.xlsx')

    payments['merchant'] = payments['merchant'].astype(str)
    payments['date'] = pd.to_datetime(payments['date'])
    merchants['merchant'] = merchants['merchant'].astype(str)

    pay_agg = payments.groupby('merchant').agg(
        subscription_volume=('subscription_volume', 'sum'),
        checkout_volume=('checkout_volume', 'sum'),
        payment_link_volume=('payment_link_volume', 'sum'),
        total_volume=('total_volume', 'sum'),
        active_days=('date', 'nunique')
    ).reset_index()

    df = pd.merge(merchants, pay_agg, on='merchant', how='inner')

    non_subs = df[(df['subscription_volume'] == 0) & (df['active_days'] >= MIN_ACTIVE_DAYS)].copy()
    print(f"Analyzing {len(non_subs)} non-subscribers with {MIN_ACTIVE_DAYS}+ active days...")

    date_range = pd.date_range(payments['date'].min(), payments['date'].max(), freq='D')
    rows = []

    for i, (_, mrow) in enumerate(non_subs.iterrows()):
        mid = mrow['merchant']
        m_pay = payments[payments['merchant'] == mid][['date', 'checkout_volume', 'payment_link_volume']]
        m_ts = m_pay.set_index('date').reindex(date_range, fill_value=0)
        combined = (m_ts['checkout_volume'] + m_ts['payment_link_volume']).values.astype(float)

        res = seasonality_strength(combined)
        rows.append({
            'merchant': mid,
            'seasonality_score': res['score'],
            'best_period_days': res['best_period'],
            'best_acf': max(res['acf_at_lags'].values(), default=0),
            'spectral_ratio': res['spectral_ratio'],
            'acf_7': res['acf_at_lags'].get(7, 0),
            'acf_14': res['acf_at_lags'].get(14, 0),
            'acf_30': res['acf_at_lags'].get(30, 0),
            'acf_60': res['acf_at_lags'].get(60, 0),
            'acf_91': res['acf_at_lags'].get(91, 0),
        })
        if (i + 1) % 500 == 0:
            print(f"  Processed {i + 1}/{len(non_subs)} merchants...")

    results_df = pd.DataFrame(rows)
    scored = pd.merge(non_subs, results_df, on='merchant', how='inner')
    scored = scored.sort_values('seasonality_score', ascending=False)
    scored['cycle_type'] = scored['best_period_days'].map(PERIOD_LABELS).fillna('other')

    top_candidates = scored.head(500)
    output_path = 'results.csv'
    top_candidates.to_csv(output_path, index=False)

    print(f"\nSaved {len(top_candidates)} candidates to {output_path}")
    print(f"Score range: {top_candidates['seasonality_score'].min():.4f} – "
          f"{top_candidates['seasonality_score'].max():.4f} "
          f"(median {top_candidates['seasonality_score'].median():.4f})")
    print(f"\nCycle type breakdown:\n{top_candidates['cycle_type'].value_counts().to_string()}")

    print("\nGenerating visualizations for top seasonal merchants...")
    plot_top_seasonal(payments, scored, date_range, n=10)
    print("Done.")


def plot_top_seasonal(payments, scored, date_range, n=10):
    """Produce visualizations for merchants with the strongest seasonality."""
    os.makedirs('plots', exist_ok=True)
    top = scored.head(n)

    # ---- Grid overview: time series + ACF side-by-side ----
    fig, axes = plt.subplots(n, 2, figsize=(18, 3 * n))
    if n == 1:
        axes = axes.reshape(1, -1)

    for idx, (_, row) in enumerate(top.iterrows()):
        mid = row['merchant']
        m_ts = _merchant_ts(payments, mid, date_range)
        combined = m_ts['checkout_volume'] + m_ts['payment_link_volume']

        period = int(row['best_period_days']) if pd.notna(row['best_period_days']) else 7
        rolling = combined.rolling(window=period, center=True).mean()

        ax_ts = axes[idx, 0]
        ax_ts.plot(date_range, combined.values, lw=0.8, color='#2563eb', alpha=0.6)
        ax_ts.plot(date_range, rolling.values, lw=2, color='#dc2626', alpha=0.85)
        ax_ts.set_title(
            f"Merchant {mid}  |  {row['cycle_type']} ({period}d)  |  "
            f"score {row['seasonality_score']:.3f}", fontsize=10)
        ax_ts.set_ylabel('Volume (cents)')
        _setup_weekday_axis(ax_ts, date_range)

        ax_acf = axes[idx, 1]
        _plot_acf_bar(combined.values, ax_acf)

    plt.tight_layout()
    fig.savefig('plots/top_seasonal_merchants.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("  Saved plots/top_seasonal_merchants.png")

    # ---- Detailed 3-panel plots for top 5 ----
    for rank, (_, row) in enumerate(top.head(5).iterrows(), start=1):
        mid = row['merchant']
        m_ts = _merchant_ts(payments, mid, date_range)
        combined = m_ts['checkout_volume'] + m_ts['payment_link_volume']
        period = int(row['best_period_days']) if pd.notna(row['best_period_days']) else 7

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))
        fig.suptitle(
            f"Seasonality Deep-Dive: Merchant {mid}  "
            f"({row['cycle_type']}, score={row['seasonality_score']:.3f})",
            fontsize=13, fontweight='bold')

        # Panel 1 – time series
        ax1.plot(date_range, combined.values, lw=0.7, alpha=0.55, color='#2563eb', label='Daily volume')
        rolling = combined.rolling(window=period, center=True).mean()
        ax1.plot(date_range, rolling.values, lw=2, color='#dc2626',
                 label=f'{period}-day rolling avg')
        ax1.set_ylabel('Volume (cents)')
        ax1.legend(loc='upper right')
        _setup_weekday_axis(ax1, date_range)
        ax1.set_title('Non-Subscription Volume (Checkout + Payment Links)')

        # Panel 2 – ACF
        _plot_acf_bar(combined.values, ax2, highlight=True)
        ax2.set_title('Autocorrelation Function (red bars = seasonal reference lags)')

        # Panel 3 – periodogram
        freqs, psd = signal.periodogram(combined.values - combined.mean())
        periods_arr = np.zeros_like(freqs)
        periods_arr[1:] = 1.0 / freqs[1:]
        mask = (periods_arr >= 3) & (periods_arr <= 120)
        ax3.plot(periods_arr[mask], psd[mask], color='#6366f1', lw=1.0)
        ax3.set_xlabel('Period (days)')
        ax3.set_ylabel('Power Spectral Density')
        ax3.set_title('Periodogram')
        for p, label in PERIOD_LABELS.items():
            ax3.axvline(x=p, color='#dc2626', ls='--', alpha=0.4)
            ax3.text(p, ax3.get_ylim()[1] * 0.9, label.capitalize(),
                     ha='center', fontsize=8, color='#dc2626', rotation=45)

        plt.tight_layout()
        fig.savefig(f'plots/merchant_{rank}_detail.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved plots/merchant_{rank}_detail.png")

    # ---- Cycle-type distribution bar chart ----
    strong = scored[scored['seasonality_score'] > 0.1]
    if len(strong) > 0:
        fig, ax = plt.subplots(figsize=(8, 5))
        palette = ['#2563eb', '#dc2626', '#16a34a', '#f59e0b', '#6366f1']
        counts = strong['cycle_type'].value_counts()
        counts.plot(kind='bar', ax=ax, color=palette[:len(counts)])
        ax.set_title('Dominant Cycle Types Among Seasonal Merchants (score > 0.1)')
        ax.set_ylabel('Number of Merchants')
        ax.set_xlabel('Cycle Type')
        plt.xticks(rotation=0)
        plt.tight_layout()
        fig.savefig('plots/cycle_distribution.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print("  Saved plots/cycle_distribution.png")


# ---- helpers ----

_DOW_LABEL = {0: 'M', 2: 'W', 4: 'F'}


def _setup_weekday_axis(ax, date_range):
    """Configure x-axis with M/W/F tick marks and start/end date labels only."""
    ax.xaxis.set_major_locator(WeekdayLocator(byweekday=[MO, WE, FR]))
    ax.xaxis.set_major_formatter(FuncFormatter(
        lambda x, _: _DOW_LABEL.get(mdates.num2date(x).weekday(), '')))
    ax.tick_params(axis='x', labelsize=4, rotation=0, pad=1, length=2)
    ax.xaxis.set_minor_locator(plt.NullLocator())

    start_str = date_range[0].strftime('%b %d, %Y')
    end_str = date_range[-1].strftime('%b %d, %Y')
    ax.text(0.0, -0.08, start_str, transform=ax.transAxes,
            fontsize=7, ha='left', color='#555')
    ax.text(1.0, -0.08, end_str, transform=ax.transAxes,
            fontsize=7, ha='right', color='#555')


def _merchant_ts(payments, merchant_id, date_range):
    """Return a daily-reindexed DataFrame for one merchant."""
    m = payments[payments['merchant'] == merchant_id][['date', 'checkout_volume', 'payment_link_volume']]
    return m.set_index('date').reindex(date_range, fill_value=0)


def _plot_acf_bar(values, ax, highlight=False):
    """Draw an ACF bar chart with seasonal reference lines."""
    max_lag = min(len(values) // 2, 120)
    acf = compute_acf(values, max_lag)
    lags = np.arange(max_lag + 1)
    if highlight:
        colors = ['#dc2626' if l in CANDIDATE_PERIODS else '#6366f1' for l in lags]
    else:
        colors = '#6366f1'
    ax.bar(lags, acf, width=1.0, color=colors, alpha=0.7)
    for p, label in [(7, 'W'), (14, '2W'), (30, 'M'), (60, '2M'), (91, 'Q')]:
        if p < max_lag:
            ax.axvline(x=p, color='#dc2626', ls='--', alpha=0.5, lw=0.8)
            ax.text(p, ax.get_ylim()[1] * 0.95, label, ha='center', fontsize=7, color='#dc2626')
    conf = 1.96 / np.sqrt(len(values))
    ax.axhline(y=conf, color='gray', ls=':', alpha=0.5)
    ax.axhline(y=-conf, color='gray', ls=':', alpha=0.5)
    ax.set_xlabel('Lag (days)')
    ax.set_ylabel('ACF')

    from matplotlib.ticker import MultipleLocator
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.set_xlim(-0.5, max_lag + 0.5)
    ax.tick_params(axis='x', labelsize=6, rotation=90)


if __name__ == '__main__':
    main()
