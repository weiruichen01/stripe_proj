# Identifying Subscription Upsell Candidates via Seasonality Detection

## Approach

I used time series analysis to find non-subscriber merchants whose payment volumes repeat on a regular schedule (weekly, biweekly, monthly, etc.). If a merchant's customers are already paying on a predictable cycle, Subscriptions is a natural next step to automate what's already happening.

**Why this approach over alternatives (heuristic filtering, lookalike modeling, propensity scoring):** it looks at what merchants actually do, not just their attributes. The signal comes directly from transaction patterns, which makes it easy to explain in a sales conversation ("your checkout volume spikes every Monday. Subscriptions can automate that").

## Data Preparation

1. **Scoped to non-subscribers only.** Filtered to merchants with zero subscription volume, since these are the upsell targets.
2. **Minimum 30 active days.** Seasonality detection requires sufficient observations. This left 6,694 merchants.
3. **Gap-filled daily time series.** For each merchant, reindexed daily Checkout + Payment Link volumes onto the full calendar date range, filling missing days with zero. Both autocorrelation and FFT require evenly-spaced data.
4. **No normalization or detrending.** I preserved raw volume magnitudes so the scoring reflects both pattern strength and business activity level.

## Methodology

Each merchant was scored using two complementary techniques:

- **Autocorrelation (ACF)** at five candidate lags (7, 14, 30, 60, 91 days). Checks whether a merchant's volume on a given day looks similar to their volume *N* days later. High ACF at lag 7 means the pattern repeats weekly.
- **Spectral analysis (periodogram via FFT)**. Checks whether the volume signal is dominated by one clean repeating cycle or is mostly random noise.

I combined these into a composite score:

```
seasonality_score = 0.6 × max(ACF, 0) + 0.4 × spectral_ratio
```

ACF gets more weight because it handles real-world patterns well (e.g., sharp weekly spikes followed by quiet days). The spectral ratio serves as a sanity check: it confirms the pattern is a genuine cycle rather than a fluke in the data.

## Results

**Top 500 merchants** were ranked by seasonality score (range: 0.146 to 0.789, median: 0.252).

### Cycle type breakdown

| Cycle     | Count | Share |
|-----------|-------|-------|
| Weekly    | 372   | 74%   |
| Biweekly  | 95    | 19%   |
| Monthly   | 21    | 4%    |
| Quarterly | 8     | 2%    |
| Bimonthly | 4     | 1%    |

### Which merchants to target

**Tier 1: Highest-confidence targets (score > 0.5, ~top 30 merchants).**
These have very clear repeating patterns. The top-ranked merchant (`7e0cec36`, Food & drink, GB) has an ACF of 0.88 at lag 7, meaning each week's volume is 88% correlated with the prior week's. Food & drink dominates this tier, which makes sense: restaurants, cafés, and meal-prep services naturally serve repeat weekly customers.

**Tier 2: Strong candidates (score 0.25 to 0.5, ~220 merchants).**
Clear periodic patterns with some noise. Industries include digital goods, merchandise, and business services. These merchants would benefit from a consultative sales touch.

**Tier 3: Moderate signal (score 0.15 to 0.25, ~250 merchants).**
Detectable periodicity but weaker. Better suited to automated/low-touch outreach (e.g., in-product nudges or email campaigns).

**Monthly-cycle merchants (21 merchants) deserve special attention** regardless of score tier, since they're already billing on the most common subscription interval.

## Evaluation

- **Visual validation.** I plotted the top 5 merchants (time series, ACF, periodogram) and confirmed the detected patterns are real, not scoring artifacts.
- **Statistical significance.** ACF values exceed the 95% confidence bound (±1.96/√n) for all top-ranked merchants.
- **Known limitation: false positives from operating schedules.** A strong weekly pattern might just mean a merchant is closed on weekends, not that their customers buy on a recurring basis. This could be resolved with unique-customer-count data (not available here).
- **Coverage gap.** The 30-day minimum excludes newer merchants (~35% of non-subscribers). Acceptable for an initial target list, but worth noting.

## Recommendation for Stripe

1. **Sales prioritization.** Use the ranked list to prioritize outreach. Tier 1 merchants should receive direct sales contact with a tailored pitch referencing their specific cycle pattern. Tier 2/3 are suited to scaled campaigns.
2. **Combine with propensity scoring.** Merchants that rank highly on *both* seasonality and propensity (Approach 3) are the highest-confidence targets: they show the right behavior *and* the right profile.
3. **In-product integration.** Surface the detected cycle in the Stripe Dashboard ("Your customers tend to pay every week. Set up a subscription to automate this.") as a contextual upsell prompt.
4. **Segment by cycle type.** Tailor the Subscriptions pitch to the detected cadence: weekly merchants hear about weekly billing plans; monthly merchants hear about monthly auto-invoicing.

## Next Steps with More Resources

- **Unique customer analysis.** Check whether the repeating pattern comes from the same customers buying again (true subscription signal) or just the merchant's operating hours. Requires per-customer purchase data.
- **Expand candidate periods.** Move from five fixed lags to continuous peak detection on the ACF/periodogram, so non-standard cycles (e.g., 10-day or 45-day) are caught too.
- **Trend decomposition (STL).** Separate trend from seasonality so a growing or declining merchant's seasonal strength is scored independently of their trajectory.
- **Conversion modeling.** Track which targeted merchants actually adopt Subscriptions, then use that outcome data to refine scoring weights and thresholds.
- **Real-time scoring.** Integrate the pipeline into Stripe's data infrastructure so scores stay current as new transaction data arrives.
