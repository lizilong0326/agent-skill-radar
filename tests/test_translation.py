import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from radar.taxonomy import GROUP_LABELS, GROUP_LABELS_EN, TAXONOMY, TAXONOMY_EN
from radar.translation import _translate_batch, description_hash, load_local_config, native_chinese, retained_translation, translate_catalog


class TranslationTests(unittest.TestCase):
    def test_english_description_waits_for_chinese_when_key_missing(self):
        item = {"description": "Review code changes and identify bugs."}
        catalog = {"repositories": [], "items": [item]}
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}):
            calls, pending, changed = translate_catalog(catalog, 100)
        self.assertEqual((calls, pending, changed), (0, 1, True))
        self.assertEqual(item["description_en"], item["description"])
        self.assertNotIn("description_zh", item)

    def test_chinese_words_in_english_description_still_need_translation(self):
        self.assertFalse(native_chinese("English(README.md) | 简体中文(README.zh-CN.md)"))
        self.assertFalse(native_chinese("Use this skill for research, 调研, 搜索, and web lookup."))
        self.assertTrue(native_chinese("基于 AI 的研究助手，帮助检索资料并整理来源。"))

    def test_chinese_original_gets_english_translation(self):
        item = {"description": "帮助检查代码变更并查找错误。"}
        catalog = {"repositories": [], "items": [item]}
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}), patch(
            "radar.translation._translate_batch", return_value={"0": "Review code changes and find bugs."}
        ) as model:
            calls, pending, _ = translate_catalog(catalog, 1)
        self.assertEqual((calls, pending), (1, 0))
        self.assertEqual(item["description_zh_source"], "original")
        self.assertEqual(item["description_en"], "Review code changes and find bugs.")
        self.assertEqual(model.call_args.args[2], "en")

    def test_unchanged_translation_is_reused_and_stale_one_is_cleared(self):
        item = {"description": "Review code changes.", "description_zh": "检查代码变更。",
                "description_en": "Review code changes.", "description_translation_hash": description_hash("Review code changes.")}
        self.assertEqual(retained_translation(item, item["description"])["description_zh"], "检查代码变更。")
        self.assertEqual(retained_translation(item, "Build web pages."), {})
        item["description"] = "Build web pages."
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}):
            calls, pending, _ = translate_catalog({"repositories": [], "items": [item]}, 0)
        self.assertEqual((calls, pending), (0, 1))
        self.assertNotIn("description_zh", item)

    def test_taxonomy_has_both_languages(self):
        self.assertEqual(set(TAXONOMY_EN), set(TAXONOMY))
        self.assertEqual(set(GROUP_LABELS_EN), set(GROUP_LABELS))

    def test_model_response_must_match_id_and_requested_language(self):
        response = {"choices": [{"message": {"content": json.dumps({"translations": [
            {"id": "0", "text": "检查代码变更并查找错误。"},
            {"id": "1", "text": "Review code changes and find bugs."},
            {"id": "other", "text": "凭空添加的内容。"},
        ]}, ensure_ascii=False)}}]}
        requested = []
        def fake_urlopen(request, timeout):
            requested.append(json.loads(request.data)["model"])
            return io.BytesIO(json.dumps(response).encode())
        with patch.dict("os.environ", {"DEEPSEEK_MODEL": "deepseek-v4-flash"}), patch(
            "radar.translation.urllib.request.urlopen", side_effect=fake_urlopen
        ):
            result = _translate_batch([{"id": "0", "text": "Review code changes."},
                                       {"id": "1", "text": "Find bugs."}], "test-key", "zh")
        self.assertEqual(result, {"0": "检查代码变更并查找错误。"})
        self.assertEqual(requested, ["deepseek-v4-flash"])

    def test_local_config_loads_model_without_filling_blank_key(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, ".env").write_text("DEEPSEEK_API_KEY=\nDEEPSEEK_MODEL=deepseek-v4-flash\n", encoding="utf-8")
            with patch("radar.translation.ROOT", Path(directory)), patch.dict(
                "os.environ", {"DEEPSEEK_API_KEY": "", "DEEPSEEK_MODEL": ""}
            ):
                load_local_config()
                self.assertEqual(os.getenv("DEEPSEEK_API_KEY"), "")
                self.assertEqual(os.getenv("DEEPSEEK_MODEL"), "deepseek-v4-flash")

    def test_long_chinese_source_can_have_longer_english_translation(self):
        source = "聚合多平台信息，筛选热点并生成趋势分析简报。" * 10
        translated = "Aggregate information from multiple platforms, filter trending topics, and produce trend reports. " * 6
        response = {"choices": [{"message": {"content": json.dumps({"translations": [{"id": "0", "text": translated}]})}}]}
        with patch("radar.translation.urllib.request.urlopen", return_value=io.BytesIO(json.dumps(response).encode())):
            result = _translate_batch([{"id": "0", "text": source}], "test-key", "en")
        self.assertEqual(result["0"], translated.strip())


if __name__ == "__main__":
    unittest.main()
