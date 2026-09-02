from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DebounceOutput:
    debounced: bool
    changed: bool
    consecutive: int


class DebounceFilterReferenceModel:
    """Consecutive-sample debounce model for an already sampled input."""

    def __init__(self, stable_cycles: int = 3) -> None:
        if stable_cycles < 2:
            raise ValueError("stable_cycles must be at least two")
        self.stable_cycles = stable_cycles
        self.debounced = False
        self.changed = False
        self.consecutive = 0

    def step(
        self, *, rst: bool = False, noisy_in: bool = False
    ) -> DebounceOutput:
        if rst:
            self.debounced = False
            self.changed = False
            self.consecutive = 0
        else:
            self.changed = False
            if bool(noisy_in) == self.debounced:
                self.consecutive = 0
            elif self.consecutive == self.stable_cycles - 1:
                self.debounced = bool(noisy_in)
                self.changed = True
                self.consecutive = 0
            else:
                self.consecutive += 1
        return DebounceOutput(
            self.debounced, self.changed, self.consecutive
        )
