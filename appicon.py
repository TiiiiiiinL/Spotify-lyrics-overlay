"""Ritar appens ikon i kod. Återanvänds av både tray-ikonen och .exe-bygget.

Ikonen är en musikskiva i Minecraft-stil: handritad 16x16 pixelkonst med svart
kontur, ljusare ovansida/vänster och mörkare undersida/höger.
"""

from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtCore import Qt

# Paletten. Nycklarna används i PIXELS nedan.
PALETTE = {
    "K": "#12101a",  # kontur, nästan svart
    "M": "#4f4b5c",  # skivans ljusa sida (uppe/vänster)
    "D": "#2b2833",  # skivans mörka sida (nere/höger)
    "W": "#7d7891",  # glansreflex
    "G": "#1DB954",  # Spotify-grön etikett
    "L": "#3ee87a",  # ljus grön highlight på etiketten
}

# 16x16 rutnät. "." = genomskinlig.
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
    """Ritar pixelkonsten skalad till `size`. Kanterna snappas till hela pixlar
    så att rutorna aldrig glappar eller blir suddiga."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setPen(Qt.NoPen)  # ingen antialiasing – vi vill ha skarpa rutor

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
    """QIcon med flera storlekar (skarp både liten och stor)."""
    icon = QIcon()
    for size in (16, 32, 48, 256):
        icon.addPixmap(render_pixmap(size))
    return icon
