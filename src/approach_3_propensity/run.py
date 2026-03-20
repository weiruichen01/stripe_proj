import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
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
    
    # Target variable: 1 if they use subscriptions, 0 otherwise
    features_df['adopt_subscription'] = (df['subscription_volume'] > 0).astype(int)
    
    # Split into training data (we can use the entire dataset to train the model to recognize the pattern)
    # Get feature columns (exclude merchant, first_charge_date, and raw volume cols we don't want to use directly for similarity like subscription_volume itself)
    exclude_cols = ['merchant', 'first_charge_date', 'subscription_volume', 'adopt_subscription']
    feature_cols = [c for c in features_df.columns if c not in exclude_cols]
    
    X = features_df[feature_cols]
    y = features_df['adopt_subscription']
    
    # Train Random Forest
    print("Training Random Forest model...")
    rf = RandomForestClassifier(n_estimators=5, random_state=42, n_jobs=1, max_depth=3)
    rf.fit(X, y)
    
    import matplotlib.pyplot as plt
    from sklearn.tree import plot_tree
    
    print("Plotting trees...")
    for i, tree in enumerate(rf.estimators_):
        print(f"Plotting tree {i+1}...")
        plt.figure(figsize=(20, 10))
        plot_tree(tree, feature_names=feature_cols, class_names=['No Sub', 'Sub'], filled=True, rounded=True, fontsize=10)
        plt.title(f'Decision Tree {i+1}')
        plt.savefig(f'tree_{i+1}.png', bbox_inches='tight')
        plt.close()
        print(f"Saved tree_{i+1}.png")
    
    # Predict probabilities for non-subscribers
    non_subscribers_df = df[df['subscription_volume'] == 0].copy()
    non_subscribers_features = features_df[df['subscription_volume'] == 0][feature_cols]
    
    print("Predicting propensity scores...")
    propensity_scores = rf.predict_proba(non_subscribers_features)[:, 1]
    
    non_subscribers_df['propensity_score'] = propensity_scores
    
    # Rank candidates
    ranked_candidates = non_subscribers_df.sort_values('propensity_score', ascending=False)
    
    # Select top 500 candidates
    top_candidates = ranked_candidates.head(500)
    
    output_path = 'results.csv'
    top_candidates.to_csv(output_path, index=False)
    print(f"Saved {len(top_candidates)} candidates to {output_path}")

if __name__ == '__main__':
    main()
