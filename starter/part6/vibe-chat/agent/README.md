PART 6 agent files. Run everything from the vibe-chat folder (the parent of this folder):

    pip install -r agent/requirements.txt
    python agent/agent_plain.py       # 6.1
    python agent/demo_structured.py   # 6.2.2
    python agent/agent_langchain.py   # 6.2.3
    python agent/agent_graph.py       # 6.3 + 6.4

Before running, put your server, model ID and access token in agent/config.py.
