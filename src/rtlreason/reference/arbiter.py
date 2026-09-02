from __future__ import annotations


class RoundRobinArbiterReferenceModel:
    def __init__(self, requesters: int = 4) -> None:
        if requesters < 2:
            raise ValueError("requesters must be at least two")
        self.requesters = requesters
        self.pointer = 0
        self.grant = 0

    def step(self, req: int, *, rst: bool = False) -> int:
        if rst:
            self.pointer = 0
            self.grant = 0
            return self.grant
        self.grant = 0
        for offset in range(self.requesters):
            index = (self.pointer + offset) % self.requesters
            if req & (1 << index):
                self.grant = 1 << index
                self.pointer = (index + 1) % self.requesters
                break
        return self.grant
