from __future__ import annotations


class GrantHoldArbiterReferenceModel:
    """Registered fixed-priority grant that remains stable until accepted."""

    def __init__(self, requesters: int = 4) -> None:
        if requesters < 2:
            raise ValueError("requesters must be at least two")
        self.requesters = requesters
        self.mask = (1 << requesters) - 1
        self.grant = 0

    def step(
        self, req: int = 0, *, rst: bool = False, accept: bool = False
    ) -> int:
        req &= self.mask
        if rst:
            self.grant = 0
        elif self.grant:
            if accept:
                self.grant = 0
        else:
            self.grant = req & -req
        return self.grant
