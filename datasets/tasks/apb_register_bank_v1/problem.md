# Zero-Wait APB Register Bank

Design a synthesizable SystemVerilog module named `apb_register_bank`.

Implement two 32-bit registers at byte addresses 0x0 and 0x4 using the defined
APB-like setup/access interface. Transfers occur only in the access phase
(`psel && penable`). The slave is always ready. Valid writes update exactly one
register; reads return the current addressed value. Any other address reports
an access-phase error and has no side effect.

Use exactly the ports and observable timing in `interface_semantics.json`.
