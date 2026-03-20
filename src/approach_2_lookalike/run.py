import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import os

def main():
    print("Loading data...")
    merchants = pd.read_csv('../../data/dstakehome_merchants.csv')
    payments = pd.read_excel('../../data/dstakehome_payments.xlsx')
    
    payments['merchant'] = payments['merchant'].astype(str)
    payments['date'] = payments['date'].astype(str)
    merchants['merchant'] = merchants['merchant'].astype(str)
    
    # Aggregate payments
    pay_agg = payments.groupby('merchant').agg(
        subscription_volume=('subscription_volume', 'sum'),
        checkout_volume=('checkout_volume', 'sum'),
        payment_link_volume=('payment_link_volume', 'sum'),
        total_volume=('total_volume', 'sum'),
        active_days=('date', 'nunique')
    ).reset_index()
    
    df = pd.merge(merchants, pay_agg, on='merchant', how='inner')
    
    # Feature Engineering
    # Categorical: industry, business_size, country
    # Numerical: total_volume, active_days, checkout_volume, payment_link_volume
    
    features_df = df.copy()
    
    # One-hot encode categorical variables
    cat_cols = ['industry', 'business_size', 'country']
    features_df = pd.get_dummies(features_df, columns=cat_cols, drop_first=True)
    
    # Numerical features
    num_cols = ['total_volume', 'active_days', 'checkout_volume', 'payment_link_volume']
    
    # Scale numerical features
    scaler = StandardScaler()
    features_df[num_cols] = scaler.fit_transform(features_df[num_cols])
    
    # Split into subscribers and non-subscribers
    adopt_subscription = df['subscription_volume'] > 0
    
    # Get feature columns (exclude merchant, first_charge_date, and raw volume cols we don't want to use directly for similarity like subscription_volume itself)
    exclude_cols = ['merchant', 'first_charge_date', 'subscription_volume']
    feature_cols = [c for c in features_df.columns if c not in exclude_cols]
    
    subscribers_features = features_df[adopt_subscription][feature_cols]
    non_subscribers_df = df[~adopt_subscription].copy()
    non_subscribers_features = features_df[~adopt_subscription][feature_cols]
    
    # Define "Success Profile"
    # Let's take the top 20% of subscribers by subscription_volume to define our ideal customer profile
    top_subscribers_idx = df[adopt_subscription].sort_values('subscription_volume', ascending=False).head(int(sum(adopt_subscription)*0.2)).index
    success_profile = features_df.loc[top_subscribers_idx, feature_cols].mean().values.reshape(1, -1)
    
    # Calculate Cosine Similarity
    print("Calculating similarity...")
    similarities = cosine_similarity(non_subscribers_features, success_profile)
    
    non_subscribers_df['similarity_score'] = similarities.flatten()
    
    # Rank candidates
    ranked_candidates = non_subscribers_df.sort_values('similarity_score', ascending=False)
    
    # Select top 500 candidates
    top_candidates = ranked_candidates.head(500)
    
    output_path = 'results.csv'
    top_candidates.to_csv(output_path, index=False)
    print(f"Saved {len(top_candidates)} candidates to {output_path}")

if __name__ == '__main__':
    main()
