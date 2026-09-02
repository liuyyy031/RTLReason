from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CounterOutput:
    count: int
    overflow: bool


class CounterReferenceModel:
    def __init__(self, width: int = 8) -> None:
        if width < 1:
            raise ValueError("width must be positive")
        self.width = width
        self.mask = (1 << width) - 1
        self.count = 0
        self.overflow = False

    def step(
        self,
        *,
        rst: bool = False,
        load: bool = False,
        en: bool = False,
        load_value: int = 0,
    ) -> CounterOutput:
        if rst:
            self.count = 0
            self.overflow = False
        elif load:
            self.count = load_value & self.mask
            self.overflow = False
        elif en:
            self.overflow = self.count == self.mask
            self.count = (self.count + 1) & self.mask
        else:
            self.overflow = False
        return CounterOutput(self.count, self.overflow)
