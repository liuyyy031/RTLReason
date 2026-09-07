from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApbRegisterBankOutput:
    pready: bool
    prdata: int
    pslverr: bool


class ApbRegisterBankReferenceModel:
    def __init__(self) -> None:
        self.registers = {0: 0, 4: 0}

    def step(self, *, rst: bool = False, psel: bool = False, penable: bool = False, pwrite: bool = False, paddr: int = 0, pwdata: int = 0) -> ApbRegisterBankOutput:
        access = bool(psel and penable)
        valid = paddr in self.registers
        if rst:
            self.registers = {0: 0, 4: 0}
        elif access and pwrite and valid:
            self.registers[paddr] = pwdata & 0xFFFFFFFF
        return ApbRegisterBankOutput(True, self.registers.get(paddr, 0), access and not valid)
