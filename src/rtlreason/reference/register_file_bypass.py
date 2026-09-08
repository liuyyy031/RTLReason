from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterFileReadOutput:
    rdata_a: int
    rdata_b: int


class RegisterFileBypassReferenceModel:
    """Storage model with two combinational write-through read ports."""

    def __init__(self, data_width: int = 8, addr_width: int = 2) -> None:
        if data_width < 1 or addr_width < 1:
            raise ValueError("data_width and addr_width must be positive")
        self.data_mask = (1 << data_width) - 1
        self.depth = 1 << addr_width
        self.addr_mask = self.depth - 1
        self.words = [0] * self.depth

    def observe(
        self,
        *,
        rst: bool = False,
        we: bool = False,
        waddr: int = 0,
        wdata: int = 0,
        raddr_a: int = 0,
        raddr_b: int = 0,
    ) -> RegisterFileReadOutput:
        write_address = waddr & self.addr_mask
        write_data = wdata & self.data_mask

        def read(address: int) -> int:
            selected = address & self.addr_mask
            if not rst and we and selected == write_address:
                return write_data
            return self.words[selected]

        return RegisterFileReadOutput(read(raddr_a), read(raddr_b))

    def step(
        self,
        *,
        rst: bool = False,
        we: bool = False,
        waddr: int = 0,
        wdata: int = 0,
        raddr_a: int = 0,
        raddr_b: int = 0,
    ) -> RegisterFileReadOutput:
        if rst:
            self.words = [0] * self.depth
        elif we:
            self.words[waddr & self.addr_mask] = wdata & self.data_mask
        return self.observe(
            rst=rst,
            we=we,
            waddr=waddr,
            wdata=wdata,
            raddr_a=raddr_a,
            raddr_b=raddr_b,
        )
