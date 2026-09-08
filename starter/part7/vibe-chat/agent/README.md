PART 7 agent files. Run everything from the vibe-chat folder (the parent of this folder):

    pip install -r agent/requirements.txt
    python agent/agent_plain.py       # 7.1
    python agent/demo_structured.py   # 7.2.2
    python agent/agent_langchain.py   # 7.2.3
    python agent/agent_graph.py       # 7.3 + 7.4

Before running, put your server, model ID and access token in agent/config.py.
