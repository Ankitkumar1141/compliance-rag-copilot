import os

def init_langsmith():
    """
    Initializes LangSmith tracing by checking and configuring environment variables.
    Tracing is automatically picked up by LangChain once variables are set.
    """
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    api_key = os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGCHAIN_PROJECT", "compliance-copilot")

    if tracing_enabled:
        if not api_key:
            print("[WARNING] LangSmith tracing was set to TRUE, but LANGCHAIN_API_KEY is empty. Tracing is disabled.")
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
        else:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = api_key
            os.environ["LANGCHAIN_PROJECT"] = project
            print(f"[INFO] LangSmith tracing enabled for project: {project}")
    else:
        # Explicitly disable
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        print("[INFO] LangSmith tracing is disabled.")
