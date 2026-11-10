"""Cassandra access layer for Hospital Data Analytics."""
from cassandra.cluster import Cluster
from cassandra import OperationTimedOut
import pandas as pd

CASSANDRA_HOSTS = ["127.0.0.1"]
CASSANDRA_PORT = 9042
KEYSPACE = "hospital_db"
TABLE = "patient_records"

_cluster = None
_session = None


def get_session():
    """Create/reuse a Cassandra session."""
    global _cluster, _session
    if _session is None:
        _cluster = Cluster(contact_points=CASSANDRA_HOSTS, port=CASSANDRA_PORT)
        _session = _cluster.connect(KEYSPACE)
        _session.default_timeout = 30
    return _session


def close_connection():
    global _cluster, _session
    if _session is not None:
        _session.shutdown()
        _session = None
    if _cluster is not None:
        _cluster.shutdown()
        _cluster = None


def test_connection():
    try:
        session = get_session()
        row = session.execute("SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name=%s", [KEYSPACE]).one()
        if row is None:
            return False, f"Keyspace '{KEYSPACE}' was not found."
        return True, f"Connected to Cassandra keyspace '{KEYSPACE}'."
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def fetch_patient_data(filters=None):
    """
    Read from the existing patient_records table.
    No ALLOW FILTERING and no new tables. Filters are applied in pandas
    after the bounded full-table read, suitable for this ~55k-record project.
    """
    session = get_session()
    rows = session.execute(f"SELECT * FROM {TABLE}")
    records = [row._asdict() for row in rows]
    data = pd.DataFrame(records)
    if data.empty or not filters:
        return data

    for column, value in filters.items():
        if column in data.columns and value not in (None, "", "All", "All Hospitals",
                                                    "All Conditions", "All Providers",
                                                    "All Admission Types"):
            data = data[data[column].astype(str) == str(value)]
    return data.reset_index(drop=True)


def get_all_patient_data():
    return fetch_patient_data()
