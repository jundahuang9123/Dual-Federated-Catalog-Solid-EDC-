from dataclasses import dataclass


@dataclass(frozen=True)
class EdcMode:
    name: str = "edc"


def register() -> EdcMode:
    return EdcMode()

