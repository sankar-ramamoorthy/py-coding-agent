# py_mono/ui/cli.py
"""
Command-line interface for py-coding-agent.

Provides a simple interactive REPL loop that passes user input to the agent
and prints responses. Supports special commands handled by the agent itself:

    /clear  — reset conversation memory
    /bye    — end the session
    exit    — exit the CLI loop
    quit    — exit the CLI loop
"""


def start_cli(agent) -> None:
    """
    Start the interactive CLI loop for the coding agent.

    Reads user input, passes it to the agent, and prints the response.
    Continues until the user types 'exit' or 'quit'.

    Args:
        agent (Agent): Initialized Agent instance to handle user queries
    """
    print("Welcome to Python Coding Agent (V1)!")
    print("Type 'exit' or 'quit' to quit.")
    print("Type '/clear' to reset memory, '/bye' to end session.\n")

    while True:
        try:
            prompt = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if not prompt:
            continue

        if prompt.lower() in ("exit", "quit"):
            break

        response = agent.run(prompt)

        if response is not None:
            print(response)