from typing import Optional

from pydantic import Field, SecretStr

from prefect.blocks.abstract import Block


class CoiledCredentials(Block):
    api_token: Optional[SecretStr] = Field(default=None, description="Coiled API token")
    workspace: Optional[str] = Field(default=None, description="Coiled Workspace")
