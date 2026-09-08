from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UartRxOutput:
    data_out: int
    data_valid: bool
    framing_error: bool
    busy: bool


class UartRxReferenceModel:
    def __init__(self, clks_per_bit: int = 4) -> None:
        if clks_per_bit < 2 or clks_per_bit % 2:
            raise ValueError("clks_per_bit must be an even integer at least two")
        self.cpb = clks_per_bit
        self.state = "idle"
        self.count = 0
        self.bit_index = 0
        self.shift = 0
        self.data_out = 0
        self.busy = False

    def step(self, *, rst: bool = False, rx: bool = True) -> UartRxOutput:
        valid = False
        error = False
        if rst:
            self.state = "idle"
            self.count = self.bit_index = self.shift = self.data_out = 0
            self.busy = False
        elif self.state == "idle":
            self.busy = False
            self.count = 0
            if not rx:
                self.state = "start"
                self.busy = True
        elif self.state == "start":
            if self.count == self.cpb // 2 - 1:
                self.count = 0
                if not rx:
                    self.state = "data"
                    self.bit_index = 0
                else:
                    self.state = "idle"
                    self.busy = False
            else:
                self.count += 1
        elif self.state == "data":
            if self.count == self.cpb - 1:
                self.count = 0
                self.shift = (self.shift & ~(1 << self.bit_index)) | (
                    int(rx) << self.bit_index
                )
                if self.bit_index == 7:
                    self.state = "stop"
                else:
                    self.bit_index += 1
            else:
                self.count += 1
        elif self.count == self.cpb - 1:
            self.count = 0
            self.data_out = self.shift
            valid = True
            error = not rx
            self.state = "idle"
            self.busy = False
        else:
            self.count += 1
        return UartRxOutput(self.data_out, valid, error, self.busy)
