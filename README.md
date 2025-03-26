# IRR Calculator App

This is a Streamlit-based web application that calculates the Internal Rate of Return (IRR) for investment deals based on uploaded Excel cash flow data.

## Features

- Upload an Excel file with cash flows and deal metadata
- Filter by industry, region, fund, and liquidation status
- Select a date range for filtering
- IRR calculated by:
  - Category (Industry, Region, Status, Fund)
  - Deal level
- Logs skipped entries (no valid cash flows)
- Download outputs as:
  - CSV (category IRRs, deal IRRs)
  - Excel (multi-sheet export including skipped entries)
- IRR visualized in a bar chart

## How to Run

### Locally

1. Clone this repo or download the zip
2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
streamlit run irr_app.py
```

### On Streamlit Cloud

1. Push to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Create a new app pointing to `irr_app.py`
4. Deploy and share your live URL!

---

**Built with ❤️ using Streamlit**