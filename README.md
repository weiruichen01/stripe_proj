You have access to two datasets, available in data/:

Payments: Contains merchant-day volume data. Volume is reported for three Stripe products: Subscriptions, Checkout, and Payment Links.
Merchants: Contains merchant data including signup date, region, company size, and industry.
Please note that additional information about the data is available in the “Data Descriptions” sheet.

Notes:

Stripe provides a suite of payments, financial services, and business operations products, including:
Subscription: APIs for creating and managing subscriptions, recurring payments, and recurring revenue.
Checkout: Prebuilt, Stripe hosted checkout page
Payment Link: No-code payment
{subscriptions, checkout, payment_link}_volume in `payments` represents transaction volume associated with that product. Note that the product usage is not mutually exclusive. For example, a user can use both Checkout and Subscription products for one transaction.
The dataset has future merchant transaction activity from 2041-2042. The data is made up, but you can consider this to be a random sample of future merchants using Stripe.
Each observation in the `payments`  transaction volume is in cents.
Questions

Suppose you are working with the Head of Product to get more existing Stripe users to start using the Subscriptions product. Please develop a quantitative approach which identifies a list of users for a sales or marketing campaign.

Constraint: The model needs to be runable on a Macbook Pro in a feasible compute time (<5 mins).