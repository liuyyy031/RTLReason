from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgrammableTimerOutput:
    remaining: int
    tick: bool


class ProgrammableTimerReferenceModel:
    def __init__(self, width: int = 8) -> None:
        if width < 1:
            raise ValueError("width must be positive")
        self.mask = (1 << width) - 1
        self.stored_period = 1
        self.remaining = 1

    def step(self, *, rst: bool = False, load: bool = False, period: int = 0, enable: bool = False) -> ProgrammableTimerOutput:
        tick = False
        if rst:
            self.stored_period = 1
            self.remaining = 1
        elif load:
            effective = period & self.mask
            effective = effective or 1
            self.stored_period = effective
            self.remaining = effective
        elif enable and self.remaining == 1:
            self.remaining = self.stored_period
            tick = True
        elif enable:
            self.remaining -= 1
        return ProgrammableTimerOutput(self.remaining, tick)
