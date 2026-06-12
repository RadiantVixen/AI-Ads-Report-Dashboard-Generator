import io
import re
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Color Palette Definitions
PRIMARY_COLOR = colors.HexColor("#1A365D")  # Deep Navy Blue
ACCENT_COLOR = colors.HexColor("#0D9488")   # Teal
DARK_TEXT = colors.HexColor("#1F2937")      # Off-black
LIGHT_BG = colors.HexColor("#F3F4F6")       # Light Grey
WHITE = colors.HexColor("#FFFFFF")
BORDER_COLOR = colors.HexColor("#E5E7EB")

def parse_inline_markdown(text: str) -> str:
    """
    Translates basic markdown bold, italic, and code text into ReportLab HTML-like tags.
    """
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    
    # Re-allow tags we intend to use
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', text)
    
    # Re-normalize escaped symbols
    text = text.replace("&amp;lt;", "&lt;").replace("&amp;gt;", "&gt;")
    return text

def markdown_to_story(md_text: str, styles: dict) -> list:
    """
    Parses a markdown string and returns a list of ReportLab Flowables.
    """
    story = []
    lines = md_text.split('\n')
    
    body_style = ParagraphStyle(
        'PDFBodyText',
        parent=styles['Normal'],
        textColor=DARK_TEXT,
        fontSize=10,
        leading=14,
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'PDFBulletText',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    h1_style = ParagraphStyle(
        'PDFH1',
        parent=styles['Heading1'],
        textColor=PRIMARY_COLOR,
        fontSize=16,
        leading=20,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'PDFH2',
        parent=styles['Heading2'],
        textColor=ACCENT_COLOR,
        fontSize=13,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'PDFH3',
        parent=styles['Heading3'],
        textColor=DARK_TEXT,
        fontSize=11,
        leading=14,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 4))
            continue
            
        if stripped.startswith('# '):
            text = parse_inline_markdown(stripped[2:])
            story.append(Paragraph(text, h1_style))
        elif stripped.startswith('## '):
            text = parse_inline_markdown(stripped[3:])
            story.append(Paragraph(text, h2_style))
        elif stripped.startswith('### '):
            text = parse_inline_markdown(stripped[4:])
            story.append(Paragraph(text, h3_style))
        elif stripped.startswith('- ') or stripped.startswith('* '):
            text = parse_inline_markdown(stripped[2:])
            story.append(Paragraph(f"&bull; {text}", bullet_style))
        elif re.match(r'^\d+\s*[\.\)]\s', stripped) or stripped.startswith('[ ]') or stripped.startswith('[x]'):
            # Match task list or numbered list
            text = parse_inline_markdown(stripped)
            story.append(Paragraph(text, bullet_style))
        else:
            text = parse_inline_markdown(stripped)
            story.append(Paragraph(text, body_style))
            
    return story

