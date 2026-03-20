# Identifying Subscription Upsell Candidates via Seasonality Detection

## Approach

I used time series analysis to find merchants whose payment volumes repeat on a regular schedule (weekly, biweekly, monthly, etc.). If a merchant's customers are already paying on a predictable cycle, Subscriptions is a natural next step to automate what's already happening.

## Data Preparation

1. **Scoped to non-subscribers only.** Filtered to merchants with zero subscription volume, since these are the upsell targets.
2. **Minimum 30 active days.** Seasonality detection requires sufficient observations. This left 6,694 merchants.
3. **Gap-filled daily time series.** For each merchant, reindexed daily Checkout + Payment Link volumes onto the full calendar date range, filling missing days with zero. Autocorrelation requires evenly-spaced data.

## Methodology

Each merchant was scored using **autocorrelation (ACF)** at five candidate lags (7, 14, 30, 60, 91 days). This checks whether a merchant's volume on a given day looks similar to their volume n days before. High ACF at lag 7 means the pattern repeats weekly.

The seasonality score is the highest ACF value across the five candidate lags. ACF is used as the sole scoring signal because it handles real-world patterns well (e.g., sharp weekly spikes followed by quiet days) and directly answers whether a merchant's volume repeats on a fixed schedule.

## Results

**Top 500 merchants** were ranked by seasonality score.

### Cycle type breakdown

| Cycle     | Count | Share |
|-----------|-------|-------|
| Weekly    | 335   | 67%   |
| Biweekly  | 112   | 22%   |
| Monthly   | 26    | 5%    |
| Quarterly | 19    | 4%    |
| Bimonthly | 8     | 2%    |

### Which merchants to target

Starting from the candidates with the highest scores. These have very clear repeating patterns. The top-ranked merchant (`01f9bf03`) has an ACF of 0.925 at lag 7, meaning each week's volume is ~93% correlated with the prior week's; in particular, the spikes occur every Monday.

## Evaluation

- **Visual validation.** I plotted top merchant candidates (time series, ACF) and confirmed the detected patterns are real.

- **Statistical significance.** ACF values exceed the 95% confidence bound.

## Recommendation for Stripe

1. **Sales prioritization.** Use the ranked list to prioritize outreach.
2. **In-product integration.** Surface the detected cycle in the Stripe Dashboard ("Your customers tend to pay every week. Set up a subscription to automate this.") as a contextual upsell prompt.
3. **Segment by cycle type.** For a more precise promotion, tailor the Subscriptions pitch to the detected cadence: weekly merchants hear about a success story of weekly billing plans; monthly merchants hear about a success story of monthly billing plans. If time and resources permit, an industry-oriented or a nearest neighbor (via clustering) success story can be used to target the merchant.

## Next Steps with More Resources

### Key observation from exploratory analysis

Software (~44%) and Consulting services (~39%) have the highest subscription adoption rates by a wide margin (see chart below), likely because their teams have the technical background to evaluate and set up recurring billing. We can produce step-by-step onboarding guides and video walkthroughs tailored to merchants without technical backgrounds, so that adoption doesn't require a developer.

### Decision trees to identify the determining factors of adoption

Train a decision tree on the full merchant base with `adopted_subscription` as the target and more features from the actual database. The resulting splits reveal which attributes most strongly separate adopters from non-adopters. These learned rules can then sharpen marketing: instead of broad outreach, target the exact merchant profiles where the model shows adoption is most likely but hasn't happened yet.