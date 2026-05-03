from langchain.agents import create_agent
from multi_agent.wedding_planner.model import ollama

from multi_agent.wedding_planner.tools import query_playlist_db

def get_playlist_agent():
    playlist_agent = create_agent(
        model=ollama,
        tools=[query_playlist_db],
        system_prompt="""
            you are a playlist specialist. Query the sql database and curate the perfect playlist for a wedding givena genre.
            once you have your playlist, calculate the total durartion and cost of the playlist, each song has an associated price.
            if you run into errors when querying the database, try to fix them by making changes to the query.
            do not come empty handed, keep trying to query the db until you find a list of songs.

            this is sqlite database. before wrinting any queries, first discover the schema.
        """
    )
    return playlist_agent


