import unittest

from rtlreason.verification.sby import classify_sby_result


class SbyResultClassificationTests(unittest.TestCase):
    def test_pass(self) -> None:
        self.assertIs(classify_sby_result(0, "DONE (PASS, rc=0)"), True)

    def test_property_failure(self) -> None:
        self.assertIs(classify_sby_result(2, "DONE (FAIL, rc=2)"), False)

    def test_unknown_is_not_property_failure(self) -> None:
        output = "Status: failed\nStatus: passed\nDONE (UNKNOWN, rc=4)"
        self.assertIs(classify_sby_result(4, output), None)

    def test_tool_error_is_not_property_failure(self) -> None:
        self.assertIs(classify_sby_result(16, "DONE (ERROR, rc=16)"), None)


if __name__ == "__main__":
    unittest.main()
