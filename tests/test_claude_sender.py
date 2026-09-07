import unittest
from unittest.mock import MagicMock, patch

from src.automation.claude_sender import (
    _is_valid_input_element,
    find_input_box,
)


class MockRect:
    def __init__(self, left=100, top=500, right=800, bottom=550):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def width(self):
        return self.right - self.left

    def height(self):
        return self.bottom - self.top

    def __repr__(self):
        return f"(L{self.left}, T{self.top}, R{self.right}, B{self.bottom})"


class MockElementInfo:
    def __init__(self, control_type="Edit", name="", class_name="", automation_id=""):
        self.control_type = control_type
        self.name = name
        self.class_name = class_name
        self.automation_id = automation_id


class MockElement:
    def __init__(
        self,
        control_type="Edit",
        name="",
        class_name="",
        rect=None,
        is_enabled=True,
    ):
        self.element_info = MockElementInfo(
            control_type=control_type,
            name=name,
            class_name=class_name,
        )
        self._rect = rect or MockRect()
        self._enabled = is_enabled

    def rectangle(self):
        return self._rect

    def is_enabled(self):
        return self._enabled

    def click_input(self):
        pass

    def set_focus(self):
        pass


class MockClaudeWindow:
    def __init__(self, edit_elements=None, all_elements=None):
        self._edits = edit_elements or []
        self._all = all_elements or self._edits

    def descendants(self, control_type=None):
        if control_type == "Edit":
            return [e for e in self._edits if e.element_info.control_type == "Edit"]
        if control_type == "Document":
            return [e for e in self._edits if e.element_info.control_type == "Document"]
        if control_type == "Button":
            return [e for e in self._all if e.element_info.control_type == "Button"]
        return self._all

    def set_focus(self):
        pass


class TestClaudeSender(unittest.TestCase):

    def test_is_valid_input_element(self):
        # Valid element
        el_valid = MockElement(rect=MockRect(100, 100, 300, 150))
        self.assertTrue(_is_valid_input_element(el_valid))

        # Too small / invisible width
        el_narrow = MockElement(rect=MockRect(100, 100, 120, 150))
        self.assertFalse(_is_valid_input_element(el_narrow))

        # Too small height
        el_flat = MockElement(rect=MockRect(100, 100, 300, 105))
        self.assertFalse(_is_valid_input_element(el_flat))

        # Disabled
        el_disabled = MockElement(is_enabled=False)
        self.assertFalse(_is_valid_input_element(el_disabled))

    @patch("src.automation.claude_sender._ensure_desktop_access")
    @patch("src.automation.claude_sender._ensure_window_active")
    def test_find_input_box_tier1_prosemirror_class(self, mock_active, mock_desktop):
        # Matches via ProseMirror class even if name is empty
        input_el = MockElement(
            control_type="Edit",
            name="",
            class_name="tiptap ProseMirror",
        )
        claude = MockClaudeWindow(edit_elements=[input_el])

        result = find_input_box(claude, timeout=0.5)
        self.assertIsNotNone(result)
        self.assertEqual(result.element_info.class_name, "tiptap ProseMirror")

    @patch("src.automation.claude_sender._ensure_desktop_access")
    @patch("src.automation.claude_sender._ensure_window_active")
    def test_find_input_box_tier2_placeholder_name(self, mock_active, mock_desktop):
        # Matches via 'Reply to Claude...' in existing chat
        input_el = MockElement(
            control_type="Edit",
            name="Reply to Claude...",
            class_name="custom-editor",
        )
        claude = MockClaudeWindow(edit_elements=[input_el])

        result = find_input_box(claude, timeout=0.5)
        self.assertIsNotNone(result)
        self.assertEqual(result.element_info.name, "Reply to Claude...")

    @patch("src.automation.claude_sender._ensure_desktop_access")
    @patch("src.automation.claude_sender._ensure_window_active")
    def test_find_input_box_tier3_document_control(self, mock_active, mock_desktop):
        # Matches Document control with ProseMirror class
        doc_el = MockElement(
            control_type="Document",
            name="Write your prompt to Claude",
            class_name="tiptap ProseMirror",
        )
        claude = MockClaudeWindow(edit_elements=[doc_el])

        result = find_input_box(claude, timeout=0.5)
        self.assertIsNotNone(result)
        self.assertEqual(result.element_info.control_type, "Document")

    @patch("src.automation.claude_sender._ensure_desktop_access")
    @patch("src.automation.claude_sender._ensure_window_active")
    def test_find_input_box_tier4_single_edit_fallback(self, mock_active, mock_desktop):
        # Matches single visible Edit even if name and class are unfamiliar
        generic_el = MockElement(
            control_type="Edit",
            name="Type here",
            class_name="unknown-class",
            rect=MockRect(100, 500, 700, 550),
        )
        claude = MockClaudeWindow(edit_elements=[generic_el])

        result = find_input_box(claude, timeout=0.5)
        self.assertIsNotNone(result)
        self.assertEqual(result.element_info.name, "Type here")

    @patch("src.automation.claude_sender._ensure_desktop_access")
    @patch("src.automation.claude_sender._ensure_window_active")
    def test_find_input_box_not_found(self, mock_active, mock_desktop):
        # Empty window returns None after timeout
        claude = MockClaudeWindow(edit_elements=[])
        result = find_input_box(claude, timeout=0.2, poll_interval=0.1)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
