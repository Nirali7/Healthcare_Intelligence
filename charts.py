"""Plotly chart builders. Functions return Plotly figures."""
import plotly.express as px

NAVY = "#102A43"
TEAL = "#0D9488"
BLUE = "#3B82F6"
PALETTE = ["#0D9488", "#3B82F6", "#F59E0B", "#8B5CF6", "#EC4899", "#14B8A6", "#64748B"]


def _empty_fig(message="No data available for this chart"):
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(size=16, color="#486581"))
    fig.update_layout(height=420, template="plotly_white")
    return fig


def _count_chart(data, column, title, horizontal=False):
    if data is None or data.empty or column not in data.columns:
        return _empty_fig()
    counts = data[column].fillna("Unknown").astype(str).value_counts().reset_index()
    counts.columns = [column, "Patients"]
    if horizontal:
        fig = px.bar(counts.sort_values("Patients"), x="Patients", y=column, orientation="h",
                     title=title, color_discrete_sequence=[TEAL], text="Patients")
    else:
        fig = px.bar(counts, x=column, y="Patients", title=title,
                     color_discrete_sequence=[TEAL], text="Patients")
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(height=460, template="plotly_white", title_font_size=20,
                      margin=dict(l=20, r=30, t=65, b=45),
                      xaxis_title=None, yaxis_title=None)
    return fig


def patients_by_condition_chart(data):
    return _count_chart(data, "medical_condition", "Patients by Medical Condition", True)


def patients_by_hospital_chart(data):
    return _count_chart(data, "hospital", "Patients by Hospital", True)


def admission_type_chart(data):
    if data is None or data.empty or "admission_type" not in data.columns:
        return _empty_fig()
    counts = data["admission_type"].fillna("Unknown").astype(str).value_counts().reset_index()
    counts.columns = ["Admission Type", "Patients"]
    fig = px.pie(counts, names="Admission Type", values="Patients", hole=.55,
                 title="Admission Type Distribution", color_discrete_sequence=PALETTE)
    fig.update_layout(height=460, template="plotly_white", title_font_size=20)
    return fig


def insurance_provider_chart(data):
    return _count_chart(data, "insurance_provider", "Patients by Insurance Provider", True)


def age_distribution_chart(data):
    if data is None or data.empty or "age" not in data.columns:
        return _empty_fig()
    fig = px.histogram(data, x="age", nbins=20, title="Patient Age Distribution",
                       color_discrete_sequence=[TEAL])
    fig.update_layout(height=460, template="plotly_white", title_font_size=20,
                      xaxis_title="Age", yaxis_title="Number of patients")
    return fig


def billing_by_condition_chart(data):
    if data is None or data.empty or not {"medical_condition", "billing_amount"}.issubset(data.columns):
        return _empty_fig()
    grouped = data.groupby("medical_condition", dropna=False)["billing_amount"].mean().reset_index()
    grouped["medical_condition"] = grouped["medical_condition"].fillna("Unknown").astype(str)
    fig = px.bar(grouped.sort_values("billing_amount"), x="billing_amount", y="medical_condition",
                 orientation="h", title="Average Billing by Medical Condition",
                 labels={"billing_amount": "Average billing amount", "medical_condition": "Condition"},
                 color_discrete_sequence=[BLUE])
    fig.update_layout(height=460, template="plotly_white", title_font_size=20)
    return fig


def length_of_stay_chart(data):
    if data is None or data.empty or "length_of_stay" not in data.columns:
        return _empty_fig()
    fig = px.histogram(data.dropna(subset=["length_of_stay"]), x="length_of_stay", nbins=20,
                       title="Length of Stay Distribution", color_discrete_sequence=[BLUE])
    fig.update_layout(height=460, template="plotly_white", title_font_size=20,
                      xaxis_title="Length of stay (days)", yaxis_title="Number of patients")
    return fig


def gender_distribution_chart(data):
    if data is None or data.empty or "gender" not in data.columns:
        return _empty_fig()
    counts = data["gender"].fillna("Unknown").astype(str).value_counts().reset_index()
    counts.columns = ["Gender", "Patients"]
    fig = px.pie(counts, names="Gender", values="Patients", hole=.55,
                 title="Gender Distribution", color_discrete_sequence=[TEAL, BLUE, "#F59E0B"])
    fig.update_layout(height=460, template="plotly_white", title_font_size=20)
    return fig
