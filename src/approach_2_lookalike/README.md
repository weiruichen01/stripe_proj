# Approach 2: Lookalike Modeling (Similarity Scoring)

## Design & Rationale
This approach uses a data-driven Lookalike Model to identify merchants who are not using the Subscriptions product but closely resemble the most successful users of the product. 

**The Process:**
1. **Feature Engineering:** We extract merchant attributes (industry, business size, country) and behavioral metrics (total volume, active days, checkout volume, payment link volume) and scale them.
2. **Success Profile:** We isolate the top 20% of current Subscriptions users (by volume) and calculate their average feature vector to create a "Success Profile."
3. **Similarity Scoring:** We compute the Cosine Similarity between every non-subscriber and the Success Profile. The higher the score, the more closely the non-subscriber resembles an ideal Subscriptions customer.

## Results & Analysis
The script outputs a ranked list of the top 500 non-subscribers based on their similarity score to the Success Profile. 

**Why it's a great solution:**
- **Data-Driven but Intuitive:** It relies on the actual data of what a good Subscriptions user looks like, rather than guessing. The pitch to the sales team is simple: "These users look exactly like our best Subscriptions customers."
- **Uncovers Hidden Segments:** It might find that a specific niche (e.g., medium-sized merchants in a specific region using Payment Links) strongly resembles current Subscriptions users, something a manual rule might miss.
- **Fast Execution:** Computing pairwise distances or running a simple KNN algorithm on aggregated merchant profiles is computationally light and easily fits the <5 mins time constraint on a MacBook Pro.
