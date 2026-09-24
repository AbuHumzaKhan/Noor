"""Capability discovery across local skills and connected repositories."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    source: str
    description: str


class CapabilityDiscovery:
    def discover(self) -> list[Capability]:
        return []
