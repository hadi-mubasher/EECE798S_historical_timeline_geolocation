from agents import Agent, Runner
from historical_map_server.server import (
    events_near_location,
    region_timeline,
    route_history_summary,
)
import asyncio


def build_historical_agent(model="gpt-4o-mini"):
    """
    Build the historical timeline agent.

    Input
    -----
    model
        Model name used by the agent for reasoning

    Returns
    -------
    Agent object

    Behavior
    --------
    Creates a HistoricalTimelineServer toolset and registers all
    tools with the Agent object. The resulting agent can call
    these tools automatically when responding to user queries.
    """
    # Register tools (top-level functions) exposed by the server
    tools = [
        events_near_location,
        region_timeline,
        route_history_summary,
    ]

    # Build and return agent
    agent = Agent(
        name="historical_agent",
        model=model,
        tools=tools,
        instructions=(
            "You are a historical map assistant. "
            "Use the timeline, location, and route tools to retrieve "
            "historical information when needed."
        ),
    )
    return agent


def interactive_demo():
    """
    Run an interactive demonstration.

    Input
    -----
    None

    Returns
    -------
    None

    Behavior
    --------
    Creates an agent, starts a Runner session, and demonstrates the
    usage of each tool by sending example prompts. Results are
    printed directly for verification and assignment requirements.
    """
    # Build agent
    agent = build_historical_agent()

    # Runner executes requests
    runner = Runner()

    # Helper for cleaner printing (async-safe)
    async def ask(prompt):
        print("\nUSER:", prompt)
        response = await runner.run(agent, prompt)
        print("ASSISTANT:", response)

    # Demonstration queries
    asyncio.run(ask("Show historical events near Beirut at 33.89, 35.50."))
    asyncio.run(ask("Give me a timeline for Baalbek sorted by year."))
    asyncio.run(ask("I am traveling from Beirut to Baalbek. Summarize the history along my route."))


# Run demo when invoked as a script
if __name__ == "__main__":
interactive_demo()
