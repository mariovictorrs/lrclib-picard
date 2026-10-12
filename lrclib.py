"""Helpers for querying and interpreting LRCLIB responses."""

from typing import Any, Mapping, Optional


SIDECAR_LYRICS_TAG = "~lrclib_synced_lyrics"


def build_query(
    title: str,
    artist: str,
    album: str,
    duration_ms: int,
) -> Optional[dict]:
    """Build an LRCLIB exact-match query, or return None without core tags."""
    title = title.strip()
    artist = artist.strip()
    if not title or not artist:
        return None

    query = {
        "track_name": title,
        "artist_name": artist,
    }
    if album.strip():
        query["album_name"] = album.strip()
    if duration_ms > 0:
        query["duration"] = str(max(1, round(duration_ms / 1000)))
    return query


def build_search_query(title: str, artist: str, album: str) -> Optional[str]:
    """Build a text query for the LRCLIB search endpoint."""
    title = title.strip()
    artist = artist.strip()
    if not title or not artist:
        return None

    terms = [artist, title]
    if album.strip():
        terms.append(album.strip())
    return " ".join(terms)


def lyrics_for_mode(response: Any, mode: str) -> Optional[str]:
    """Return the configured LRCLIB lyric version from a response."""
    if not isinstance(response, Mapping) or response.get("instrumental"):
        return None

    if mode == "synced":
        return select_lyrics(response)
    if mode != "unsynced":
        return None

    lyrics = response.get("plainLyrics")
    return lyrics.strip() if isinstance(lyrics, str) and lyrics.strip() else None


def select_lyrics(response: Any) -> Optional[str]:
    """Choose synchronized lyrics first, then plain lyrics, from a response."""
    if not isinstance(response, Mapping) or response.get("instrumental"):
        return None

    for key in ("syncedLyrics", "plainLyrics"):
        lyrics = response.get(key)
        if isinstance(lyrics, str) and lyrics.strip():
            return lyrics.strip()
    return None


def has_synced_lyrics(response: Any) -> bool:
    """Return whether an LRCLIB result includes usable timestamped lyrics."""
    if not isinstance(response, Mapping) or response.get("instrumental"):
        return False
    lyrics = response.get("syncedLyrics")
    return isinstance(lyrics, str) and bool(lyrics.strip())
