"""6.2.3 — The same agent as 6.1, but LangChain/LangGraph run the loop.

Run from the vibe-chat folder:   python agent/agent_langchain.py
"""

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config import BASE_URL, MODEL, HEADERS, API_KEY
import tools as t


# The docstring of each tool is what the model sees. 6.2.4 asks you to change them.
@tool
def read_file(path: str) -> str:
    """Read a file inside the project. Use it to look at app.py and tests/test_app.py."""
    return t.read_file(path)


@tool
def write_file(path: str, content: str) -> str:
    """Overwrite a .py file inside the project with new content."""
    return t.write_file(path, content)


@tool
def run_tests() -> str:
    """Run pytest and return the result."""
    return t.run_tests()


model = ChatOpenAI(base_url=BASE_URL, api_key=API_KEY, model=MODEL, temperature=0,
                   default_headers=HEADERS)

SYSTEM = (
    "You are a careful coding agent working inside a small Flask project. "
    "Fix the failing test by fixing the application code, not by changing the test. "
    "When the tests pass, reply with a short summary of what you changed."
)

agent_executor = create_react_agent(model, [read_file, write_file, run_tests], prompt=SYSTEM)


def run(goal: str) -> str:
    result = agent_executor.invoke({"messages": [("user", goal)]}, {"recursion_limit": 30})
    return result["messages"][-1].content


if __name__ == "__main__":
    print(run("Run the tests, find out why one of them fails, and fix it."))
