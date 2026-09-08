from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignedAluOutput:
    result: int
    zero: bool
    negative: bool
    carry: bool
    overflow: bool


class SignedAluFlagsReferenceModel:
    """Pure bit-vector ALU model with frozen C and V definitions."""

    def __init__(self, width: int = 8) -> None:
        if width < 2:
            raise ValueError("width must be at least two")
        self.width = width
        self.mask = (1 << width) - 1
        self.sign = 1 << (width - 1)

    def evaluate(self, a: int, b: int, op: int) -> SignedAluOutput:
        a &= self.mask
        b &= self.mask
        op &= 0b11
        carry = False
        overflow = False
        if op == 0:
            full = a + b
            result = full & self.mask
            carry = bool(full >> self.width)
            overflow = not bool((a ^ b) & self.sign) and bool(
                (result ^ a) & self.sign
            )
        elif op == 1:
            result = (a - b) & self.mask
            carry = a >= b
            overflow = bool((a ^ b) & self.sign) and bool(
                (result ^ a) & self.sign
            )
        elif op == 2:
            result = a & b
        else:
            result = a ^ b
        return SignedAluOutput(
            result=result,
            zero=result == 0,
            negative=bool(result & self.sign),
            carry=carry,
            overflow=overflow,
        )
