import unittest

from rtlreason.reference import FifoReferenceModel


class FifoReferenceModelTests(unittest.TestCase):
    def test_reset_and_empty_simultaneous_request(self) -> None:
        model = FifoReferenceModel(depth=4, data_width=8)
        reset = model.step(rst=True, wr_en=True, rd_en=True, din=0xEE)
        self.assertTrue(reset.empty)
        self.assertEqual(reset.dout, 0)

        written = model.step(wr_en=True, rd_en=True, din=0x1A1)
        self.assertTrue(written.write_accepted)
        self.assertFalse(written.read_accepted)
        self.assertFalse(written.read_data_valid)
        self.assertEqual(written.occupancy, 1)

        read = model.step(rd_en=True)
        self.assertTrue(read.read_data_valid)
        self.assertEqual(read.dout, 0xA1)
        self.assertTrue(read.empty)

    def test_full_simultaneous_replaces_oldest(self) -> None:
        model = FifoReferenceModel(depth=4, data_width=8)
        model.step(rst=True)
        for value in (0x11, 0x22, 0x33, 0x44):
            observation = model.step(wr_en=True, din=value)
        self.assertTrue(observation.full)

        simultaneous = model.step(wr_en=True, rd_en=True, din=0x55)
        self.assertTrue(simultaneous.write_accepted)
        self.assertTrue(simultaneous.read_accepted)
        self.assertEqual(simultaneous.dout, 0x11)
        self.assertTrue(simultaneous.full)

        returned = [model.step(rd_en=True).dout for _ in range(4)]
        self.assertEqual(returned, [0x22, 0x33, 0x44, 0x55])
        self.assertEqual(model.occupancy, 0)

    def test_illegal_operations_hold_state(self) -> None:
        model = FifoReferenceModel(depth=2, data_width=4)
        model.step(rst=True)
        empty_read = model.step(rd_en=True)
        self.assertFalse(empty_read.read_accepted)
        self.assertEqual(empty_read.dout, 0)
        model.step(wr_en=True, din=1)
        model.step(wr_en=True, din=2)
        full_write = model.step(wr_en=True, din=3)
        self.assertFalse(full_write.write_accepted)
        self.assertEqual(full_write.occupancy, 2)


if __name__ == "__main__":
    unittest.main()
