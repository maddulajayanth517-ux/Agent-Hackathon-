import os

import pandas as pd
import streamlit as st

from api_client import APIClient, APIError


st.set_page_config(
    page_title="Compliance Reports",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Mentoring Compliance & Insights")

st.caption(
    "Institution-level evidence generated from mentoring activity"
)


user_id = st.sidebar.number_input(
    "Demo User ID",
    min_value=1,
    value=1,
)

client = APIClient(
    base_url=os.getenv(
        "API_BASE_URL",
        "http://localhost:8000",
    ),
    user_id=user_id,
)


try:

    compliance = client.compliance_report()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Meeting Compliance",
        f"{compliance['meeting_compliance_percentage']:.1f}%",
    )

    col2.metric(
        "Action Closure",
        f"{compliance['action_closure_percentage']:.1f}%",
    )

    col3.metric(
        "Overdue Actions",
        compliance["overdue_action_items"],
    )

    col4.metric(
        "Active Flags",
        compliance["active_flags"],
    )


    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader("Meeting Coverage")

        st.write(
            f"Students: "
            f"{compliance['students_with_meeting']} / "
            f"{compliance['total_students']}"
        )

        st.progress(
            min(
                compliance[
                    "meeting_compliance_percentage"
                ] / 100,
                1.0,
            )
        )

    with right:

        st.subheader("Action Item Closure")

        st.write(
            f"Completed: "
            f"{compliance['completed_action_items']} / "
            f"{compliance['total_action_items']}"
        )

        st.progress(
            min(
                compliance[
                    "action_closure_percentage"
                ] / 100,
                1.0,
            )
        )


    st.divider()

    st.subheader("👨‍🏫 Mentor Workload")

    mentor_data = client.mentor_load()

    if mentor_data:

        df = pd.DataFrame(mentor_data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        st.bar_chart(
            df.set_index("mentor_name")[
                [
                    "active_students",
                    "meetings_last_30_days",
                    "open_actions",
                ]
            ]
        )

    else:
        st.info(
            "No mentor workload data available."
        )


    st.divider()

    st.subheader("🔐 Audit Activity")

    audit_data = client.audit_summary()

    if audit_data:

        audit_df = pd.DataFrame(
            audit_data
        )

        st.dataframe(
            audit_df,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "No audit events recorded."
        )


    st.divider()

    st.subheader("Institutional Risk Snapshot")

    risk1, risk2 = st.columns(2)

    risk1.metric(
        "Active Student Flags",
        compliance["active_flags"],
    )

    risk2.metric(
        "Open Escalations",
        compliance["open_escalations"],
    )


except APIError as exc:

    st.error(
        f"Unable to load compliance data: {exc}"
    )