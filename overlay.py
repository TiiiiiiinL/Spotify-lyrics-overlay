"""Det flytande, alltid-överst, genomskinliga undertext-fönstret.

Allt utseende styrs av `settings` (se settings.py) och uppdateras live när
inställningarna ändras.
"""

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QWidget, QApplication, QMenu


class OverlayWindow(QWidget):
    def __init__(self, settings, on_open_settings=None):
        super().__init__()
        self.settings = settings
        self.on_open_settings = on_open_settings

        # Ramlöst, alltid överst, syns inte i aktivitetsfältet
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("Spotify Lyrics Overlay")

        self.current_line = ""
        self.next_line = ""
        # Latinska tecken via Segoe UI, kinesiska (förenklat OCH traditionellt)
        # via samma YaHei/JhengHei → jämn tjocklek överallt.
        self.font_families = [
            "Segoe UI",
            "Microsoft YaHei UI",
            "Microsoft JhengHei UI",
            "Arial",
        ]
        self._drag_offset = None

        # Storlek + placering (återställ sparad position om den finns)
        screen = QApplication.primaryScreen().availableGeometry()
        width = min(int(screen.width() * 0.8), 1100)
        height = 170
        if settings.pos_x is not None and settings.pos_y is not None:
            x, y = settings.pos_x, settings.pos_y
        else:
            x = screen.x() + (screen.width() - width) // 2
            y = screen.y() + screen.height() - height - 70
        self.setGeometry(x, y, width, height)

        # Rita om live när inställningarna ändras
        settings.changed.connect(self.update)

    # ---- Innehåll -------------------------------------------------------

    def set_lines(self, current, nxt):
        if current == self.current_line and nxt == self.next_line:
            return
        self.current_line = current
        self.next_line = nxt
        self.update()

    # ---- Ritning --------------------------------------------------------

    def _make_font(self, size):
        font = QFont()
        font.setFamilies(self.font_families)
        font.setPointSize(size)
        font.setWeight(QFont.Normal)
        return font

    def _text_rect(self, font, width, text, flags):
        """Hur stor plats texten faktiskt tar (efter radbrytning) inom `width`."""
        metrics = QFontMetrics(font)
        rect = QRect(0, 0, width, 100000)
        return metrics.boundingRect(rect, flags, text)

    def paintEvent(self, _event):
        if not self.current_line and not self.next_line:
            return  # helt genomskinligt när inget visas

        s = self.settings
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        margin = 26
        gap = max(2, int(s.font_size * s.line_gap / 100))
        pad_v = max(4, int(s.font_size * 0.25))
        avail_w = self.width() - 2 * margin
        flags = Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap

        main_font = self._make_font(s.font_size)
        next_font = self._make_font(int(s.font_size * 0.58))

        show_next = s.show_next and bool(self.next_line)
        main_rect_size = self._text_rect(main_font, avail_w, self.current_line, flags) \
            if self.current_line else QRect()
        next_rect_size = self._text_rect(next_font, avail_w, self.next_line, flags) \
            if show_next else QRect()
        main_h = main_rect_size.height()
        next_h = next_rect_size.height()

        content_h = main_h + (gap + next_h if show_next else 0)
        total_h = content_h + 2 * pad_v
        top = (self.height() - total_h) // 2  # centrera lodrätt i fönstret

        # Bakgrundsplatta. Höjden följer alltid texten; bredden beror på
        # inställningen bg_fit_text (hela fönstret, eller krymp till texten).
        if s.show_bg:
            if s.bg_fit_text:
                pad_h = max(8, int(s.font_size * 0.45))
                text_w = max(main_rect_size.width(), next_rect_size.width())
                bg_w = min(self.width(), text_w + 2 * pad_h)
                bg_x = (self.width() - bg_w) // 2  # texten är centrerad, så plattan med
            else:
                bg_x, bg_w = 0, self.width()
            alpha = round(255 * s.bg_opacity / 100)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.setPen(Qt.NoPen)
            painter.drawRect(bg_x, top, bg_w, total_h)

        text_color = QColor(s.text_color)
        outline_color = QColor(s.outline_color)
        next_color = QColor(s.text_color)
        next_color.setAlpha(210)
        next_outline = QColor(s.outline_color)
        next_outline.setAlpha(180)

        y = top + pad_v
        if self.current_line:
            main_rect = QRect(margin, y, avail_w, main_h)
            self._draw_outlined(painter, main_rect, self.current_line, main_font,
                                text_color, outline_color, 2, flags)
        if show_next:
            next_rect = QRect(margin, y + main_h + gap, avail_w, next_h)
            self._draw_outlined(painter, next_rect, self.next_line, next_font,
                                next_color, next_outline, 1, flags)

    def _draw_outlined(self, painter, rect, text, font, fill, outline, width, flags):
        """Ritar text med kontur (kopior i alla riktningar) — filmlook."""
        if not text:
            return
        painter.setFont(font)
        painter.setPen(outline)
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                if dx == 0 and dy == 0:
                    continue
                painter.drawText(rect.translated(dx, dy), flags, text)
        painter.setPen(fill)
        painter.drawText(rect, flags, text)

    # ---- Dra fönstret med musen -----------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.settings.locked:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, _event):
        if self._drag_offset is not None:
            self._drag_offset = None
            pos = self.pos()
            self.settings.update(pos_x=pos.x(), pos_y=pos.y())  # spara position

    # ---- Högerklicksmeny ------------------------------------------------

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        if self.on_open_settings:
            menu.addAction("Inställningar…", self.on_open_settings)
        lock = menu.addAction("Lås position")
        lock.setCheckable(True)
        lock.setChecked(self.settings.locked)
        lock.toggled.connect(lambda v: self.settings.update(locked=v))
        menu.addSeparator()
        menu.addAction("Avsluta", QApplication.quit)
        menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        s = self.settings
        if event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            s.update(font_size=min(96, s.font_size + 4))
        elif event.key() in (Qt.Key_Minus, Qt.Key_Underscore):
            s.update(font_size=max(14, s.font_size - 4))
        elif event.key() == Qt.Key_Escape:
            QApplication.quit()
