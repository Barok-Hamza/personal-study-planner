from datetime import date, datetime, time

import streamlit as st

from task_utils import calculate_end_time

st.title("Personal Study & Task Planner")
st.write("Organize your study tasks and track your progress.")
st.success("Welcome! Your study planner is ready.")

st.session_state.setdefault("tasks", [])

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
                "name": task_name.strip(),
                "start": start,
                "end": end,
                "duration": duration,
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
else:
    st.write("No tasks yet. Add one using the form above.")