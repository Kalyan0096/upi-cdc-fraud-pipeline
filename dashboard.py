import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="UPI Fraud Monitor", layout="wide")
st.title("UPI Fraud Monitor")
st.caption("Postgres CDC, Debezium, Redpanda, PySpark Structured Streaming")

def q(sql):
    conn = psycopg2.connect(host="localhost", port=5432, user="upi",
                            password="upi", dbname="upidb")
    try:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)
    finally:
        conn.close()

@st.fragment(run_every=5)
def live():
    txns = q("SELECT count(*) AS n FROM transactions")["n"][0]
    alerts = q("SELECT count(*) AS n FROM fraud_alerts")["n"][0]
    flagged = q("SELECT coalesce(sum(amount),0) AS s FROM fraud_alerts")["s"][0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Transactions", f"{txns:,}")
    c2.metric("Fraud alerts", f"{alerts:,}")
    c3.metric("Amount flagged (INR)", f"{float(flagged):,.0f}")

    left, right = st.columns(2)
    with left:
        st.subheader("Alerts by rule")
        st.bar_chart(q("SELECT * FROM v_alerts_by_rule").set_index("rule"))
    with right:
        st.subheader("Top risky users")
        st.dataframe(q("SELECT * FROM v_top_risky_users LIMIT 10"),
                     hide_index=True, width='stretch')

    st.subheader("Latest alerts")
    st.dataframe(q("SELECT txn_id, user_id, device_id, amount, city, reasons, "
                   "detected_at FROM fraud_alerts ORDER BY alert_id DESC LIMIT 20"),
                 hide_index=True, width='stretch')

live()
