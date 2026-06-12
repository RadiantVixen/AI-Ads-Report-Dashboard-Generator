import pandas as pd
import os
from groq import Groq

def get_currency_symbol(df: pd.DataFrame) -> str:
    """
    Detects the currency symbol based on regions present in the dataset.
    """
    if df is not None and 'region' in df.columns:
        eu_regions = {'france', 'spain', 'germany', 'italy', 'europe'}
        regions_present = set(df['region'].dropna().astype(str).str.lower())
        if regions_present.intersection(eu_regions):
            return '€'
    return '$'

def generate_insights(
    summary_metrics: dict,
    campaign_df: pd.DataFrame,
    product_df: pd.DataFrame,
    region_df: pd.DataFrame,
    api_key: str,
    currency_symbol: str = "€"
) -> str:
    """
    Generates marketing, product, and regional insights using Groq Cloud API.
    
    Adheres to the direct, witty Elite CMO consultant persona.
    """
    if not api_key:
        raise ValueError("Groq API key is missing. Please set it in the sidebar or environment variables.")

    client = Groq(api_key=api_key)

    has_revenue = summary_metrics.get('has_revenue', False)
    has_products = summary_metrics.get('has_products', False) and product_df is not None and not product_df.empty
    has_regions = summary_metrics.get('has_regions', False) and region_df is not None and not region_df.empty

    # Pick worst campaign by net profit (or conversions if no revenue)
    if not campaign_df.empty:
        sort_col = 'profit' if 'profit' in campaign_df.columns else 'conversions'
        worst_campaign = campaign_df.sort_values(by=sort_col, ascending=True).iloc[0]
    else:
        worst_campaign = None

    # Pick worst product
    if has_products:
        sort_col = 'profit' if 'profit' in product_df.columns else 'conversions'
        worst_product = product_df.sort_values(by=sort_col, ascending=True).iloc[0]
    else:
        worst_product = None

    # Pick worst region
    if has_regions:
        sort_col = 'profit' if 'profit' in region_df.columns else 'conversions'
        worst_region = region_df.sort_values(by=sort_col, ascending=True).iloc[0]
    else:
        worst_region = None

    # Format the data package for the LLM
    data_package = f"=== PROGRAM PRE-CALCULATED METRICS (Currency: {currency_symbol}) ===\n\n"
    
    # Portfolio summary
    data_package += f"Overall Portfolio Summary:\n"
    data_package += f"- Total Spend: {currency_symbol}{summary_metrics['total_spend']:,.2f}\n"
    if has_revenue:
        data_package += f"- Total Revenue: {currency_symbol}{summary_metrics['total_revenue']:,.2f}\n"
        data_package += f"- Net Profit: {currency_symbol}{summary_metrics['total_profit']:,.2f}\n"
        data_package += f"- Overall ROAS: {summary_metrics['overall_roas']:.2f}x\n"
    data_package += "\n"

    # Worst Campaign
    if worst_campaign is not None:
        data_package += f"Worst Performing Campaign Profile:\n"
        data_package += f"- Campaign Name: {worst_campaign['campaign_name']}\n"
        data_package += f"- Total Spend: {currency_symbol}{worst_campaign['spend']:,.2f}\n"
        if has_revenue:
            data_package += f"- Revenue: {currency_symbol}{worst_campaign['revenue']:,.2f}\n"
            data_package += f"- Net Profit: {currency_symbol}{worst_campaign['profit']:,.2f}\n"
            data_package += f"- Calculated ROAS: {worst_campaign['roas']:.2f}x\n"
        data_package += f"- CTR: {worst_campaign['ctr']:.2%}\n"
        data_package += f"- CVR: {worst_campaign['cvr']:.2%}\n\n"

    # Worst Product
    if worst_product is not None:
        data_package += f"Worst Performing Product Profile:\n"
        data_package += f"- Product Name: {worst_product['product_name']}\n"
        data_package += f"- Total Spend: {currency_symbol}{worst_product['spend']:,.2f}\n"
        if has_revenue:
            data_package += f"- Revenue: {currency_symbol}{worst_product['revenue']:,.2f}\n"
            data_package += f"- Net Profit: {currency_symbol}{worst_product['profit']:,.2f}\n"
            data_package += f"- Calculated ROAS: {worst_product['roas']:.2f}x\n"
        data_package += f"- CVR: {worst_product['cvr']:.2%}\n\n"

    # Worst Region
    if worst_region is not None:
        data_package += f"Worst Performing Region Profile:\n"
        data_package += f"- Region Name: {worst_region['region']}\n"
        data_package += f"- Total Spend: {currency_symbol}{worst_region['spend']:,.2f}\n"
        if has_revenue:
            data_package += f"- Revenue: {currency_symbol}{worst_region['revenue']:,.2f}\n"
            data_package += f"- Net Profit: {currency_symbol}{worst_region['profit']:,.2f}\n"
            data_package += f"- Calculated ROAS: {worst_region['roas']:.2f}x\n"
        data_package += f"- CVR: {worst_region['cvr']:.2%}\n\n"

    # System prompts
    system_prompt = f"""
You are an elite, direct, and slightly witty Digital Marketing Consultant integrated into a B2B SaaS dashboard. 

Your sole job is to review a pre-calculated performance summary provided by the system python engine and translate it into clear, plain-English business decisions.

CRITICAL INSTRUCTIONS:
1. NEVER perform raw arithmetic or calculate percentages. Rely ONLY on the pre-calculated metrics (ROAS, Spend, Net Profit) passed to you by the program.
2. Structure your response into two brief sections:
   - 📉 Financial Impact: A 1-2 sentence blunt assessment of where money is being made or lost.
   - 🚀 Direct Action: A clear directive stating whether to SCALE, FIX, or STOP the campaign/region/product, and exactly what the user should change.
3. Keep the tone professional, direct, slightly witty, and focused strictly on financial optimization. Use localized currency symbols ({currency_symbol}) as passed by the data. Do not use generic markdown placeholders.
"""

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this pre-calculated metrics summary:\n{data_package}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Error calling Groq API: {str(e)}")