def generate_pdf(
    summary_metrics: dict,
    campaign_df: pd.DataFrame,
    product_df: pd.DataFrame = None,
    region_df: pd.DataFrame = None,
    ai_insights_text: str = None
) -> bytes:
    """
    Generates a beautifully structured multi-page PDF performance report in memory.
    """
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom main styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY_COLOR,
        alignment=0,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )

    cell_label_style = ParagraphStyle(
        'CellLabel',
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#4B5563")
    )
    
    cell_value_style = ParagraphStyle(
        'CellValue',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=PRIMARY_COLOR
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=WHITE
    )

    table_body_style = ParagraphStyle(
        'TableBody',
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=DARK_TEXT
    )

    story = []
    
    # --- Header Section ---
    story.append(Paragraph("AI Marketing + Product + Region Intelligence Report", title_style))
    curr_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"CMO Executive Dashboard & Strategic Action Plan &bull; Generated on {curr_date}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_COLOR, spaceAfter=15))
    
    # --- KPI Section ---
    story.append(Paragraph("Key Performance Metrics Summary", section_title_style))
    
    has_revenue = summary_metrics.get('has_revenue', False)
    has_products = summary_metrics.get('has_products', False) and product_df is not None and not product_df.empty
    has_regions = summary_metrics.get('has_regions', False) and region_df is not None and not region_df.empty
    
    spend = f"${summary_metrics['total_spend']:,.2f}"
    clicks = f"{summary_metrics['total_clicks']:,}"
    convs = f"{summary_metrics['total_conversions']:,}"
    ctr = f"{summary_metrics['overall_ctr']:.2%}"
    cpc = f"${summary_metrics['overall_cpc']:.2f}"
    cvr = f"{summary_metrics['overall_cvr']:.2%}"
    
    def make_kpi_cell(label, val):
        return [
            Paragraph(label, cell_label_style),
            Paragraph(val, cell_value_style)
        ]
        
    kpi_data = [
        [make_kpi_cell("Total Spend", spend), make_kpi_cell("Total Clicks", clicks)],
        [make_kpi_cell("Overall CTR", ctr), make_kpi_cell("Average CPC", cpc)],
        [make_kpi_cell("Overall Conversion Rate", cvr), make_kpi_cell("Total Conversions", convs)]
    ]
    
    if has_revenue:
        revenue = f"${summary_metrics['total_revenue']:,.2f}"
        profit = f"${summary_metrics['total_profit']:,.2f}"
        roas = f"{summary_metrics['overall_roas']:.2f}x"
        
        kpi_data = [
            [make_kpi_cell("Total Spend", spend), make_kpi_cell("Total Revenue", revenue)],
            [make_kpi_cell("Net Profit", profit), make_kpi_cell("Return on Ad Spend (ROAS)", roas)],
            [make_kpi_cell("Overall CTR (Clicks/Imps)", ctr), make_kpi_cell("Total Conversions", convs)],
            [make_kpi_cell("Average CPC", cpc), make_kpi_cell("Overall Conversion Rate (CVR)", cvr)]
        ]

    flat_kpi_table_data = []
    for row in kpi_data:
        cell1 = [row[0][0], Spacer(1, 2), row[0][1]]
        cell2 = [row[1][0], Spacer(1, 2), row[1][1]]
        flat_kpi_table_data.append([cell1, cell2])
        
    kpi_table = Table(flat_kpi_table_data, colWidths=[270, 270])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(kpi_table)
    story.append(Spacer(1, 15))
    
    # --- Campaign Breakdown Section ---
    story.append(Paragraph("Campaign Performance Summary Table", section_title_style))
    
    headers = [
        Paragraph("Campaign Name", table_header_style),
        Paragraph("Spend", table_header_style),
        Paragraph("Conversions", table_header_style),
        Paragraph("CTR", table_header_style),
        Paragraph("CPC", table_header_style),
        Paragraph("CVR", table_header_style)
    ]
    col_widths = [160, 60, 65, 55, 55, 55]
    
    if has_revenue:
        headers.extend([
            Paragraph("Revenue", table_header_style),
            Paragraph("ROAS", table_header_style)
        ])
        col_widths = [140, 55, 60, 45, 45, 45, 60, 45]
        
    table_data = [headers]
    for idx, row in campaign_df.iterrows():
        camp_name_p = Paragraph(str(row['campaign_name']), table_body_style)
        spend_p = Paragraph(f"${row['spend']:,.2f}", table_body_style)
        convs_p = Paragraph(f"{int(row['conversions']):,}", table_body_style)
        ctr_p = Paragraph(f"{row['ctr']:.2%}", table_body_style)
        cpc_p = Paragraph(f"${row['cpc']:.2f}", table_body_style)
        cvr_p = Paragraph(f"{row['cvr']:.2%}", table_body_style)
        
        row_cells = [camp_name_p, spend_p, convs_p, ctr_p, cpc_p, cvr_p]
        if has_revenue:
            rev_p = Paragraph(f"${row['revenue']:,.2f}", table_body_style)
            roas_p = Paragraph(f"{row['roas']:.2f}x", table_body_style)
            row_cells.extend([rev_p, roas_p])
        table_data.append(row_cells)
        
    scale_factor = 540.0 / sum(col_widths)
    final_col_widths = [w * scale_factor for w in col_widths]
    
    campaign_table = Table(table_data, colWidths=final_col_widths)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), LIGHT_BG))
    campaign_table.setStyle(TableStyle(t_style))
    story.append(campaign_table)

    # --- Product & Region Section (Page 2) ---
    if has_products or has_regions:
        story.append(PageBreak())
        story.append(Paragraph("Product & Regional Intelligence Analysis", title_style))
        story.append(Paragraph(f"Granular performance rollups &bull; Generated on {curr_date}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_COLOR, spaceAfter=15))
        
        # Product Table
        if has_products:
            story.append(Paragraph("Product Sales Performance Rollup", section_title_style))
            p_headers = [
                Paragraph("Product Name", table_header_style),
                Paragraph("Spend", table_header_style),
                Paragraph("Conversions", table_header_style),
                Paragraph("CVR", table_header_style)
            ]
            p_widths = [200, 110, 110, 120]
            if has_revenue:
                p_headers.extend([
                    Paragraph("Revenue", table_header_style),
                    Paragraph("Profit", table_header_style),
                    Paragraph("ROAS", table_header_style)
                ])
                p_widths = [140, 60, 70, 60, 70, 80, 60]
                
            p_table_data = [p_headers]
            for idx, row in product_df.iterrows():
                p_name_p = Paragraph(str(row['product_name']), table_body_style)
                spend_p = Paragraph(f"${row['spend']:,.2f}", table_body_style)
                convs_p = Paragraph(f"{int(row['conversions']):,}", table_body_style)
                cvr_p = Paragraph(f"{row['cvr']:.2%}", table_body_style)
                
                row_cells = [p_name_p, spend_p, convs_p, cvr_p]
                if has_revenue:
                    rev_p = Paragraph(f"${row['revenue']:,.2f}", table_body_style)
                    prof_p = Paragraph(f"${row['profit']:,.2f}", table_body_style)
                    roas_p = Paragraph(f"{row['roas']:.2f}x", table_body_style)
                    row_cells.extend([rev_p, prof_p, roas_p])
                p_table_data.append(row_cells)
                
            p_scale = 540.0 / sum(p_widths)
            p_final_widths = [w * p_scale for w in p_widths]
            product_table = Table(p_table_data, colWidths=p_final_widths)
            pt_style = [
                ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ]
            for i in range(1, len(p_table_data)):
                if i % 2 == 0:
                    pt_style.append(('BACKGROUND', (0, i), (-1, i), LIGHT_BG))
            product_table.setStyle(TableStyle(pt_style))
            story.append(product_table)
            story.append(Spacer(1, 15))
            
        # Region Table
        if has_regions:
            story.append(Paragraph("Regional Performance Rollup", section_title_style))
            r_headers = [
                Paragraph("Region Name", table_header_style),
                Paragraph("Spend", table_header_style),
                Paragraph("Conversions", table_header_style),
                Paragraph("CVR", table_header_style)
            ]
            r_widths = [200, 110, 110, 120]
            if has_revenue:
                r_headers.extend([
                    Paragraph("Revenue", table_header_style),
                    Paragraph("ROAS", table_header_style)
                ])
                r_widths = [180, 80, 80, 70, 80, 50]
                
            r_table_data = [r_headers]
            for idx, row in region_df.iterrows():
                r_name_p = Paragraph(str(row['region']), table_body_style)
                spend_p = Paragraph(f"${row['spend']:,.2f}", table_body_style)
                convs_p = Paragraph(f"{int(row['conversions']):,}", table_body_style)
                cvr_p = Paragraph(f"{row['cvr']:.2%}", table_body_style)
                
                row_cells = [r_name_p, spend_p, convs_p, cvr_p]
                if has_revenue:
                    rev_p = Paragraph(f"${row['revenue']:,.2f}", table_body_style)
                    roas_p = Paragraph(f"{row['roas']:.2f}x", table_body_style)
                    row_cells.extend([rev_p, roas_p])
                r_table_data.append(row_cells)
                
            r_scale = 540.0 / sum(r_widths)
            r_final_widths = [w * r_scale for w in r_widths]
            region_table = Table(r_table_data, colWidths=r_final_widths)
            rt_style = [
                ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ]
            for i in range(1, len(r_table_data)):
                if i % 2 == 0:
                    rt_style.append(('BACKGROUND', (0, i), (-1, i), LIGHT_BG))
            region_table.setStyle(TableStyle(rt_style))
            story.append(region_table)

    # --- AI Insights Section (Page 3) ---
    if ai_insights_text:
        story.append(PageBreak())
        story.append(Paragraph("AI Strategic Business Intelligence Analysis", title_style))
        story.append(Paragraph("CMO Recommendations and Tactical Action Items", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_COLOR, spaceAfter=15))
        
        ai_story = markdown_to_story(ai_insights_text, styles)
        story.extend(ai_story)
        
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
