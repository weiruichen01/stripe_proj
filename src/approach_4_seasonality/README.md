# Approach 4: Seasonality Detection via Time Series Analysis

## Hypothesis

Merchants whose non-subscription revenue (Checkout + Payment Links) follows strong, recurring periodic cycles — weekly, biweekly, monthly, etc. — likely have an inherent recurring-payment need. These are prime candidates for Stripe Subscriptions because the product would formalize what is already happening organically: their customers are paying on a predictable schedule.

For example, a food-and-drink merchant whose checkout volume spikes every Monday is almost certainly serving repeat buyers. A consulting firm with a monthly invoice surge already has a de-facto subscription model — they just haven't automated it yet.

---

## Technical Implementation

### Step 1: Data Preparation

We load the same two data sources as the other approaches (`dstakehome_merchants.csv` and `dstakehome_payments.xlsx`), then:

1. **Filter to non-subscribers** — only merchants with `subscription_volume == 0` (the target audience for upselling).
2. **Require ≥ 30 active days** — seasonality detection needs enough data points; merchants with only a handful of transactions don't provide a meaningful signal. This yields **6,694 merchants** for analysis.
3. **Build a gap-filled daily time series** — for each merchant, we take their per-day Checkout + Payment Link volumes and reindex onto the full calendar date range (min to max date across the dataset), filling gaps with 0. This is critical because real transaction data has missing days (weekends, holidays, slow periods), and autocorrelation assumes evenly-spaced observations.

### Step 2: Autocorrelation Analysis (ACF)

The **autocorrelation function** measures how correlated a time series is with a lagged copy of itself. If a merchant's volume on day *t* tends to look similar to their volume on day *t − 7*, the ACF at lag 7 will be high — indicating a weekly cycle.

**How we compute it:**

1. **Compute the raw ACF** (`compute_acf`):
   - Center the series by subtracting the mean.
   - Compute the full cross-correlation of the series with itself using `numpy.correlate(centered, centered, mode='full')`, which returns a symmetric array of length *2n − 1*.
   - Slice out the non-negative lags: `full[n-1 : n+max_lag]` gives lags 0 through `max_lag`.
   - Normalize by dividing by `var × n`, so the ACF at lag 0 equals 1.0 and all other values fall in [−1, 1].

2. **Sample at candidate lags**: The ACF is evaluated at five canonical seasonal lags — **7** (weekly), **14** (biweekly), **30** (monthly), **60** (bimonthly), and **91** (quarterly) — stored in the `acf_at_lags` dictionary.

3. **Select the best**: `best_period` is the candidate lag with the highest ACF value (`max(acf_at_lags, key=acf_at_lags.get)`). `best_acf` is that maximum value — it answers *"at the strongest seasonal cadence, how correlated is this merchant's volume with its own value one cycle ago?"*

**How to read the ACF plots:**
- The x-axis is the lag in days; the y-axis is the autocorrelation coefficient (−1 to +1).
- A tall bar at lag 7 means "today's volume strongly predicts next week's volume" → weekly seasonality.
- The dashed horizontal grey lines show the **95 % confidence bound** (`±1.96 / √n`). Bars exceeding this bound are statistically significant.
- Red dashed vertical lines mark the five candidate lags (W = weekly, 2W = biweekly, M = monthly, 2M = bimonthly, Q = quarterly) for quick visual reference.

### Step 3: Scoring

Each merchant's `seasonality_score` is based purely on autocorrelation:

```
seasonality_score = max(best_acf, 0)
```

The score is the highest ACF value across the five candidate lags, clamped to ≥ 0 so that negative autocorrelation (anti-seasonal patterns) does not produce a positive score. This directly answers "does this merchant's volume repeat on a fixed schedule?" — the higher the score, the stronger the recurring pattern. Merchants are ranked by this score to identify the best Subscriptions upsell candidates.

### Step 4: Output

The top 500 merchants by `seasonality_score` are written to `results.csv`. Each row includes:

| Column | Description |
|--------|-------------|
| `merchant` … `active_days` | Standard merchant attributes (same schema as other approaches) |
| `seasonality_score` | ACF-based score (0–1 range in practice) |
| `best_period_days` | The candidate lag with the highest ACF (7, 14, 30, 60, or 91) |
| `cycle_type` | Human-readable label: weekly / biweekly / monthly / bimonthly / quarterly |
| `best_acf` | The highest ACF value across the five candidate lags |
| `acf_7` … `acf_91` | Raw ACF values at each of the five candidate lags (useful for secondary analysis) |

---

## Visualizations

All plots are saved to the `plots/` subdirectory.

### `top_seasonal_merchants.png`
A 10-row × 2-column grid showing the **top 10 merchants** by seasonality score. Left column: daily volume (blue) with a rolling average smoothed over one full period (red). Right column: ACF bar chart. This gives a quick side-by-side overview — you can immediately see which merchants have crisp repeating patterns vs. noisy ones.

