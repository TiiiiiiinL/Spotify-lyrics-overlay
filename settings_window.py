"""Inställningsfönstret — justera overlayn live med reglage och färgval."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class SettingsWindow(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("Inställningar – Spotify Lyrics Overlay")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        # Textstorlek
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(14, 96)
        self.size_slider.setValue(settings.font_size)
        self.size_label = QLabel(str(settings.font_size))
        size_row = QHBoxLayout()
        size_row.addWidget(self.size_slider)
        size_row.addWidget(self.size_label)
        self.size_slider.valueChanged.connect(self._on_size)
        form.addRow("Textstorlek", size_row)

        # Textfärg / konturfärg
        self.text_color_btn = QPushButton()
        self.text_color_btn.clicked.connect(self._pick_text_color)
        form.addRow("Textfärg", self.text_color_btn)

        self.outline_color_btn = QPushButton()
        self.outline_color_btn.clicked.connect(self._pick_outline_color)
        form.addRow("Konturfärg", self.outline_color_btn)

        # Bakgrund + genomskinlighet
        self.bg_check = QCheckBox("Visa mörk platta bakom texten")
        self.bg_check.setChecked(settings.show_bg)
        self.bg_check.toggled.connect(self._on_bg_toggle)
        form.addRow("Bakgrund", self.bg_check)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(settings.bg_opacity)
        self.opacity_slider.setEnabled(settings.show_bg)
        self.opacity_slider.valueChanged.connect(
            lambda v: self.settings.update(bg_opacity=v)
        )
        form.addRow("Genomskinlighet", self.opacity_slider)

        self.fit_check = QCheckBox("Anpassa bredden efter texten")
        self.fit_check.setToolTip(
            "Av: plattan är lika bred som fönstret.\n"
            "På: plattan krymper till den rad som visas just nu."
        )
        self.fit_check.setChecked(settings.bg_fit_text)
        self.fit_check.setEnabled(settings.show_bg)
        self.fit_check.toggled.connect(lambda v: self.settings.update(bg_fit_text=v))
        form.addRow("Bredd", self.fit_check)

        # Nästa rad + radavstånd
        self.next_check = QCheckBox("Visa kommande rad")
        self.next_check.setChecked(settings.show_next)
        self.next_check.toggled.connect(lambda v: self.settings.update(show_next=v))
        form.addRow("Nästa rad", self.next_check)

        self.gap_slider = QSlider(Qt.Horizontal)
        self.gap_slider.setRange(0, 60)
        self.gap_slider.setValue(settings.line_gap)
        self.gap_slider.valueChanged.connect(lambda v: self.settings.update(line_gap=v))
        form.addRow("Radavstånd", self.gap_slider)

        # Synk-justering
        self.sync_spin = QDoubleSpinBox()
        self.sync_spin.setRange(-3.0, 3.0)
        self.sync_spin.setSingleStep(0.1)
        self.sync_spin.setSuffix(" s")
        self.sync_spin.setValue(settings.sync_offset)
        self.sync_spin.valueChanged.connect(
            lambda v: self.settings.update(sync_offset=round(v, 1))
        )
        form.addRow("Synk-justering", self.sync_spin)

        hint = QLabel("+ = texten byts tidigare, − = senare")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint)

        # Återställ
        reset_btn = QPushButton("Återställ till standard")
        reset_btn.clicked.connect(self.settings.reset)
        layout.addWidget(reset_btn)

        self._refresh_color_buttons()
        settings.changed.connect(self._sync_from_settings)

    # ---- Händelser ------------------------------------------------------

    def _on_size(self, value):
        self.size_label.setText(str(value))
        self.settings.update(font_size=value)

    def _on_bg_toggle(self, value):
        self.opacity_slider.setEnabled(value)
        self.fit_check.setEnabled(value)
        self.settings.update(show_bg=value)

    def _pick_text_color(self):
        color = QColorDialog.getColor(
            QColor(self.settings.text_color), self, "Välj textfärg"
        )
        if color.isValid():
            self.settings.update(text_color=color.name())
            self._refresh_color_buttons()

    def _pick_outline_color(self):
        color = QColorDialog.getColor(
            QColor(self.settings.outline_color), self, "Välj konturfärg"
        )
        if color.isValid():
            self.settings.update(outline_color=color.name())
            self._refresh_color_buttons()

    def _refresh_color_buttons(self):
        text_c = self.settings.text_color
        outline_c = self.settings.outline_color
        self.text_color_btn.setText(text_c)
        self.text_color_btn.setStyleSheet(f"background:{text_c}; color:black;")
        self.outline_color_btn.setText(outline_c)
        self.outline_color_btn.setStyleSheet(f"background:{outline_c}; color:white;")

    def _sync_from_settings(self):
        """Håll kontrollerna i synk om värden ändras utanför fönstret (+/- eller Återställ)."""
        s = self.settings
        for widget, value in (
            (self.size_slider, s.font_size),
            (self.opacity_slider, s.bg_opacity),
            (self.gap_slider, s.line_gap),
            (self.sync_spin, s.sync_offset),
        ):
            widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(False)
        self.size_label.setText(str(s.font_size))
        for check, value in (
            (self.bg_check, s.show_bg),
            (self.next_check, s.show_next),
            (self.fit_check, s.bg_fit_text),
        ):
            check.blockSignals(True)
            check.setChecked(value)
            check.blockSignals(False)
        self.opacity_slider.setEnabled(s.show_bg)
        self.fit_check.setEnabled(s.show_bg)
        self._refresh_color_buttons()

    def show_raise(self):
        """Visa fönstret och ta det längst fram."""
        self.show()
        self.raise_()
        self.activateWindow()
