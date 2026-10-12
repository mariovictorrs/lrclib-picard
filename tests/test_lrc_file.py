import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lrc_file import lrc_path_for, move_lrc_file, write_lrc_file


class LrcFileTest(unittest.TestCase):
    def test_uses_audio_filename_with_lrc_extension(self):
        self.assertEqual(str(lrc_path_for("/music/track.flac")), "/music/track.lrc")

    def test_writes_utf8_lyrics(self):
        with tempfile.TemporaryDirectory() as directory:
            audio_path = os.path.join(directory, "track.flac")

            self.assertTrue(write_lrc_file(audio_path, "[00:01.00]Canção", overwrite=False))

            with open(os.path.join(directory, "track.lrc"), encoding="utf-8") as lrc_file:
                self.assertEqual(lrc_file.read(), "[00:01.00]Canção\n")

    def test_preserves_or_overwrites_existing_file_as_requested(self):
        with tempfile.TemporaryDirectory() as directory:
            audio_path = os.path.join(directory, "track.flac")
            lrc_path = os.path.join(directory, "track.lrc")
            with open(lrc_path, "w", encoding="utf-8") as lrc_file:
                lrc_file.write("Original\n")

            self.assertFalse(write_lrc_file(audio_path, "Replacement", overwrite=False))
            with open(lrc_path, encoding="utf-8") as lrc_file:
                self.assertEqual(lrc_file.read(), "Original\n")

            self.assertTrue(write_lrc_file(audio_path, "Replacement", overwrite=True))
            with open(lrc_path, encoding="utf-8") as lrc_file:
                self.assertEqual(lrc_file.read(), "Replacement\n")

    def test_moves_lrc_file_with_audio_rename(self):
        with tempfile.TemporaryDirectory() as directory:
            source_path = os.path.join(directory, "old-name.lrc")
            destination_path = os.path.join(directory, "new-name.lrc")
            with open(source_path, "w", encoding="utf-8") as lrc_file:
                lrc_file.write("Lyrics\n")

            self.assertTrue(move_lrc_file(source_path, destination_path, overwrite=False))
            self.assertFalse(os.path.exists(source_path))
            with open(destination_path, encoding="utf-8") as lrc_file:
                self.assertEqual(lrc_file.read(), "Lyrics\n")

    def test_preserves_conflicting_lrc_when_moving(self):
        with tempfile.TemporaryDirectory() as directory:
            source_path = os.path.join(directory, "old-name.lrc")
            destination_path = os.path.join(directory, "new-name.lrc")
            with open(source_path, "w", encoding="utf-8") as lrc_file:
                lrc_file.write("Source\n")
            with open(destination_path, "w", encoding="utf-8") as lrc_file:
                lrc_file.write("Destination\n")

            self.assertFalse(move_lrc_file(source_path, destination_path, overwrite=False))
            with open(source_path, encoding="utf-8") as lrc_file:
                self.assertEqual(lrc_file.read(), "Source\n")
            with open(destination_path, encoding="utf-8") as lrc_file:
                self.assertEqual(lrc_file.read(), "Destination\n")