### `merchant_N_detail.png` (N = 1–5)
Two-panel deep-dive for each of the **top 5 merchants**:
1. **Time series** — raw daily volume overlaid with a rolling average at the detected period length. Lets you visually confirm the recurring spikes.
2. **ACF** — bar chart with seasonal reference lags highlighted in red. The repeating pattern of tall bars at regular intervals is the hallmark of true seasonality.

### `cycle_distribution.png`
Bar chart showing how many merchants (among all those with score > 0.1) fall into each cycle type. Useful for understanding the macro distribution of seasonal behaviors in the merchant base.

---

## Results & Interpretation

### Score Distribution (Top 500)

| Metric | Value |
|--------|-------|
| Max score | 0.789 |
| Median score | 0.252 |
| Min score (500th) | 0.146 |

The long right tail suggests a small number of merchants with very strong, textbook-quality seasonality, followed by a large group with moderate-but-detectable patterns.

### Cycle Type Breakdown (Top 500)

| Cycle Type | Count | Interpretation |
|------------|-------|----------------|
| **Weekly** | 372 | The dominant pattern. These merchants see regular spikes on specific days of the week — classic for food & drink, retail, and service businesses with recurring weekly demand. |
| **Biweekly** | 95 | Likely reflects pay-cycle-aligned purchasing (many employees are paid biweekly) or businesses that invoice on a 2-week cadence. |
| **Monthly** | 21 | Consistent with businesses that bill clients on a monthly cycle — the most natural fit for a Subscriptions product. |
| **Quarterly** | 8 | Seasonal businesses or those with quarterly billing/reporting cycles. |
| **Bimonthly** | 4 | Less common; may reflect 60-day billing terms or bimonthly service contracts. |

### Top Merchant Examples

| Rank | Merchant | Industry | Country | Cycle | Score | ACF at best lag |
|------|----------|----------|---------|-------|-------|-----------------|
| 1 | `7e0cec36` | Food & drink | GB | Weekly | 0.789 | 0.881 |
| 2 | `bf59b44d` | Food & drink | BE | Weekly | 0.666 | 0.865 |
| 3 | `fd87f37b` | Food & drink | GB | Weekly | 0.644 | 0.747 |
| 4 | `83a4aec9` | Business services | ES | Weekly | 0.634 | 0.820 |
| 5 | `01f9bf03` | Digital goods | US | Weekly | 0.628 | 0.925 |

The top-ranked merchant (`7e0cec36`) is a small Food & drink business in GB with an ACF of 0.88 at lag 7 — meaning each week's volume is 88 % correlated with the prior week's. This is a near-perfect weekly recurring pattern, strongly suggesting this merchant's customers are buying on a weekly schedule that Subscriptions could automate.

Notably, Food & drink dominates the top ranks, which makes intuitive sense — restaurants, cafés, and meal-prep services naturally serve repeat customers on a weekly cadence. Business services and Digital goods also appear, likely reflecting recurring consulting engagements or digital membership purchases.

---

## Strengths and Limitations

**Strengths:**
- **Direct behavioral evidence** — unlike attribute-based models (Approaches 1–3), this surfaces a measurable, recurring pattern in the merchant's own transaction history.
- **Highly interpretable** — every candidate comes with a human-readable cycle type and visual proof, making it easy for sales/marketing to craft a targeted pitch ("We noticed your checkout volume spikes every week — Subscriptions could automate that for your repeat customers").
- **Complementary to other approaches** — merchants scoring high on both propensity (Approach 3) *and* seasonality are the highest-confidence targets.
- **No training labels needed** — purely unsupervised; no risk of label leakage or overfitting.

**Limitations:**
- **Requires sufficient history** — merchants with < 30 active days are excluded. Very new merchants can't be evaluated.
- **Zero-filling assumption** — days without transactions are filled with 0, which is reasonable for volume but could inflate apparent periodicity for merchants who only transact on specific days regardless of demand patterns.
- **Fixed candidate periods** — we only test 5 pre-defined periods (7, 14, 30, 60, 91 days). A merchant with, say, a 10-day billing cycle would not be detected optimally, though it would still show up as a partial match to the 7- or 14-day bins.
- **No causal inference** — a strong weekly pattern might reflect a merchant's operating hours (closed on weekends) rather than genuinely recurring customer demand. Domain knowledge or additional data (e.g., unique customer counts) would be needed to distinguish these.

---

## How to Run

```bash
cd src/approach_4_seasonality
python run.py
```

Runtime: ~7 minutes on a modern laptop (dominated by per-merchant ACF computation across 6,694 merchants). Outputs `results.csv` and all plots to `plots/`.
