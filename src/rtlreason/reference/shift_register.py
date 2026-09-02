from __future__ import annotations


class ShiftRegisterReferenceModel:
    def __init__(self, width: int = 8) -> None:
        if width < 2:
            raise ValueError("width must be at least two")
        self.width = width
        self.mask = (1 << width) - 1
        self.q = 0

    @property
    def serial_out(self) -> int:
        return (self.q >> (self.width - 1)) & 1

    def step(
        self, *, rst: bool = False, en: bool = False, serial_in: int = 0
    ) -> tuple[int, int]:
        if rst:
            self.q = 0
        elif en:
            self.q = ((self.q << 1) | (serial_in & 1)) & self.mask
        return self.q, self.serial_out
