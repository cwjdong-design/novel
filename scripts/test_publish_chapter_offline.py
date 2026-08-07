#!/usr/bin/env python3
"""publish_chapter.py 纯离线安全回归测试。"""

import contextlib
import io
import json
import os
import tempfile
import unittest

import publish_chapter as pc


SELECTORS = {
    '.serial-editor-title-left input[type="text"]',
    'input[placeholder*="标题"]',
    '.serial-editor-container .ProseMirror[contenteditable="true"]',
    'button:has-text("存草稿")',
}


class FakeLocator:
    def __init__(self, count=1, visible=True, enabled=True):
        self._count = count
        self._visible = visible
        self._enabled = enabled
        self.evaluate_calls = []

    def count(self):
        return self._count

    def is_visible(self):
        return self._visible

    def is_enabled(self):
        return self._enabled

    def evaluate(self, script, arg=None):
        self.evaluate_calls.append((script, arg))


class FakePage:
    def __init__(self, overrides=None):
        self.overrides = overrides or {}

    def locator(self, selector):
        return self.overrides.get(selector, FakeLocator())


def write_md(content):
    f = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.md', delete=False)
    f.write(content)
    f.close()
    return f.name


class TestParseAndValidateMd(unittest.TestCase):
    def test_normal_utf8_preserves_title_and_paragraphs(self):
        path = write_md('## 第12章「蛏苗」\n\n第一段。\n\n第二段。\n')
        try:
            result = pc.parse_and_validate_md(path, 12)
        finally:
            os.unlink(path)
        self.assertEqual(result['chapter'], 12)
        self.assertEqual(result['title'], '蛏苗')
        self.assertEqual(result['body_html'], '<p>第一段。</p><p>第二段。</p>')

    def test_rejects_chapter_mismatch(self):
        path = write_md('## 第12章「蛏苗」\n\n正文。\n')
        try:
            with self.assertRaisesRegex(ValueError, '不一致'):
                pc.parse_and_validate_md(path, 13)
        finally:
            os.unlink(path)

    def test_rejects_nul(self):
        path = write_md('## 第12章「蛏苗」\n\n正文\x00污染。\n')
        try:
            with self.assertRaisesRegex(ValueError, 'NUL'):
                pc.parse_and_validate_md(path, 12)
        finally:
            os.unlink(path)

    def test_rejects_empty_title(self):
        path = write_md('## 第12章\n\n正文。\n')
        try:
            with self.assertRaisesRegex(ValueError, '标题'):
                pc.parse_and_validate_md(path, 12)
        finally:
            os.unlink(path)

    def test_rejects_empty_body(self):
        path = write_md('## 第12章「蛏苗」\n')
        try:
            with self.assertRaisesRegex(ValueError, '正文'):
                pc.parse_and_validate_md(path, 12)
        finally:
            os.unlink(path)

    def test_escapes_html_metacharacters(self):
        path = write_md('## 第12章「蛏苗」\n\nx < 5 & y > 3\n<script>alert(1)</script>\n')
        try:
            result = pc.parse_and_validate_md(path, 12)
        finally:
            os.unlink(path)
        self.assertIn('x &lt; 5 &amp; y &gt; 3', result['body_html'])
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', result['body_html'])
        self.assertNotIn('<script>', result['body_html'])


class TestEditorSafety(unittest.TestCase):
    def test_set_input_value_passes_data_as_argument(self):
        locator = FakeLocator()
        value = '标题含"双引号"、\\反斜杠和\n换行'
        pc.set_input_value(locator, value)
        self.assertEqual(len(locator.evaluate_calls), 1)
        script, arg = locator.evaluate_calls[0]
        self.assertEqual(arg, value)
        self.assertNotIn(value, script)

    def test_missing_element_fails_closed(self):
        page = FakePage({'input[placeholder*="标题"]': FakeLocator(count=0)})
        with self.assertRaisesRegex(RuntimeError, '缺少'):
            pc.validate_editor_elements(page)

    def test_ambiguous_element_fails_closed(self):
        page = FakePage({'button:has-text("存草稿")': FakeLocator(count=2)})
        with self.assertRaisesRegex(RuntimeError, '不唯一'):
            pc.validate_editor_elements(page)

    def test_invisible_editor_fails_closed(self):
        selector = '.serial-editor-container .ProseMirror[contenteditable="true"]'
        page = FakePage({selector: FakeLocator(visible=False)})
        with self.assertRaisesRegex(RuntimeError, '不可见'):
            pc.validate_editor_elements(page)

    def test_disabled_save_button_fails_closed(self):
        selector = 'button:has-text("存草稿")'
        page = FakePage({selector: FakeLocator(enabled=False)})
        with self.assertRaisesRegex(RuntimeError, '不可用'):
            pc.validate_editor_elements(page)


