import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

def load_data():
    print("Loading data...")
    # Assuming this script is run from the root of the project or src/visualization
    # Adjust paths based on where it's executed. Let's use absolute paths or relative to this file.
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    merchants_path = os.path.join(base_dir, 'data', 'dstakehome_merchants.csv')
    payments_path = os.path.join(base_dir, 'data', 'dstakehome_payments.xlsx')
    
    merchants = pd.read_csv(merchants_path)
    payments = pd.read_excel(payments_path)
    
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
    df['adopt_subscription'] = df['subscription_volume'] > 0
    return df

def plot_adopted_vs_not_adopted_profile(df, output_dir):
    """
    Shows the typical type of merchants that would adopt subscription vs not.
    Compares average volumes and active days.
    """
    print("Generating Adopted vs Not Adopted profile...")
    
    # Calculate means for key metrics
    metrics = ['total_volume', 'checkout_volume', 'payment_link_volume', 'active_days']
    profile = df.groupby('adopt_subscription')[metrics].mean().reset_index()
    profile['adopt_subscription'] = profile['adopt_subscription'].map({True: 'Adopted', False: 'Not Adopted'})
    
    # Melt for easier plotting with seaborn
    profile_melted = pd.melt(profile, id_vars=['adopt_subscription'], value_vars=metrics, 
                             var_name='Metric', value_name='Average Value')
    
    # We need to plot active_days on a different scale or separate plot since volume is in cents and much larger
    volume_metrics = ['total_volume', 'checkout_volume', 'payment_link_volume']
    vol_data = profile_melted[profile_melted['Metric'].isin(volume_metrics)]
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=vol_data, x='Metric', y='Average Value', hue='adopt_subscription', palette='Set2')
    plt.title('Average Volume Profile: Adopted vs Not Adopted')
    plt.ylabel('Average Volume (Cents)')
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'adopted_vs_not_adopted_volume.png'))
    plt.close()
    
    # Plot active days separately
    days_data = profile_melted[profile_melted['Metric'] == 'active_days']
    plt.figure(figsize=(6, 5))
    sns.barplot(data=days_data, x='Metric', y='Average Value', hue='adopt_subscription', palette='Set2')
    plt.title('Average Active Days: Adopted vs Not Adopted')
    plt.ylabel('Average Active Days')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'adopted_vs_not_adopted_days.png'))
    plt.close()

def plot_industry_distribution(df, output_dir):
    """
    Shows the distribution of merchants across different industries,
    split by whether they use subscriptions or not.
    """
    print("Generating Industry distribution...")
    plt.figure(figsize=(14, 8))

    df = df[~df['industry'].isin(['0', 'Money transmitters'])]

    # Calculate percentage of subscribers in each industry to sort them
    industry_stats = df.groupby('industry')['adopt_subscription'].agg(['count', 'mean']).reset_index()
    industry_stats = industry_stats.rename(columns={'count': 'total_merchants', 'mean': 'subscription_rate'})
    industry_stats = industry_stats.sort_values('total_merchants', ascending=False)
    
    # Plot total counts
    sns.countplot(data=df, y='industry', hue='adopt_subscription', 
                  order=industry_stats['industry'], palette='Set2')
    
    plt.title('Merchant Distribution by Industry (Adopted vs Not Adopted)')
    plt.xlabel('Number of Merchants')
    plt.ylabel('Industry')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'industry_distribution.png'))
    plt.close()
    
    # Also plot the adoption rate per industry
    industry_stats = industry_stats.sort_values('subscription_rate', ascending=False)
    plt.figure(figsize=(14, 8))
    sns.barplot(data=industry_stats, x='subscription_rate', y='industry', color='skyblue')
    plt.title('Subscription Adoption Rate by Industry')
    plt.xlabel('Adoption Rate (%)')
    plt.ylabel('Industry')
    # Format x-axis as percentage
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'industry_adoption_rate.png'))
    plt.close()

def plot_business_size_distribution(df, output_dir):
    """
    Shows how subscription adoption varies by business size.
    """
    print("Generating Business Size distribution...")
    plt.figure(figsize=(8, 5))
    
    # Define order if it's small, medium, large
    size_order = ['small', 'medium', 'large']
    if not all(s in df['business_size'].unique() for s in size_order):
        size_order = df['business_size'].value_counts().index # fallback
        
    sns.countplot(data=df, x='business_size', hue='adopt_subscription', 
                  order=size_order, palette='Set2')
    
    plt.title('Subscription Adoption by Business Size')
    plt.xlabel('Business Size')
    plt.ylabel('Number of Merchants')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'business_size_distribution.png'))
    plt.close()

def plot_volume_by_business_size(df, output_dir):
    """
    Sums total payment volume for each business size category and plots as a bar chart.
    """
    print("Generating Total Volume by Business Size...")

    size_order = ['small', 'medium', 'large']
    if not all(s in df['business_size'].unique() for s in size_order):
        size_order = df['business_size'].value_counts().index.tolist()

    volume_by_size = (
        df.groupby('business_size')['total_volume']
        .sum()
        .reindex(size_order)
        .reset_index()
    )
    # Convert cents to dollars for readability
    volume_by_size['total_volume_usd'] = volume_by_size['total_volume'] / 100

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = sns.color_palette('Set2', len(size_order))
    bars = ax.bar(
        volume_by_size['business_size'],
        volume_by_size['total_volume_usd'],
        color=colors,
        edgecolor='white',
        linewidth=0.8
    )

    # Annotate each bar with its value
    for bar, val in zip(bars, volume_by_size['total_volume_usd']):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() * 1.01,
            f'${val:,.0f}',
            ha='center', va='bottom', fontsize=10, fontweight='bold'
        )

    ax.set_title('Total Payment Volume by Business Size', fontsize=14, fontweight='bold')
    ax.set_xlabel('Business Size', fontsize=12)
    ax.set_ylabel('Total Volume (USD)', fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax.set_ylim(0, volume_by_size['total_volume_usd'].max() * 1.15)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'volume_by_business_size.png'), dpi=150)
    plt.close()


def plot_volume_distribution_kde(df, output_dir):
    """
    Plots the distribution of total volume for adopted vs not adopted
    using a KDE plot with log scale (since volume is usually highly skewed).
    """
    print("Generating Volume KDE distribution...")
    plt.figure(figsize=(10, 6))
    
    # Add a small constant to avoid log(0)
    import numpy as np
    df['log_total_volume'] = (df['total_volume'] + 1).apply(lambda x: np.log10(x) if x > 0 else 0)
    
    sns.kdeplot(data=df, x='log_total_volume', hue='adopt_subscription', 
                common_norm=False, fill=True, palette='Set2')
    
    plt.title('Distribution of Total Volume (Log10 Scale)')
    plt.xlabel('Log10(Total Volume in Cents)')
    plt.ylabel('Density')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'volume_distribution_kde.png'))
    plt.close()

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(base_dir, 'src', 'visualization', 'plots')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    df = load_data()
    
    plot_adopted_vs_not_adopted_profile(df, output_dir)
    plot_industry_distribution(df, output_dir)
    plot_business_size_distribution(df, output_dir)
    plot_volume_distribution_kde(df, output_dir)
    plot_volume_by_business_size(df, output_dir)
    
    print(f"All visualizations saved to {output_dir}")

if __name__ == '__main__':
    main()
