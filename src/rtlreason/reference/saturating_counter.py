from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SaturatingCounterOutput:
    count: int
    at_min: bool
    at_max: bool


class SaturatingCounterReferenceModel:
    def __init__(self, width: int = 8) -> None:
        if width < 1:
            raise ValueError("width must be positive")
        self.maximum = (1 << width) - 1
        self.count = 0

    def step(self, *, rst: bool = False, en: bool = False, up: bool = False) -> SaturatingCounterOutput:
        if rst:
            self.count = 0
        elif en and up and self.count < self.maximum:
            self.count += 1
        elif en and not up and self.count > 0:
            self.count -= 1
        return SaturatingCounterOutput(self.count, self.count == 0, self.count == self.maximum)
