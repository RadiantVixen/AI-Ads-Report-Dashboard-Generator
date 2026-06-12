import pandas as pd
import numpy as np

def load_and_validate_data(file_or_path) -> pd.DataFrame:
    """
    Loads ads data from a CSV file or file-like object and validates it.
    
    Raises:
        ValueError: If required columns are missing or data format is invalid.
    """
    try:
        df = pd.read_csv(file_or_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {str(e)}")

    # Standardize column names to lowercase and strip whitespace
    df.columns = [col.strip().lower() for col in df.columns]

    # Required columns check
    required_cols = ['date', 'campaign_name', 'impressions', 'clicks', 'spend', 'conversions']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in CSV: {', '.join(missing_cols)}")

    # Clean date column
    try:
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        raise ValueError(f"Could not parse 'date' column as datetime: {str(e)}")

    # Clean campaign_name: drop rows with null names
    df = df.dropna(subset=['campaign_name'])
    df['campaign_name'] = df['campaign_name'].astype(str)

    # Optional product and region checks
    if 'product_name' in df.columns:
        df = df.dropna(subset=['product_name'])
        df['product_name'] = df['product_name'].astype(str).str.strip()

    if 'region' in df.columns:
        df = df.dropna(subset=['region'])
        df['region'] = df['region'].astype(str).str.strip()

    # Cast metrics to proper numeric types, filling NaNs with 0
    numeric_cols = ['impressions', 'clicks', 'spend', 'conversions']
    if 'revenue' in df.columns:
        numeric_cols.append('revenue')

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        # Ensure values are non-negative
        df[col] = df[col].clip(lower=0)

    # Convert counts to integers
    df['impressions'] = df['impressions'].astype(int)
    df['clicks'] = df['clicks'].astype(int)
    df['conversions'] = df['conversions'].astype(int)

    # Sort by date and campaign
    df = df.sort_values(by=['date', 'campaign_name']).reset_index(drop=True)

    return df

def compute_summary_metrics(df: pd.DataFrame) -> dict:
    """
    Computes overall summary metrics for the dashboard.
    """
    has_revenue = 'revenue' in df.columns
    has_products = 'product_name' in df.columns and not df['product_name'].dropna().empty
    has_regions = 'region' in df.columns and not df['region'].dropna().empty

    total_impressions = df['impressions'].sum()
    total_clicks = df['clicks'].sum()
    total_spend = df['spend'].sum()
    total_conversions = df['conversions'].sum()

    # Safe divisions for overall ratios
    overall_ctr = total_clicks / total_impressions if total_impressions > 0 else 0.0
    overall_cpc = total_spend / total_clicks if total_clicks > 0 else 0.0
    overall_cvr = total_conversions / total_clicks if total_clicks > 0 else 0.0

    metrics = {
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'total_spend': total_spend,
        'total_conversions': total_conversions,
        'overall_ctr': overall_ctr,
        'overall_cpc': overall_cpc,
        'overall_cvr': overall_cvr,
        'has_revenue': has_revenue,
        'has_products': has_products,
        'has_regions': has_regions
    }

    if has_revenue:
        total_revenue = df['revenue'].sum()
        total_profit = total_revenue - total_spend
        overall_roas = total_revenue / total_spend if total_spend > 0 else 0.0
        metrics.update({
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'overall_roas': overall_roas
        })
    else:
        metrics.update({
            'total_revenue': 0.0,
            'total_profit': 0.0,
            'overall_roas': 0.0
        })

    return metrics

def compute_campaign_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups by campaign_name and computes metrics for each.
    """
    has_revenue = 'revenue' in df.columns
    
    agg_dict = {
        'impressions': 'sum',
        'clicks': 'sum',
        'spend': 'sum',
        'conversions': 'sum'
    }
    if has_revenue:
        agg_dict['revenue'] = 'sum'

    campaign_df = df.groupby('campaign_name').agg(agg_dict).reset_index()

    # Calculate ratios per campaign
    campaign_df['ctr'] = campaign_df['clicks'] / campaign_df['impressions'].replace(0, np.nan)
    campaign_df['cpc'] = campaign_df['spend'] / campaign_df['clicks'].replace(0, np.nan)
    campaign_df['cvr'] = campaign_df['conversions'] / campaign_df['clicks'].replace(0, np.nan)

    # Fill NaNs with 0.0
    campaign_df['ctr'] = campaign_df['ctr'].fillna(0.0)
    campaign_df['cpc'] = campaign_df['cpc'].fillna(0.0)
    campaign_df['cvr'] = campaign_df['cvr'].fillna(0.0)

    if has_revenue:
        campaign_df['roas'] = campaign_df['revenue'] / campaign_df['spend'].replace(0, np.nan)
        campaign_df['roas'] = campaign_df['roas'].fillna(0.0)
        campaign_df['profit'] = campaign_df['revenue'] - campaign_df['spend']
    
    return campaign_df

def compute_product_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups by product_name and computes performance metrics per product.
    """
    if 'product_name' not in df.columns:
        return pd.DataFrame()
        
    has_revenue = 'revenue' in df.columns
    
    agg_dict = {
        'spend': 'sum',
        'conversions': 'sum',
        'clicks': 'sum',
        'impressions': 'sum'
    }
    if has_revenue:
        agg_dict['revenue'] = 'sum'

    product_df = df.groupby('product_name').agg(agg_dict).reset_index()
    
    # Calculate conversion rate per product
    product_df['cvr'] = product_df['conversions'] / product_df['clicks'].replace(0, np.nan)
    product_df['cvr'] = product_df['cvr'].fillna(0.0)
    
    if has_revenue:
        product_df['profit'] = product_df['revenue'] - product_df['spend']
        product_df['roas'] = product_df['revenue'] / product_df['spend'].replace(0, np.nan)
        product_df['roas'] = product_df['roas'].fillna(0.0)
        # Sort by profit descending
        product_df = product_df.sort_values(by='profit', ascending=False).reset_index(drop=True)
    else:
        # Sort by conversions descending
        product_df = product_df.sort_values(by='conversions', ascending=False).reset_index(drop=True)
        
    return product_df

def compute_region_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups by region and computes performance metrics per region.
    """
    if 'region' not in df.columns:
        return pd.DataFrame()
        
    has_revenue = 'revenue' in df.columns
    
    agg_dict = {
        'spend': 'sum',
        'conversions': 'sum',
        'clicks': 'sum',
        'impressions': 'sum'
    }
    if has_revenue:
        agg_dict['revenue'] = 'sum'

    region_df = df.groupby('region').agg(agg_dict).reset_index()
    
    # Calculate conversion rate per region
    region_df['cvr'] = region_df['conversions'] / region_df['clicks'].replace(0, np.nan)
    region_df['cvr'] = region_df['cvr'].fillna(0.0)
    
    if has_revenue:
        region_df['roas'] = region_df['revenue'] / region_df['spend'].replace(0, np.nan)
        region_df['roas'] = region_df['roas'].fillna(0.0)
        region_df['profit'] = region_df['revenue'] - region_df['spend']
        # Sort by ROAS descending
        region_df = region_df.sort_values(by='roas', ascending=False).reset_index(drop=True)
    else:
        # Sort by conversions descending
        region_df = region_df.sort_values(by='conversions', ascending=False).reset_index(drop=True)
        
    return region_df

def get_best_and_worst_campaigns(campaign_df: pd.DataFrame, has_revenue: bool) -> dict:
    """
    Identifies the best and worst performing campaigns.
    
    If revenue exists, ranks by ROAS (with conversions as tie-breaker).
    Otherwise, ranks by Conversions (with CVR as tie-breaker).
    """
    if campaign_df.empty:
        return {
            'best_name': 'N/A', 'best_value': 0.0, 'best_metric': 'ROAS',
            'worst_name': 'N/A', 'worst_value': 0.0, 'worst_metric': 'ROAS'
        }

    if has_revenue:
        # Sort by ROAS, then conversions
        sorted_df = campaign_df.sort_values(by=['roas', 'conversions'], ascending=False).reset_index(drop=True)
        best_name = sorted_df.iloc[0]['campaign_name']
        best_val = sorted_df.iloc[0]['roas']
        best_metric = 'ROAS'
        
        worst_name = sorted_df.iloc[-1]['campaign_name']
        worst_val = sorted_df.iloc[-1]['roas']
        worst_metric = 'ROAS'
    else:
        # Sort by conversions, then cvr
        sorted_df = campaign_df.sort_values(by=['conversions', 'cvr'], ascending=False).reset_index(drop=True)
        best_name = sorted_df.iloc[0]['campaign_name']
        best_val = float(sorted_df.iloc[0]['conversions'])
        best_metric = 'Conversions'
        
        worst_name = sorted_df.iloc[-1]['campaign_name']
        worst_val = float(sorted_df.iloc[-1]['conversions'])
        worst_metric = 'Conversions'

    return {
        'best_name': best_name,
        'best_value': best_val,
        'best_metric': best_metric,
        'worst_name': worst_name,
        'worst_value': worst_val,
        'worst_metric': worst_metric
    }

def compute_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates spend, revenue, clicks, and conversions by date to get trend metrics.
    """
    has_revenue = 'revenue' in df.columns
    
    agg_dict = {
        'spend': 'sum',
        'clicks': 'sum',
        'conversions': 'sum',
        'impressions': 'sum'
    }
    if has_revenue:
        agg_dict['revenue'] = 'sum'

    trend_df = df.groupby('date').agg(agg_dict).reset_index()
    
    # Calculate ratios per date
    trend_df['ctr'] = trend_df['clicks'] / trend_df['impressions'].replace(0, np.nan)
    trend_df['cpc'] = trend_df['spend'] / trend_df['clicks'].replace(0, np.nan)
    trend_df['cvr'] = trend_df['conversions'] / trend_df['clicks'].replace(0, np.nan)
    
    trend_df['ctr'] = trend_df['ctr'].fillna(0.0)
    trend_df['cpc'] = trend_df['cpc'].fillna(0.0)
    trend_df['cvr'] = trend_df['cvr'].fillna(0.0)

    if has_revenue:
        trend_df['roas'] = trend_df['revenue'] / trend_df['spend'].replace(0, np.nan)
        trend_df['roas'] = trend_df['roas'].fillna(0.0)
        trend_df['profit'] = trend_df['revenue'] - trend_df['spend']

    return trend_df
