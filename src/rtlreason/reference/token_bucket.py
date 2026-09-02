from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenBucketOutput:
    tokens: int
    grant: bool


class TokenBucketReferenceModel:
    """One-token-per-cycle bucket with current-state request acceptance."""

    def __init__(self, capacity: int = 3) -> None:
        if capacity < 2:
            raise ValueError("capacity must be at least two")
        self.capacity = capacity
        self.tokens = 0
        self.grant = False

    def step(
        self, *, rst: bool = False, req: bool = False
    ) -> TokenBucketOutput:
        if rst:
            self.tokens = 0
            self.grant = False
        else:
            add = self.tokens < self.capacity
            take = bool(req) and self.tokens > 0
            self.grant = take
            self.tokens += int(add) - int(take)
        return TokenBucketOutput(self.tokens, self.grant)
