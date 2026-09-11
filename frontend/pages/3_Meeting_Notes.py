import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from datetime import date, datetime, time

import streamlit as st

from api_client import (
    APIError,
    create_meeting,
    get_student_brief,
    get_student_meetings,
    update_action,
)


st.set_page_config(
    page_title="Meeting Notes",
    page_icon="📝",
    layout="wide",
)


if "user_id" not in st.session_state:
    st.session_state.user_id = 3

if "student_id" not in st.session_state:
    st.session_state.student_id = 1


user_id = st.session_state.user_id
student_id = st.session_state.student_id


st.title("Meeting Notes & Action Tracker")
st.caption("Mentoring conversations, follow-ups and action-item management")


try:
    brief = get_student_brief(user_id, student_id)
    meetings = get_student_meetings(user_id, student_id)
except APIError as exc:
    st.error(f"API Error ({exc.status_code})")
    st.json(exc.detail)
    st.stop()


student = brief.get("student", {})
mentor = brief.get("mentor", {})
summary = brief.get("summary", {})
actions = brief.get("action_items", [])


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Meetings", summary.get("total_meetings", 0))

with col2:
    st.metric("Total Actions", summary.get("total_actions", 0))

with col3:
    st.metric("Open Actions", summary.get("open_actions", 0))

with col4:
    st.metric("Overdue", summary.get("overdue_actions", 0))


st.divider()


left, right = st.columns([1, 2])


with left:
    st.subheader("Student")

    st.write(f"**Name:** {student.get('name', 'N/A')}")
    st.write(f"**Register No:** {student.get('register_number', 'N/A')}")
    st.write(f"**Department:** {student.get('department', 'N/A')}")
    st.write(f"**Year:** {student.get('year', 'N/A')}")
    st.write(f"**Section:** {student.get('section', 'N/A')}")

    st.subheader("Mentor")

    if mentor:
        st.write(f"**Name:** {mentor.get('name', 'N/A')}")
        st.write(f"**Specialization:** {mentor.get('specialization', 'N/A')}")
        st.write(f"**Email:** {mentor.get('email', 'N/A')}")
    else:
        st.warning("No mentor allocation found.")


with right:
    st.subheader("Record New Meeting")

    with st.form("meeting_form"):
        meeting_date = st.date_input(
            "Meeting Date",
            value=date.today(),
        )

        meeting_time = st.time_input(
            "Meeting Time",
            value=time(10, 0),
        )

        mode = st.selectbox(
            "Meeting Mode",
            ["in_person", "online", "phone"],
        )

        agenda = st.text_input(
            "Agenda",
            placeholder="Academic progress, career planning, attendance...",
        )

        notes = st.text_area(
            "Meeting Notes",
            placeholder="Enter detailed discussion notes...",
            height=130,
        )

        concerns = st.text_area(
            "Student Concerns",
            placeholder="Record concerns raised by the student...",
            height=100,
        )

        observations = st.text_area(
            "Mentor Observations",
            placeholder="Mentor assessment and observations...",
            height=100,
        )

        next_meeting = st.date_input(
            "Next Meeting Date",
            value=None,
        )

        st.markdown("#### Action Item")

        action_title = st.text_input(
            "Action Title",
            placeholder="Complete ML project documentation",
        )

        action_description = st.text_area(
            "Action Description",
            placeholder="Describe the expected action...",
        )

        action_owner = st.number_input(
            "Action Owner User ID",
            min_value=1,
            value=user_id,
            step=1,
        )

        action_due_date = st.date_input(
            "Action Due Date",
            value=date.today(),
        )

        submitted = st.form_submit_button(
            "Create Meeting",
            use_container_width=True,
        )

        if submitted:
            if not notes.strip():
                st.error("Meeting notes are required.")
                st.stop()

            payload = {
                "student_id": student_id,
                "meeting_at": datetime.combine(
                    meeting_date,
                    meeting_time,
                ).isoformat(),
                "mode": mode,
                "agenda": agenda.strip() or None,
                "notes": notes.strip(),
                "student_concerns": concerns.strip() or None,
                "mentor_observations": observations.strip() or None,
                "next_meeting_at": (
                    datetime.combine(
                        next_meeting,
                        time(10, 0),
                    ).isoformat()
                    if next_meeting
                    else None
                ),
                "action_items": (
                    [
                        {
                            "title": action_title.strip(),
                            "description": action_description.strip() or None,
                            "owner_id": int(action_owner),
                            "due_date": action_due_date.isoformat(),
                        }
                    ]
                    if action_title.strip()
                    else []
                ),
            }

            try:
                result = create_meeting(user_id, payload)
                st.success(
                    f"Meeting #{result.get('id')} created successfully."
                )
                st.rerun()

            except APIError as exc:
                st.error(f"API Error ({exc.status_code})")
                st.json(exc.detail)


st.divider()


st.subheader("Action Items")


if not actions:
    st.info("No action items available.")
else:
    for action in actions:
        action_id = action.get("id")
        action_status = action.get("status", "").upper()
        due_date = action.get("due_date", "N/A")

        with st.expander(
            f"#{action_id} — {action.get('title', 'Untitled')} — {action_status}"
        ):
            st.write(
                f"**Description:** "
                f"{action.get('description') or 'No description'}"
            )

            st.write(f"**Owner ID:** {action.get('owner_id')}")
            st.write(f"**Due Date:** {due_date}")
            st.write(f"**Status:** {action_status}")

            new_status = st.selectbox(
                "Update Status",
                [
                    "open",
                    "in_progress",
                    "completed",
                    "overdue",
                    "cancelled",
                ],
                index=[
                    "open",
                    "in_progress",
                    "completed",
                    "overdue",
                    "cancelled",
                ].index(
                    action.get("status", "open")
                ),
                key=f"status_{action_id}",
            )

            if st.button(
                "Update Action",
                key=f"update_{action_id}",
            ):
                try:
                    update_action(
                        user_id,
                        action_id,
                        {"status": new_status},
                    )

                    st.success("Action item updated.")
                    st.rerun()

                except APIError as exc:
                    st.error(f"API Error ({exc.status_code})")
                    st.json(exc.detail)


st.divider()


st.subheader("Meeting History")


if not meetings:
    st.info("No meetings recorded.")
else:
    for meeting in meetings:
        with st.expander(
            f"{meeting.get('meeting_at', 'Unknown date')} — "
            f"{meeting.get('mode', '').upper()}"
        ):
            st.write(
                f"**Agenda:** {meeting.get('agenda') or 'N/A'}"
            )

            st.write(
                f"**Notes:** {meeting.get('notes') or 'N/A'}"
            )

            st.write(
                f"**Student Concerns:** "
                f"{meeting.get('student_concerns') or 'N/A'}"
            )

            st.write(
                f"**Mentor Observations:** "
                f"{meeting.get('mentor_observations') or 'N/A'}"
            )

            st.write(
                f"**Next Meeting:** "
                f"{meeting.get('next_meeting_at') or 'N/A'}"
            )