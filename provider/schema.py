import typing as t

from pydantic import BaseModel, Extra, Field


class GlobusSshDirectorySchema(BaseModel):
    ssh_server: str = Field(
        ...,
        title="ssh_server",
        description="The server to execute the remote ssh command on.",
    )
    command: str = Field(
        ...,
        title="command",
        description="A command to execute remotely.",
    )
    limit: int = Field(100_000, title="limit", description="Set the page size.")
    offset: t.Optional[int] = Field(
        None,
        title="offset",
        description="If using a limit < 100,000, this can be used to page through the results.",
    )

    class Config:
        title = "Ssh Action Provider Schema"
        schema_extra = {
            "example": {
                "ssh_server": "ssh.my.example.edu",
                "command": "ls -la",
                "limit": 1000,
            }
        }
        extra = Extra.forbid
