from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadyValidOutput:
    in_ready: bool
    out_valid: bool
    out_data: int


class ReadyValidSliceReferenceModel:
    def __init__(self, data_width: int = 8) -> None:
        if data_width < 1:
            raise ValueError("data_width must be positive")
        self.mask = (1 << data_width) - 1
        self.valid = False
        self.data = 0

    def observe(self, *, out_ready: bool) -> ReadyValidOutput:
        return ReadyValidOutput(
            in_ready=(not self.valid) or out_ready,
            out_valid=self.valid,
            out_data=self.data,
        )

    def step(
        self,
        *,
        rst: bool = False,
        in_valid: bool = False,
        in_data: int = 0,
        out_ready: bool = False,
    ) -> ReadyValidOutput:
        ready = (not self.valid) or out_ready
        if rst:
            self.valid = False
            self.data = 0
        elif ready:
            self.valid = in_valid
            if in_valid:
                self.data = in_data & self.mask
        return self.observe(out_ready=out_ready)
