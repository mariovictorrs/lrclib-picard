"""Manual LRCLIB search dialog."""

from PyQt6 import QtCore, QtWidgets

from .lrclib import SIDECAR_LYRICS_TAG, build_search_query, has_synced_lyrics, lyrics_for_mode, select_lyrics


LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"


class LyricsSearchDialog(QtWidgets.QDialog):
    """Search LRCLIB and apply a user-selected result to one track."""

    def __init__(self, api, metadata, parent):
        super().__init__(parent)
        self.api = api
        self.metadata = metadata
        self.setWindowTitle("Search LRCLIB Lyrics")
        self.resize(680, 420)

        form = QtWidgets.QFormLayout()
        self.title_input = QtWidgets.QLineEdit(metadata.get("title", ""))
        self.artist_input = QtWidgets.QLineEdit(metadata.get("artist", ""))
        self.album_input = QtWidgets.QLineEdit(metadata.get("album", ""))
        form.addRow("Title:", self.title_input)
        form.addRow("Artist:", self.artist_input)
        form.addRow("Album:", self.album_input)

        self.results = QtWidgets.QListWidget()
        self.results.itemSelectionChanged.connect(self._update_apply_button)
        self.status = QtWidgets.QLabel()

        self.search_button = QtWidgets.QPushButton("Search")
        self.search_button.clicked.connect(self.search)
        self.apply_button = QtWidgets.QPushButton("Apply selected lyrics")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.apply_selected)
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self.search_button)
        buttons.addStretch()
        buttons.addWidget(self.apply_button)
        buttons.addWidget(self.cancel_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.status)
        layout.addWidget(self.results)
        layout.addLayout(buttons)

    def search(self):
        """Search LRCLIB with the values currently entered by the user."""
        query = build_search_query(
            self.title_input.text(),
            self.artist_input.text(),
            self.album_input.text(),
        )
        if query is None:
            self.status.setText("Title and artist are required.")
            return

        self.results.clear()
        self.apply_button.setEnabled(False)
        self.search_button.setEnabled(False)
        self.status.setText("Searching LRCLIB...")

        self.api.web_service.get_url(
            url=LRCLIB_SEARCH_URL,
            handler=self._handle_search_response,
            unencoded_queryargs={"q": query},
            priority=True,
        )

    def _handle_search_response(self, response, reply, error):
        self.search_button.setEnabled(True)
        if error:
            self.status.setText("LRCLIB search failed. Check the Picard log for details.")
            self.api.logger.warning("LRCLIB manual search failed: %s", error)
            return
        if not isinstance(response, list):
            self.status.setText("LRCLIB returned an unexpected response.")
            return

        matches = [match for match in response if select_lyrics(match)]
        for match in matches:
            item = QtWidgets.QListWidgetItem(self._format_match(match))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, match)
            self.results.addItem(item)

        self.status.setText(f"{len(matches)} matching lyric result(s).")

    @staticmethod
    def _format_match(match):
        artist = match.get("artistName", "Unknown artist")
        title = match.get("trackName", "Unknown title")
        album = match.get("albumName", "Unknown album")
        duration = match.get("duration")
        suffix = f" ({duration:.0f}s)" if isinstance(duration, (int, float)) else ""
        lyrics_type = "Synced" if has_synced_lyrics(match) else "Plain"
        return f"[{lyrics_type}] {artist} - {title} — {album}{suffix}"

    def _update_apply_button(self):
        self.apply_button.setEnabled(self.results.currentItem() is not None)

    def apply_selected(self):
        """Write the selected result, deliberately replacing any existing lyrics."""
        item = self.results.currentItem()
        if item is None:
            return
        lyrics = select_lyrics(item.data(QtCore.Qt.ItemDataRole.UserRole))
        if lyrics is None:
            self.status.setText("The selected result does not contain lyrics.")
            self.apply_button.setEnabled(False)
            return
        match = item.data(QtCore.Qt.ItemDataRole.UserRole)
        synced_lyrics = lyrics_for_mode(match, "synced")
        if synced_lyrics:
            self.metadata[SIDECAR_LYRICS_TAG] = synced_lyrics

        tag_lyrics = lyrics_for_mode(match, self.api.plugin_config["audio_tag_lyrics_mode"])
        if tag_lyrics:
            self.metadata["lyrics"] = tag_lyrics
        self.accept()
