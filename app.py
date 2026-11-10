"""Healthcare Intelligence dashboard: presentation and Streamlit interactions.

The Cassandra access, cleaning, analytics and chart-building modules are unchanged.
Filters inside the form are draft selections; only an Analyze submission updates
an independent, non-widget snapshot of the filters used for results.
"""

import html
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from db import fetch_patient_data, test_connection
from analytics import (
    calculate_kpis,
    generate_insights,
    get_summary_statistics,
    prepare_analytics_data,
)
from charts import (
    admission_type_chart,
    age_distribution_chart,
    billing_by_condition_chart,
    gender_distribution_chart,
    insurance_provider_chart,
    length_of_stay_chart,
    patients_by_condition_chart,
    patients_by_hospital_chart,
)
from utils import (
    dataframe_to_csv,
    format_currency,
    format_number,
    get_filter_options,
    prepare_patient_table,
)


st.set_page_config(
    page_title="Healthcare Intelligence | Hospital Analytics",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

STYLESHEET = Path(__file__).with_name("style.css")
if STYLESHEET.is_file():
    st.markdown(f"<style>{STYLESHEET.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

DEFAULTS = {
    "hospital_filter": "All Hospitals",
    "condition_filter": "All Conditions",
    "insurance_filter": "All Providers",
    "admission_filter": "All Admission Types",
}
CHART_COLORS = ["#FF5C8D", "#5DADE2", "#F8BBD9", "#8C79D9", "#64C6BC", "#FFB77A", "#8194AD"]
SECTIONS = [
    "🏠 Overview",
    "♡ Patient Analytics",
    "🏥 Hospital Performance",
    "💰 Billing & Stay",
    "📋 Patient Records",
]


@st.cache_data(ttl=300, show_spinner=False)
def load_patient_records():
    """Use the original Cassandra query and cleaning routine."""
    raw = fetch_patient_data()
    return prepare_analytics_data(raw)


@st.cache_data(ttl=300, show_spinner=False)
def load_csv_records(csv_path):
    """Keep the original local CSV fallback and column normalization."""
    raw = pd.read_csv(csv_path, low_memory=False)
    raw.columns = [str(c).strip().lower().replace(" ", "_") for c in raw.columns]
    raw = raw.rename(columns={"date_of_admission": "admission_date"})
    return prepare_analytics_data(raw)


def options_for(df, column, all_label):
    return [all_label] + get_filter_options(df, column)


def filter_data(df, selected):
    """Preserved in-memory filtering; Cassandra queries are not altered."""
    result = df
    mapping = {
        "hospital": selected["hospital_filter"],
        "medical_condition": selected["condition_filter"],
        "insurance_provider": selected["insurance_filter"],
        "admission_type": selected["admission_filter"],
    }
    all_labels = {
        "hospital": "All Hospitals",
        "medical_condition": "All Conditions",
        "insurance_provider": "All Providers",
        "admission_type": "All Admission Types",
    }
    for col, value in mapping.items():
        if col in result.columns and value != all_labels[col]:
            result = result[result[col].astype(str) == value]
    return result.reset_index(drop=True)


def section_heading(eyebrow, heading, description=""):
    subtitle = f'<p class="section-description">{html.escape(description)}</p>' if description else ""
    st.markdown(
        f'<div class="section-heading"><span class="section-eyebrow">{html.escape(eyebrow)}</span>'
        f'<h2>{html.escape(heading)}</h2>{subtitle}</div>',
        unsafe_allow_html=True,
    )


def show_kpi(icon, label, value, detail, accent):
    st.markdown(
        f'<div class="kpi-card {accent}">'
        f'<span class="kpi-icon" aria-hidden="true">{icon}</span>'
        f'<div class="kpi-label">{html.escape(label)}</div>'
        f'<div class="kpi-value">{html.escape(value)}</div>'
        f'<div class="kpi-detail">{html.escape(detail)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def style_chart(figure):
    """Style Plotly figures without changing their data, labels or calculations."""
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#455675", size=12),
        title_font=dict(family="Inter, sans-serif", color="#25334D", size=17),
        colorway=CHART_COLORS,
        margin=dict(l=18, r=25, t=66, b=38),
        legend=dict(font=dict(size=11)),
    )
    figure.update_xaxes(showline=False, zeroline=False, gridcolor="#F0EEF6")
    figure.update_yaxes(showline=False, zeroline=False, gridcolor="#F0EEF6")
    for trace in figure.data:
        if trace.type == "pie":
            trace.update(marker=dict(colors=CHART_COLORS))
        elif trace.type in ("bar", "histogram"):
            trace.update(marker=dict(color=CHART_COLORS[0]))
    return figure


def chart_card(title, caption, chart_fn, dataset, key):
    with st.container(border=True):
        st.markdown(
            f'<div class="chart-card-heading"><span class="chart-card-icon">✦</span>'
            f'<div><div class="chart-card-title">{html.escape(title)}</div>'
            f'<div class="chart-card-caption">{html.escape(caption)}</div></div></div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            style_chart(chart_fn(dataset)),
            use_container_width=True,
            key=key,
            config={"displaylogo": False, "responsive": True},
        )


def insight_html(message):
    """Preserve analytics bold emphasis while escaping patient-derived strings."""
    escaped = html.escape(message)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def show_insights(dataset):
    section_heading("DATA-DRIVEN OBSERVATIONS", "Smart Insights", "Highlights generated from your selected patient records.")
    for item in generate_insights(dataset):
        st.markdown(
            f'<div class="insight-card"><span class="insight-spark">✦</span>'
            f'<div>{insight_html(item)}</div></div>',
            unsafe_allow_html=True,
        )


def first_patient_page():
    """A widget callback runs before the next script run, safe for page state."""
    st.session_state["patient_page"] = 1


def patient_records(dataset):
    section_heading(
        "PATIENT DATA EXPLORER", "Patient Records",
        "Search the filtered dataset, explore individual pages, or export matching records.",
    )
    with st.container(border=True):
        st.markdown(
            '<div class="table-toolbar-heading"><span>🔎</span><div>'
            '<strong>Explore patient records</strong><small>Search across all visible fields</small>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        search_col, size_col = st.columns([3, 1], gap="medium")
        with search_col:
            query = st.text_input(
                "Search patient records", placeholder="Search name, hospital, condition, provider...",
                key="patient_search", on_change=first_patient_page,
            )
        with size_col:
            page_size = st.selectbox(
                "Rows per page", [10, 25, 50, 100], index=1,
                key="patient_page_size", on_change=first_patient_page,
            )

        table = prepare_patient_table(dataset)
        if query.strip():
            # Literal matching avoids regex errors for input such as "[" or "+".
            mask = table.astype(str).apply(
                lambda column: column.str.contains(query.strip(), case=False, regex=False, na=False)
            ).any(axis=1)
            table = table.loc[mask]

        total_rows = len(table)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        # This adjustment happens BEFORE number_input is instantiated on this run.
        if "patient_page" in st.session_state:
            current_page = st.session_state["patient_page"]
            if current_page is None or current_page < 1 or current_page > total_pages:
                st.session_state["patient_page"] = 1

        info_col, page_col = st.columns([3, 1], gap="medium")
        with page_col:
            page = st.number_input(
                "Page", min_value=1, max_value=total_pages, step=1,
                key="patient_page",
            )
        start_row = (int(page) - 1) * page_size
        end_row = min(start_row + page_size, total_rows)
        with info_col:
            first_shown = start_row + 1 if total_rows else 0
            st.markdown(
                f'<div class="table-count">Showing <strong>{first_shown:,}–{end_row:,}</strong>'
                f' of <strong>{total_rows:,}</strong> matching records</div>',
                unsafe_allow_html=True,
            )

        st.dataframe(
            table.iloc[start_row:end_row],
            use_container_width=True,
            hide_index=True,
            height=490,
        )
        st.download_button(
            "↓  Download matching records (CSV)",
            data=dataframe_to_csv(table),
            file_name="hospital_patient_records.csv",
            mime="text/csv",
            use_container_width=True,
            key="patient_csv_download",
        )
        st.caption("The CSV includes every record matching the applied filters and search—not just the current page.")


# Sidebar and source selection are intentionally rendered before accessing the data.
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand"><span class="brand-icon">✚</span>'
        '<div><strong>HEALTHCARE</strong><small>INTELLIGENCE PLATFORM</small></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-workspace">🩺 <span>Hospital Analytics</span><b>●</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">DATA CONNECTION</div>', unsafe_allow_html=True)
    csv_path = Path(__file__).with_name("healthcare_dataset.csv")
    sources = ["Apache Cassandra"] + (["Provided CSV (local)"] if csv_path.is_file() else [])
    source = st.radio("Patient data source", sources, key="data_source_choice")
    st.markdown(
        '<div class="sidebar-help"><span>💡</span><div><strong>How it works</strong>'
        '<p>Choose your filters and click <b>Analyze</b> to refresh dashboards, '
        'charts, insights and patient records.</p></div></div>',
        unsafe_allow_html=True,
    )
    st.caption("Data cache: 5 minutes · Read-only analytics")

if source == "Apache Cassandra":
    with st.spinner("Connecting to Cassandra and retrieving patient records..."):
        try:
            ok, message = test_connection()
            if not ok:
                st.error("Cassandra is not available. Start your existing Cassandra server or choose the local CSV.")
                st.code(message)
                st.stop()
            data = load_patient_records()
        except Exception as exc:
            st.error("Unable to retrieve data from Apache Cassandra. Your database was not changed.")
            st.code(f"{type(exc).__name__}: {exc}")
            st.stop()
else:
    try:
        data = load_csv_records(str(csv_path))
    except Exception as exc:
        st.error("Unable to read the provided CSV dataset.")
        st.code(f"{type(exc).__name__}: {exc}")
        st.stop()

if data.empty:
    st.warning("No patient records are available in the selected data source.")
    st.stop()

with st.sidebar:
    st.markdown(
        f'<div class="sidebar-connection"><span class="connection-dot"></span>'
        f'<div><strong>Dataset ready</strong><small>{html.escape(source)} · {len(data):,} records</small></div></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<section class="hero"><div class="hero-main">'
    '<span class="hero-eyebrow"><span class="hero-eyebrow-dot">✚</span> HEALTHCARE INTELLIGENCE PLATFORM</span>'
    '<h1>Smarter insights.<br><span>Better care.</span></h1>'
    '<p class="hero-description">A beautiful, intelligent view of patient analytics, hospital performance '
    'and billing intelligence—all in one place.</p>'
    '<div class="hero-tags"><span>✿ Patient Analytics</span><span>⌁ Hospital Performance</span>'
    '<span>✧ Billing Intelligence</span></div></div>'
    '<div class="hero-visual" aria-hidden="true"><div class="visual-glow"></div>'
    '<div class="hero-visual-card"><span class="visual-caption">CARE INTELLIGENCE</span>'
    '<div class="medical-symbol">✚</div><div class="pulse-line">'
    '<svg viewBox="0 0 260 70" role="presentation" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M0 37 H56 L73 37 L88 15 L103 59 L121 27 L133 37 H260" '
    'fill="none" stroke="#FF5C8D" stroke-width="4.2" stroke-linecap="round" '
    'stroke-linejoin="round"/></svg></div><div class="visual-bottom">'
    '<span>HEALTHCARE ANALYTICS</span><span class="visual-live"><i></i> CONNECTED</span>'
    '</div></div><div class="visual-deco deco-one">✿</div><div class="visual-deco deco-two">✚</div>'
    '</div></section>',
    unsafe_allow_html=True,
)

option_sets = {
    "hospital_filter": options_for(data, "hospital", DEFAULTS["hospital_filter"]),
    "condition_filter": options_for(data, "medical_condition", DEFAULTS["condition_filter"]),
    "insurance_filter": options_for(data, "insurance_provider", DEFAULTS["insurance_filter"]),
    "admission_filter": options_for(data, "admission_type", DEFAULTS["admission_filter"]),
}

# Only these two keys are managed by the application itself; the four selectbox
# keys are managed exclusively by Streamlit's widgets, never assigned in code.
if st.session_state.get("_active_source") != source:
    st.session_state["_applied_filters"] = DEFAULTS.copy()
    st.session_state["_active_source"] = source

section_heading("01  /  ANALYSIS WORKSPACE", "Your analysis workspace", "Select your attributes and run a focused analysis.")
with st.container(border=True):
    st.markdown(
        '<div class="filter-panel-head"><span class="filter-panel-icon">⚕</span><div>'
        '<strong>Explore healthcare data</strong>'
        '<p>Personalize your analysis with four powerful filters</p>'
        '</div><span class="panel-pill">INTERACTIVE FILTERS</span></div>',
        unsafe_allow_html=True,
    )
    with st.form("analysis_form", border=False):
        filter_left, filter_right = st.columns(2, gap="large")
        with filter_left:
            st.selectbox("🏥  Hospital", option_sets["hospital_filter"], key="hospital_filter")
            st.selectbox("💳  Insurance provider", option_sets["insurance_filter"], key="insurance_filter")
        with filter_right:
            st.selectbox("🩺  Medical condition", option_sets["condition_filter"], key="condition_filter")
            st.selectbox("📋  Admission type", option_sets["admission_filter"], key="admission_filter")
        st.markdown(
            '<div class="filter-note">✦ Filters take effect when you click <b>Analyze selected data</b>.'
            ' Your previous results remain available until then.</div>',
            unsafe_allow_html=True,
        )
        analyze = st.form_submit_button("✦  Analyze selected data", type="primary", use_container_width=True)

    if analyze:
        # This is a non-widget key. Form widget keys are read, not modified.
        st.session_state["_applied_filters"] = {
            name: st.session_state.get(name, DEFAULTS[name]) for name in DEFAULTS
        }
        st.toast("Analysis refreshed with your selected filters.", icon="✅")

# Normalize stale applied selections if the user switches datasets. This does
# not write to any active or previously created widget's session_state key.
selected = {
    name: value if value in option_sets[name] else DEFAULTS[name]
    for name, value in st.session_state["_applied_filters"].items()
}
filtered = filter_data(data, selected)

st.markdown(
    f'<div class="result-status"><span class="status-indicator"></span>'
    f'<strong>{len(filtered):,} records ready</strong>'
    f'<span>Results based on your last completed analysis</span>'
    f'<span class="status-source">{html.escape(source)}</span></div>',
    unsafe_allow_html=True,
)
if filtered.empty:
    st.warning("No records match the applied filters. Choose a broader selection and click Analyze again.")

section_heading("02  /  PERFORMANCE SNAPSHOT", "Dashboard at a glance", "Key hospital metrics from the current selection.")
kpis = calculate_kpis(filtered)
k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1:
    show_kpi("👥", "Total Patients", format_number(kpis["total_patients"]), "Patient records", "accent-pink")
with k2:
    show_kpi("🩺", "Average Age", f'{kpis["average_age"]:.1f} years', "Patient demographic", "accent-blue")
with k3:
    show_kpi("💳", "Average Billing", format_currency(kpis["average_billing"]), "Billing intelligence", "accent-lilac")
with k4:
    show_kpi("⌛", "Average Stay", f'{kpis["average_stay"]:.1f} days', "Length of stay", "accent-peach")

section_heading("03  /  ANALYTICS EXPLORER", "Explore your insights", "Choose a workspace to focus on the metrics that matter.")
section = st.radio(
    "Dashboard section", SECTIONS, horizontal=True,
    label_visibility="collapsed", key="dashboard_section",
)

if section == "🏠 Overview":
    section_heading("OVERVIEW", "Patient & admission overview")
    left, right = st.columns(2, gap="large")
    with left:
        chart_card("Patient conditions", "Distribution by medical diagnosis", patients_by_condition_chart, filtered, "overview_condition_chart")
    with right:
        chart_card("Admission types", "How patients enter care", admission_type_chart, filtered, "overview_admission_chart")
    left, right = st.columns(2, gap="large")
    with left:
        chart_card("Age distribution", "Age profile of patient records", age_distribution_chart, filtered, "overview_age_chart")
    with right:
        chart_card("Gender distribution", "Patient demographic split", gender_distribution_chart, filtered, "overview_gender_chart")
    show_insights(filtered)

elif section == "♡ Patient Analytics":
    section_heading("PATIENT INTELLIGENCE", "Patient Analytics")
    left, right = st.columns(2, gap="large")
    with left:
        chart_card("Patient conditions", "Most common medical conditions", patients_by_condition_chart, filtered, "patient_condition_chart")
    with right:
        chart_card("Age distribution", "Age range and concentration", age_distribution_chart, filtered, "patient_age_chart")
    left, right = st.columns(2, gap="large")
    with left:
        chart_card("Gender distribution", "Distribution of patient genders", gender_distribution_chart, filtered, "patient_gender_chart")
    with right:
        chart_card("Admission types", "Admission category breakdown", admission_type_chart, filtered, "patient_admission_chart")

elif section == "🏥 Hospital Performance":
    section_heading("HOSPITAL INTELLIGENCE", "Hospital Performance")
    chart_card("Hospital activity", "Patient volumes across hospitals", patients_by_hospital_chart, filtered, "hospital_performance_chart")
    chart_card("Insurance providers", "Patient volumes by insurance provider", insurance_provider_chart, filtered, "insurance_provider_chart")

elif section == "💰 Billing & Stay":
    section_heading("FINANCIAL INTELLIGENCE", "Billing & Length of Stay")
    left, right = st.columns(2, gap="large")
    with left:
        chart_card("Average billing", "Mean billing by medical condition", billing_by_condition_chart, filtered, "billing_condition_chart")
    with right:
        chart_card("Length of stay", "Distribution of hospital stay durations", length_of_stay_chart, filtered, "length_of_stay_chart")
    section_heading("DATA HYGIENE", "Data Quality Summary")
    stats = get_summary_statistics(filtered)
    q1, q2, q3 = st.columns(3, gap="medium")
    q1.metric("Filtered records", format_number(stats["records"]))
    q2.metric("Columns", format_number(stats["columns"]))
    q3.metric("Missing cells", format_number(stats["missing_cells"]))

elif section == "📋 Patient Records":
    patient_records(filtered)

st.markdown(
    f'<footer class="dashboard-footer"><span><b>✚ HEALTHCARE INTELLIGENCE</b> · A clearer view of care.</span>'
    f'<span>Powered by {html.escape(source)} · {len(filtered):,} of {len(data):,} records</span></footer>',
    unsafe_allow_html=True,
)
