# Approach 3: Propensity-to-Adopt Modeling (Binary Classification)

## Design & Rationale
This approach frames the problem as a machine learning classification task. We aim to predict the likelihood (propensity) that a merchant will adopt the Subscriptions product based on their current behavior and attributes.

**The Process:**
1. **Target Variable:** We create a binary target variable (`1` if the merchant uses Subscriptions, `0` if they do not).
2. **Feature Engineering:** We extract and scale merchant attributes (industry, business size, country) and behavioral metrics (total volume, active days, checkout volume, payment link volume).
3. **Model Training:** We train a Random Forest Classifier on the entire dataset to learn the complex, non-linear patterns that distinguish Subscriptions users from non-users.
4. **Scoring:** We use the trained model to predict the probability (propensity score) of Subscriptions adoption for all merchants currently not using the product.

## Results & Analysis
The script outputs a ranked list of the top 500 non-subscribers based on their predicted propensity score.

**Why it's a great solution:**
- **Prioritized Output:** It outputs a precise probability score, allowing the marketing/sales team to rank the list and focus their budget/time on the top decile of users.
- **Captures Complex Interactions:** Tree-based models (like Random Forest) can capture non-linear relationships (e.g., business size might matter a lot for the Software industry, but not at all for Education).
- **Scalable & Fast:** Training a Random Forest model on aggregated user-level data takes only seconds on a modern MacBook Pro, easily satisfying the <5 mins constraint.
