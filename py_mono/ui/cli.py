# py_mono/ui/cli.py

def start_cli(agent):
    """
    Start the interactive CLI for Python Coding Agent.
    Executes user commands and prints tool results directly.
    """
    print("Welcome to Python Coding Agent (V1)!")
    print("Type 'exit' to quit.")
    
    while True:
        prompt = input("> ")
        if prompt.lower() in ("exit", "quit"):
            break
        
        # Run user input through agent
        response = agent.run(prompt)
        
        # Only print actual response if it's not None
        if response is not None:
            print(response)