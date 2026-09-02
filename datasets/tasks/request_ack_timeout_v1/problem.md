# Request/Acknowledge Controller with Timeout

Design a synthesizable SystemVerilog module named `request_ack_timeout`.

When idle, a sampled high `req` starts one outstanding transaction. The
controller then waits for `ack` for exactly `TIMEOUT_CYCLES` subsequent service
edges. Acknowledgement has priority on the final allowed edge. If no acknowledgement
arrives, assert a one-cycle `timeout` pulse and return idle. A successful
acknowledgement asserts a one-cycle `done` pulse and returns idle. Requests while
busy, including a request on the completion edge, do not restart or replace the
outstanding transaction.

Use the exact edge numbering and simultaneous-input rules in
`interface_semantics.json`.
