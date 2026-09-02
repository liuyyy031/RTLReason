from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RisingEdgeOutput:
    pulse: bool
    previous_sample: bool


class RisingEdgeDetectorReferenceModel:
    """Architecture-independent sampled rising-edge detector."""

    def __init__(self) -> None:
        self.previous_sample = False
        self.pulse = False

    def step(
        self, *, rst: bool = False, signal_in: bool = False
    ) -> RisingEdgeOutput:
        if rst:
            self.previous_sample = False
            self.pulse = False
        else:
            sampled = bool(signal_in)
            self.pulse = sampled and not self.previous_sample
            self.previous_sample = sampled
        return RisingEdgeOutput(self.pulse, self.previous_sample)
