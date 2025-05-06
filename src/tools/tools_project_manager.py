from langchain.tools import tool
from typing_extensions import Annotated
import json
import os
from src.utilities.print_formatters import print_formatted, print_text_snippet
from src.utilities.manager_utils import actualize_progress_description_file, research_second_task, cleanup_research_histories
from src.utilities.user_input import user_input
from src.utilities.graphics import task_completed_animation
from src.utilities.util_functions import join_paths
from dotenv import load_dotenv, find_dotenv
from single_task_coder import run_clean_coder_pipeline
import uuid
import requests
from requests.exceptions import HTTPError
import json
from concurrent.futures import ThreadPoolExecutor


load_dotenv(find_dotenv())

work_dir = os.getenv("WORK_DIR")
load_dotenv(join_paths(work_dir, ".clean_coder/.env"))
todos_file = join_paths(work_dir, ".clean_coder/todos.json")

def load_todos():
    if not os.path.exists(todos_file):
        return []
    with open(todos_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_todos(todos):
    with open(todos_file, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2)


# Create a persistent ThreadPoolExecutor for background tasks
background_executor = ThreadPoolExecutor(max_workers=1)

@tool
def add_task(
    task_name: Annotated[
        str,
        "Name of the task. Good name is descriptive, starts with a verb and usually could be fitted in formula 'To complete this task, I need to $TASK_NAME'",
    ],
    task_description: Annotated[
        str,
        "Detailed description of what needs to be done in order to implement task. Good description includes: - Definition of done (required) - section, describing what need to be done with acceptance criteria. - Resources (optional) - Include here all information that will be helpful for developer to complete task",
    ],
    order: Annotated[int, "Order of the task in project"],
):
    """Add new task to Todoist.
    Think very carefully before adding a new task to know what do you want exactly. Explain in detail what needs to be
    done in order to execute task.
    Avoid creating new tasks that have overlapping scope with old ones - modify or delete old tasks first.
    """
    human_message = user_input("Type (o)k to agree or provide commentary.")
    if human_message not in ["o", "ok"]:
        return f"Action wasn't executed because of human interruption. He said: {human_message}"

    todos = load_todos()
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "content": task_name,
        "description": task_description,
        "order": order
    }
    todos.append(task)
    todos.sort(key=lambda t: t["order"])
    save_todos(todos)
    return "Task added successfully"


@tool
def modify_task(
    task_id: Annotated[str, "ID of the task"],
    new_task_name: Annotated[str, "New name of the task (optional)"] = None,
    new_task_description: Annotated[
        str, "New detailed description of what needs to be done in order to implement task (optional)"
    ] = None,
    delete: Annotated[bool, "If True, task will be deleted"] = False,
):
    """Modify task in project management platform (Todoist)."""
    todos = load_todos()
    idx = next((i for i, t in enumerate(todos) if t["id"] == task_id), None)
    if idx is None:
        return f"Task with id {task_id} not found."
    task = todos[idx]
    human_message = user_input(
        f"I want to {'delete' if delete else 'modify'} task '{task['content']}'. Type (o)k or provide commentary. "
    )
    if human_message not in ["o", "ok"]:
        return f"Action wasn't executed because of human interruption. He said: {human_message}"
    if delete:
        todos.pop(idx)
        save_todos(todos)
        return "Task deleted successfully"
    if new_task_name:
        task["content"] = new_task_name
    if new_task_description:
        task["description"] = new_task_description
    todos[idx] = task
    save_todos(todos)
    return "Task modified successfully"


@tool
def reorder_tasks(
    task_items: Annotated[
        list,
        "List of dictionaries with 'id' (str) and 'child_order' (int) keys. Example: [{'id': '123', 'child_order': 0}, {'id': '456', 'child_order': 1}]",
    ],
):
    """Reorder tasks in project management platform (Todoist)."""
    todos = load_todos()
    id_to_order = {item['id']: item['child_order'] for item in task_items}
    for t in todos:
        if t['id'] in id_to_order:
            t['order'] = id_to_order[t['id']]
    todos.sort(key=lambda t: t["order"])
    save_todos(todos)
    return "Tasks reordered successfully"


@tool
def finish_project_planning(dummy: Annotated[str, "Type 'ok' to proceed."]):
    """Call that tool to fire execution of top task from list. Use tool when all task in Todoist correctly reflect work."""
    human_message = user_input(
        "Project planning finished. Provide your proposition of changes in task list or type (o)k to continue...\n"
    )
    if human_message not in ["o", "ok"]:
        return f"Human: {human_message}"
        
    # Get tasks
    todos = load_todos()
    if not todos:
        return "No tasks to execute"
    
    first_task = todos[0]
    task_name_description = f"{first_task['content']}\n\n{first_task['description']}"

    # Start background research of second task if available and not researched yet
    if len(todos) >= 2:
        second_task = todos[1]
        history_file = join_paths(work_dir, ".clean_coder", f"research_history_task_{second_task['id']}.json")
        if not os.path.exists(history_file):
            background_executor.submit(research_second_task, second_task)

    # Execute the main pipeline to implement the task
    print_formatted("Asked programmer to execute task:", color="light_blue")
    print_text_snippet(first_task['description'], title=first_task['content'])
    run_clean_coder_pipeline(task_name_description, work_dir, task_id=first_task['id'])

    actualize_progress_description_file(task_name_description)

    # Mark task as done (remove from list)
    todos.pop(0)
    save_todos(todos)

    cleanup_research_histories()

    task_completed_animation()

    return "Task completed successfully"
