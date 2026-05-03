from datetime import datetime
from langchain.tools import ToolRuntime, tool
from langchain.agents import create_agent
from langchain.messages import HumanMessage, ToolMessage
from langgraph.types import Command
from multi_agent.wedding_planner.model import ollama

from multi_agent.wedding_planner.state import WeddingState

from multi_agent.wedding_planner.agents import playlist, venue, travel

class Coordinator:
    def __init__(self) -> None:
        self.travel_agent = None
        self.venue_agent = venue.get_venue_agent()
        self.playlist_agent = playlist.get_playlist_agent()

    def get_tools(self):
        @tool
        async def search_flights(runtime:ToolRuntime) -> str:
            """travel agent searches for flights to the desired destination wedding location."""
            print("searching for flights")
            travel_agent = self.travel_agent
            if not self.travel_agent:
                travel_agent = await travel.create_travel_agent()
            origin = runtime.state["origin"]
            destination = runtime.state["destination"]
            response = await travel_agent.ainvoke({"messages": [HumanMessage(content=f"find flight from {origin} to {destination}")]})
            return response['messages'][-1].content
        
        @tool
        def search_venue(runtime:ToolRuntime) -> str:
            """Venue agent chooses the best venue for the given location and capacity"""
            print("searching for venues")
            venue_agent = self.venue_agent
            destination = runtime.state["destination"]
            capacity = runtime.state["guest_count"]
            query = f"find wedding venues in {destination} for {capacity} guests"
            response = venue_agent.invoke({"messages": [HumanMessage(content=query)]})
            return response["messages"][-1].content
        
        @tool
        def suggest_playlist(runtime: ToolRuntime)->str:
            """Playlist agent curated the perfect playlist for the given genre"""
            print("searching for playlist")
            genre = runtime.state["genre"]
            query = f"Find {genre} tracks for wedding playlist"
            response = self.playlist_agent.invoke({"messages": [HumanMessage(content=query)]})
            return response["messages"][-1].content
        
        @tool
        def update_state(origin:str, destination: str, guest_count:str, genre:str, runtime:ToolRuntime) -> str:
            """
            Update the state whern you know all of the values: origin, destination, guest_count, genre.
            this tool must be called alone, without any other tool calls. it must complete and return to make the information available to other tools
            """
            print("updating state")
            return Command(update={
                "origin": origin,
                "destination": destination,
                "guest_count": guest_count,
                "genre": genre,
                "messages": [ToolMessage("successfully updated state", tool_call_id=runtime.tool_call_id)]
            })
        return [search_flights, search_venue, suggest_playlist, update_state]
    
    async def get_coordinator(self):
        coordinator = create_agent(
            model=ollama,
            tools=self.get_tools(),
            state_schema=WeddingState,
            system_prompt=f"""
                You are a wedding coordinator. Do not ask for follow up questions. work on whatever information you have.
                First find all the information you need to update the state. When you have the information, update the state.
                once that has completed and returned, you can delegate the tasks to your specialists for fligts, venues, and playlists.
                once you have received their answers, coordinate the perfect wedding for me.
                current date time - {datetime.now()}

            """
        )
        return coordinator
    
    async def run(self):
        coordinator = await self.get_coordinator()
        response = await coordinator.ainvoke({
            "messages": HumanMessage(content="I'm from delhi and i'd like a destination wedding in Udaipur for 100 guests, genre will be bollywood.")
        }, config={"tags": ["WP"], "recursion_limit": 40})
        print("response", response)
        print("responseresponse", response["messages"][-1].content)
        return
    


if __name__ == "__main__":
    import asyncio    
    coo = Coordinator()
    asyncio.run(coo.run())