from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterruptPendingOutput:
    pending: int
    valid: bool
    index: int


class InterruptPendingReferenceModel:
    def __init__(self) -> None:
        self.pending = 0

    def step(self, *, rst: bool = False, irq: int = 0, mask: int = 0, ack: bool = False) -> InterruptPendingOutput:
        if rst:
            self.pending = 0
        else:
            clear = (self.pending & -self.pending) if ack else 0
            self.pending = ((self.pending & ~clear) | (irq & ~mask)) & 0xF
        valid = self.pending != 0
        index = ((self.pending & -self.pending).bit_length() - 1) if valid else 0
        return InterruptPendingOutput(self.pending, valid, index)
