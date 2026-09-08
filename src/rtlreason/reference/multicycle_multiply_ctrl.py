from dataclasses import dataclass


@dataclass(frozen=True)
class MultiplyOutput:
    busy: bool
    done: bool
    result: int


class MulticycleMultiplyReferenceModel:
    def __init__(self, width: int = 8) -> None:
        if width < 1:
            raise ValueError("width must be at least one")
        self.width = width
        self.busy = False
        self.remaining = 0
        self.a = self.b = self.result = 0

    def step(self, *, rst=False, start=False, a=0, b=0) -> MultiplyOutput:
        done = False
        if rst:
            self.busy = False
            self.remaining = self.a = self.b = self.result = 0
        elif not self.busy and start:
            mask = (1 << self.width) - 1
            self.busy, self.remaining = True, self.width
            self.a, self.b = a & mask, b & mask
        elif self.busy:
            self.remaining -= 1
            if self.remaining == 0:
                self.result = self.a * self.b
                self.busy, done = False, True
        return MultiplyOutput(self.busy, done, self.result)
