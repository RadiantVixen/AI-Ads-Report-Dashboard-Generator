import pandas as pd
from openai import OpenAI

def generate_insights(
    summary_metrics: dict,
    campaign_df: pd.DataFrame,
    product_df: pd.DataFrame,
    region_df: pd.DataFrame,
    api_key: str
) -> str:
    """
    Generates marketing, product, and regional insights using OpenAI's API.
    """
    if not api_key:
        raise ValueError("OpenAI API key is missing. Please set it in the sidebar or environment variables.")

    client = OpenAI(api_key=api_key)

    has_revenue = summary_metrics.get('has_revenue', False)
    has_products = summary_metrics.get('has_products', False) and product_df is not None and not product_df.empty
    has_regions = summary_metrics.get('has_regions', False) and region_df is not None and not region_df.empty

    # 1. Overall Summary
    overall_summary = f"""
    - Total Impressions: {summary_metrics['total_impressions']:,}
    - Total Clicks: {summary_metrics['total_clicks']:,}
    - Total Spend: ${summary_metrics['total_spend']:,.2f}
    - Total Conversions: {summary_metrics['total_conversions']:,}
    - Click-Through Rate (CTR): {summary_metrics['overall_ctr']:.2%}
    - Cost Per Click (CPC): ${summary_metrics['overall_cpc']:.2f}
    - Conversion Rate (CVR): {summary_metrics['overall_cvr']:.2%}
    """
    if has_revenue:
        overall_summary += f"""- Total Revenue: ${summary_metrics['total_revenue']:,.2f}
    - Total Profit: ${summary_metrics['total_profit']:,.2f}
    - Return on Ad Spend (ROAS): {summary_metrics['overall_roas']:.2f}x
    """

    # 2. Campaign breakdown
    campaign_rows = []
    for _, row in campaign_df.iterrows():
        camp_str = (
            f"Campaign: {row['campaign_name']} | "
            f"Spend: ${row['spend']:,.2f} | "
            f"Clicks: {row['clicks']:,} | "
            f"Conversions: {row['conversions']:,} | "
            f"CTR: {row['ctr']:.2%} | "
            f"CPC: ${row['cpc']:.2f} | "
            f"CVR: {row['cvr']:.2%}"
        )
        if has_revenue:
            camp_str += f" | Revenue: ${row['revenue']:,.2f} | ROAS: {row['roas']:.2f}x"
        campaign_rows.append(camp_str)
    campaign_summary_str = "\n".join([f"- {row}" for row in campaign_rows])

    # 3. Product breakdown
    product_summary_str = "No product data available."
    if has_products:
        product_rows = []
        for _, row in product_df.iterrows():
            prod_str = (
                f"Product: {row['product_name']} | "
                f"Spend: ${row['spend']:,.2f} | "
                f"Conversions: {row['conversions']:,} | "
                f"CVR: {row['cvr']:.2%}"
            )
            if has_revenue:
                prod_str += f" | Revenue: ${row['revenue']:,.2f} | Profit: ${row['profit']:,.2f} | ROAS: {row['roas']:.2f}x"
            product_rows.append(prod_str)
        product_summary_str = "\n".join([f"- {row}" for row in product_rows])

    # 4. Region breakdown
    region_summary_str = "No regional data available."
    if has_regions:
        region_rows = []
        for _, row in region_df.iterrows():
            reg_str = (
                f"Region: {row['region']} | "
                f"Spend: ${row['spend']:,.2f} | "
                f"Conversions: {row['conversions']:,} | "
                f"CVR: {row['cvr']:.2%}"
            )
            if has_revenue:
                reg_str += f" | Revenue: ${row['revenue']:,.2f} | ROAS: {row['roas']:.2f}x"
            region_rows.append(reg_str)
        region_summary_str = "\n".join([f"- {row}" for row in region_rows])

    # Construct Prompt
    prompt = f"""
You are a senior business strategist, product marketer, and digital marketing expert. Analyze this performance data from the "AI Marketing + Product + Region Intelligence Engine" and write a strategic business report.

### OVERALL FINANCIAL PERFORMANCE
{overall_summary}

### CAMPAIGN PERFORMANCE ROLLUP
{campaign_summary_str}

### PRODUCT PERFORMANCE ROLLUP
{product_summary_str}

### REGIONAL PERFORMANCE ROLLUP
{region_summary_str}

Please generate a professional, strategic markdown report answering the following core business questions:

1. **Are my ads profitable?**
   - Provide a clear, objective verdict on profitability. Detail whether the overall ROAS and profit figures represent a successful business model.
2. **Which campaigns should I scale or stop?**
   - Identify specific high-performing campaigns to scale (e.g. high conversions, high ROAS, low CPC).
   - Identify low-performing campaigns to fix or completely stop.
3. **Which products make the most money?**
   - Highlight the best-selling products driving the highest revenue and profit margins.
   - Call out products that are wasting valuable ad budget (high spend, low conversion rates or net losses).
4. **Which regions should I focus on?**
   - If regional data is present, evaluate where to double down geographically. Identify top-performing and underperforming territories.
5. **Exact Actions Checklist**:
   Write a structured markdown task list of concrete actions to execute immediately:
   - `[ ]` **Campaign Actions**: [Scale / Fix / Stop] campaign name (e.g., scale 'Google Search - Brand' due to 4.1x ROAS).
   - `[ ]` **Product Actions**: [Promote / Reduce] product name (e.g., promote 'Enterprise SaaS').
   - `[ ]` **Regional Actions**: [Increase / Decrease targeting] region name (e.g., increase targeting in 'North America').

Use clean Markdown layout. Do not include raw tables, just the structured report headers and paragraphs. Keep the tone analytical, concise, and executive-level.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional business strategist and CMO. Your job is to analyze advertising, product sales, and regional performance metrics, and draft a clear, action-oriented business report."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1800
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Error calling OpenAI API: {str(e)}")
