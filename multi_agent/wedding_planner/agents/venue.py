from langchain.agents import create_agent

from multi_agent.wedding_planner.model import ollama
from multi_agent.wedding_planner.tools import web_search


def get_venue_agent():
    venue_agent = create_agent(
        model=ollama,
        tools=[web_search],
        system_prompt="""
            You are a venue specialist. Search for venues in the desired location, and with the desired capacity.
            you are not allowed to ask any more follow up questions, you must find the best venue options based on the follwowing criteria:
            - Price (lowest)
            - Capacity (exact match)
            - Reviews (highest)
            You may need to make multiple searches to iteratively find the best options.
            YOu have a suggested limit of 12 web searches. Count every web_search call you make.
            after 12 searches, you should stop searching and summarize the best options you have found so far
        """,
    )
    return venue_agent
