from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PulseStretcherOutput:
    active: bool
    remaining: int


class PulseStretcherReferenceModel:
    """Reference model for an exactly timed, retriggerable active pulse."""

    def __init__(self, pulse_cycles: int = 4) -> None:
        if pulse_cycles < 2:
            raise ValueError("pulse_cycles must be at least two")
        self.pulse_cycles = pulse_cycles
        self.active = False
        self.remaining = 0

    def step(
        self, *, rst: bool = False, trigger: bool = False
    ) -> PulseStretcherOutput:
        if rst:
            self.active = False
            self.remaining = 0
        elif trigger:
            self.active = True
            self.remaining = self.pulse_cycles
        elif self.active:
            if self.remaining == 1:
                self.active = False
                self.remaining = 0
            else:
                self.remaining -= 1
        return PulseStretcherOutput(self.active, self.remaining)