class TestDraftPayload(unittest.TestCase):
    def test_normalizes_documented_api_payload(self):
        payload = {'data': {'total_count': 2, 'draft_list': [
            {'item_id': 'a1', 'title': '第12章 蛏苗', 'word_number': 2230, 'modify_time': 100},
            {'item_id': 'a2', 'title': '第13章「回潮」', 'word_number': 2201, 'modify_time': 101},
        ]}}
        result = pc.normalize_draft_payload(payload)
        self.assertEqual(result, [
            {'chapter': 12, 'title': '蛏苗', 'id': 'a1', 'word_count': 2230, 'modify_time': 100},
            {'chapter': 13, 'title': '回潮', 'id': 'a2', 'word_count': 2201, 'modify_time': 101},
        ])

    def test_ignores_incomplete_entries_without_guessing(self):
        payload = {'data': {'draft_list': [
            {'item_id': 'missing-title', 'word_number': 10},
            {'item_id': 'bad-title', 'title': '没有章节号', 'word_number': 20},
            {'item_id': 'ok', 'title': '第8章 测试', 'word_number': 30},
        ]}}
        self.assertEqual(pc.normalize_draft_payload(payload), [
            {'chapter': 8, 'title': '测试', 'id': 'ok', 'word_count': 30, 'modify_time': None}
        ])
    def test_rejects_partial_or_unparseable_snapshot(self):
        partial = {'data': {'total_count': 2, 'draft_list': [
            {'item_id': 'a1', 'title': '第12章 蛏苗', 'word_number': 2230},
        ]}}
        with self.assertRaisesRegex(RuntimeError, '不完整'):
            pc.snapshot_from_payload(partial)

        ambiguous = {'data': {'total_count': 1, 'draft_list': [
            {'item_id': 'a2', 'title': '只有标题没有章节号', 'word_number': 2200},
        ]}}
        with self.assertRaisesRegex(RuntimeError, '无法解析'):
            pc.snapshot_from_payload(ambiguous)

    def test_accepts_complete_structured_snapshot(self):
        payload = {'data': {'total_count': 1, 'draft_list': [
            {'item_id': 'a1', 'title': '第12章 蛏苗', 'word_number': 2230, 'modify_time': 100},
        ]}}
        self.assertEqual(pc.snapshot_from_payload(payload), [
            {'chapter': 12, 'title': '蛏苗', 'id': 'a1', 'word_count': 2230, 'modify_time': 100}
        ])


class TestReconciliation(unittest.TestCase):
    def test_preexisting_same_chapter_blocks_even_if_title_differs(self):
        before = [{'chapter': 12, 'title': '旧标题', 'id': 'old', 'word_count': 100}]
        result = pc.reconcile_draft_result(before, before, 12, '蛏苗')
        self.assertEqual(result['status'], 'duplicate_detected')
        self.assertEqual(result['duplicate_count'], 1)

    def test_before_absent_after_present_is_verified(self):
        after = [{'chapter': 12, 'title': '蛏苗', 'id': 'new', 'word_count': 2230}]
        result = pc.reconcile_draft_result([], after, 12, '蛏苗')
        self.assertEqual(result['status'], 'draft_saved_verified')
        self.assertEqual(result['platform_word_count'], 2230)
        json.dumps(result)

    def test_after_absent_is_unverified(self):
        result = pc.reconcile_draft_result([], [], 12, '蛏苗')
        self.assertEqual(result['status'], 'save_unverified')
        self.assertIsNone(result['platform_word_count'])

    def test_after_same_chapter_wrong_title_is_unverified(self):
        after = [{'chapter': 12, 'title': '错误标题', 'id': 'new', 'word_count': 2230}]
        result = pc.reconcile_draft_result([], after, 12, '蛏苗')
        self.assertEqual(result['status'], 'save_unverified')


class TestExecutionOrder(unittest.TestCase):
    def test_duplicate_stops_before_open_or_click(self):
        calls = []
        before = [{'chapter': 12, 'title': '已有草稿', 'id': 'old', 'word_count': 10}]
        result = pc.execute_draft_flow(
            before, 12, '蛏苗',
            open_editor=lambda: calls.append('open'),
            click_save=lambda: calls.append('click'),
            postcheck=lambda: calls.append('post') or [],
        )
        self.assertEqual(result['status'], 'duplicate_detected')
        self.assertEqual(calls, [])

    def test_nonduplicate_order_is_open_click_postcheck(self):
        calls = []
        after = [{'chapter': 12, 'title': '蛏苗', 'id': 'new', 'word_count': 2230}]
        result = pc.execute_draft_flow(
            [], 12, '蛏苗',
            open_editor=lambda: calls.append('open'),
            click_save=lambda: calls.append('click'),
            postcheck=lambda: calls.append('post') or after,
        )
        self.assertEqual(calls, ['open', 'click', 'post'])
        self.assertEqual(result['status'], 'draft_saved_verified')

    def test_unverified_path_prints_no_success_claim(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = pc.execute_draft_flow(
                [], 12, '蛏苗',
                open_editor=lambda: None,
                click_save=lambda: None,
                postcheck=lambda: [],
            )
        self.assertEqual(result['status'], 'save_unverified')
        self.assertNotIn('已存草稿', out.getvalue())
        self.assertNotIn('draft_saved_verified', out.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
