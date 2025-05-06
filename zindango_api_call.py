import os
from typing import Dict, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://47d568h3nisp5o-8080.proxy.runpod.net/ollama/")
OLLAMA_API_TOKEN = os.getenv("OLLAMA_API_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjgyZmQzYWY2LTZmMmEtNDM0OC1iMjM5LWYwNmFhMjM5ZjNjZiJ9.HxP9_iYKozTssdMvHq3F7nBNfC33RZV8OoAO0aHedxY")
OLLAMA_HEADERS: Dict[str, str] = {
    'Authorization': f'Bearer {OLLAMA_API_TOKEN}',
    'Content-Type': 'application/json'
}

def get_ollama_config(model_name: str = "mathzenepoch3"):
    return {
        "model": model_name,
        "model_provider": "ollama",
        "temperature": 0,
        "max_tokens": 1000,
        "base_url": OLLAMA_BASE_URL,
        "streaming": True,
        "client_kwargs": {"headers": OLLAMA_HEADERS},
        "headers": OLLAMA_HEADERS,
    }

class ZindangoLLM:
    def __init__(self, model_name: str = "mathzenepoch3"):
        self.model = ChatOllama(**get_ollama_config(model_name))

    def _stream_and_save(self, query: str, out_path: Optional[str] = None) -> str:
        output = ""
        f = open(out_path, "w", encoding="utf-8") if out_path else None
        try:
            for chunk in self.model.stream(query):
                content = chunk.content
                if isinstance(content, str):
                    if content == '<think>':
                        content = "<reasoning>"
                    elif content == '</think>':
                        content = "</reasoning>"
                    output += content
                    print(content, end="", flush=True)
                    if f:
                        f.write(content)
        finally:
            if f:
                f.close()
        return output

    def generate_prfaq_md(self, user_idea: str, out_path: str = "PRFAQ.md"):
        prompt = f"""
You are an expert product manager. Write a complete PRFAQ (Press Release + FAQ) for the following product idea:

{user_idea}
"""
        return self._stream_and_save(prompt, out_path)

    def generate_functional_doc(self, user_idea: str, prfaq: str, out_path: str = "functional_doc.md"):
        prompt = f"""
Given the following product idea and PRFAQ, write a detailed functional specification and feature list:

Product Idea:
{user_idea}

PRFAQ:
{prfaq}
"""
        return self._stream_and_save(prompt, out_path)

    def generate_design_doc(self, user_idea: str, prfaq: str, functional_doc: str, out_path: str = "design_doc.md"):
        prompt = f"""
Given the following product idea, PRFAQ, and functional document, write a comprehensive design document:

Product Idea:
{user_idea}

PRFAQ:
{prfaq}

Functional Document:
{functional_doc}
"""
        return self._stream_and_save(prompt, out_path)

    def generate_architecture_doc(self, user_idea: str, prfaq: str, functional_doc: str, design_doc: str, out_path: str = "architecture_doc.md"):
        prompt = f"""
Given the following product idea, PRFAQ, functional document, and design document, write a detailed architecture document (including diagrams in markdown if appropriate):

Product Idea:
{user_idea}

PRFAQ:
{prfaq}

Functional Document:
{functional_doc}

Design Document:
{design_doc}
"""
        return self._stream_and_save(prompt, out_path)

    def generate_user_stories_and_tasks(self, user_idea: str, prfaq: str, functional_doc: str, design_doc: str, architecture_doc: str, out_path: str = "user_stories.md"):
        prompt = f"""
Given the following product idea, PRFAQ, functional document, design document, and architecture document, generate user stories, tasks, and sub-tasks for implementation:

Product Idea:
{user_idea}

PRFAQ:
{prfaq}

Functional Document:
{functional_doc}

Design Document:
{design_doc}

Architecture Document:
{architecture_doc}
"""
        return self._stream_and_save(prompt, out_path)

    def generate_vibe_coding_prompts(self, user_story: str, out_path: str = "vibe_coding_prompts.md"):
        prompt = f"""
Given the following user story, generate a detailed coding prompt for a developer to implement it, including context and acceptance criteria:

User Story:
{user_story}
"""
        return self._stream_and_save(prompt, out_path)

    def generate_devplan_md(self, user_idea: str, prfaq: str, functional_doc: str, design_doc: str, architecture_doc: str, user_stories: str, out_path: str = "devplan.md"):
        prompt = f"""
Given the following documents, generate a step-by-step development plan (devplan.md) for the project:

Product Idea:
{user_idea}

PRFAQ:
{prfaq}

Functional Document:
{functional_doc}

Design Document:
{design_doc}

Architecture Document:
{architecture_doc}

User Stories:
{user_stories}
"""
        return self._stream_and_save(prompt, out_path)

if __name__ == "__main__":
    # Example usage:
    zindango = ZindangoLLM(model_name="mathzenepoch3")
    idea = "Uber for flying cars."
    print("\n--- Generating PRFAQ.md ---\n")
    prfaq = zindango.generate_prfaq_md(idea)
    print("\n--- Generating functional_doc.md ---\n")
    functional_doc = zindango.generate_functional_doc(idea, prfaq)
    print("\n--- Generating design_doc.md ---\n")
    design_doc = zindango.generate_design_doc(idea, prfaq, functional_doc)
    print("\n--- Generating architecture_doc.md ---\n")
    architecture_doc = zindango.generate_architecture_doc(idea, prfaq, functional_doc, design_doc)
    print("\n--- Generating user_stories.md ---\n")
    user_stories = zindango.generate_user_stories_and_tasks(idea, prfaq, functional_doc, design_doc, architecture_doc)
    print("\n--- Generating vibe_coding_prompts.md ---\n")
    zindango.generate_vibe_coding_prompts(user_stories)
    print("\n--- Generating devplan.md ---\n")
    zindango.generate_devplan_md(idea, prfaq, functional_doc, design_doc, architecture_doc, user_stories)