"""7.3 + 7.4 — A workflow with a stop condition and a human approval step.

    plan -> implement -> check --pass--> review --approve/stop--> END
                            |               |
                            |               +--revise--> implement
                            +--fail, < MAX_ATTEMPTS--> implement
                            +--fail, MAX_ATTEMPTS----> give_up -> END

Only `implement` calls the model. Everything else is ordinary Python.

Run from the vibe-chat folder:   python agent/agent_graph.py
"""

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

import tools as t
from agent_langchain import agent_executor

MAX_ATTEMPTS = 3        # 7.3.2: the stop condition. Try changing it.


class State(TypedDict, total=False):
    goal: str
    attempts: int
    before: dict          # snapshot of the watched files, taken in plan
    check_output: str
    passed: bool
    diff: str
    decision: str
    review_feedback: str


def plan(state: State) -> State:
    return {**state, "attempts": 0, "before": t.snapshot()}


def implement(state: State) -> State:
    # The only place the model is called.
    prompt = state["goal"]
    if state.get("check_output"):
        prompt += f"\n\nResult of the last test run:\n{state['check_output']}"
    if state.get("review_feedback"):
        prompt += f"\n\nFeedback from the human reviewer:\n{state['review_feedback']}"
    agent_executor.invoke({"messages": [("user", prompt)]}, {"recursion_limit": 30})
    return {**state, "attempts": state["attempts"] + 1}


def check(state: State) -> State:
    # pytest is a node of its own. The model never gets to "say" the tests passed.
    output = t.run_tests()
    return {**state, "check_output": output, "passed": t.tests_pass()}


def route_after_check(state: State) -> str:
    if state["passed"]:
        return "review"
    if state["attempts"] >= MAX_ATTEMPTS:
        return "give_up"
    return "implement"


def give_up(state: State) -> State:
    print(f"\nGave up after {MAX_ATTEMPTS} attempts. Handing over to a human.\n")
    print(state["check_output"])
    return state


def review(state: State) -> State:
    diff = t.make_diff(state["before"])
    answer = interrupt({
        "diff": diff[:4000],
        "check_output": state["check_output"],
        "question": "Approve these changes?",
        "choices": ["approve", "revise", "stop"],
    })
    return {**state, "diff": diff,
            "decision": answer["decision"],
            "review_feedback": answer.get("feedback", "")}


def route_after_review(state: State) -> str:
    if state["decision"] == "revise":
        return "implement"          # send the feedback back to the agent
    return END                      # approve and stop both end here


graph = StateGraph(State)
graph.add_node("plan", plan)
graph.add_node("implement", implement)
graph.add_node("check", check)
graph.add_node("review", review)
graph.add_node("give_up", give_up)
graph.add_edge(START, "plan")
graph.add_edge("plan", "implement")
graph.add_edge("implement", "check")
graph.add_conditional_edges("check", route_after_check)
graph.add_conditional_edges("review", route_after_review)
graph.add_edge("give_up", END)
app = graph.compile(checkpointer=MemorySaver())


def main():
    config = {"configurable": {"thread_id": "task-001"}}
    result = app.invoke({"goal": "Run the tests, find out why one of them fails, and fix it."}, config)

    # While the graph is paused at `review`, show the diff and ask the human.
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n" + "=" * 60)
        print("TESTS:\n" + payload["check_output"].strip().splitlines()[-1])
        print("-" * 60)
        print("DIFF:\n" + payload["diff"])
        print("=" * 60)
        decision = ""
        while decision not in ("approve", "revise", "stop"):
            decision = input("approve / revise / stop > ").strip().lower()
        feedback = input("What should be changed? > ") if decision == "revise" else ""
        result = app.invoke(Command(resume={"decision": decision, "feedback": feedback}), config)

    print("\nFinished. Decision:", result.get("decision", "(gave up)"))


if __name__ == "__main__":
    main()
