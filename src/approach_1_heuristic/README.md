# Approach 1: Heuristic / Rule-Based Targeting

## Design & Rationale
This approach relies on behavioral profiling through simple, interpretable business rules. We hypothesize that merchants who are not currently using the Subscriptions product, but operate in industries prone to recurring billing (e.g., Software, Education, Digital Goods, Insurance), and process high volumes of transactions via Checkout or Payment Links, are prime candidates for the Subscriptions product. They are likely manually processing recurring payments or using a suboptimal flow. 

**Rules Applied:**
1. **Zero Subscription Volume:** The merchant is not currently using the product.
2. **Target Industries:** The merchant operates in an industry where subscriptions are common (Software, Education, Digital goods, Religion/politics memberships, Consulting services, Insurance).
3. **High Activity & Volume:** The merchant has high total volume and a high number of active days, indicating a mature business that would benefit from the automation Subscriptions provides.

## Results & Analysis
The script identifies the top 500 merchants matching these rules, ranked by their total volume and active days. These merchants represent the "low-hanging fruit" for a sales or marketing campaign. 

**Why it's a great solution:**
- **Highly Interpretable:** Sales teams can easily understand the "why" behind the list (e.g., "This is a high-volume Software company not using Subscriptions").
- **Actionable:** The messaging can be tailored directly to the pain point of manual billing.
- **Fast Execution:** The logic is simple aggregation and filtering, taking less than a minute to run on a MacBook Pro.
