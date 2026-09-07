from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamWidthAdapterOutput:
    in_ready: bool
    out_valid: bool
    out_data: int


class StreamWidthAdapterReferenceModel:
    def __init__(self) -> None:
        self.have_low = False
        self.low_byte = 0
        self.out_valid = False
        self.out_data = 0

    def step(self, *, rst: bool = False, in_valid: bool = False, in_data: int = 0, out_ready: bool = False) -> StreamWidthAdapterOutput:
        if rst:
            self.have_low = False
            self.low_byte = 0
            self.out_valid = False
            self.out_data = 0
        elif self.out_valid:
            if out_ready:
                self.out_valid = False
        elif in_valid:
            if not self.have_low:
                self.low_byte = in_data & 0xFF
                self.have_low = True
            else:
                self.out_data = ((in_data & 0xFF) << 8) | self.low_byte
                self.out_valid = True
                self.have_low = False
        return StreamWidthAdapterOutput(not self.out_valid, self.out_valid, self.out_data)
