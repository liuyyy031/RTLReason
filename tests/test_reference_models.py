import unittest

from rtlreason.reference import (
    ApbRegisterBankReferenceModel,
    AsyncHandshakeReferenceModel,
    AxiStreamPacketCounterReferenceModel,
    CounterReferenceModel,
    CacheTagLookupReferenceModel,
    CreditFlowControlReferenceModel,
    DebounceFilterReferenceModel,
    DualPortRamReferenceModel,
    GrantHoldArbiterReferenceModel,
    GrayCodeCounterReferenceModel,
    InterruptPendingReferenceModel,
    MulticycleMultiplyReferenceModel,
    ProgrammableTimerReferenceModel,
    ReadyValidSliceReferenceModel,
    RegisterFileBypassReferenceModel,
    PulseStretcherReferenceModel,
    ReadyValidFifo2ReferenceModel,
    RequestAckTimeoutReferenceModel,
    RisingEdgeDetectorReferenceModel,
    RoundRobinArbiterReferenceModel,
    SequenceDetector1011ReferenceModel,
    ShiftRegisterReferenceModel,
    SaturatingCounterReferenceModel,
    SerialParityReferenceModel,
    SignedAluFlagsReferenceModel,
    StreamWidthAdapterReferenceModel,
    SpiTxReferenceModel,
    TokenBucketReferenceModel,
    UartRxReferenceModel,
)


