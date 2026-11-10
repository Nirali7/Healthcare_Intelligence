# Hospital Data Analytics — Hospital Intelligence

A Streamlit dashboard using Python, Plotly, pandas and the existing Apache Cassandra database.

## Requirements
- Windows
- Apache Cassandra running locally on `127.0.0.1:9042`
- Python 3.11
- Existing keyspace `hospital_db` and table `patient_records`

## Run in VS Code
Open this folder in VS Code, then open **Terminal → New Terminal**.

### Terminal 1 — start Cassandra
```cmd
C:\CASSANDRA\cassandra\bin\cassandra.bat -f
```
Keep this terminal open.

### Terminal 2 — install dependencies
```cmd
py -3.11 -m pip install -r requirements.txt
```

### Terminal 3 — start dashboard
```cmd
py -3.11 -m py_compile app.py db.py analytics.py charts.py utils.py
py -3.11 -m streamlit run app.py
```
Open the Local URL printed in the terminal if the browser does not open automatically.

## Database
The app reads the existing `hospital_db.patient_records` table. It does not create tables or use `ALLOW FILTERING`. To preserve correctness with this dataset size, dashboard filters are applied after the records are loaded into pandas. Data is cached for 5 minutes.

Expected columns commonly include: `patient_id`, `admission_date`, `admission_type`, `age`, `billing_amount`, `blood_type`, `discharge_date`, `doctor`, `gender`, `hospital`, `insurance_provider`, `medical_condition`, `medication`, `name`, `room_number`, and `test_results`.

If your Cassandra table uses different column names, the dashboard still loads available columns; charts requiring missing columns display a no-data message.

## Troubleshooting: duplicate Plotly chart IDs
The dashboard assigns a unique `key` to each Plotly chart instance. If replacing files manually, use the updated `app.py` included in this package.

## Performance note
The dashboard displays one section at a time instead of building every tab's charts simultaneously. This reduces browser work on each filter change. Plotly charts use a white template to match the navy/teal/white visual theme.
