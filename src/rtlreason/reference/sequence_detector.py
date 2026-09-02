from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SequenceDetectorOutput:
    match: bool
    prefix_length: int


class SequenceDetector1011ReferenceModel:
    """Architecture-independent recognizer for valid-sampled, overlapping 1011."""

    def __init__(self) -> None:
        self.prefix_length = 0
        self.match = False

    def step(
        self,
        *,
        rst: bool = False,
        bit_valid: bool = False,
        bit_in: bool = False,
    ) -> SequenceDetectorOutput:
        if rst:
            self.prefix_length = 0
            self.match = False
        else:
            self.match = False
            if bit_valid:
                bit = bool(bit_in)
                if self.prefix_length == 0:
                    self.prefix_length = 1 if bit else 0
                elif self.prefix_length == 1:
                    self.prefix_length = 1 if bit else 2
                elif self.prefix_length == 2:
                    self.prefix_length = 3 if bit else 0
                else:
                    if bit:
                        self.match = True
                        self.prefix_length = 1
                    else:
                        self.prefix_length = 2
        return SequenceDetectorOutput(self.match, self.prefix_length)
