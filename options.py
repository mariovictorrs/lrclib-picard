"""Configuration page for LRCLIB Lyrics."""

from PyQt6 import QtWidgets

from picard.plugin3.api import OptionsPage


class LyricsOptionsPage(OptionsPage):
    """Configure optional sidecar LRC writing."""

    NAME = "lrclib_lyrics"
    TITLE = "LRCLIB Lyrics"
    PARENT = "plugins"

    def __init__(self):
        super().__init__()
        self.save_lrc_file = QtWidgets.QCheckBox("Save an .lrc file next to the audio file")
        self.audio_tag_lyrics_mode = QtWidgets.QComboBox()
        self.audio_tag_lyrics_mode.addItem("Prefer synchronized lyrics", "synced")
        self.audio_tag_lyrics_mode.addItem("Unsynchronized lyrics only", "unsynced")
        self.audio_tag_lyrics_mode.addItem("Do not save lyrics in audio tags", "none")
        self.existing_lrc_policy = QtWidgets.QComboBox()
        self.existing_lrc_policy.addItem("Preserve existing .lrc files", "preserve")
        self.existing_lrc_policy.addItem("Overwrite existing .lrc files", "overwrite")

        form = QtWidgets.QFormLayout(self)
        form.addRow("Lyrics saved in audio tags:", self.audio_tag_lyrics_mode)
        form.addRow(self.save_lrc_file)
        form.addRow("When an .lrc file already exists:", self.existing_lrc_policy)

    def load(self):
        self.save_lrc_file.setChecked(self.api.plugin_config["save_lrc_file"])
        index = self.audio_tag_lyrics_mode.findData(self.api.plugin_config["audio_tag_lyrics_mode"])
        self.audio_tag_lyrics_mode.setCurrentIndex(max(0, index))
        index = self.existing_lrc_policy.findData(self.api.plugin_config["existing_lrc_policy"])
        self.existing_lrc_policy.setCurrentIndex(max(0, index))

    def save(self):
        self.api.plugin_config["save_lrc_file"] = self.save_lrc_file.isChecked()
        self.api.plugin_config["audio_tag_lyrics_mode"] = self.audio_tag_lyrics_mode.currentData()
        self.api.plugin_config["existing_lrc_policy"] = self.existing_lrc_policy.currentData()
