from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SerialParityOutput:
    busy: bool
    parity: bool
    done: bool


class SerialParityReferenceModel:
    def __init__(self) -> None:
        self.busy = False
        self.parity = False
        self.working = False

    def step(self, *, rst: bool = False, start: bool = False, bit_valid: bool = False, bit_in: bool = False, finish: bool = False) -> SerialParityOutput:
        done = False
        if rst:
            self.busy = False
            self.parity = False
            self.working = False
        elif not self.busy:
            if start:
                self.busy = True
                self.working = bool(bit_valid and bit_in)
        elif finish:
            self.parity = self.working ^ bool(bit_valid and bit_in)
            self.busy = False
            self.working = False
            done = True
        elif bit_valid:
            self.working ^= bool(bit_in)
        return SerialParityOutput(self.busy, self.parity, done)
