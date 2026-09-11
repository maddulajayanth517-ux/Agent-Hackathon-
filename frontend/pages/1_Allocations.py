from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.api_client import (
    create_allocation,
    create_flag,
    get_allocation_recommendation,
    get_allocations,
    get_escalation,
    get_flags,
    get_workloads,
    generate_brief,
    update_allocation,
)

st.set_page_config(page_title="Mentor Intelligence", page_icon="🧠")
st.title("Mentor–Mentee Allocation & Briefing")

if "student_list" not in st.session_state:
    st.session_state.student_list = [
        {"id": 1, "name": "Riya Kumar"},
        {"id": 2, "name": "Arjun Singh"},
        {"id": 3, "name": "Meera Joshi"},
        {"id": 4, "name": "Leo Martin"},
        {"id": 5, "name": "Sara Ahmed"},
    ]

if "mentor_list" not in st.session_state:
    st.session_state.mentor_list = [
        {"id": 1, "name": "Ava Shah", "capacity": 3},
        {"id": 2, "name": "Noah Patel", "capacity": 2},
        {"id": 3, "name": "Iris Chen", "capacity": 2},
    ]

with st.container():
    st.subheader("Allocation overview")
    try:
        workloads = get_workloads()
        st.dataframe(workloads, use_container_width=True)
    except Exception as exc:
        st.warning(f"Workload data unavailable: {exc}")

    st.subheader("Create or reallocate an allocation")
    col1, col2, col3 = st.columns(3)
    with col1:
        student_id = st.selectbox("Student", [s["id"] for s in st.session_state.student_list], format_func=lambda x: next(s["name"] for s in st.session_state.student_list if s["id"] == x))
    with col2:
        mentor_id = st.selectbox("Mentor", [m["id"] for m in st.session_state.mentor_list], format_func=lambda x: next(m["name"] for m in st.session_state.mentor_list if m["id"] == x))
    with col3:
        reason = st.text_input("Reason", value="INITIAL")

    if st.button("Create allocation"):
        try:
            result = create_allocation(student_id, mentor_id, reason)
            st.success(f"Allocation created: {result}")
        except Exception as exc:
            st.error(f"Could not create allocation: {exc}")

    try:
        allocations = get_allocations()
        if allocations:
            st.dataframe(allocations, use_container_width=True)
    except Exception as exc:
        st.warning(f"Allocation list unavailable: {exc}")

    recommendation = None
    if st.button("Get recommendation"):
        try:
            recommendation = get_allocation_recommendation(student_id)
            st.info(f"Recommended mentor: {recommendation['mentor_name']} ({recommendation['mentor_id']})")
            st.write(recommendation['reason'])
        except Exception as exc:
            st.error(f"Recommendation unavailable: {exc}")

    if recommendation:
        st.caption(f"Current workload: {recommendation['current_workload']} / {recommendation['capacity']}")

with st.container():
    st.subheader("Pre-meeting brief")
    student_id = st.selectbox("Student for brief", [s["id"] for s in st.session_state.student_list], format_func=lambda x: next(s["name"] for s in st.session_state.student_list if s["id"] == x), key="brief_student")
    if st.button("Generate brief"):
        try:
            brief = generate_brief(student_id)
            st.write(f"Source: {brief.get('source', 'fallback')}")
            if brief.get('warning'):
                st.warning(brief['warning'])
            st.subheader("Summary")
            st.write(brief.get('summary', ''))
            st.subheader("Key changes")
            for item in brief.get('key_changes', []):
                st.write(f"- {item}")
            st.subheader("Open concerns")
            for item in brief.get('open_concerns', []):
                st.write(f"- {item}")
            st.subheader("Pending actions")
            for item in brief.get('pending_actions', []):
                st.write(f"- {item}")
            st.subheader("Discussion points")
            for item in brief.get('discussion_points', []):
                st.write(f"- {item}")
            st.subheader("Recommended next steps")
            for item in brief.get('recommended_next_steps', []):
                st.write(f"- {item}")
        except Exception as exc:
            st.error(f"Brief generation failed: {exc}")

with st.container():
    st.subheader("Flag intake")
    flag_student_id = st.selectbox("Student", [s["id"] for s in st.session_state.student_list], format_func=lambda x: next(s["name"] for s in st.session_state.student_list if s["id"] == x), key="flag_student")
    flag_category = st.selectbox("Category", ["ACADEMIC", "ATTENDANCE", "PERSONAL", "FINANCIAL", "CAREER", "OTHER"])
    flag_severity = st.selectbox("Severity", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    flag_title = st.text_input("Flag title")
    flag_desc = st.text_area("Flag description")
    if st.button("Create flag"):
        try:
            flag = create_flag(flag_student_id, flag_category, flag_severity, flag_title, flag_desc)
            st.success(f"Flag created: {flag}")
            escalation = get_escalation(flag['id'])
            st.info(f"Routing: {escalation['destination']} | Priority: {escalation['priority']} | Reason: {escalation['reason']}")
        except Exception as exc:
            st.error(f"Could not create flag: {exc}")

    try:
        flags = get_flags()
        if flags:
            st.dataframe(flags, use_container_width=True)
    except Exception as exc:
        st.warning(f"Flags unavailable: {exc}")

with st.container():
    st.subheader("Escalation routing")
    try:
        flags = get_flags()
        if flags:
            selected_flag_id = st.selectbox("Flag", [f["id"] for f in flags], format_func=lambda x: next(f["title"] for f in flags if f["id"] == x))
            if st.button("Check escalation decision"):
                result = get_escalation(selected_flag_id)
                st.write(result)
    except Exception as exc:
        st.warning(f"Escalation data unavailable: {exc}")
