"""
In manager_utils.py we are placing all functions used by manager agent only, which are not tools.
"""
# imports
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from src.utilities.llms import init_llms_medium_intelligence
from src.utilities.util_functions import join_paths, read_coderrules, list_directory_tree, load_prompt
from src.utilities.start_project_functions import create_project_plan_file
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.load import loads

import questionary
import concurrent.futures
from dotenv import load_dotenv, find_dotenv
import os
import uuid
import requests
import json
from requests.exceptions import HTTPError
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
load_dotenv(join_paths(work_dir, ".clean_coder/.env"))
todos_file = join_paths(work_dir, ".clean_coder/todos.json")

def load_todos():
    if not os.path.exists(todos_file):
        return []
    with open(todos_file, "r", encoding="utf-8") as f:
        return json.load(f)


QUESTIONARY_STYLE = questionary.Style(
    [
        ("qmark", "fg:magenta bold"),  # The '?' symbol
        ("question", "fg:white bold"),  # The question text
        ("answer", "fg:orange bold"),  # Selected answer
        ("pointer", "fg:green bold"),  # Selection pointer
        ("highlighted", "fg:green bold"),  # Highlighted choice
        ("selected", "fg:green bold"),  # Selected choice
        ("separator", "fg:magenta"),  # Separator between choices
        ("instruction", "fg:#FFD700"),  # Additional instructions now in golden yellow (hex color)
    ]
)



actualize_progress_description_prompt_template = load_prompt("actualize_progress_description")
tasks_progress_template = load_prompt("manager_progress")

llms = init_llms_medium_intelligence(run_name="Progress description")
llm = llms[0].with_fallbacks(llms[1:])


def read_project_plan():
    file_path = os.path.join(work_dir, ".clean_coder", "project_plan.txt")

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return "None"

    # If the file exists, read the file
    with open(file_path, "r") as f:
        project_knowledge = f.read()

    return project_knowledge


def fetch_epics():
    # No epics in local mode, return empty list
    return []

def fetch_tasks():
    return load_todos()


# store_project_id is not needed for local storage, so remove it.

def get_project_tasks_and_epics():
    tasks = fetch_tasks()
    if not tasks:
        return "<empty>"
    output_string = ""
    for task in tasks:
        output_string += f"Task:\nid: {task['id']}, \nName: {task['content']}, \nDescription: \n'''{task['description']}''', \nOrder: {task['order']}\n\n"
    return output_string


def parse_project_tasks(tasks):
    output_string = str()
    if tasks:
        output_string += "\n".join(
            f"Task:\nid: {task['id']}, \nName: {task['content']}, \nDescription: \n'''{task['description']}''', \nOrder: {task['order']}\n"
            for task in tasks
        )
    else:
        output_string += "No tasks planned yet.\n\n"

    return output_string


def cleanup_research_histories() -> None:
    """
    Delete every file matching research_history_task_<id>.json inside
    .clean_coder/research_histories when <id> is not among current
    task IDs.
    """
    history_dir = join_paths(work_dir, ".clean_coder", "research_histories")
    if not os.path.exists(history_dir):
        return

    active_ids = {str(t['id']) for t in fetch_tasks()}

    for fname in os.listdir(history_dir):
        if fname.startswith("research_history_task_") and fname.endswith(".json"):
            task_id = fname[len("research_history_task_") : -len(".json")]
            if task_id not in active_ids:
                os.remove(join_paths(history_dir, fname))



def actualize_progress_description_file(task_name_description):
    progress_description = read_progress_description()
    actualize_description_prompt = PromptTemplate.from_template(actualize_progress_description_prompt_template)
    chain = actualize_description_prompt | llm | StrOutputParser()
    progress_description = chain.invoke(
        {
            "progress_description": progress_description,
            "task_name_description": task_name_description,
        }
    )
    with open(os.path.join(work_dir, ".clean_coder", "manager_progress_description.txt"), "w") as f:
        f.write(progress_description)
    print("Writing description of progress done.")


def read_progress_description():
    file_path = os.path.join(work_dir, ".clean_coder", "manager_progress_description.txt")
    if not os.path.exists(file_path):
        open(file_path, "a").close()  # Creates file if it doesn't exist
        progress_description = "<empty>"
    else:
        with open(file_path, "r") as f:
            progress_description = f.read()
    return progress_description


def move_task(task_id, epic_id):
    command = {"type": "item_move", "uuid": str(uuid.uuid4()), "args": {"id": task_id, "section_id": epic_id}}
    commands_json = json.dumps([command])
    requests.post(
        "https://api.todoist.com/sync/v9/sync",
        headers={"Authorization": f"Bearer {todoist_api_key}"},
        data={"commands": commands_json},
    )


