from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpiTxOutput:
    sclk: bool
    mosi: bool
    busy: bool
    done: bool


class SpiTxReferenceModel:
    def __init__(self, half_period_cycles: int = 2) -> None:
        if half_period_cycles < 1:
            raise ValueError("half_period_cycles must be positive")
        self.half_period = half_period_cycles
        self.sclk = self.mosi = self.busy = self.done = False
        self.word = self.bit_index = self.half_count = 0

    def step(
        self, *, rst: bool = False, start: bool = False, data_in: int = 0
    ) -> SpiTxOutput:
        if rst:
            self.sclk = self.mosi = self.busy = self.done = False
            self.word = self.bit_index = self.half_count = 0
        else:
            self.done = False
            if self.busy:
                if self.half_count == self.half_period - 1:
                    self.half_count = 0
                    if not self.sclk:
                        self.sclk = True
                    else:
                        self.sclk = False
                        if self.bit_index == 7:
                            self.busy = False
                            self.mosi = False
                            self.done = True
                        else:
                            self.bit_index += 1
                            self.word = (self.word << 1) & 0xFF
                            self.mosi = bool(self.word & 0x80)
                else:
                    self.half_count += 1
            elif start:
                self.word = data_in & 0xFF
                self.bit_index = self.half_count = 0
                self.sclk = False
                self.mosi = bool(self.word & 0x80)
                self.busy = True
            else:
                self.sclk = self.mosi = False
        return SpiTxOutput(self.sclk, self.mosi, self.busy, self.done)
