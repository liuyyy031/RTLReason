import unittest

from rtlreason.reference import (
    CounterReferenceModel,
    DebounceFilterReferenceModel,
    DualPortRamReferenceModel,
    GrantHoldArbiterReferenceModel,
    ReadyValidSliceReferenceModel,
    PulseStretcherReferenceModel,
    ReadyValidFifo2ReferenceModel,
    RequestAckTimeoutReferenceModel,
    RisingEdgeDetectorReferenceModel,
    RoundRobinArbiterReferenceModel,
    SequenceDetector1011ReferenceModel,
    ShiftRegisterReferenceModel,
    TokenBucketReferenceModel,
)


class ReferenceModelTests(unittest.TestCase):
    def test_dual_port_ram_is_registered_read_first_and_holds(self) -> None:
        model = DualPortRamReferenceModel(data_width=8, addr_width=2)
        model.step(wr_en=True, wr_addr=1, wr_data=0xA1)
        self.assertEqual(model.step(rd_en=True, rd_addr=1).rd_data, 0xA1)
        collision = model.step(
            wr_en=True,
            wr_addr=1,
            wr_data=0xB2,
            rd_en=True,
            rd_addr=1,
        )
        self.assertEqual(collision.rd_data, 0xA1)
        self.assertEqual(model.step(rd_en=True, rd_addr=1).rd_data, 0xB2)
        self.assertEqual(model.step(rd_en=False, rd_addr=3).rd_data, 0xB2)
        self.assertEqual(model.step(rst=True).rd_data, 0)

    def test_rising_edge_detector_pulses_once_per_sampled_rise(self) -> None:
        model = RisingEdgeDetectorReferenceModel()
        self.assertFalse(model.step(rst=True, signal_in=True).pulse)
        self.assertTrue(model.step(signal_in=True).pulse)
        self.assertFalse(model.step(signal_in=True).pulse)
        self.assertFalse(model.step(signal_in=False).pulse)
        self.assertTrue(model.step(signal_in=True).pulse)

    def test_counter_priority_and_overflow_pulse(self) -> None:
        model = CounterReferenceModel(width=4)
        self.assertEqual(
            model.step(rst=True, load=True, en=True, load_value=9).count, 0
        )
        self.assertEqual(model.step(load=True, en=True, load_value=15).count, 15)
        wrapped = model.step(en=True)
        self.assertEqual(wrapped.count, 0)
        self.assertTrue(wrapped.overflow)
        self.assertFalse(model.step().overflow)

    def test_shift_direction_and_hold(self) -> None:
        model = ShiftRegisterReferenceModel(width=4)
        for bit in (1, 0, 1, 1):
            model.step(en=True, serial_in=bit)
        self.assertEqual(model.q, 0b1011)
        self.assertEqual(model.serial_out, 1)
        self.assertEqual(model.step(en=False, serial_in=0)[0], 0b1011)

    def test_round_robin_rotation_and_idle_hold(self) -> None:
        model = RoundRobinArbiterReferenceModel(4)
        self.assertEqual(model.step(0b1010), 0b0010)
        self.assertEqual(model.step(0b1010), 0b1000)
        self.assertEqual(model.step(0), 0)
        self.assertEqual(model.step(0b0101), 0b0001)

    def test_ready_valid_backpressure_replace_and_drain(self) -> None:
        model = ReadyValidSliceReferenceModel(8)
        first = model.step(in_valid=True, in_data=0xA1, out_ready=False)
        self.assertTrue(first.out_valid)
        blocked = model.step(in_valid=True, in_data=0xB2, out_ready=False)
        self.assertEqual(blocked.out_data, 0xA1)
        replaced = model.step(in_valid=True, in_data=0xB2, out_ready=True)
        self.assertEqual(replaced.out_data, 0xB2)
        drained = model.step(in_valid=False, out_ready=True)
        self.assertFalse(drained.out_valid)
        self.assertEqual(drained.out_data, 0xB2)

    def test_request_ack_exact_timeout_and_final_ack_priority(self) -> None:
        model = RequestAckTimeoutReferenceModel(timeout_cycles=3)
        accepted = model.step(req=True, ack=True)
        self.assertTrue(accepted.busy)
        self.assertFalse(accepted.done)
        self.assertTrue(model.step(ack=True).done)

        model.step(req=True)
        self.assertFalse(model.step().timeout)
        self.assertFalse(model.step().timeout)
        expired = model.step()
        self.assertTrue(expired.timeout)
        self.assertFalse(expired.busy)

        model.step(req=True)
        model.step()
        model.step()
        completed = model.step(ack=True)
        self.assertTrue(completed.done)
        self.assertFalse(completed.timeout)

    def test_ready_valid_fifo2_full_replacement_preserves_order(self) -> None:
        model = ReadyValidFifo2ReferenceModel(8)
        model.step(in_valid=True, in_data=0xA1)
        model.step(in_valid=True, in_data=0xB2)
        self.assertFalse(model.observe(out_ready=False).in_ready)
        replaced = model.step(
            in_valid=True, in_data=0xC3, out_ready=True
        )
        self.assertTrue(replaced.out_valid)
        self.assertEqual(replaced.out_data, 0xB2)
        next_word = model.step(out_ready=True)
        self.assertEqual(next_word.out_data, 0xC3)

    def test_sequence_detector_valid_gating_and_overlap(self) -> None:
        model = SequenceDetector1011ReferenceModel()
        matches = [
            model.step(bit_valid=True, bit_in=bool(bit)).match
            for bit in (1, 0, 1, 1, 0, 1, 1)
        ]
        self.assertEqual(matches, [False, False, False, True, False, False, True])

        model.step(rst=True)
        model.step(bit_valid=True, bit_in=True)
        held = model.step(bit_valid=False, bit_in=False)
        self.assertEqual(held.prefix_length, 1)
        for bit in (0, 1):
            self.assertFalse(model.step(bit_valid=True, bit_in=bool(bit)).match)
        self.assertTrue(model.step(bit_valid=True, bit_in=True).match)

    def test_pulse_stretcher_exact_duration_and_retrigger(self) -> None:
        model = PulseStretcherReferenceModel(pulse_cycles=3)
        self.assertTrue(model.step(trigger=True).active)
        self.assertTrue(model.step().active)
        self.assertTrue(model.step().active)
        self.assertFalse(model.step().active)

        model.step(trigger=True)
        model.step()
        restarted = model.step(trigger=True)
        self.assertEqual(restarted.remaining, 3)
        self.assertTrue(model.step().active)
        self.assertTrue(model.step().active)
        self.assertFalse(model.step().active)

    def test_grant_hold_arbiter_stability_and_completion_gap(self) -> None:
        model = GrantHoldArbiterReferenceModel(4)
        self.assertEqual(model.step(0b1010), 0b0010)
        self.assertEqual(model.step(0b0001), 0b0010)
        self.assertEqual(model.step(0b1000, accept=True), 0)
        self.assertEqual(model.step(0b1000), 0b1000)
        self.assertEqual(model.step(0, accept=True), 0)
        self.assertEqual(model.step(0b1101, accept=True), 0b0001)

    def test_debounce_requires_consecutive_samples_both_directions(self) -> None:
        model = DebounceFilterReferenceModel(stable_cycles=3)
        self.assertFalse(model.step(noisy_in=True).debounced)
        self.assertFalse(model.step(noisy_in=True).debounced)
        cancelled = model.step(noisy_in=False)
        self.assertEqual(cancelled.consecutive, 0)
        model.step(noisy_in=True)
        model.step(noisy_in=True)
        rising = model.step(noisy_in=True)
        self.assertTrue(rising.debounced)
        self.assertTrue(rising.changed)
        self.assertFalse(model.step(noisy_in=True).changed)
        model.step(noisy_in=False)
        model.step(noisy_in=False)
        falling = model.step(noisy_in=False)
        self.assertFalse(falling.debounced)
        self.assertTrue(falling.changed)

    def test_token_bucket_uses_current_state_acceptance(self) -> None:
        model = TokenBucketReferenceModel(capacity=3)
        empty_request = model.step(req=True)
        self.assertFalse(empty_request.grant)
        self.assertEqual(empty_request.tokens, 1)
        self.assertEqual(model.step().tokens, 2)
        middle = model.step(req=True)
        self.assertTrue(middle.grant)
        self.assertEqual(middle.tokens, 2)
        self.assertEqual(model.step().tokens, 3)
        full = model.step(req=True)
        self.assertTrue(full.grant)
        self.assertEqual(full.tokens, 2)


if __name__ == "__main__":
    unittest.main()
