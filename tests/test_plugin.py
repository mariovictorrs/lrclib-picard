import importlib.util
import os
import sys
import types
import unittest


ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_NAME = "lrclib_picard"


def load_plugin_module():
    picard = types.ModuleType("picard")
    plugin3 = types.ModuleType("picard.plugin3")
    api = types.ModuleType("picard.plugin3.api")
    api.PluginApi = object
    api.BaseAction = object
    sys.modules["picard"] = picard
    sys.modules["picard.plugin3"] = plugin3
    sys.modules["picard.plugin3.api"] = api

    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        os.path.join(ROOT, "__init__.py"),
        submodule_search_locations=[ROOT],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = module
    spec.loader.exec_module(module)
    options = types.ModuleType(f"{PACKAGE_NAME}.options")
    options.LyricsOptionsPage = type("LyricsOptionsPage", (), {})
    sys.modules[f"{PACKAGE_NAME}.options"] = options
    return module


PLUGIN = load_plugin_module()


class Metadata(dict):
    def __init__(self, length, **tags):
        super().__init__(tags)
        self.length = length


class Logger:
    def debug(self, *args):
        pass


class WebService:
    def __init__(self):
        self.requests = []

    def get_url(self, **kwargs):
        self.requests.append(kwargs)


class Api:
    def __init__(self):
        self.logger = Logger()
        self.web_service = WebService()
        self.processor = None
        self.actions = []
        self.file_processors = []
        self.pre_save_processors = []
        self.options_pages = []
        self.plugin_config = PluginConfig()

    def register_track_metadata_processor(self, processor):
        self.processor = processor

    def register_track_action(self, action):
        self.actions.append(action)

    def register_file_post_save_processor(self, processor):
        self.file_processors.append(processor)

    def register_file_pre_save_processor(self, processor):
        self.pre_save_processors.append(processor)

    def register_options_page(self, page):
        self.options_pages.append(page)


class PluginConfig(dict):
    def register_option(self, name, default):
        self.setdefault(name, default)


class PluginTest(unittest.TestCase):
    def test_enable_registers_track_processor(self):
        api = Api()

        PLUGIN.enable(api)

        self.assertIs(api.processor, PLUGIN.download_lyrics)
        self.assertEqual(api.actions, [PLUGIN.RetryLyricsAction, PLUGIN.SearchLyricsAction])
        self.assertEqual(api.file_processors, [PLUGIN.save_lrc_after_file_save])
        self.assertEqual(api.pre_save_processors, [PLUGIN.capture_lrc_before_file_save])
        self.assertEqual(api.plugin_config["save_lrc_file"], False)
        self.assertEqual(api.plugin_config["existing_lrc_policy"], "preserve")
        self.assertEqual(api.plugin_config["audio_tag_lyrics_mode"], "synced")

    def test_downloads_and_stores_synchronized_lyrics(self):
        api = Api()
        PLUGIN.enable(api)
        metadata = Metadata(213000, title="Never Gonna Give You Up", artist="Rick Astley", album="Album")

        PLUGIN.download_lyrics(api, None, metadata, {})

        self.assertEqual(len(api.web_service.requests), 1)
        request = api.web_service.requests[0]
        self.assertEqual(request["url"], PLUGIN.LRCLIB_GET_URL)
        self.assertEqual(
            request["unencoded_queryargs"],
            {
                "track_name": "Never Gonna Give You Up",
                "artist_name": "Rick Astley",
                "album_name": "Album",
                "duration": "213",
            },
        )
        request["handler"]({"syncedLyrics": "[00:00.00]Lyrics", "plainLyrics": "Lyrics"}, None, None)
        self.assertEqual(metadata["lyrics"], "[00:00.00]Lyrics")

    def test_preserves_existing_lyrics(self):
        api = Api()
        PLUGIN.enable(api)
        metadata = Metadata(213000, title="Title", artist="Artist", lyrics="Keep this")

        PLUGIN.download_lyrics(api, None, metadata, {})

        self.assertEqual(api.web_service.requests, [])
        self.assertEqual(metadata["lyrics"], "Keep this")

    def test_stores_only_the_configured_unsynchronized_lyrics(self):
        api = Api()
        PLUGIN.enable(api)
        api.plugin_config["audio_tag_lyrics_mode"] = "unsynced"
        metadata = Metadata(213000, title="Title", artist="Artist")

        PLUGIN.download_lyrics(api, None, metadata, {})
        api.web_service.requests[0]["handler"](
            {"syncedLyrics": "[00:00.00]Synced", "plainLyrics": "Plain"},
            None,
            None,
        )

        self.assertEqual(metadata["lyrics"], "Plain")
        self.assertEqual(metadata[PLUGIN.SIDECAR_LYRICS_TAG], "[00:00.00]Synced")

    def test_does_not_store_audio_tag_when_configured_not_to(self):
        api = Api()
        PLUGIN.enable(api)
        api.plugin_config["audio_tag_lyrics_mode"] = "none"
        api.plugin_config["save_lrc_file"] = True
        metadata = Metadata(213000, title="Title", artist="Artist")

        PLUGIN.download_lyrics(api, None, metadata, {})
        api.web_service.requests[0]["handler"](
            {"syncedLyrics": "[00:00.00]Synced", "plainLyrics": "Plain"},
            None,
            None,
        )

        self.assertNotIn("lyrics", metadata)
        self.assertEqual(metadata[PLUGIN.SIDECAR_LYRICS_TAG], "[00:00.00]Synced")


if __name__ == "__main__":
    unittest.main()
