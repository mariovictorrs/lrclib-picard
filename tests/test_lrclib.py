import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lrclib import build_query, build_search_query, has_synced_lyrics, lyrics_for_mode, select_lyrics


class BuildQueryTest(unittest.TestCase):
    def test_requires_title_and_artist(self):
        self.assertIsNone(build_query("", "Artist", "Album", 180000))
        self.assertIsNone(build_query("Title", "   ", "Album", 180000))

    def test_includes_available_match_fields(self):
        self.assertEqual(
            build_query(" Title ", " Artist ", " Album ", 180500),
            {
                "track_name": "Title",
                "artist_name": "Artist",
                "album_name": "Album",
                "duration": "180",
            },
        )

    def test_omits_unknown_optional_fields(self):
        self.assertEqual(
            build_query("Title", "Artist", "", 0),
            {"track_name": "Title", "artist_name": "Artist"},
        )

    def test_builds_search_query(self):
        self.assertEqual(
            build_search_query(" Title ", " Artist ", " Album "),
            "Artist Title Album",
        )
        self.assertIsNone(build_search_query("Title", "", "Album"))


class SelectLyricsTest(unittest.TestCase):
    def test_prefers_synchronized_lyrics(self):
        self.assertEqual(
            select_lyrics({"syncedLyrics": "[00:01.00]Synced", "plainLyrics": "Plain"}),
            "[00:01.00]Synced",
        )

    def test_falls_back_to_plain_lyrics(self):
        self.assertEqual(select_lyrics({"syncedLyrics": " ", "plainLyrics": " Plain "}), "Plain")

    def test_identifies_results_with_synchronized_lyrics(self):
        self.assertTrue(has_synced_lyrics({"syncedLyrics": "[00:01.00]Synced"}))
        self.assertFalse(has_synced_lyrics({"syncedLyrics": " ", "plainLyrics": "Plain"}))

    def test_selects_only_the_configured_lyric_version(self):
        response = {"syncedLyrics": "[00:01.00]Synced", "plainLyrics": "Plain"}
        self.assertEqual(lyrics_for_mode(response, "synced"), "[00:01.00]Synced")
        self.assertEqual(lyrics_for_mode(response, "unsynced"), "Plain")
        self.assertIsNone(lyrics_for_mode(response, "none"))
        self.assertEqual(lyrics_for_mode({"plainLyrics": "Plain"}, "synced"), "Plain")
        self.assertIsNone(lyrics_for_mode({"syncedLyrics": "[00:01.00]Synced"}, "unsynced"))

    def test_rejects_instrumentals_and_invalid_responses(self):
        self.assertIsNone(select_lyrics({"instrumental": True, "plainLyrics": "No lyrics"}))
        self.assertFalse(has_synced_lyrics({"instrumental": True, "syncedLyrics": "[00:01.00]No lyrics"}))
        self.assertIsNone(select_lyrics(None))


if __name__ == "__main__":
    unittest.main()
