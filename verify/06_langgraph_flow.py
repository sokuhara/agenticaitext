"""PART 7.3-7.4 のグラフが、いま入っているLangGraphで動くかを確かめる。

    python3 06_langgraph_flow.py

LLMは使いません。implement を偽物に差し替えて、
状態、分岐、再試行の上限、interrupt、再開だけを検証します。

確認すること:
  - StateGraph / add_conditional_edges が想定どおり動くか
  - MAX_ATTEMPTS で give_up に落ちるか
  - interrupt() で止まり、Command(resume=...) で再開できるか
  - revise で implement に戻り、指摘が次に渡るか
"""

from __future__ import annotations

from typing import TypedDict


class State(TypedDict, total=False):
    goal: str
    attempts: int
    check_output: str
    passed: bool
    diff: str
    decision: str
    review_feedback: str


MAX_ATTEMPTS = 3

# 何回目で成功したことにするか（テスト用のダイヤル）
SUCCEED_AT = 2


def main() -> int:
    try:
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import Command, interrupt
    except ImportError as e:
        print("langgraph がありません:", e)
        print("  uv add langgraph")
        return 1

    log: list[str] = []

    def plan(state: State) -> State:
        log.append("plan")
        return {**state, "attempts": 0}

    def implement(state: State) -> State:
        n = state["attempts"] + 1
        log.append(f"implement#{n}")
        if state.get("review_feedback"):
            log.append(f"  指摘を受け取った: {state['review_feedback']}")
        return {**state, "attempts": n}

    def check(state: State) -> State:
        ok = state["attempts"] >= SUCCEED_AT
        log.append(f"check -> {'pass' if ok else 'fail'}")
        return {**state, "passed": ok, "check_output": f"attempt {state['attempts']}"}

    def route_after_check(state: State) -> str:
        if state["passed"]:
            return "review"
        if state["attempts"] >= MAX_ATTEMPTS:
            return "give_up"
        return "implement"

    def review(state: State) -> State:
        log.append("review (止まる)")
        answer = interrupt({
            "diff": "(ここに git diff が入る)",
            "check_output": state["check_output"],
            "question": "採用しますか？",
            "choices": ["approve", "revise", "stop"],
        })
        return {**state,
                "decision": answer["decision"],
                "review_feedback": answer.get("feedback", "")}

    def route_after_review(state: State) -> str:
        return "implement" if state["decision"] == "revise" else END

    def give_up(state: State) -> State:
        log.append("give_up")
        return state

    g = StateGraph(State)
    for name, fn in [("plan", plan), ("implement", implement), ("check", check),
                     ("review", review), ("give_up", give_up)]:
        g.add_node(name, fn)
    g.add_edge(START, "plan")
    g.add_edge("plan", "implement")
    g.add_edge("implement", "check")
    g.add_conditional_edges("check", route_after_check)
    g.add_conditional_edges("review", route_after_review)
    g.add_edge("give_up", END)

    app = g.compile(checkpointer=MemorySaver())

    print("=== 1. 実行して interrupt で止まるか ===")
    cfg = {"configurable": {"thread_id": "t1"}}
    out = app.invoke({"goal": "テストを直す"}, cfg)
    stopped = "__interrupt__" in out
    print("  止まった:", stopped)
    if not stopped:
        print("  !! interrupt が効いていません。LangGraphのバージョンを確認してください。")
        return 1

    print("\n=== 2. revise で implement に戻り、指摘が渡るか ===")
    app.invoke(Command(resume={"decision": "revise", "feedback": "テスト側ではなく実装側を"}), cfg)
    got_feedback = any("指摘を受け取った" in x for x in log)
    print("  戻った:", "implement" in log[-4:] or got_feedback)
    print("  指摘が渡った:", got_feedback)

    print("\n=== 3. approve で終了するか ===")
    app.invoke(Command(resume={"decision": "approve"}), cfg)

    print("\n=== 4. 3回失敗したら give_up に落ちるか ===")
    global SUCCEED_AT
    saved, SUCCEED_AT = SUCCEED_AT, 99
    log2: list[str] = []
    log.clear()
    app.invoke({"goal": "直らない"}, {"configurable": {"thread_id": "t2"}})
    hit = "give_up" in log
    SUCCEED_AT = saved
    print("  give_up に到達:", hit)

    print("\n--- 経路のログ ---")
    for line in log:
        print("  ", line)

    ok = stopped and got_feedback and hit
    print("\n=>", "教材の7.3-7.4はそのまま動きます" if ok else "どこかが期待どおりではありません")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
