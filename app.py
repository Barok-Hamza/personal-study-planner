import uuid
from datetime import date, datetime, time

import streamlit as st

from task_storage import load_tasks, save_tasks
from task_utils import calculate_end_time, find_conflicting_task, update_task


def save_task_changes(tasks):
    if st.session_state.get("task_storage_error"):
        st.error(
            "Tasks cannot be changed because the saved task file could not "
            "be loaded."
        )
        return False
    try:
        save_tasks(tasks)
        return True
    except (OSError, ValueError) as error:
        st.error(f"Could not save tasks: {error}")
        return False


st.title("Personal Study & Task Planner")
st.write("Organize your study tasks and track your progress.")
st.success("Welcome! Your study planner is ready.")

if "tasks" not in st.session_state:
    try:
        st.session_state["tasks"] = load_tasks()
        st.session_state["task_storage_error"] = None
    except (OSError, ValueError) as error:
        st.session_state["tasks"] = []
        st.session_state["task_storage_error"] = str(error)

if st.session_state.get("task_storage_error"):
    st.error(
        "Saved tasks could not be loaded. Task changes are disabled to avoid "
        f"overwriting the saved file. {st.session_state['task_storage_error']}"
    )

st.session_state.setdefault("editing_task_id", None)
st.session_state.setdefault("deleting_task_id", None)

with st.form("task_form"):
    task_name = st.text_input("Task name")
    scheduled_date = st.date_input("Scheduled date", value=date.today())
    start_time = st.time_input("Start time", value=time(9, 0))
    duration = st.number_input(
        "Duration (minutes)", min_value=1, value=60, step=1
    )
    submitted = st.form_submit_button(
        "Add task", disabled=bool(st.session_state.get("task_storage_error"))
    )

if submitted:
    if st.session_state.get("task_storage_error"):
        st.error("Tasks cannot be changed until the saved task file is fixed.")
    elif not task_name.strip():
        st.error("Enter a task name before adding the task.")
    else:
        start = datetime.combine(scheduled_date, start_time)
        end = calculate_end_time(scheduled_date, start_time, duration)
        conflict = find_conflicting_task(
            st.session_state["tasks"], start, end
        )
        if conflict:
            st.error(
                f"Schedule conflicts with '{conflict['name']}' "
                f"({conflict['start'].strftime('%Y-%m-%d %H:%M')} - "
                f"{conflict['end'].strftime('%Y-%m-%d %H:%M')})."
            )
        else:
            new_task = {
                "id": uuid.uuid4().hex,
                "name": task_name.strip(),
                "start": start,
                "end": end,
                "duration": duration,
                "status": "Pending",
            }
            updated_tasks = [*st.session_state["tasks"], new_task]
            if save_task_changes(updated_tasks):
                st.session_state["tasks"] = updated_tasks
                st.success("Task added.")

st.subheader("Your tasks")
if st.session_state["tasks"]:
    for task in st.session_state["tasks"]:
        st.write(f"**{task['name']}**")
        st.write(f"Start: {task['start'].strftime('%Y-%m-%d %H:%M')}")
        st.write(f"End: {task['end'].strftime('%Y-%m-%d %H:%M')}")
        st.write(f"Duration: {task['duration']} minutes")
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
                    edited_start = datetime.combine(edited_date, edited_time)
                    edited_end = calculate_end_time(
                        edited_date, edited_time, edited_duration
                    )
                    conflict = find_conflicting_task(
                        st.session_state["tasks"],
                        edited_start,
                        edited_end,
                        exclude_task_id=task["id"],
                    )
                    if conflict:
                        st.error(
                            f"Schedule conflicts with '{conflict['name']}' "
                            f"({conflict['start'].strftime('%Y-%m-%d %H:%M')} - "
                            f"{conflict['end'].strftime('%Y-%m-%d %H:%M')})."
                        )
                    else:
                        updated_tasks = [
                            dict(saved_task)
                            for saved_task in st.session_state["tasks"]
                        ]
                        edited_task = next(
                            (
                                saved_task
                                for saved_task in updated_tasks
                                if saved_task["id"] == task["id"]
                            ),
                            None,
                        )
                        if edited_task is None:
                            st.error("This task no longer exists.")
                        else:
                            update_task(
                                edited_task,
                                edited_name.strip(),
                                edited_date,
                                edited_time,
                                edited_duration,
                            )
                            if save_task_changes(updated_tasks):
                                st.session_state["tasks"] = updated_tasks
                                st.session_state["editing_task_id"] = None
                                st.rerun()
        elif st.session_state["deleting_task_id"] == task["id"]:
            st.warning(f"Delete '{task['name']}'?")
            if st.button("Confirm Delete", key=f"confirm_delete_{task['id']}"):
                deleting_task_id = st.session_state["deleting_task_id"]
                updated_tasks = [
                    saved_task
                    for saved_task in st.session_state["tasks"]
                    if saved_task["id"] != deleting_task_id
                ]
                if save_task_changes(updated_tasks):
                    st.session_state["tasks"] = updated_tasks
                    st.session_state["deleting_task_id"] = None
                    st.rerun()
            if st.button("Cancel", key=f"cancel_delete_{task['id']}"):
                st.session_state["deleting_task_id"] = None
                st.rerun()
        elif (
            st.session_state["editing_task_id"] is None
            and st.session_state["deleting_task_id"] is None
        ):
            if st.button("Edit", key=f"edit_{task['id']}"):
                st.session_state["editing_task_id"] = task["id"]
                st.session_state["deleting_task_id"] = None
                st.session_state[f"edit_name_{task['id']}"] = task["name"]
                st.session_state[f"edit_date_{task['id']}"] = task["start"].date()
                st.session_state[f"edit_time_{task['id']}"] = task["start"].time()
                st.session_state[f"edit_duration_{task['id']}"] = task["duration"]
                st.rerun()
            button_label = (
                "Mark Completed"
                if task["status"] == "Pending"
                else "Undo completion"
            )
            if st.button(button_label, key=f"status_{task['id']}"):
                updated_tasks = [
                    dict(saved_task)
                    for saved_task in st.session_state["tasks"]
                ]
                updated_task = next(
                    saved_task
                    for saved_task in updated_tasks
                    if saved_task["id"] == task["id"]
                )
                updated_task["status"] = (
                    "Completed"
                    if updated_task["status"] == "Pending"
                    else "Pending"
                )
                if save_task_changes(updated_tasks):
                    st.session_state["tasks"] = updated_tasks
                    st.rerun()
            if st.button("Delete", key=f"delete_{task['id']}"):
                st.session_state["deleting_task_id"] = task["id"]
                st.session_state["editing_task_id"] = None
                st.rerun()
        st.write(f"Status: {task['status']}")
else:
    if st.session_state.get("task_storage_error"):
        st.write("Saved tasks are unavailable until the storage issue is resolved.")
    else:
        st.write("No tasks yet. Add one using the form above.")