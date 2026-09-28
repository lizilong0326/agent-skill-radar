import io
import json
import unittest
from unittest.mock import patch

from radar.translation import description_hash
from radar.use_cases import _summarize_batch, generate_use_cases, retained_use_case


class UseCaseTests(unittest.TestCase):
    def test_summary_is_reused_only_for_the_same_source(self):
        old = {"use_case_zh": "适合审查代码。", "use_case_en": "Good for reviewing code.",
               "use_case_hash": description_hash("Review code changes.")}
        self.assertEqual(retained_use_case(old, "Review code changes."), old)
        self.assertEqual(retained_use_case(old, "Build a website."), {})

    def test_batch_uses_configured_model_and_rejects_wrong_language(self):
        response = {"choices": [{"message": {"content": json.dumps({"summaries": [
            {"id": "0", "zh": "适合审查代码变更并查找缺陷。", "en": "Good for reviewing code changes and finding bugs."},
            {"id": "1", "zh": "Review code changes.", "en": "Good for reviewing code changes."},
        ]}, ensure_ascii=False)}}]}
        requested = []

        def fake_urlopen(request, timeout):
            requested.append(json.loads(request.data)["model"])
            return io.BytesIO(json.dumps(response).encode())

        entries = [{"id": "0", "zh": "检查代码变更。", "en": "Review code changes."},
                   {"id": "1", "zh": "审查变更。", "en": "Review changes."}]
        with patch.dict("os.environ", {"DEEPSEEK_MODEL": "deepseek-v4-flash"}), patch(
            "radar.use_cases.urllib.request.urlopen", side_effect=fake_urlopen
        ):
            result = _summarize_batch(entries, "test-key")
        self.assertEqual(requested, ["deepseek-v4-flash"])
        self.assertEqual(list(result), ["0"])

    def test_only_pending_items_are_generated(self):
        first = {"description": "Review code changes.", "description_zh": "检查代码变更。",
                 "description_en": "Review code changes."}
        second = {**first, "use_case_zh": "适合审查代码。", "use_case_en": "Good for reviewing code.",
                  "use_case_hash": description_hash(first["description"])}
        catalog = {"items": [first, second], "workflow_labels": {}, "workflow_labels_en": {}}
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}), patch(
            "radar.use_cases._summarize_batch", return_value={"0": {
                "use_case_zh": "适合审查代码变更并查找缺陷。",
                "use_case_en": "Good for reviewing code changes and finding bugs.",
            }}
        ) as model:
            self.assertEqual(generate_use_cases(catalog, 1), (1, 0))
        self.assertEqual(len(model.call_args.args[0]), 1)
        self.assertEqual(first["use_case_hash"], description_hash(first["description"]))
        self.assertEqual(second["use_case_zh"], "适合审查代码。")


if __name__ == "__main__":
    unittest.main()