class ReferenceModelTests(unittest.TestCase):
    def test_multicycle_multiply_exact_latency_and_busy_ignore(self) -> None:
        model = MulticycleMultiplyReferenceModel(width=4)
        self.assertTrue(model.step(start=True, a=3, b=5).busy)
        self.assertTrue(model.step(start=True, a=15, b=15).busy)
        model.step()
        model.step()
        completed = model.step()
        self.assertTrue(completed.done)
        self.assertEqual(completed.result, 15)

    def test_uart_rx_lsb_first_and_bad_stop(self) -> None:
        model = UartRxReferenceModel(4)
        model.step(rst=True)
        levels = [False] * 4
        for bit in range(8):
            levels.extend([bool((0xA6 >> bit) & 1)] * 4)
        levels.extend([False] * 4)
        outputs = [model.step(rx=value) for value in levels]
        completed = [output for output in outputs if output.data_valid]
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].data_out, 0xA6)
        self.assertTrue(completed[0].framing_error)

    def test_async_handshake_delivers_once_and_gates_busy(self) -> None:
        model = AsyncHandshakeReferenceModel()
        model.source_step(rst=True, send=False)
        model.destination_step(rst=True)
        accepted = model.source_step(rst=False, send=True)
        self.assertTrue(accepted.accept)
        blocked = model.source_step(rst=False, send=True)
        self.assertFalse(blocked.accept)

        pulses = []
        for _ in range(4):
            pulses.append(model.destination_step(rst=False))
            model.source_step(rst=False, send=False)
        self.assertEqual(sum(pulses), 1)
        self.assertFalse(model.source_step(rst=False, send=False).busy)

    def test_credit_flow_current_state_and_simultaneous_boundaries(self) -> None:
        model = CreditFlowControlReferenceModel(max_credits=3)
        full_pair = model.step(
            rst=False, send_req=True, credit_return=True
        )
        self.assertTrue(full_pair.send_accept)
        self.assertEqual(full_pair.credits, 3)

        for _ in range(3):
            output = model.step(
                rst=False, send_req=True, credit_return=False
            )
            self.assertTrue(output.send_accept)
        self.assertEqual(output.credits, 0)

        empty_pair = model.step(
            rst=False, send_req=True, credit_return=True
        )
        self.assertFalse(empty_pair.send_accept)
        self.assertEqual(empty_pair.credits, 1)

    def test_cache_tag_valid_and_lowest_way_priority(self) -> None:
        model = CacheTagLookupReferenceModel()
        miss = model.evaluate(5, [False, False], [5, 5], [10, 20])
        self.assertEqual((miss.hit, miss.hit_way, miss.hit_data), (False, 0, 0))
        hit = model.evaluate(5, [True, True], [5, 5], [10, 20])
        self.assertEqual((hit.hit, hit.hit_way, hit.hit_data), (True, 0, 10))

    def test_spi_tx_msb_first_and_busy_start_ignored(self) -> None:
        model = SpiTxReferenceModel(half_period_cycles=1)
        model.step(start=True, data_in=0xA6)
        previous_sclk = False
        sampled: list[int] = []
        saw_done = False
        for cycle in range(20):
            output = model.step(start=cycle == 3, data_in=0xFF)
            if not previous_sclk and output.sclk:
                sampled.append(int(output.mosi))
            previous_sclk = output.sclk
            saw_done |= output.done
        self.assertEqual(sampled, [1, 0, 1, 0, 0, 1, 1, 0])
        self.assertTrue(saw_done)
        self.assertFalse(model.busy)

    def test_signed_alu_carry_no_borrow_and_overflow(self) -> None:
        model = SignedAluFlagsReferenceModel(width=4)
        add_overflow = model.evaluate(0b0111, 0b0001, 0)
        self.assertEqual(add_overflow.result, 0b1000)
        self.assertTrue(add_overflow.overflow)
        self.assertFalse(add_overflow.carry)

        subtract = model.evaluate(0b0011, 0b0101, 1)
        self.assertEqual(subtract.result, 0b1110)
        self.assertFalse(subtract.carry)
        self.assertFalse(subtract.overflow)

        subtract_overflow = model.evaluate(0b1000, 0b0001, 1)
        self.assertEqual(subtract_overflow.result, 0b0111)
        self.assertTrue(subtract_overflow.carry)
        self.assertTrue(subtract_overflow.overflow)

    def test_register_file_dual_read_bypass_and_reset_priority(self) -> None:
        model = RegisterFileBypassReferenceModel(data_width=8, addr_width=2)
        bypassed = model.observe(
            we=True,
            waddr=1,
            wdata=0xA5,
            raddr_a=1,
            raddr_b=1,
        )
        self.assertEqual((bypassed.rdata_a, bypassed.rdata_b), (0xA5, 0xA5))
        model.step(we=True, waddr=1, wdata=0xA5)
        independent = model.observe(raddr_a=1, raddr_b=2)
        self.assertEqual((independent.rdata_a, independent.rdata_b), (0xA5, 0))
        reset = model.step(
            rst=True,
            we=True,
            waddr=1,
            wdata=0xFF,
            raddr_a=1,
            raddr_b=1,
        )
        self.assertEqual((reset.rdata_a, reset.rdata_b), (0, 0))

    def test_axi_stream_packet_counter_gating_clear_and_saturation(self) -> None:
        model = AxiStreamPacketCounterReferenceModel(count_width=2)
        self.assertEqual(model.step(tvalid=True, tlast=True).beat_count, 0)
        self.assertEqual(
            model.step(tvalid=True, tready=True).beat_count,
            1,
        )
        completed = model.step(tvalid=True, tready=True, tlast=True)
        self.assertEqual((completed.beat_count, completed.packet_count), (2, 1))
        cleared = model.step(clear=True, tvalid=True, tready=True, tlast=True)
        self.assertEqual((cleared.beat_count, cleared.packet_count), (0, 0))
        for _ in range(5):
            saturated = model.step(tvalid=True, tready=True, tlast=True)
        self.assertEqual((saturated.beat_count, saturated.packet_count), (3, 3))

    def test_gray_counter_sequence_hold_wrap_and_reset_priority(self) -> None:
        model = GrayCodeCounterReferenceModel(width=3)
        self.assertEqual(model.step(rst=True, en=True).gray, 0)
        sequence = [model.step(en=True) for _ in range(8)]
        self.assertEqual(
            [item.gray for item in sequence],
            [0b001, 0b011, 0b010, 0b110, 0b111, 0b101, 0b100, 0b000],
        )
        self.assertEqual([item.wrap for item in sequence], [False] * 7 + [True])
        self.assertEqual(model.step().gray, 0)
        self.assertFalse(model.step().wrap)

    def test_saturating_counter_holds_boundaries(self) -> None:
        model = SaturatingCounterReferenceModel(width=2)
        self.assertTrue(model.step(rst=True).at_min)
        self.assertTrue(model.step(en=True, up=False).at_min)
        for _ in range(4):
            top = model.step(en=True, up=True)
        self.assertEqual(top.count, 3)
        self.assertTrue(top.at_max)

    def test_serial_parity_includes_start_and_finish_bits(self) -> None:
        model = SerialParityReferenceModel()
        self.assertTrue(model.step(start=True, bit_valid=True, bit_in=True).busy)
        model.step(bit_valid=True, bit_in=False)
        final = model.step(finish=True, bit_valid=True, bit_in=True)
        self.assertFalse(final.parity)
        self.assertTrue(final.done)
        self.assertFalse(model.step(bit_valid=True, bit_in=True).done)

    def test_programmable_timer_clamps_and_reloads(self) -> None:
        model = ProgrammableTimerReferenceModel(width=4)
        self.assertEqual(model.step(load=True, period=0).remaining, 1)
        self.assertTrue(model.step(enable=True).tick)
        model.step(load=True, period=3)
        self.assertEqual(model.step(enable=True).remaining, 2)
        self.assertEqual(model.step(enable=True).remaining, 1)
        expired = model.step(enable=True)
        self.assertTrue(expired.tick)
        self.assertEqual(expired.remaining, 3)

    def test_interrupt_pending_is_set_dominant(self) -> None:
        model = InterruptPendingReferenceModel()
        self.assertEqual(model.step(irq=0b0110).index, 1)
        collision = model.step(ack=True, irq=0b0010)
        self.assertEqual(collision.pending, 0b0110)
        self.assertEqual(model.step(ack=True).pending, 0b0100)

    def test_stream_width_adapter_packs_little_endian_and_has_gap(self) -> None:
        model = StreamWidthAdapterReferenceModel()
        self.assertTrue(model.step(in_valid=True, in_data=0x34).in_ready)
        word = model.step(in_valid=True, in_data=0x12)
        self.assertTrue(word.out_valid)
        self.assertEqual(word.out_data, 0x1234)
        drained = model.step(in_valid=True, in_data=0x56, out_ready=True)
        self.assertFalse(drained.out_valid)
        self.assertEqual(model.step(in_valid=True, in_data=0x56).out_data, 0x1234)

    def test_apb_register_bank_requires_access_phase(self) -> None:
        model = ApbRegisterBankReferenceModel()
        model.step(psel=True, penable=False, pwrite=True, paddr=0, pwdata=0xAA)
        self.assertEqual(model.step(paddr=0).prdata, 0)
        model.step(psel=True, penable=True, pwrite=True, paddr=0, pwdata=0xAA)
        self.assertEqual(model.step(paddr=0).prdata, 0xAA)
        self.assertTrue(model.step(psel=True, penable=True, paddr=8).pslverr)

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
