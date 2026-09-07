import unittest
from unittest.mock import MagicMock, call, patch

from src.automation.antigravity_automation import AntigravityAutomation
from src.automation.automation_result import AutomationResult


class MockElementInfo:
    def __init__(self, name="", control_type="", class_name=""):
        self.name = name
        self.control_type = control_type
        self.class_name = class_name


class MockRect:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def width(self):
        return self.right - self.left

    def height(self):
        return self.bottom - self.top


class MockUIAElement:
    def __init__(self, name="", control_type="", class_name="", rect=None, has_focus=True):
        self.element_info = MockElementInfo(name=name, control_type=control_type, class_name=class_name)
        self._rect = rect or MockRect(200, 380, 800, 440)
        self._has_focus = has_focus
        self.click_count = 0
        self.focus_count = 0

    def rectangle(self):
        return self._rect

    def is_enabled(self):
        return True

    def click_input(self):
        self.click_count += 1

    def set_focus(self):
        self.focus_count += 1

    def has_keyboard_focus(self):
        return self._has_focus


class TestAntigravityInputPositioning(unittest.TestCase):

    def setUp(self):
        self.automation = AntigravityAutomation()

    def test_new_chat_layout_candidate_selection(self):
        """1. Detects NEW_CHAT layout and selects middle-region input candidate."""
        win_mock = MagicMock()
        win_mock.rectangle.return_value = MockRect(0, 0, 1000, 800)

        # Candidates: search bar at top, middle chat input, bottom panel
        search_bar = MockUIAElement(
            name="Search",
            control_type="Edit",
            class_name="search-input",
            rect=MockRect(50, 40, 250, 70),  # width 200, top 40 -> rel_y = 0.05
        )
        middle_input = MockUIAElement(
            name="Message input",
            control_type="ComboBox",
            class_name="rounded-md cursor-text",
            rect=MockRect(200, 380, 800, 440),  # width 600, top 380 -> rel_y = 0.475 (middle)
        )
        win_mock.descendants.return_value = [search_bar, middle_input]

        layout = self.automation._detect_chat_layout(win_mock)
        self.assertEqual(layout, "NEW_CHAT")

        candidate = self.automation._find_chat_input_candidate(win_mock, layout=layout)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate, middle_input)

    def test_existing_chat_layout_candidate_selection(self):
        """2. Detects EXISTING_CHAT layout and selects bottom-region input candidate."""
        win_mock = MagicMock()
        win_mock.rectangle.return_value = MockRect(0, 0, 1000, 800)

        user_msg = MockUIAElement(
            name="user message",
            control_type="Group",
            class_name="chat-bubble",
            rect=MockRect(200, 100, 800, 200),
        )
        bottom_input = MockUIAElement(
            name="Message input",
            control_type="ComboBox",
            class_name="rounded-md cursor-text",
            rect=MockRect(200, 720, 800, 770),  # width 600, top 720 -> rel_y = 0.90 (bottom)
        )
        win_mock.descendants.return_value = [user_msg, bottom_input]

        layout = self.automation._detect_chat_layout(win_mock)
        self.assertEqual(layout, "EXISTING_CHAT")

        candidate = self.automation._find_chat_input_candidate(win_mock, layout=layout)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate, bottom_input)

    def test_unknown_layout_handling(self):
        """3. UNKNOWN layout handling still selects best available chat input candidate."""
        win_mock = MagicMock()
        win_mock.rectangle.return_value = MockRect(0, 0, 1000, 800)

        # No messages, no explicit new chat marker, neutral input position
        neutral_input = MockUIAElement(
            name="Ask anything",
            control_type="Edit",
            class_name="cursor-text",
            rect=MockRect(250, 520, 750, 570),
        )
        win_mock.descendants.return_value = [neutral_input]

        layout = self.automation._detect_chat_layout(win_mock)
        self.assertIn(layout, ("UNKNOWN", "NEW_CHAT"))

        candidate = self.automation._find_chat_input_candidate(win_mock, layout="UNKNOWN")
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate, neutral_input)

    @patch("src.automation.antigravity_automation._ensure_desktop_access")
    @patch("win32gui.GetForegroundWindow")
    def test_uia_preferred_when_available(self, mock_fg, mock_access):
        """4. UIA is preferred when available and verified."""
        hwnd = 12345
        mock_fg.return_value = hwnd

        win_mock = MagicMock()
        win_mock.rectangle.return_value = MockRect(0, 0, 1000, 800)

        target_input = MockUIAElement(
            name="Message input",
            control_type="ComboBox",
            class_name="cursor-text",
            rect=MockRect(200, 720, 800, 770),
            has_focus=True,
        )
        win_mock.descendants.return_value = [target_input]

        with patch("pyautogui.click") as mock_click:
            result = self.automation._focus_chat_input(hwnd, uia_window=win_mock)
            self.assertTrue(result)
            self.assertEqual(target_input.click_count, 1)
            # Pyautogui fallback click should NOT have been called
            mock_click.assert_not_called()

    @patch("src.automation.antigravity_automation._ensure_desktop_access")
    @patch("win32gui.GetWindowRect")
    @patch("win32gui.GetForegroundWindow")
    def test_fallback_when_uia_fails(self, mock_fg, mock_rect, mock_access):
        """5. Fallback occurs when UI Automation returns no candidate."""
        hwnd = 12345
        mock_fg.return_value = hwnd
        mock_rect.return_value = (100, 100, 900, 700)  # width 800, height 600

        win_mock = MagicMock()
        win_mock.rectangle.return_value = MockRect(100, 100, 900, 700)
        win_mock.descendants.return_value = []  # No UIA elements

        with patch("pyautogui.click") as mock_click:
            result = self.automation._focus_chat_input(hwnd, uia_window=win_mock)
            self.assertTrue(result)
            self.assertTrue(mock_click.called)

    @patch("src.automation.antigravity_automation._ensure_desktop_access")
    @patch("win32gui.GetWindowRect")
    @patch("win32gui.GetForegroundWindow")
    def test_middle_region_fallback_for_new_chat(self, mock_fg, mock_rect, mock_access):
        """6. NEW_CHAT layout attempts middle coordinate first in fallback."""
        hwnd = 12345
        mock_fg.return_value = hwnd
        mock_rect.return_value = (0, 0, 1000, 1000)

        # Mock detect_chat_layout returning NEW_CHAT
        with patch.object(self.automation, "_detect_chat_layout", return_value="NEW_CHAT"):
            with patch.object(self.automation, "_find_chat_input_candidate", return_value=None):
                with patch("pyautogui.click") as mock_click:
                    result = self.automation._focus_chat_input(hwnd, uia_window=MagicMock())
                    self.assertTrue(result)
                    # First click should be middle: x = 500, y = 500
                    first_call = mock_click.call_args_list[0]
                    self.assertEqual(first_call, call(500, 500))

    @patch("src.automation.antigravity_automation._ensure_desktop_access")
    @patch("win32gui.GetWindowRect")
    @patch("win32gui.GetForegroundWindow")
    def test_bottom_region_fallback_for_existing_chat(self, mock_fg, mock_rect, mock_access):
        """7. EXISTING_CHAT layout attempts bottom coordinate first in fallback."""
        hwnd = 12345
        mock_fg.return_value = hwnd
        mock_rect.return_value = (0, 0, 1000, 1000)

        with patch.object(self.automation, "_detect_chat_layout", return_value="EXISTING_CHAT"):
            with patch.object(self.automation, "_find_chat_input_candidate", return_value=None):
                with patch("pyautogui.click") as mock_click:
                    result = self.automation._focus_chat_input(hwnd, uia_window=MagicMock())
                    self.assertTrue(result)
                    # First click should be bottom: x = 500, y = 1000 - 80 = 920
                    first_call = mock_click.call_args_list[0]
                    self.assertEqual(first_call, call(500, 920))

    @patch("src.automation.antigravity_automation._ensure_desktop_access")
    @patch("win32gui.GetWindowRect")
    @patch("win32gui.GetForegroundWindow")
    def test_bounded_failure_when_no_input_exists(self, mock_fg, mock_rect, mock_access):
        """8. Bounded failure when focus verification fails on all attempts."""
        hwnd = 12345
        mock_rect.return_value = (0, 0, 1000, 1000)
        # Window never gains foreground focus
        mock_fg.return_value = 99999

        with patch.object(self.automation, "_find_chat_input_candidate", return_value=None):
            with patch("pyautogui.click") as mock_click:
                result = self.automation._focus_chat_input(hwnd, uia_window=MagicMock())
                self.assertFalse(result)
                # Bounded attempts: exactly 2 attempts (primary + secondary)
                self.assertEqual(mock_click.call_count, 2)

    @patch.object(AntigravityAutomation, "_find_antigravity_window")
    @patch.object(AntigravityAutomation, "_activate_window", return_value=True)
    @patch.object(AntigravityAutomation, "_focus_chat_input", return_value=False)
    @patch.object(AntigravityAutomation, "_is_window_foreground", return_value=True)
    def test_focus_verification_prevents_typing_into_wrong_target(
        self, mock_fg, mock_focus, mock_activate, mock_find
    ):
        """9. Focus verification prevents prompt typing when input cannot be focused."""
        mock_find.return_value = (12345, "Antigravity", "Antigravity.exe")

        with patch("pyautogui.hotkey") as mock_hotkey:
            with patch("pyautogui.write") as mock_write:
                res = self.automation.execute("Hello prompt")
                self.assertFalse(res.success)
                self.assertIn("Could not focus", res.error)
                mock_hotkey.assert_not_called()
                mock_write.assert_not_called()

    @patch.object(AntigravityAutomation, "_find_antigravity_window")
    @patch.object(AntigravityAutomation, "_activate_window", return_value=True)
    @patch.object(AntigravityAutomation, "_focus_chat_input", return_value=True)
    @patch.object(AntigravityAutomation, "_is_window_foreground", return_value=True)
    @patch("pyperclip.copy")
    @patch("pyautogui.press")
    @patch("pyautogui.hotkey")
    def test_existing_prompt_content_is_safely_cleared(
        self, mock_hotkey, mock_press, mock_copy, mock_fg, mock_focus, mock_activate, mock_find
    ):
        """10. Existing prompt content is safely cleared with Ctrl+A, Backspace before typing."""
        mock_find.return_value = (12345, "Antigravity", "Antigravity.exe")

        res = self.automation.execute("TEST PROMPT")
        self.assertTrue(res.success)

        # Check sequence:
        # 1. hotkey("ctrl", "a")
        # 2. press("backspace")
        # 3. copy("TEST PROMPT")
        # 4. hotkey("ctrl", "v")
        # 5. press("enter")
        mock_hotkey.assert_any_call("ctrl", "a")
        mock_press.assert_any_call("backspace")
        mock_copy.assert_called_once_with("TEST PROMPT")
        mock_hotkey.assert_any_call("ctrl", "v")
        mock_press.assert_any_call("enter")


if __name__ == "__main__":
    unittest.main()
