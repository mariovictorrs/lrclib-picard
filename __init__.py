"""Download missing lyrics from LRCLIB as tracks are loaded by Picard."""

from picard.plugin3.api import BaseAction, PluginApi

from .lrc_file import lrc_path_for, move_lrc_file, write_lrc_file
from .lrclib import SIDECAR_LYRICS_TAG, build_query, lyrics_for_mode


LRCLIB_GET_URL = "https://lrclib.net/api/get"
PENDING_LRC_PATHS = {}


def request_lyrics(api, metadata):
    """Request the configured lyrics versions for metadata."""
    tag_mode = api.plugin_config["audio_tag_lyrics_mode"]
    needs_tag_lyrics = tag_mode != "none" and not metadata.get("lyrics")
    needs_sidecar_lyrics = api.plugin_config["save_lrc_file"] and not metadata.get(SIDECAR_LYRICS_TAG)
    if not needs_tag_lyrics and not needs_sidecar_lyrics:
        return

    query = build_query(
        metadata.get("title", ""),
        metadata.get("artist", ""),
        metadata.get("album", ""),
        metadata.length,
    )
    if query is None:
        api.logger.debug("Skipping LRCLIB lookup: title or artist is missing")
        return

    def handle_response(response, reply, error):
        if error:
            api.logger.debug("LRCLIB request failed for %r: %s", query, error)
            return

        synced_lyrics = lyrics_for_mode(response, "synced")
        if synced_lyrics:
            metadata[SIDECAR_LYRICS_TAG] = synced_lyrics

        tag_lyrics = lyrics_for_mode(response, tag_mode)
        if tag_lyrics and not metadata.get("lyrics"):
            metadata["lyrics"] = tag_lyrics
            api.logger.debug("Added LRCLIB %s lyrics for %s - %s", tag_mode, query["artist_name"], query["track_name"])

    api.web_service.get_url(
        url=LRCLIB_GET_URL,
        handler=handle_response,
        unencoded_queryargs=query,
        priority=True,
    )


def download_lyrics(api, track, metadata, track_node, release_node=None):
    """Request lyrics while Picard loads a track."""
    request_lyrics(api, metadata)


def capture_lrc_before_file_save(api, file):
    """Remember the current sidecar path before Picard renames or moves audio."""
    if not api.plugin_config["save_lrc_file"]:
        return
    PENDING_LRC_PATHS[id(file)] = lrc_path_for(file.filename)


def save_lrc_after_file_save(api, file):
    """Move and optionally save the lyrics tag as a sidecar LRC file."""
    old_lrc_path = PENDING_LRC_PATHS.pop(id(file), None)
    if not api.plugin_config["save_lrc_file"]:
        return

    lrc_path = lrc_path_for(file.filename)
    overwrite = api.plugin_config["existing_lrc_policy"] == "overwrite"
    lyrics = file.metadata.get(SIDECAR_LYRICS_TAG)
    try:
        moved = move_lrc_file(old_lrc_path, lrc_path, overwrite) if old_lrc_path else False
        written = write_lrc_file(file.filename, lyrics, overwrite) if lyrics else False
    except OSError as error:
        api.logger.error("Could not write LRCLIB sidecar file %s: %s", lrc_path, error)
        return

    if moved:
        api.logger.debug("Moved LRCLIB sidecar file to %s", lrc_path)
    elif old_lrc_path and old_lrc_path.exists() and old_lrc_path != lrc_path and lrc_path.exists():
        api.logger.warning("Preserved existing sidecar file %s instead of moving %s", lrc_path, old_lrc_path)
    if written:
        api.logger.debug("Wrote LRCLIB sidecar file %s", lrc_path)


class RetryLyricsAction(BaseAction):
    """Retry the automatic lookup for selected tracks."""

    TITLE = "Download missing lyrics"
    MENU = ("LRCLIB Lyrics",)

    def callback(self, tracks):
        for track in tracks:
            request_lyrics(self.api, track.metadata)


class SearchLyricsAction(BaseAction):
    """Open LRCLIB search for one selected track."""

    TITLE = "Search and select lyrics..."
    MENU = ("LRCLIB Lyrics",)

    def callback(self, tracks):
        if len(tracks) != 1:
            self.api.logger.warning("Select exactly one track to search LRCLIB manually.")
            return

        from .search_dialog import LyricsSearchDialog

        track = next(iter(tracks))
        LyricsSearchDialog(self.api, track.metadata, self.api.tagger.window).exec()


def enable(api: PluginApi) -> None:
    """Register the automatic track metadata processor."""
    from .options import LyricsOptionsPage

    api.plugin_config.register_option("save_lrc_file", False)
    api.plugin_config.register_option("existing_lrc_policy", "preserve")
    api.plugin_config.register_option("audio_tag_lyrics_mode", "synced")
    api.register_track_metadata_processor(download_lyrics)
    api.register_file_pre_save_processor(capture_lrc_before_file_save)
    api.register_file_post_save_processor(save_lrc_after_file_save)
    api.register_track_action(RetryLyricsAction)
    api.register_track_action(SearchLyricsAction)
    api.register_options_page(LyricsOptionsPage)
