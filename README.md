# Mai Shan Yun Inventory Intelligence Dashboard

An interactive dashboard for restaurant inventory management that analyzes sales data, tracks ingredient usage, and predicts reorder needs.

## About

This dashboard helps Mai Shan Yun restaurant optimize inventory by:
- Tracking shipment patterns and supply levels
- Identifying cost-saving opportunities
- Monitoring ingredient usage trends

Built for the Mai Shan Yun Challenge.

## Features

**Shipment Tracking**
- Monitor ingredient supply levels in real-time
- Automated alerts for low stock items
- Visualization of shipment frequency patterns

**Cost Optimization**
- Identify high-spending categories
- Track which menu items drive the most costs
- Recommendations for bulk purchasing

**Ingredient Insights**
- Monthly usage tracking for all ingredients
- Top-used and least-used ingredient analysis
- Usage trend visualization over time

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mai-shan-inventory-dashboard.git
cd mai-shan-inventory-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure your data files are organized:
```
mai-shan-inventory-dashboard/
├── csv_files/
│   ├── may.csv
│   ├── june.csv
│   ├── july.csv
│   ├── august.csv
│   ├── september.csv
│   └── october.csv
├── Ingredient.csv
└── Shipment.csv
```

## Usage

Run the main dashboard:
```bash
streamlit run dash2.py
```

The dashboard will open in your browser

You can also run individual analysis scripts

## Tech Stack

- Python 3.8+
- Streamlit (dashboard framework)
- Pandas (data analysis)
- Plotly (visualizations)
- Scikit-learn (predictions)

## Key Findings

- 2-3 ingredients require immediate reordering
- Proteins account for 38% of total spending
- May and October have 15% higher sales
- Top 10 items generate 60% of revenue

## Requirements

```
streamlit==1.29.0
pandas==2.1.3
plotly==5.18.0
numpy==1.26.2
scikit-learn==1.3.2
seaborn==0.13.2

```

## License

Created for educational purposes as part of a datathon challenge.

---

This dashboard uses sample restaurant data for demonstration purposes.
