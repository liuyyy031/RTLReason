import json
import unittest

from rtlreason.config import Settings
from rtlreason.hy3.client import Hy3Client, extract_json_object
from rtlreason.hy3.prompts import JUDGE_PROMPT_VERSION, JUDGE_SYSTEM_PROMPT


class Hy3ClientTests(unittest.TestCase):
    def test_request_shape_and_response(self) -> None:
        captured = {}

        def transport(request, timeout):
            captured["url"] = request.full_url
            captured["authorization"] = request.headers["Authorization"]
            captured["timeout"] = timeout
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return json.dumps({
                "id": "request-1",
                "model": "hy3",
                "choices": [{"finish_reason": "stop", "message": {"content": "{\"ok\": true}", "reasoning_content": "not persisted"}}],
                "usage": {"total_tokens": 3},
            }).encode("utf-8")

        settings = Settings(api_key="test-key", timeout_seconds=12)
        response = Hy3Client(settings, transport=transport).chat(
            [{"role": "user", "content": "hello"}]
        )
        self.assertEqual(captured["url"], "https://tokenhub.tencentmaas.com/v1/chat/completions")
        self.assertEqual(captured["authorization"], "Bearer test-key")
        self.assertEqual(captured["payload"]["thinking"], {"type": "enabled"})
        self.assertEqual(captured["payload"]["reasoning_effort"], "high")
        self.assertEqual(response.content, '{"ok": true}')
        self.assertEqual(response.finish_reason, "stop")
        self.assertFalse(hasattr(response, "reasoning_content"))

    def test_json_extraction(self) -> None:
        self.assertEqual(extract_json_object("```json\n{\"x\": 1}\n```"), {"x": 1})
        wrapped = '{"note": 1}\nnoise\n{"task_id": "t", "stages": [], "rtl": {}}'
        selected = extract_json_object(
            wrapped, required_keys={"task_id", "stages", "rtl"}
        )
        self.assertEqual(selected["task_id"], "t")

    def test_judge_prompt_requires_property_priority_checks(self) -> None:
        self.assertEqual(JUDGE_PROMPT_VERSION, "1.1")
        self.assertIn("reset", JUDGE_SYSTEM_PROMPT)
        self.assertIn("priority", JUDGE_SYSTEM_PROMPT)
        self.assertIn("correct RTL", JUDGE_SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
