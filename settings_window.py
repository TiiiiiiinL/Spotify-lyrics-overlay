"""The settings window — adjust the overlay live with sliders and color pickers."""

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
        self.setWindowTitle("Settings – Spotify Lyrics Overlay")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        # Text size
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(14, 96)
        self.size_slider.setValue(settings.font_size)
        self.size_label = QLabel(str(settings.font_size))
        size_row = QHBoxLayout()
        size_row.addWidget(self.size_slider)
        size_row.addWidget(self.size_label)
        self.size_slider.valueChanged.connect(self._on_size)
        form.addRow("Text size", size_row)

        # Text color / outline color
        self.text_color_btn = QPushButton()
        self.text_color_btn.clicked.connect(self._pick_text_color)
        form.addRow("Text color", self.text_color_btn)

        self.outline_color_btn = QPushButton()
        self.outline_color_btn.clicked.connect(self._pick_outline_color)
        form.addRow("Outline color", self.outline_color_btn)

        # Background + transparency
        self.bg_check = QCheckBox("Show dark backdrop behind the lyrics")
        self.bg_check.setChecked(settings.show_bg)
        self.bg_check.toggled.connect(self._on_bg_toggle)
        form.addRow("Background", self.bg_check)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(settings.bg_opacity)
        self.opacity_slider.setEnabled(settings.show_bg)
        self.opacity_slider.valueChanged.connect(
            lambda v: self.settings.update(bg_opacity=v)
        )
        form.addRow("Opacity", self.opacity_slider)

        self.fit_check = QCheckBox("Fit width to the text")
        self.fit_check.setToolTip(
            "Off: the backdrop is as wide as the window.\n"
            "On: the backdrop shrinks to the line currently shown."
        )
        self.fit_check.setChecked(settings.bg_fit_text)
        self.fit_check.setEnabled(settings.show_bg)
        self.fit_check.toggled.connect(lambda v: self.settings.update(bg_fit_text=v))
        form.addRow("Width", self.fit_check)

        # Next line + line spacing
        self.next_check = QCheckBox("Show upcoming line")
        self.next_check.setChecked(settings.show_next)
        self.next_check.toggled.connect(lambda v: self.settings.update(show_next=v))
        form.addRow("Next line", self.next_check)

        self.gap_slider = QSlider(Qt.Horizontal)
        self.gap_slider.setRange(0, 60)
        self.gap_slider.setValue(settings.line_gap)
        self.gap_slider.valueChanged.connect(lambda v: self.settings.update(line_gap=v))
        form.addRow("Line spacing", self.gap_slider)

        # Sync offset
        self.sync_spin = QDoubleSpinBox()
        self.sync_spin.setRange(-3.0, 3.0)
        self.sync_spin.setSingleStep(0.1)
        self.sync_spin.setSuffix(" s")
        self.sync_spin.setValue(settings.sync_offset)
        self.sync_spin.valueChanged.connect(
            lambda v: self.settings.update(sync_offset=round(v, 1))
        )
        form.addRow("Sync offset", self.sync_spin)

        hint = QLabel("+ = lines change earlier, − = later")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint)

        # Reset
        reset_btn = QPushButton("Reset to defaults")
        reset_btn.clicked.connect(self.settings.reset)
        layout.addWidget(reset_btn)

        self._refresh_color_buttons()
        settings.changed.connect(self._sync_from_settings)

    # ---- Events ---------------------------------------------------------

    def _on_size(self, value):
        self.size_label.setText(str(value))
        self.settings.update(font_size=value)

    def _on_bg_toggle(self, value):
        self.opacity_slider.setEnabled(value)
        self.fit_check.setEnabled(value)
        self.settings.update(show_bg=value)

    def _pick_text_color(self):
        color = QColorDialog.getColor(
            QColor(self.settings.text_color), self, "Choose text color"
        )
        if color.isValid():
            self.settings.update(text_color=color.name())
            self._refresh_color_buttons()

    def _pick_outline_color(self):
        color = QColorDialog.getColor(
            QColor(self.settings.outline_color), self, "Choose outline color"
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
        """Keep the controls in sync if values change outside the window (+/- or Reset)."""
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
        """Show the window and bring it to the front."""
        self.show()
        self.raise_()
        self.activateWindow()
