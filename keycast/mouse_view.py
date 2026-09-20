"""A stylized mouse widget with left / right / middle + scroll highlighting."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QTimer, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont
from PySide6.QtWidgets import QWidget

from . import theme


class MouseView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {theme.BG_PANEL}; border-radius: 10px;")
        self.setMinimumSize(90, 130)
        self._active: set[str] = set()
        self._scroll_dir: str | None = None
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.setInterval(260)
        self._scroll_timer.timeout.connect(self._clear_scroll)

    # ------------------------------------------------------------------ #
    def set_button_active(self, canonical: str, active: bool):
        if active:
            self._active.add(canonical)
        else:
            self._active.discard(canonical)
        self.update()

    def flash_scroll(self, direction: str):
        self._scroll_dir = direction
        self._scroll_timer.start()
        self.update()

    def _clear_scroll(self):
        self._scroll_dir = None
        self.update()

    def clear_all(self):
        self._active.clear()
        self._scroll_dir = None
        self.update()

    # ------------------------------------------------------------------ #
    def _body_rect(self) -> QRectF:
        pad = 14
        w = self.width() - 2 * pad
        h = self.height() - 2 * pad
        # Keep a mouse-like aspect ratio (width : height = 1 : 1.55).
        ratio = 1.55
        if h / w > ratio:
            bw = w
            bh = w * ratio
        else:
            bh = h
            bw = h / ratio
        x = (self.width() - bw) / 2
        y = (self.height() - bh) / 2
        return QRectF(x, y, bw, bh)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        body = self._body_rect()
        radius_top = body.width() * 0.5
        radius_bot = body.width() * 0.32

        # Body outline
        path = QPainterPath()
        path.addRoundedRect(body, radius_bot, radius_bot)
        # round the top more using an extra ellipse-ish clip via a second rect
        p.setPen(QPen(QColor(theme.KEY_BORDER), 1.4))
        p.setBrush(QColor(theme.KEY_BG))
        p.drawPath(path)

        split_y = body.top() + body.height() * 0.44
        mid_x = body.center().x()
        wheel_w = body.width() * 0.16
        wheel_rect = QRectF(
            mid_x - wheel_w / 2,
            body.top() + body.height() * 0.08,
            wheel_w,
            body.height() * 0.22,
        )

        def fill_region(rect_path, cid):
            if cid in self._active:
                col = QColor(theme.HL_BG)
                p.setBrush(col)
                p.setPen(QPen(QColor(theme.HL_BORDER), 1.6))
                p.drawPath(rect_path)

        # Left button region
        left_path = QPainterPath()
        left_path.moveTo(body.left(), split_y)
        left_path.lineTo(body.left(), body.top() + radius_top)
        left_path.quadTo(body.left(), body.top(), body.left() + radius_top, body.top())
        left_path.lineTo(mid_x - 2, body.top())
        left_path.lineTo(mid_x - 2, split_y)
        left_path.closeSubpath()

        right_path = QPainterPath()
        right_path.moveTo(body.right(), split_y)
        right_path.lineTo(body.right(), body.top() + radius_top)
        right_path.quadTo(body.right(), body.top(), body.right() - radius_top, body.top())
        right_path.lineTo(mid_x + 2, body.top())
        right_path.lineTo(mid_x + 2, split_y)
        right_path.closeSubpath()

        # Clip highlights to body so corners stay rounded.
        p.save()
        p.setClipPath(path)
        fill_region(left_path, "mouse_left")
        fill_region(right_path, "mouse_right")
        p.restore()

        # Divider lines
        p.setPen(QPen(QColor(theme.KEY_BORDER), 1.2))
        p.drawLine(QPointF(mid_x, body.top() + 4), QPointF(mid_x, split_y))
        p.drawLine(QPointF(body.left(), split_y), QPointF(body.right(), split_y))

        # Scroll wheel (middle button)
        wheel_active = "mouse_middle" in self._active or self._scroll_dir is not None
        wpath = QPainterPath()
        wpath.addRoundedRect(wheel_rect, wheel_w / 2, wheel_w / 2)
        p.setPen(QPen(QColor(theme.HL_BORDER if wheel_active else theme.KEY_BORDER), 1.4))
        p.setBrush(QColor(theme.HL_BG if wheel_active else theme.KEY_BG_MOD))
        p.drawPath(wpath)

        # Scroll direction arrow
        if self._scroll_dir is not None:
            p.setPen(QColor(theme.HL_TEXT))
            f = QFont("Segoe UI")
            f.setPixelSize(int(wheel_rect.height() * 0.7))
            f.setBold(True)
            p.setFont(f)
            arrow = "\u25B2" if self._scroll_dir == "scroll_up" else "\u25BC"
            p.drawText(wheel_rect, Qt.AlignCenter, arrow)

        # Label
        p.setPen(QColor(theme.KEY_SUB_TEXT))
        lf = QFont("Segoe UI")
        lf.setPixelSize(11)
        p.setFont(lf)
        p.drawText(
            QRectF(0, body.bottom() + 2, self.width(), 16),
            Qt.AlignHCenter | Qt.AlignTop,
            "Mouse",
        )
        p.end()
