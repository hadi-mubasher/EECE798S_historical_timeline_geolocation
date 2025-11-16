# geolocation_server/agent.py

from agents import Agent, Runner
from geolocation_server.server import GeolocationServer
import asyncio

def build_geolocation_agent(model: str = "gpt-4o-mini") -> Agent:
    """
    Build the geolocation agent.

    Input
    -----
    model
        Model name used by the agent for reasoning

    Returns
    -------
    Agent object

    Behavior
    --------
    Registers geocode, reverse geocode, and nearby search tools
    from a GeolocationServer instance so the agent can route calls.
    """
    server = GeolocationServer()
    tools = [server.geocode, server.reverse_geocode, server.nearby_search]
    agent = Agent(
        name="geolocation_agent",
        model=model,
        tools=tools,
        instructions=(
            "You are a geolocation assistant. Use geocoding, reverse geocoding, "
            "and nearby search tools when appropriate. If a coordinate or POI type "
            "is missing, ask for clarification briefly."
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
    usage of each geolocation tool by sending example prompts.
    """
    agent = build_geolocation_agent()
    runner = Runner()

    async def demo():
        prompts = [
            "Geocode AUB",
            "What is near 33.90, 35.48? Show hospitals within 3 km.",
            "What city is closest to 33.84, 35.49?",
        ]
        for p in prompts:
            print("\nUSER:", p)
            result = await runner.run(agent, p)
            print("ASSISTANT:", result.final_output)

    asyncio.run(demo())

if __name__ == "__main__":
    interactive_demo()
