# Healthcare Intelligence — Premium UI Upgrade

This edition redesigns `app.py` and `style.css` with a responsive baby-pink, white, and medical-blue Streamlit interface. It preserves the supplied Cassandra access layer, data preparation, analytics calculations, Plotly chart builders, utility functions, dataset, and dependency requirements.

## Run

Start your existing, initialized Apache Cassandra server in one terminal:

```bash
cassandra -f
```

From this project directory, start the dashboard in another terminal:

```bash
streamlit run app.py
```

These commands assume the packages in `requirements.txt` are already installed and the original `hospital_db.patient_records` table exists. On a new Python environment, install dependencies once with `pip install -r requirements.txt`. For a database-free preview, choose **Provided CSV (local)** in the sidebar.

## Filters and application state

The four filter dropdowns are ordinary Streamlit form widgets (`hospital_filter`, `condition_filter`, `insurance_filter`, `admission_filter`). Their keys are never manually updated by application code. Clicking **Analyze selected data** stores a separate non-widget `_applied_filters` snapshot. Visualizations and tables use this snapshot until the next analysis.

The old `draft_*` keys, reset button, and reset function were removed. Switching between Cassandra and local CSV clears the applied-filter snapshot safely without assigning values to instantiated widget keys.

## Included features

- Overview, Patient Analytics, Hospital Performance, Billing & Stay, and Patient Records sections
- Original KPIs, existing Plotly visualizations, Smart Insights, and data-quality statistics
- Search with literal text matching, page-size selection, safe pagination, and full matching-record CSV download
- CSS-only hover/fade styling, glass-like panels, responsive layouts, and reduced-motion support

## Verification

Python syntax checks passed. Data loading, view rendering, chart construction, form submission, filtering, search, pagination, and CSV export passed a simulated Streamlit interaction test using both local CSV and a mocked Cassandra connection. A live Cassandra/Streamlit browser run must be done on a machine with those services installed and the existing keyspace available.
