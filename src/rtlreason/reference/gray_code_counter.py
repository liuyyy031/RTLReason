from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GrayCodeCounterOutput:
    gray: int
    wrap: bool


class GrayCodeCounterReferenceModel:
    """Architecture-independent model of the observable Gray sequence."""

    def __init__(self, width: int = 4) -> None:
        if width < 1:
            raise ValueError("width must be positive")
        self.width = width
        self.modulus = 1 << width
        self.index = 0

    @staticmethod
    def encode(index: int) -> int:
        return index ^ (index >> 1)

    def step(self, *, rst: bool = False, en: bool = False) -> GrayCodeCounterOutput:
        wrap = False
        if rst:
            self.index = 0
        elif en:
            wrap = self.index == self.modulus - 1
            self.index = (self.index + 1) % self.modulus
        return GrayCodeCounterOutput(self.encode(self.index), wrap)
