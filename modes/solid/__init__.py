from dataclasses import dataclass


@dataclass(frozen=True)
class SolidMode:
    name: str = "solid"


def register() -> SolidMode:
    return SolidMode()

