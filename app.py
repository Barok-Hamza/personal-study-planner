import uuid
from datetime import date, datetime, time

import streamlit as st

from task_utils import calculate_end_time, update_task

st.title("Personal Study & Task Planner")
st.write("Organize your study tasks and track your progress.")
st.success("Welcome! Your study planner is ready.")

st.session_state.setdefault("tasks", [])
st.session_state.setdefault("editing_task_id", None)

with st.form("task_form"):
    task_name = st.text_input("Task name")
    scheduled_date = st.date_input("Scheduled date", value=date.today())
    start_time = st.time_input("Start time", value=time(9, 0))
    duration = st.number_input(
        "Duration (minutes)", min_value=1, value=60, step=1
    )
    submitted = st.form_submit_button("Add task")

if submitted:
    if not task_name.strip():
        st.error("Enter a task name before adding the task.")
    else:
        start = datetime.combine(scheduled_date, start_time)
        end = calculate_end_time(scheduled_date, start_time, duration)
        st.session_state["tasks"].append(
            {
                "id": uuid.uuid4().hex,
                "name": task_name.strip(),
                "start": start,
                "end": end,
                "duration": duration,
                "status": "Pending",
            }
        )
        st.success("Task added.")

st.subheader("Your tasks")
if st.session_state["tasks"]:
    for task in st.session_state["tasks"]:
        st.write(f"**{task['name']}**")
        st.write(f"Start: {task['start'].strftime('%Y-%m-%d %H:%M')}")
        st.write(f"End: {task['end'].strftime('%Y-%m-%d %H:%M')}")
        st.write(f"Duration: {task['duration']} minutes")
        if st.session_state["editing_task_id"] != task["id"]:
            if st.button("Edit", key=f"edit_{task['id']}"):
                st.session_state["editing_task_id"] = task["id"]
                st.session_state[f"edit_name_{task['id']}"] = task["name"]
                st.session_state[f"edit_date_{task['id']}"] = task["start"].date()
                st.session_state[f"edit_time_{task['id']}"] = task["start"].time()
                st.session_state[f"edit_duration_{task['id']}"] = task["duration"]
                st.rerun()

        if st.session_state["editing_task_id"] == task["id"]:
            with st.form(f"edit_form_{task['id']}"):
                edited_name = st.text_input(
                    "Task name", key=f"edit_name_{task['id']}"
                )
                edited_date = st.date_input(
                    "Scheduled date", key=f"edit_date_{task['id']}"
                )
                edited_time = st.time_input(
                    "Start time", key=f"edit_time_{task['id']}"
                )
                edited_duration = st.number_input(
                    "Duration (minutes)",
                    min_value=1,
                    step=1,
                    key=f"edit_duration_{task['id']}",
                )
                save_clicked = st.form_submit_button("Save Changes")
                cancel_clicked = st.form_submit_button("Cancel")

            if cancel_clicked:
                st.session_state["editing_task_id"] = None
                st.rerun()
            if save_clicked:
                if not edited_name.strip():
                    st.error("Enter a task name before saving changes.")
                else:
                    update_task(
                        task,
                        edited_name.strip(),
                        edited_date,
                        edited_time,
                        edited_duration,
                    )
                    st.session_state["editing_task_id"] = None
                    st.rerun()
        else:
            button_label = (
                "Mark Completed"
                if task["status"] == "Pending"
                else "Undo completion"
            )
            if st.button(button_label, key=f"status_{task['id']}"):
                task["status"] = (
                    "Completed" if task["status"] == "Pending" else "Pending"
                )
                st.rerun()
        st.write(f"Status: {task['status']}")
else:
    st.write("No tasks yet. Add one using the form above.")