# AI Ads Report Generator 📊

An MVP web application built with **Streamlit** and **Python** to analyze advertising performance data. Upload your campaign performance CSV files, inspect real-time interactive charts and KPI metrics, generate AI-powered strategic recommendations via **OpenAI**, and export everything into a professional, download-ready **PDF performance report**.

---

## Features

- **💡 Complete KPI Dashboard**: Real-time computation of vital ad metrics like Total Spend, CTR, CPC, CVR, Net Profit, and ROAS.
- **📈 Interactive Visualizations**: Plotly-powered charts tracking trends over time and comparing campaign performance metrics dynamically.
- **🧠 AI Written Insights**: Automated campaign analysis, performance summaries, and actionable budget suggestions using OpenAI (`gpt-4o-mini`).
- **📄 Downloadable PDF Export**: Print-ready, styled PDF report compiled in memory using ReportLab.
- **🎨 Interactive Demo Mode**: Includes pre-loaded realistic data to preview application functionality immediately without uploads.

---

## Project Structure

```text
AI-Ads-Report-Dashboard-Generator/
├── app.py                  # Main Streamlit web application front-end
├── sample_data.csv         # Realistic multi-campaign sample datasett
├── requirements.txt        # Application dependencies
├── README.md               # Setup and usage instructions
└── utils/
    ├── data_processor.py   # Aggregations, metrics calculations, and input validation
    ├── openai_insights.py  # OpenAI API interaction and prompts
    └── pdf_generator.py    # ReportLab-based PDF styling and compilation
```

---

## Getting Started (Local Setup)

### Prerequisites
Make sure you have **Python 3.9+** installed on your local machine.

### 1. Clone the repository and navigate inside
```bash
git clone <repository_url>
cd AI-Ads-Report-Dashboard-Generator
```

### 2. Set up a virtual environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Configure OpenAI API Key
You can set your API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```
*Alternatively, you can type it directly into the secure sidebar input inside the running Streamlit web application.*

### 5. Launch the application
```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501` to view the app!

---

## Input CSV Data Requirements

If you upload your own ads performance data, make sure the CSV contains the following columns:

| Column | Type | Description |
| :--- | :--- | :--- |
| `date` | YYYY-MM-DD | The date of the tracked performance |
| `campaign_name`| String | Name of the campaign (e.g. "Google Search - Brand") |
| `impressions` | Integer | Total number of ad views |
| `clicks` | Integer | Total clicks recorded |
| `spend` | Decimal | Amount spent on the campaign (USD) |
| `conversions` | Integer | Total conversions (e.g. purchases, sign-ups) |
| `revenue` | Decimal | **(Optional)** Generated campaign revenue (USD) |

> [!TIP]
> If the `revenue` column is missing, the dashboard automatically hides monetary ROI values (like ROAS and Profit) and shifts targets to clicks, CTR, and conversions optimization, ensuring your dashboard remains fully functional.
