PART 7 starter (AGEWEC Mumbai). Run from this folder:

    pip install -r agent/requirements.txt
    python agent/agent_video.py

Fill in agent/config.py first (same four values as PART 6). Never hand in config.py.

The assignment is NOT to run this starter as it is. Modify it for your own video (PART 7, 7.3):
  1. THEME and AUDIENCE
  2. KEY_POINTS (three or more)
  3. two or more success conditions in check()
  4. at least one new agent behaviour (node, edge, tool, or EDITOR_SYSTEM)
Mark every changed line with a comment starting "# CHANGED:".

What the starter already checks (do not count these as your additions):
  30-60 seconds, at least 4 different clips, every key point in a subtitle,
  a SOURCES.txt line for every clip used, narration no longer than the video.

Every run writes run/EXECUTION_TRACE.jsonl (storyboards, human decisions, clip list, tool calls,
check results, release decision) and run/STORYBOARD_V*.json, and EDIT_LOG.txt at the end.
These are the "production record" you hand in. Do not edit them by hand.

Put your generated clips in assets/cut1.mp4 ... and log each one in assets/SOURCES.txt
(one line per clip, more if credit or a license must be recorded).

Hand-in: fill in CHANGE_REPORT.txt, then zip this folder as PART7_StudentID.zip keeping the
same layout, minus config.py, assets/*.mp4, build/ and output.mp4.
A video without the agent program scores at most 30 points.

The final product is not only the video. It is the modified agent, the production process, and the video.
