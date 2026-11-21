"""Regression tests for language selection and echo translations (Issue #30)."""

import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import i18n


class LanguagePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "preferences.sqlite3"
        env = patch.dict(os.environ, {"LANGUAGE_DB_PATH": str(self.db_path)})
        env.start()
        self.addCleanup(env.stop)

    def test_echo_uses_selected_russian_language(self):
        i18n.set_user_language(123, "ru")
        self.assertEqual(
            i18n.t(123, "echo_reply", text="привет"),
            "Ты написал(а): привет",
        )

    def test_echo_uses_selected_ukrainian_language(self):
        i18n.set_user_language(123, "uk")
        self.assertEqual(
            i18n.t(123, "echo_reply", text="привіт"),
            "Ти написав(ла): привіт",
        )

    def test_english_is_default_for_new_users(self):
        self.assertEqual(i18n.get_user_language(123), "en")
        self.assertEqual(
            i18n.t(123, "echo_reply", text="hello"),
            "You wrote: hello",
        )

    def test_switching_languages_updates_echo(self):
        i18n.set_user_language(123, "ru")
        i18n.set_user_language(123, "uk")
        self.assertEqual(i18n.t(123, "echo_reply", text="тест"), "Ти написав(ла): тест")

    def test_language_survives_module_reload(self):
        i18n.set_user_language(123, "ru")
        importlib.reload(i18n)  # Simulates a fresh application process.
        self.assertEqual(i18n.get_user_language(123), "ru")
        self.assertEqual(i18n.t(123, "echo_reply", text="привет"), "Ты написал(а): привет")

    def test_user_preferences_are_isolated(self):
        i18n.set_user_language(123, "ru")
        i18n.set_user_language(456, "uk")
        self.assertEqual(i18n.get_user_language(123), "ru")
        self.assertEqual(i18n.get_user_language(456), "uk")

    def test_missing_user_defaults_to_english(self):
        self.assertEqual(i18n.get_user_language(None), "en")


if __name__ == "__main__":
    unittest.main()
