"""PART 8 — A production workflow for a short PR video.

    draft ──► approve_storyboard ──► wait_for_clips ──► edit ──► check ──pass──► review ──► END
                     │ (interrupt)         │ (interrupt)   ▲         │ fail
                     └─ revise ─────────►draft             └─────────┘ (back to edit, MAX_ROUNDS)

Two nodes talk to the model, and they are different kinds of node:

  draft  — the model WRITES a plan (storyboard, narration). Plain text in, JSON out. No tools.
  edit   — the model ORCHESTRATES: it looks at the clips that actually came back, decides the
           order, the trims, the transitions and the subtitle timing, and calls the editing
           tools itself. This is the agent from PART 7, pointed at a different job.

Everything else is fixed code or a human decision.

Run from the agewec-mumbai folder:   python agent/agent_video.py
"""

import json
import re
from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt, Command

from config import BASE_URL, MODEL, HEADERS, API_KEY
import video_tools as vt
import edit_tools as et

# ---- what you decide before anything runs -----------------------------------------
THEME = "AGEWEC Mumbai: why the world should come and see Mumbai"
# Each key point: (the statement, the words that must appear in a subtitle for it to count)
KEY_POINTS = [
    ("The suburban railway carries about 7 million passengers a day", "7 million"),
    ("Marine Drive at night, the 'Queen's Necklace'", "marine drive"),
    ("Street food: vada pav and pav bhaji", "vada pav"),
]
MAX_SECONDS = 60          # the check: the video must be at most this long
MIN_SECONDS = 20          # and at least this long
NUM_CUTS = 6              # 5 to 8 works well
MAX_ROUNDS = 3            # how many times the check may send the editor back

model = ChatOpenAI(base_url=BASE_URL, api_key=API_KEY, model=MODEL, temperature=0.3,
                   default_headers=HEADERS)


class State(TypedDict, total=False):
    storyboard: list        # [{"cut": 1, "seconds": 8, "prompt": "...", "subtitle": "..."}]
    narration: str
    feedback: str
    edit_rounds: int
    edit_summary: str       # what the editor said it did
    check_output: str
    passed: bool
    decision: str


# ---- 1. draft: the model writes ----------------------------------------------------

def draft(state: State) -> State:
    feedback = state.get("feedback", "")
    prompt = f"""You are planning a PR video of at most {MAX_SECONDS} seconds.
Theme: {THEME}
Key points that MUST appear, each in at least one subtitle:
{chr(10).join('- ' + k for k, _ in KEY_POINTS)}

Return ONLY a JSON object with:
- "storyboard": a list of exactly {NUM_CUTS} cuts. Each cut: {{"cut": n, "seconds": 5-10, "prompt": "a text-to-video prompt for this shot, one sentence, no real people's faces, no logos", "subtitle": "one short line shown on screen"}}
- "narration": the voice-over for the whole video, at most {int(MAX_SECONDS * 2.3)} words, plain English.
{('Feedback from the human reviewer, apply it: ' + feedback) if feedback else ''}"""
    text = model.invoke(prompt).content
    data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
    return {**state, "storyboard": data["storyboard"], "narration": data["narration"], "feedback": ""}


def approve_storyboard(state: State) -> State:
    """Interrupt 1: the human reads every prompt before any clip is generated."""
    lines = [f"cut{c['cut']}  {c['seconds']}s  subtitle: {c['subtitle']}\n        prompt: {c['prompt']}"
             for c in state["storyboard"]]
    answer = interrupt({
        "storyboard": "\n".join(lines),
        "narration": state["narration"],
        "question": "Approve this storyboard? (approve / revise / stop)",
    })
    return {**state, "decision": answer["decision"], "feedback": answer.get("feedback", "")}


def wait_for_clips(state: State) -> State:
    """Interrupt 2: the human generates the clips with the allowed tools and puts them in assets/."""
    expected = [f"assets/cut{c['cut']}.mp4" for c in state["storyboard"]]
    answer = interrupt({
        "instruction": "Generate each cut with the allowed tools, save them as the files below, "
                       "and write one line per cut in assets/SOURCES.txt. Missing cuts are fine; "
                       "the editor will work with what is there. Then type: done",
        "files": expected,
    })
    return {**state, "decision": answer["decision"]}


# ---- 2. edit: the model orchestrates -----------------------------------------------

EDITOR_SYSTEM = f"""You are the editor of a short PR video. You have tools to inspect the clips and to build the video.
Work like this:
1. Call list_assets, then contact_sheet, and look at the sheet before deciding anything.
2. Decide the order and the length of each clip. Follow the storyboard where the clips allow it;
   if a clip is missing, too short, or does not show what its prompt asked for, say so and adapt
   (reorder, reuse a good clip for two beats, drop a cut).
3. Build the timeline with add_to_timeline, then join_timeline, then add_subtitles, then add_narration.
4. The finished video must be between {MIN_SECONDS} and {MAX_SECONDS} seconds.
   Each of these phrases must appear in some subtitle: {', '.join(repr(w) for _, w in KEY_POINTS)}.
   The narration must not be longer than the video: cut words before you cut clips.
5. Finish with a short summary of the decisions you made and why, especially where you departed from the storyboard.
Never invent clip numbers that list_assets did not return."""

