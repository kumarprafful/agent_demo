import asyncio
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Type
from client import docker_client
from docker import errors as docker_errors
from pathlib import Path


class Tool(BaseModel):
    async def __call__(self) -> str:
        raise NotImplementedError


class ToolRunCommandInDevContainer(Tool):
    """
        Run a command in the dev container you have at your disposal to test and run code.
        Then command will run in the container and the output will be returned.
        The container is a python development container with python3.14 installed.
        It has port 8888 exposed to the host in case user asks you to run http server.
    """

    command: str

    def _run(self) -> str:
        container = docker_client.containers.get("python-dev")
        exec_command = f"bash -c '{self.command}'"

        try:
            res = container.exec_run(exec_command)
            output = res.output.decode("utf-8")
        except Exception as e:
            output = f"""Error: {e}
                        here is how I run your command: {exec_command}
                    """
        return output

    async def __call__(self) -> str:
        return await asyncio.to_thread(self.run)


class ToolUpsertFile(Tool):
    """
        Create a file in the dev container you have at your disposal to test and run code.
        if the file exists, it will be updated, otherwise it will be created.
    """
    file_path: str = Field(
        description="The path to the file to create or update")
    content: str = Field(description="The content of the file")

    def _run(self) -> str:
        container = docker_client.containers.get("python-dev")

        cmd = f"sh -c 'cat > {self.file_path}'"
        _, socket = container.exec_run(
            cmd, stdin=True, stdout=True, stream=False, socket=True)
        socket._sock.sendall((self.content, "\n").encode("utf-8"))
        socket._sock.close()
        return "file written successfully"

    async def __call__(self) -> str:
        return asyncio.to_thread(self._run)


class ToolDisplayArtifact(Tool):
    """
        Use this tool to display important result for the user, such as code or file content.
        It will display on a dedicated panel on the right of the interface.
        The content must be the entire content to display, or an empty string if you don't want to display anything.
    """

    artifact: str


def create_tool_interact_with_user(prompter: Callable[[str], Awaitable[str]]) -> Type[Tool]:
    class ToolInteractWithUser(Tool):
        """
            This tool will ask the user to clarify their request, provide your query and it will be asked to the user
            you'll get the answer. Make sure that the content in the display is properly markdowned, for instance if you display code,
            use the triple backticks to display it properly with the language specified for highlighting.
        """

        query: str = Field(description="The query to ask the user")

        display: str = Field(description="The interface has a panel on the right to display the artifacts why you ask your query, use this field to display the artifacts, for instance code or file content, you must give the entire content to display or use an empty string if you don't want to display anything")
        
        async def __call__(self) -> str:
            res = await prompter(self.query)
            return res
        
    return ToolInteractWithUser


def start_python_dev_container(container_name:str) -> None:
    """Start a python development container"""

    try:
        existing_container = docker_client.containers.get(container_name)
        if existing_container.status == "running":
            existing_container.kill()
        existing_container.remove()
    except docker_errors.NotFound:
        pass

    volume_path = str(Path(".scratchpad").absolute())

    docker_client.containers.run(
        "python:3.14",
        detach=True,
        name=container_name,
        ports={"8888/tcp": 8888},
        tty=True,
        stdin_open=True,
        working_dir="/app",
        command="bash -c 'mkdir -p /app && tail -f /dev/null'",
    )