def message_to_dict(message):
    """Convert a BaseMessage object to a dictionary."""
    return {
        "type": message.type,
        "content": message.content,
        "tool_calls": getattr(message, "tool_calls", None),  # Use getattr to handle cases where id might not exist
        "tool_call_id": getattr(message, "tool_call_id", None),
        "attribute": getattr(message, "attribute", None),
    }


def dict_to_message(msg_dict):
    """Convert a dictionary back to a BaseMessage object."""
    message_type = msg_dict["type"]
    if message_type == "human":
        return HumanMessage(type=msg_dict["type"], content=msg_dict["content"])
    elif message_type == "ai":
        return AIMessage(type=msg_dict["type"], content=msg_dict["content"], tool_calls=msg_dict.get("tool_calls"))
    elif message_type == "tool":
        return ToolMessage(
            type=msg_dict["type"], content=msg_dict["content"], tool_call_id=msg_dict.get("tool_call_id")
        )


# create_todoist_project not needed for local storage.
    try:
        response = todoist_api.add_project(name=f"Clean_Coder_{os.path.basename(os.path.normpath(work_dir))}")
    except HTTPError:
        raise Exception("You have too much projects in Todoist, can't create new one.")
    return response.id


# setup_todoist_project_if_needed not needed for local storage.
    load_dotenv(join_paths(work_dir, ".clean_coder/.env"))
    if os.getenv("TODOIST_PROJECT_ID"):
        return
    setup_todoist_project()


# setup_todoist_project not needed for local storage.
    projects = todoist_api.get_projects()
    if not projects:
        new_proj_id = create_todoist_project()
        store_project_id(new_proj_id)
        return

    project_choices = [f"{proj.name} (ID: {proj.id})" for proj in projects]
    choice = questionary.select(
        "No Todoist project connected. Do you want to create a new project or use existing one?",
        choices=["Create new project", "Use existing project"],
        style=QUESTIONARY_STYLE,
    ).ask()

    if choice == "Create new project":
        new_proj_id = create_todoist_project()
        store_project_id(new_proj_id)
    else:
        selected_project = questionary.select(
            "Select a project to connect:", choices=project_choices, style=QUESTIONARY_STYLE
        ).ask()
        selected_project_id = selected_project.split("(ID:")[-1].strip(" )")
        store_project_id(selected_project_id)


def prompt_user_if_planning_needed():
    # Only one option for local mode
    return True


def get_manager_messages(saved_messages_path):
    tasks = fetch_tasks()
    if os.path.exists(saved_messages_path):
        # continue previous work
        with open(saved_messages_path, "r") as fp:
            messages = loads(json.load(fp))
    else:
        # new start
        project_tasks = parse_project_tasks(tasks)
        progress_description = read_progress_description()
        messages = [
            HumanMessage(
                content=tasks_progress_template.format(tasks=project_tasks, progress_description=progress_description),
                tasks_and_progress_message=True,
            ),
            HumanMessage(content=list_directory_tree(work_dir)),
        ]

    # Add system message as first one and execution message if needed
    messages = [load_system_message()] + messages

    # Determine if planning is needed based on existing tasks
    do_planning = prompt_user_if_planning_needed() if tasks else True

    if not do_planning:
        messages.append(HumanMessage(content="Tasks are completely done and all you need to do is to execute them."))

    return messages


def actualize_tasks_list_and_progress_description(state):
    # Remove old tasks message
    state["messages"] = [msg for msg in state["messages"] if not hasattr(msg, "tasks_and_progress_message")]
    # Add new message
    tasks = fetch_tasks()
    project_tasks = parse_project_tasks(tasks)
    progress_description = read_progress_description()
    tasks_and_progress_msg = HumanMessage(
        content=tasks_progress_template.format(tasks=project_tasks, progress_description=progress_description),
        tasks_and_progress_message=True,
    )
    # insert tasks message near the end of conversation to ensure AI task list is most actual
    state["messages"].insert(-2, tasks_and_progress_msg)
    return state


def load_system_message():
    system_prompt_template = load_prompt("manager_system")

    if os.path.exists(os.path.join(work_dir, ".clean_coder/project_plan.txt")):
        project_plan = read_project_plan()
    else:
        project_plan = create_project_plan_file(work_dir)

    return SystemMessage(
        content=system_prompt_template.format(project_plan=project_plan, project_rules=read_coderrules())
    )


def research_second_task(task) -> None:
    """Research provided task and add results to its description."""
    from src.agents.researcher_agent import Researcher  # Import here to avoid circular imports

    # Run researcher on task
    researcher = Researcher(silent=True, task_id=task.id)
    researcher.research_task(
        f"{task.content}\n\n{task.description}"
    )
