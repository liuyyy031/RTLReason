from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadyValidFifo2Output:
    in_ready: bool
    out_valid: bool
    out_data: int


class ReadyValidFifo2ReferenceModel:
    def __init__(self, data_width: int = 8) -> None:
        if data_width < 1:
            raise ValueError("data_width must be positive")
        self.mask = (1 << data_width) - 1
        self.queue: list[int] = []

    def observe(self, *, out_ready: bool) -> ReadyValidFifo2Output:
        out_valid = bool(self.queue)
        output_transfer = out_valid and out_ready
        return ReadyValidFifo2Output(
            in_ready=len(self.queue) < 2 or output_transfer,
            out_valid=out_valid,
            out_data=self.queue[0] if self.queue else 0,
        )

    def step(
        self,
        *,
        rst: bool = False,
        in_valid: bool = False,
        in_data: int = 0,
        out_ready: bool = False,
    ) -> ReadyValidFifo2Output:
        before = self.observe(out_ready=out_ready)
        if rst:
            self.queue.clear()
        else:
            output_transfer = before.out_valid and out_ready
            input_transfer = in_valid and before.in_ready
            if output_transfer:
                self.queue.pop(0)
            if input_transfer:
                self.queue.append(in_data & self.mask)
        return self.observe(out_ready=out_ready)
