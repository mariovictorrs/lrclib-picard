# LRCLIB Lyrics for MusicBrainz Picard

An **MusicBrainz Picard v3** plugin that automatically downloads lyrics from
[LRCLIB](https://lrclib.net/) while tracks are loaded.

The plugin queries LRCLIB with the track title, artist, album, and duration.
Synchronized lyrics are preferred when available; otherwise, plain lyrics are
used. The result is saved in the `lyrics` tag.

## Behavior

- Does not block Picard's UI: requests use Picard's asynchronous HTTP service.
- Does not replace an existing non-empty `lyrics` tag.
- Does not write a tag when LRCLIB finds no lyrics or the track is
  instrumental.
- Requires no account, API key, or additional Python dependencies.

## `.lrc` files

By default, the plugin writes only the `lyrics` tag when Picard saves audio.
Under **Options > Plugins > LRCLIB Lyrics**, enable **Save an .lrc file next to
the audio file** to also create a UTF-8 file with the same name as the audio
file and the `.lrc` extension. For example, `01 - Song.flac` creates
`01 - Song.lrc`.

On the same page, choose whether an existing `.lrc` should be preserved
(default) or overwritten. The sidecar file is created or updated only after
Picard saves the audio. When Picard renames or moves audio during saving, the
plugin also moves the `.lrc` to the new location.

To apply synchronized lyrics to an existing plain `.lrc`, select
**Overwrite existing .lrc files** or remove the existing file before saving.

## Lyrics in audio tags

Under **Options > Plugins > LRCLIB Lyrics**, choose which version the plugin
saves to the audio file's `lyrics` tag:

- **Prefer synchronized lyrics**: saves timestamped lyrics when available;
  otherwise, saves the plain version.
- **Unsynchronized lyrics only**: saves only plain lyrics.
- **Do not save lyrics in audio tags**: does not change the `lyrics` tag.

When sidecar `.lrc` files are enabled, they still use only synchronized
lyrics, even if writing audio tags is disabled.

## Manual search

Right-click a single track and choose **Plugins > LRCLIB Lyrics**:

- **Download missing lyrics** repeats the automatic lookup without replacing
  existing lyrics.
- **Search and select lyrics...** lets you adjust the title, artist, and album,
  select the correct match, and apply its lyrics. Results are identified as
  **[Synced]** or **[Plain]**. This action replaces the `lyrics` tag because
  the selection is explicit.

## Installation

In Picard v3, install the repository with the plugin manager or run:

```sh
picard-cli plugins install https://github.com/mariovictorrs/lrclib-picard
```

Then enable **LRCLIB Lyrics** under **Options > Plugins**. Reload albums to
have Picard fetch and fill in their lyrics.

## Development

The plugin follows the v3 plugin format:

```text
.
├── MANIFEST.toml
├── __init__.py
├── lrclib.py
└── tests/
```

Run the tests with:

```sh
python -m unittest discover -s tests -v
```

To publish to the official registry, create a SemVer tag (for example,
`v1.0.0`) and validate the manifest according to the
[submission guide](https://github.com/metabrainz/picard-plugins-registry/blob/main/PLUGIN_SUBMISSION.md).
