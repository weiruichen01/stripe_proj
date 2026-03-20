import pandas as pd
import os

def main():
    print("Loading data...")
    merchants = pd.read_csv('../../data/dstakehome_merchants.csv')
    payments = pd.read_excel('../../data/dstakehome_payments.xlsx')
    
    payments['merchant'] = payments['merchant'].astype(str)
    payments['date'] = payments['date'].astype(str)
    merchants['merchant'] = merchants['merchant'].astype(str)
    
    # Aggregate payments by merchant
    pay_agg = payments.groupby('merchant').agg(
        subscription_volume=('subscription_volume', 'sum'),
        checkout_volume=('checkout_volume', 'sum'),
        payment_link_volume=('payment_link_volume', 'sum'),
        total_volume=('total_volume', 'sum'),
        active_days=('date', 'nunique')
    ).reset_index()
    
    df = pd.merge(merchants, pay_agg, on='merchant', how='inner')
    
    # Rule 1: No current subscription volume
    non_subs = df[df['subscription_volume'] == 0].copy()
    
    # Rule 2: Industries highly prone to recurring billing models
    target_industries = [
        'Software', 
        'Education', 
        'Digital goods', 
        'Religion, politics & other memberships', 
        'Consulting services',
        'Insurance'
    ]
    
    candidates = non_subs[non_subs['industry'].isin(target_industries)].copy()
    
    # Rule 3: Must have significant volume (e.g., top 20% of these candidates)
    # We will just sort them by total_volume and active_days to find the most active, 
    # highest-volume merchants who are manually processing recurring-like payments.
    candidates['avg_daily_volume'] = candidates['total_volume'] / candidates['active_days']
    
    # Sort by total volume and active days
    candidates = candidates.sort_values(by=['total_volume', 'active_days'], ascending=[False, False])
    
    # Select top 500 candidates for the marketing campaign
    top_candidates = candidates.head(500)
    
    output_path = 'results.csv'
    top_candidates.to_csv(output_path, index=False)
    print(f"Saved {len(top_candidates)} candidates to {output_path}")

if __name__ == '__main__':
    main()
