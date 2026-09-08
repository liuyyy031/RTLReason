# SPI Mode-0 Byte Transmitter

Design a synthesizable SystemVerilog module named `spi_tx` that transmits one
8-bit word in SPI mode 0, MSB first. An idle `start` is accepted on a rising
`clk` edge. The transmitter presents bit 7 before the first `sclk` rising edge,
keeps data stable for each rising sampling edge, and advances data on falling
edges. The transaction completes on the falling edge following the eighth
sampling edge.

Use the exact divider, busy/start, reset, idle-output, and done-pulse semantics
defined in `interface_semantics.json`.
