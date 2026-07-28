from enum import Enum
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Role(str, Enum):
    both = "both"
    data_owner = "data_owner"
    linkage_unit = "linkage_unit"


class Settings(BaseSettings):
    role: Literal[Role.both, Role.data_owner, Role.linkage_unit]
    expose_docs: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        frozen=True,
    )
