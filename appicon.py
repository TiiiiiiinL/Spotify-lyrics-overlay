"""Draws the app icon in code. Reused by both the tray icon and the .exe build.

The icon is a Minecraft-style music disc: hand-drawn 16x16 pixel art with a black
outline, a lighter top/left side and a darker bottom/right side.
"""

from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtCore import Qt

# The palette. The keys are used in PIXELS below.
PALETTE = {
    "K": "#12101a",  # outline, almost black
    "M": "#4f4b5c",  # light side of the disc (top/left)
    "D": "#2b2833",  # dark side of the disc (bottom/right)
    "W": "#7d7891",  # glossy highlight
    "G": "#1DB954",  # Spotify-green label
    "L": "#3ee87a",  # light green highlight on the label
}

# 16x16 grid. "." = transparent.
PIXELS = [
    "................",
    ".....KKKKKK.....",
    "...KKMMMMMMKK...",
    "..KMMMMMMMMMDK..",
    ".KMMWWMMMMMDDDK.",
    ".KMWMMMMMMDDDDK.",
    "KMMMMMGLGGDDDDDK",
    "KMMMMMGKKGDDDDDK",
    "KMMMMMGKKGDDDDDK",
    "KMMMMMGGGGDDDDDK",
    ".KMMMDDDDDDDDDK.",
    ".KMMDDDDDDDDDDK.",
    "..KDDDDDDDDDDK..",
    "...KKDDDDDDKK...",
    ".....KKKKKK.....",
    "................",
]

GRID = len(PIXELS)


def render_pixmap(size):
    """Draws the pixel art scaled to `size`. Edges snap to whole pixels
    so the squares never leave gaps or get blurry."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setPen(Qt.NoPen)  # no antialiasing – we want crisp squares

    def edge(index):
        return round(index * size / GRID)

    for row, line in enumerate(PIXELS):
        y0, y1 = edge(row), edge(row + 1)
        for col, key in enumerate(line):
            if key == ".":
                continue
            x0, x1 = edge(col), edge(col + 1)
            painter.fillRect(x0, y0, x1 - x0, y1 - y0, QColor(PALETTE[key]))

    painter.end()
    return pixmap


def app_qicon():
    """QIcon with several sizes (crisp both small and large)."""
    icon = QIcon()
    for size in (16, 32, 48, 256):
        icon.addPixmap(render_pixmap(size))
    return icon
