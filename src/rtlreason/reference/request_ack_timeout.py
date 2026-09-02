from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestAckOutput:
    busy: bool
    done: bool
    timeout: bool


class RequestAckTimeoutReferenceModel:
    def __init__(self, timeout_cycles: int = 4) -> None:
        if timeout_cycles < 2:
            raise ValueError("timeout_cycles must be at least two")
        self.timeout_cycles = timeout_cycles
        self.busy = False
        self.remaining = 0
        self.done = False
        self.timeout = False

    def step(
        self, *, rst: bool = False, req: bool = False, ack: bool = False
    ) -> RequestAckOutput:
        if rst:
            self.busy = False
            self.remaining = 0
            self.done = False
            self.timeout = False
        else:
            self.done = False
            self.timeout = False
            if not self.busy:
                if req:
                    self.busy = True
                    self.remaining = self.timeout_cycles
            elif ack:
                self.busy = False
                self.remaining = 0
                self.done = True
            elif self.remaining == 1:
                self.busy = False
                self.remaining = 0
                self.timeout = True
            else:
                self.remaining -= 1
        return RequestAckOutput(self.busy, self.done, self.timeout)
