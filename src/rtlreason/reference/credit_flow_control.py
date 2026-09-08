from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreditFlowOutput:
    send_accept: bool
    credits: int
    empty: bool
    full: bool


class CreditFlowControlReferenceModel:
    def __init__(self, max_credits: int = 3) -> None:
        if max_credits < 1:
            raise ValueError("max_credits must be at least one")
        self.max_credits = max_credits
        self.credits = max_credits

    def step(
        self,
        *,
        rst: bool,
        send_req: bool,
        credit_return: bool,
    ) -> CreditFlowOutput:
        accepted = not rst and send_req and self.credits > 0
        if rst:
            self.credits = self.max_credits
        elif accepted and not credit_return:
            self.credits -= 1
        elif credit_return and not accepted and self.credits < self.max_credits:
            self.credits += 1

        return CreditFlowOutput(
            send_accept=accepted,
            credits=self.credits,
            empty=self.credits == 0,
            full=self.credits == self.max_credits,
        )
