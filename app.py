import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from utils.data_processor import (
    load_and_validate_data,
    compute_summary_metrics,
    compute_campaign_metrics,
    compute_product_metrics,
    compute_region_metrics,
    get_best_and_worst_campaigns,
    compute_trends
)
from utils.openai_insights import generate_insights
from utils.pdf_generator import generate_pdf

# Set page config for responsive layout
st.set_page_config(
    page_title="AI Ads Report Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS
st.markdown("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Metrics Card container */
    .metric-container {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 24px;
    }
    
    /* Premium KPI Card styling */
    .kpi-card {
        flex: 1 1 200px;
        background: #ffffff;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    }
    
    .kpi-label {
        font-size: 0.85rem;
        color: #4B5563;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 4px;
    }
    
    .kpi-subtext {
        font-size: 0.75rem;
        color: #0D9488;
        font-weight: 600;
    }
    
    /* Subtitle styling */
    .dashboard-subtitle {
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 24px;
    }
    
    /* AI Insights Container */
    .ai-insights-box {
        background-color: #F8FAFC;
        border-left: 5px solid #0D9488;
        border-radius: 8px;
        padding: 24px;
        margin-top: 16px;
        margin-bottom: 24px;
        box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02);
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONFIG -----------------
st.sidebar.markdown("<h2 style='text-align: center; color: #1E3A8A;'>⚙️ Configuration</h2>", unsafe_allow_html=True)

# API Key check order: User Input -> Environment Variable
env_key = os.getenv("OPENAI_API_KEY", "")
api_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    value=env_key,
    help="Enter your OpenAI API key to unlock written reports. We respect your privacy, your key is never saved."
)

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Ads Performance Data")

# Option to use demo data
use_demo = st.sidebar.checkbox("Use Demo Data", value=False, help="Check to load sample campaign data instead of uploading")

uploaded_file = None
if not use_demo:
    uploaded_file = st.sidebar.file_uploader(
        "Upload Ads Performance CSV",
        type=["csv"],
        key="sidebar_uploader",
        help="CSV must contain: date, campaign_name, impressions, clicks, spend, conversions. Revenue column is optional."
    )

# Sample Data Download
with open("sample_data.csv", "r") as f:
    sample_csv = f.read()

st.sidebar.download_button(
    label="📥 Download Sample CSV Template",
    data=sample_csv,
    file_name="sample_ads_data.csv",
    mime="text/csv",
    help="Download this template to see required columns."
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align: center; font-size: 0.8rem; color: #9CA3AF;'>"
    "AI Ads Report Generator v1.1.0<br>Marketing, Product & Region Intelligence"
    "</div>",
    unsafe_allow_html=True
)

# ----------------- DATA LOADING -----------------
df = None
data_source_name = ""

if use_demo:
    try:
        df = load_and_validate_data("sample_data.csv")
        data_source_name = "Realistic Demo Campaigns"
    except Exception as e:
        st.error(f"Error loading demo data: {str(e)}")
else:
    # Check both sidebar and main uploader
    sidebar_file = st.session_state.get("sidebar_uploader")
    main_file = st.session_state.get("main_uploader")
    active_upload = sidebar_file if sidebar_file is not None else main_file
    
    if active_upload is not None:
        try:
            df = load_and_validate_data(active_upload)
            data_source_name = active_upload.name
        except Exception as e:
            st.error(f"Failed to process uploaded file: {str(e)}")
            st.info("Please make sure your CSV contains: date, campaign_name, impressions, clicks, spend, conversions")

# ----------------- MAIN INTERFACE -----------------
if df is not None:
    # 1. Title section
    st.markdown("<h1 style='color: #1E3A8A; margin-bottom: 5px;'>📊 AI Marketing, Product & Region Intelligence</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='dashboard-subtitle'>Analyzing <b>{data_source_name}</b> across {df['campaign_name'].nunique()} campaigns.</p>", unsafe_allow_html=True)

    # 2. Compute Aggregates
    summary = compute_summary_metrics(df)
    campaign_df = compute_campaign_metrics(df)
    product_df = compute_product_metrics(df) if summary['has_products'] else None
    region_df = compute_region_metrics(df) if summary['has_regions'] else None
    
    best_worst = get_best_and_worst_campaigns(campaign_df, summary['has_revenue'])
    trends = compute_trends(df)

    # 3. KPI Cards Layout
    st.subheader("Key Performance Indicators")
    kpi_cols = st.columns(4)
    
    # Card 1: Spend
    spend_val = f"${summary['total_spend']:,.2f}"
    with kpi_cols[0]:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-label">Total Spend</div>
                <div class="kpi-value">{spend_val}</div>
                <div class="kpi-subtext">Across {summary['total_impressions']:,} impressions</div>
            </div>""",
            unsafe_allow_html=True
        )
        
    # Card 2: CTR & CPC
    ctr_val = f"{summary['overall_ctr']:.2%}"
    cpc_val = f"${summary['overall_cpc']:.2f}"
    with kpi_cols[1]:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-label">Click Performance</div>
                <div class="kpi-value">{ctr_val}</div>
                <div class="kpi-subtext">Avg CPC: {cpc_val} ({summary['total_clicks']:,} clicks)</div>
            </div>""",
            unsafe_allow_html=True
        )

    # Card 3: Conversions & CVR
    cvr_val = f"{summary['overall_cvr']:.2%}"
    conv_val = f"{summary['total_conversions']:,}"
    with kpi_cols[2]:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-label">Conversions (CVR)</div>
                <div class="kpi-value">{conv_val}</div>
                <div class="kpi-subtext">Conversion Rate: {cvr_val}</div>
            </div>""",
            unsafe_allow_html=True
        )

    # Card 4: ROAS & Profit OR Top Campaign
    if summary['has_revenue']:
        roas_val = f"{summary['overall_roas']:.2f}x"
        profit_val = f"${summary['total_profit']:,.2f}"
        with kpi_cols[3]:
            st.markdown(
                f"""<div class="kpi-card">
                    <div class="kpi-label">Return on Ad Spend</div>
                    <div class="kpi-value">{roas_val}</div>
                    <div class="kpi-subtext">Net Profit: {profit_val}</div>
                </div>""",
                unsafe_allow_html=True
            )
    else:
        with kpi_cols[3]:
            st.markdown(
                f"""<div class="kpi-card">
                    <div class="kpi-label">Top Campaign</div>
                    <div class="kpi-value" style="font-size: 1.35rem; padding-top: 8px; padding-bottom: 8px;">{best_worst['best_name']}</div>
                    <div class="kpi-subtext">By total conversions</div>
                </div>""",
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Render Tabs dynamically
    tab_titles = ["🎯 Campaign Analytics"]
    if summary['has_products']:
        tab_titles.append("📦 Product Sales")
    if summary['has_regions']:
        tab_titles.append("🗺️ Region Performance")

    dashboard_tabs = st.tabs(tab_titles)

    # --- TAB 1: CAMPAIGN ANALYTICS ---
    with dashboard_tabs[0]:
        chart_cols = st.columns(2)
        with chart_cols[0]:
            st.subheader("Performance Trends Over Time")
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=trends['date'], y=trends['spend'],
                name='Daily Spend ($)',
                line=dict(color='#1E3A8A', width=3, shape='spline'),
                fill='tozeroy',
                fillcolor='rgba(30, 58, 138, 0.05)'
            ))
            
            if summary['has_revenue']:
                fig_trend.add_trace(go.Scatter(
                    x=trends['date'], y=trends['revenue'],
                    name='Daily Revenue ($)',
                    line=dict(color='#0D9488', width=3, shape='spline'),
                    fill='tozeroy',
                    fillcolor='rgba(13, 148, 136, 0.05)'
                ))
                y_title = "Amount ($)"
            else:
                fig_trend.add_trace(go.Scatter(
                    x=trends['date'], y=trends['conversions'],
                    name='Daily Conversions',
                    line=dict(color='#0D9488', width=3, shape='spline'),
                    yaxis='y2'
                ))
                fig_trend.update_layout(
                    yaxis2=dict(title="Conversions", overlaying='y', side='right')
                )
                y_title = "Spend ($)"

            fig_trend.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='#E5E7EB', title="Date"),
                yaxis=dict(showgrid=True, gridcolor='#E5E7EB', title=y_title),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
                margin=dict(l=40, r=40, t=10, b=40), height=380
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        with chart_cols[1]:
            st.subheader("Campaign Efficiency Metrics")
            metric_options = ['spend', 'conversions', 'ctr', 'cpc', 'cvr']
            metric_labels = ['Total Spend ($)', 'Total Conversions', 'Click-Through Rate (CTR)', 'Cost Per Click (CPC)', 'Conversion Rate (CVR)']
            if summary['has_revenue']:
                metric_options.extend(['revenue', 'roas', 'profit'])
                metric_labels.extend(['Total Revenue ($)', 'Return on Ad Spend (ROAS)', 'Net Profit ($)'])
                
            selected_metric = st.selectbox(
                "Compare campaign metrics:",
                options=metric_options,
                format_func=lambda x: metric_labels[metric_options.index(x)],
                key="camp_metric_select"
            )
            
            bar_color = '#0D9488' if selected_metric in ['roas', 'profit', 'revenue', 'conversions'] else '#1E3A8A'
            fig_bar = go.Figure(data=[go.Bar(
                x=campaign_df['campaign_name'],
                y=campaign_df[selected_metric],
                marker_color=bar_color,
                hovertemplate="Campaign: %{x}<br>Value: %{y}<extra></extra>",
                width=0.4
            )])
            
            yaxis_format = {}
            if selected_metric in ['ctr', 'cvr']:
                yaxis_format = dict(tickformat='.1%')
            elif selected_metric in ['spend', 'revenue', 'profit', 'cpc']:
                yaxis_format = dict(tickformat='$,.2f')
            elif selected_metric == 'roas':
                yaxis_format = dict(ticksuffix='x')

            fig_bar.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, title="Campaign"),
                yaxis=dict(showgrid=True, gridcolor='#E5E7EB', **yaxis_format),
                margin=dict(l=40, r=40, t=35, b=40), height=320
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Detailed Campaign Performance")
        display_camp_df = campaign_df.copy()
        cols_format = {
            'campaign_name': 'Campaign Name', 'impressions': 'Impressions', 'clicks': 'Clicks',
            'spend': 'Spend ($)', 'conversions': 'Conversions', 'ctr': 'CTR', 'cpc': 'CPC ($)', 'cvr': 'CVR'
        }
        if summary['has_revenue']:
            cols_format.update({'revenue': 'Revenue ($)', 'roas': 'ROAS', 'profit': 'Profit ($)'})
            
        display_camp_df = display_camp_df[list(cols_format.keys())].rename(columns=cols_format)
        format_rules = {
            'Impressions': '{:,.0f}', 'Clicks': '{:,.0f}', 'Spend ($)': '${:,.2f}',
            'Conversions': '{:,.0f}', 'CTR': '{:.2%}', 'CPC ($)': '${:,.2f}', 'CVR': '{:.2%}'
        }
        if summary['has_revenue']:
            format_rules.update({'Revenue ($)': '${:,.2f}', 'ROAS': '{:.2f}x', 'Profit ($)': '${:,.2f}'})

        st.dataframe(display_camp_df.style.format(format_rules), use_container_width=True, hide_index=True)

    # --- TAB 2: PRODUCT SALES ---
    current_tab_idx = 1
    if summary['has_products']:
        with dashboard_tabs[current_tab_idx]:
            p_cols = st.columns(2)
            
            with p_cols[0]:
                st.subheader("Product Revenue / Conversion Share")
                pie_val = 'profit' if summary['has_revenue'] else 'conversions'
                pie_label = 'Net Profit ($)' if summary['has_revenue'] else 'Conversions'
                
                fig_p_pie = px.pie(
                    product_df, values=pie_val, names='product_name', hole=0.4,
                    color_discrete_sequence=['#1E3A8A', '#0D9488', '#6366F1', '#3B82F6']
                )
                fig_p_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_p_pie.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10), height=350,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_p_pie, use_container_width=True)
                
            with p_cols[1]:
                st.subheader("Product Spend vs. Financial Return")
                fig_p_bar = go.Figure()
                fig_p_bar.add_trace(go.Bar(
                    x=product_df['product_name'], y=product_df['spend'],
                    name='Spend ($)', marker_color='#1E3A8A', width=0.3
                ))
                if summary['has_revenue']:
                    fig_p_bar.add_trace(go.Bar(
                        x=product_df['product_name'], y=product_df['revenue'],
                        name='Revenue ($)', marker_color='#0D9488', width=0.3
                    ))
                else:
                    fig_p_bar.add_trace(go.Bar(
                        x=product_df['product_name'], y=product_df['conversions'],
                        name='Conversions', marker_color='#0D9488', width=0.3
                    ))
                fig_p_bar.update_layout(
                    barmode='group', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=40, r=40, t=35, b=40), height=350,
                    xaxis=dict(title="Product"), yaxis=dict(gridcolor='#E5E7EB', title="Value ($ / Count)")
                )
                st.plotly_chart(fig_p_bar, use_container_width=True)
                
            st.subheader("Detailed Product Performance")
            display_prod_df = product_df.copy()
            p_cols_format = {
                'product_name': 'Product Name', 'spend': 'Spend ($)', 'conversions': 'Conversions', 'cvr': 'Conversion Rate'
            }
            if summary['has_revenue']:
                p_cols_format.update({'revenue': 'Revenue ($)', 'profit': 'Profit ($)', 'roas': 'ROAS'})
                
            display_prod_df = display_prod_df[list(p_cols_format.keys())].rename(columns=p_cols_format)
            p_format_rules = {
                'Spend ($)': '${:,.2f}', 'Conversions': '{:,.0f}', 'Conversion Rate': '{:.2%}'
            }
            if summary['has_revenue']:
                p_format_rules.update({'Revenue ($)': '${:,.2f}', 'Profit ($)': '${:,.2f}', 'ROAS': '{:.2f}x'})
                
            st.dataframe(display_prod_df.style.format(p_format_rules), use_container_width=True, hide_index=True)
            
        current_tab_idx += 1

    # --- TAB 3: REGION PERFORMANCE ---
    if summary['has_regions']:
        with dashboard_tabs[current_tab_idx]:
            r_cols = st.columns(2)
            
            with r_cols[0]:
                st.subheader("Geographical Spend Allocation")
                fig_r_pie = px.pie(
                    region_df, values='spend', names='region', hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_r_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_r_pie.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10), height=350,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_r_pie, use_container_width=True)
                
            with r_cols[1]:
                st.subheader("Regional Marketing Efficiency")
                fig_r_bar = go.Figure()
                if summary['has_revenue']:
                    fig_r_bar.add_trace(go.Bar(
                        x=region_df['region'], y=region_df['roas'],
                        name='ROAS (x)', marker_color='#0D9488', width=0.3
                    ))
                    y_axis_label = "Return on Ad Spend (ROAS)"
                    hover_format = "Region: %{x}<br>ROAS: %{y:.2f}x<extra></extra>"
                else:
                    fig_r_bar.add_trace(go.Bar(
                        x=region_df['region'], y=region_df['cvr'],
                        name='Conversion Rate (CVR)', marker_color='#1E3A8A', width=0.3
                    ))
                    y_axis_label = "Conversion Rate (CVR)"
                    hover_format = "Region: %{x}<br>CVR: %{y:.2%}<extra></extra>"
                    
                fig_r_bar.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=40, r=40, t=35, b=40), height=350,
                    xaxis=dict(title="Region"), yaxis=dict(gridcolor='#E5E7EB', title=y_axis_label)
                )
                fig_r_bar.update_traces(hovertemplate=hover_format)
                st.plotly_chart(fig_r_bar, use_container_width=True)
                
            st.subheader("Detailed Region Performance")
            display_reg_df = region_df.copy()
            r_cols_format = {
                'region': 'Region Name', 'spend': 'Spend ($)', 'conversions': 'Conversions', 'cvr': 'Conversion Rate'
            }
            if summary['has_revenue']:
                r_cols_format.update({'revenue': 'Revenue ($)', 'roas': 'ROAS'})
                
            display_reg_df = display_reg_df[list(r_cols_format.keys())].rename(columns=r_cols_format)
            r_format_rules = {
                'Spend ($)': '${:,.2f}', 'Conversions': '{:,.0f}', 'Conversion Rate': '{:.2%}'
            }
            if summary['has_revenue']:
                r_format_rules.update({'Revenue ($)': '${:,.2f}', 'ROAS': '{:.2f}x'})
                
            st.dataframe(display_reg_df.style.format(r_format_rules), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 6. AI Insights Section
    st.markdown("<h2 style='color: #1E3A8A;'>🧠 AI Marketing + Product + Region Intelligence</h2>", unsafe_allow_html=True)
    
    # Initialize session state for AI insights
    if "ai_insights" not in st.session_state:
        st.session_state["ai_insights"] = None

    # Alert if API key is empty
    if not api_key:
        st.info("💡 To generate a written AI strategic plan, please enter your OpenAI API Key in the sidebar.")
    else:
        if st.session_state["ai_insights"] is None:
            trigger_button = st.button("✨ Generate AI Strategic Report", type="primary")
            if trigger_button:
                with st.spinner("Compiling marketing, product sales, and geographical metrics for executive report..."):
                    try:
                        insights = generate_insights(summary, campaign_df, product_df, region_df, api_key)
                        st.session_state["ai_insights"] = insights
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate insights: {str(e)}")
        else:
            # Display insights in a nice styled container
            st.markdown(f'<div class="ai-insights-box">', unsafe_allow_html=True)
            st.markdown(st.session_state["ai_insights"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Allow regeneration
            re_trigger = st.button("🔄 Regenerate Report")
            if re_trigger:
                st.session_state["ai_insights"] = None
                st.rerun()

    # 7. PDF Report Generation & Download
    st.markdown("---")
    st.markdown("<h3 style='color: #1E3A8A;'>📥 Download Performance Report</h3>", unsafe_allow_html=True)
    st.markdown("Export a professional PDF performance report containing the metrics summary, campaign performance table, product table, regional table, and AI-generated insights.")
    
    # Dynamic PDF Generator wrapper
    try:
        pdf_bytes = generate_pdf(
            summary_metrics=summary,
            campaign_df=campaign_df,
            product_df=product_df,
            region_df=region_df,
            ai_insights_text=st.session_state["ai_insights"]
        )
        
        st.download_button(
            label="📄 Download PDF Performance Report",
            data=pdf_bytes,
            file_name=f"Marketing_Intelligence_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            type="primary" if st.session_state["ai_insights"] else "secondary"
        )
    except Exception as e:
        st.error(f"Could not prepare PDF download: {str(e)}")

else:
    # Landing page layout before uploading files
    st.markdown("<h1 style='color: #1E3A8A; text-align: center; margin-top: 50px;'>📊 AI Marketing, Product & Region Intelligence</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #4B5563;'>Upload your ads and product metrics CSV to immediately build dashboards, compute metrics, and write LLM-powered marketing summaries.</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Prominent drag-and-drop uploader in the center of the main page
    col_upload_left, col_upload_mid, col_upload_right = st.columns([1, 2, 1])
    with col_upload_mid:
        main_uploaded_file = st.file_uploader(
            "Drag and drop your performance CSV here",
            type=["csv"],
            key="main_uploader",
            help="CSV must contain: date, campaign_name, impressions, clicks, spend, conversions. product_name and region are optional."
        )
        if main_uploaded_file is not None:
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """<div style='background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 24px; text-align: center; min-height: 200px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);'>
                <h3 style='color: #1E3A8A; margin-top: 0;'>📈 Complete Analytics</h3>
                <p style='color: #4B5563; font-size: 0.9rem;'>Instantly compute vital SaaS and advertising ratios like CTR, CPC, Conversion Rate, Profit, and ROAS overall and per campaign.</p>
            </div>""",
            unsafe_allow_html=True
        )
        
    with col2:
        st.markdown(
            """<div style='background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 24px; text-align: center; min-height: 200px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);'>
                <h3 style='color: #1E3A8A; margin-top: 0;'>🧠 AI Recommendations</h3>
                <p style='color: #4B5563; font-size: 0.9rem;'>Feed structured performance metrics to OpenAI to generate high-quality strategic advice on budgets, creative performance, and ad optimization.</p>
            </div>""",
            unsafe_allow_html=True
        )
        
    with col3:
        st.markdown(
            """<div style='background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 24px; text-align: center; min-height: 200px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);'>
                <h3 style='color: #1E3A8A; margin-top: 0;'>📄 PDF Export</h3>
                <p style='color: #4B5563; font-size: 0.9rem;'>Download a clean, executive-ready PDF report containing campaign performance metrics tables and AI written comments with a single click.</p>
            </div>""",
            unsafe_allow_html=True
        )
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info("👈 Enable 'Use Demo Data' in the sidebar or upload a CSV file to get started!")