editor = create_react_agent(model, et.EDIT_TOOLS, prompt=EDITOR_SYSTEM)


def edit(state: State) -> State:
    et.LOG.clear()
    et._timeline.clear()
    brief = {"storyboard": state["storyboard"], "narration": state["narration"]}
    text = "Storyboard and narration as approved:\n" + json.dumps(brief, indent=1)
    if state.get("feedback"):
        text += "\n\nThe last attempt failed the check. Fix these:\n" + state["feedback"]
    # The contact sheet is made first so the model can SEE the clips in its first message.
    sheet = et.contact_sheet.invoke({})
    msg = HumanMessage(content=[{"type": "text", "text": text}, et.image_message(sheet)])
    result = editor.invoke({"messages": [msg]}, {"recursion_limit": 40})
    summary = result["messages"][-1].content
    return {**state, "edit_summary": summary, "edit_rounds": state.get("edit_rounds", 0) + 1}


# ---- 3. check: fixed code ------------------------------------------------------------

def check(state: State) -> State:
    problems = []
    out = vt.PROJECT_ROOT / "output.mp4"
    if not out.exists():
        problems.append("output.mp4 was not written: the editor did not finish the tool sequence")
    else:
        dur = vt.probe_duration(out)
        if not (MIN_SECONDS <= dur <= MAX_SECONDS):
            problems.append(f"length is {dur:.1f}s, must be between {MIN_SECONDS} and {MAX_SECONDS}s")
        narr = vt.BUILD / "narration.mp3"
        if narr.exists() and vt.probe_duration(narr) > dur + 0.5:
            problems.append("narration is longer than the video: shorten the narration")
        subs_text = " ".join(et.LAST_SUBTITLES).lower()      # the subtitles the editor actually burned
        for statement, words in KEY_POINTS:
            if words.lower() not in subs_text:
                problems.append(f"no subtitle mentions '{words}' (key point: {statement})")
        sources = vt.read_sources()
        for c in et._timeline:
            if c["cut"] not in sources:
                problems.append(f"cut{c['cut']} is on the timeline but has no line in assets/SOURCES.txt")
    text = "OK" if not problems else "\n".join("- " + p for p in problems)
    print("\nCHECK:", text)
    return {**state, "check_output": text, "passed": not problems, "feedback": "" if not problems else text}


def route_after_check(state: State) -> str:
    if state["passed"]:
        return "review"
    if state["edit_rounds"] >= MAX_ROUNDS:
        return END
    return "edit"


def route_after_storyboard(state: State) -> str:
    return {"approve": "wait_for_clips", "revise": "draft"}.get(state["decision"], END)


# ---- 4. review: human ------------------------------------------------------------------

def review(state: State) -> State:
    answer = interrupt({
        "editor_decisions": state["edit_summary"],
        "tool_log": "\n".join(et.LOG),
        "question": "output.mp4 is ready. Watch it, read the editor's decisions. approve / stop",
    })
    return {**state, "decision": answer["decision"]}


def build_graph():
    g = StateGraph(State)
    for name, fn in [("draft", draft), ("approve_storyboard", approve_storyboard),
                     ("wait_for_clips", wait_for_clips), ("edit", edit),
                     ("check", check), ("review", review)]:
        g.add_node(name, fn)
    g.add_edge(START, "draft")
    g.add_edge("draft", "approve_storyboard")
    g.add_conditional_edges("approve_storyboard", route_after_storyboard)
    g.add_edge("wait_for_clips", "edit")
    g.add_edge("edit", "check")
    g.add_conditional_edges("check", route_after_check)
    g.add_edge("review", END)
    return g.compile(checkpointer=MemorySaver())


def main():
    app = build_graph()
    config = {"configurable": {"thread_id": "agewec-mumbai"}}
    result = app.invoke({"feedback": ""}, config)
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n" + "=" * 60)
        for k, v in payload.items():
            print(f"{k}:\n{v if not isinstance(v, list) else chr(10).join(v)}\n")
        print("=" * 60)
        if "files" in payload:
            while input("> ").strip().lower() != "done":
                pass
            resume = {"decision": "done"}
        else:
            d = ""
            while d not in ("approve", "revise", "stop"):
                d = input("approve / revise / stop > ").strip().lower()
            fb = input("What should change? > ") if d == "revise" else ""
            resume = {"decision": d, "feedback": fb}
        result = app.invoke(Command(resume=resume), config)
    (vt.PROJECT_ROOT / "EDIT_LOG.txt").write_text(
        "EDITOR DECISIONS\n" + str(result.get("edit_summary", "")) + "\n\nTOOL LOG\n" + "\n".join(et.LOG),
        encoding="utf-8")
    print("\nFinished:", result.get("decision", "stopped by the check"), "| edit rounds:", result.get("edit_rounds"))
    print("The editor's decisions and tool log are in EDIT_LOG.txt")


if __name__ == "__main__":
    main()
