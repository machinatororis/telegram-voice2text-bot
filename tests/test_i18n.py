"""Regression tests for language selection and echo translations (Issue #30)."""

import subprocess
import sys
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

    def test_language_survives_fresh_python_process(self):
        """The same durable SQLite path is readable by a newly started process."""
        i18n.set_user_language(123, "ru")
        process = subprocess.run(
            [
                sys.executable,
                "-c",
                "from app.i18n import t; print(t(123, 'echo_reply', text='привет'))",
            ],
            cwd=Path(__file__).resolve().parent.parent,
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(process.stdout.strip(), "Ты написал(а): привет")

    def test_new_container_without_shared_storage_loses_language(self):
        """Document the known limitation of ephemeral container filesystems."""
        i18n.set_user_language(123, "ru")

        new_container_path = Path(self.temp_dir.name) / "new-container" / "preferences.sqlite3"
        new_env = os.environ.copy()
        new_env["LANGUAGE_DB_PATH"] = str(new_container_path)

        process = subprocess.run(
            [
                sys.executable,
                "-c",
                "from app.i18n import t; print(t(123, 'echo_reply', text='привет'))",
            ],
            cwd=Path(__file__).resolve().parent.parent,
            env=new_env,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(process.stdout.strip(), "You wrote: привет")

    def test_user_preferences_are_isolated(self):
        i18n.set_user_language(123, "ru")
        i18n.set_user_language(456, "uk")
        self.assertEqual(i18n.get_user_language(123), "ru")
        self.assertEqual(i18n.get_user_language(456), "uk")

    def test_missing_user_defaults_to_english(self):
        self.assertEqual(i18n.get_user_language(None), "en")


if __name__ == "__main__":
    unittest.main()
