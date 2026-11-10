"""
Fallback procedural 2D kawaii Frieren sprite generator (using QPainter)
in case external PNG sprites in assets/sprites/ are missing, AND helper to
post-process raw sprites into clean transparent PNGs.
"""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
)

STATES = (
    # 6 Idle Poses
    "idle",
    "idle_cozy",
    "idle_sleepy",
    "idle_reading",
    "idle_dancing",
    "idle_tea",
    # 5 Thinking Poses (used for normal Q&A / chatting without opening laptop/staff)
    "thinking",
    "thinking_lookup",
    "thinking_tilt",
    "thinking_hmmm",
    # 2 Agentic Execution Poses (ONLY when actually browsing web or running CLI commands)
    "action_laptop",
    "action_magic",
    # Talking & Pleased Poses
    "talking",
    "talking_explain",
    "pleased",
    "pleased_wave",
    # 4 Needs Poses (Thirst, Hunger, Sleepy, Stretch)
    "needs_tea",
    "needs_hungry",
    "needs_sleepy",
    "needs_stretch",
)
IDLE_POSES = (
    "idle",
    "idle_cozy",
    "idle_sleepy",
    "idle_reading",
    "idle_dancing",
    "idle_tea",
)
THINKING_POSES = ("thinking", "thinking_lookup", "thinking_tilt", "thinking_hmmm", "idle_cozy")
TALKING_POSES = ("talking", "talking_explain", "idle", "idle_cozy", "pleased_wave")
PLEASED_POSES = ("pleased", "pleased_wave", "idle_dancing", "idle_cozy", "idle_tea")


def ensure_sprites(sprites_dir: Path) -> dict[str, Path]:
    """Ensure all state PNGs exist in sprites_dir (with safe fallbacks)."""
    sprites_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for state in STATES:
        target = sprites_dir / f"{state}.png"
        if not target.exists():
            if state.startswith("thinking_") or state.startswith("action_"):
                fb = sprites_dir / "thinking.png"
            elif state.startswith("talking_"):
                fb = sprites_dir / "talking.png"
            elif state.startswith("pleased_"):
                fb = sprites_dir / "pleased.png"
            else:
                fb = sprites_dir / "idle.png"
            if fb.exists():
                paths[state] = fb
                continue
            pix = render_procedural_frieren(state, 440, 480)
            pix.save(str(target), "PNG")
        paths[state] = target
    return paths


def render_procedural_frieren(state: str, width: int = 440, height: int = 480) -> QPixmap:
    """Render a clean, lightweight 2D vector illustration of Frieren (transparent PNG)."""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    cx = width * 0.52
    cy = height * 0.44

    # Soft magical aura glow behind character
    aura = QRadialGradient(QPointF(cx, cy + 20), 170)
    if state == "thinking":
        aura.setColorAt(0.0, QColor(145, 195, 255, 75))
    elif state == "pleased":
        aura.setColorAt(0.0, QColor(255, 185, 205, 85))
    else:
        aura.setColorAt(0.0, QColor(220, 235, 255, 65))
    aura.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(aura)
    p.drawEllipse(QPointF(cx, cy + 20), 170, 170)

    # Colors
    hair_base = QColor("#ECEFF6")
    hair_shade = QColor("#CFD6E6")
    hair_outline = QColor("#5B6278")
    skin_color = QColor("#FFF3EC")
    blush_color = QColor(255, 145, 160, 115 if state == "pleased" else 75)
    scarf_red = QColor("#D13B49")
    scarf_dark = QColor("#A32633")
    sweater_white = QColor("#FAFBFD")
    sweater_red = QColor("#D84352")

    pen_outline = QPen(hair_outline, 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

    # 1. Twin-tails (Rambut perak kepang ganda) behind shoulders
    p.setPen(pen_outline)
    hair_grad_l = QLinearGradient(cx - 140, cy - 80, cx - 175, cy + 210)
    hair_grad_l.setColorAt(0.0, hair_base)
    hair_grad_l.setColorAt(1.0, hair_shade)
    p.setBrush(hair_grad_l)

    left_tail = QPainterPath()
    left_tail.moveTo(cx - 72, cy - 75)
    left_tail.cubicTo(cx - 145, cy - 55, cx - 175, cy + 50, cx - 150, cy + 195)
    left_tail.cubicTo(cx - 135, cy + 215, cx - 105, cy + 200, cx - 102, cy + 165)
    left_tail.cubicTo(cx - 105, cy + 75, cx - 92, cy + 5, cx - 65, cy - 45)
    left_tail.closeSubpath()
    p.drawPath(left_tail)

    right_tail = QPainterPath()
    right_tail.moveTo(cx + 72, cy - 75)
    right_tail.cubicTo(cx + 145, cy - 55, cx + 175, cy + 50, cx + 150, cy + 195)
    right_tail.cubicTo(cx + 135, cy + 215, cx + 105, cy + 200, cx + 102, cy + 165)
    right_tail.cubicTo(cx + 105, cy + 75, cx + 92, cy + 5, cx + 65, cy - 45)
    right_tail.closeSubpath()
    p.drawPath(right_tail)

    # Twin-tail ribbons (Dark red/black clips)
    p.setBrush(scarf_dark)
    p.drawRoundedRect(QRectF(cx - 95, cy - 78, 26, 16), 5, 5)
    p.drawRoundedRect(QRectF(cx + 69, cy - 78, 26, 16), 5, 5)

    # 2. Casual white-and-red knitted sweater (Sweter kasual putih-merah)
    p.setPen(pen_outline)
    p.setBrush(sweater_white)
    body_path = QPainterPath()
    body_path.moveTo(cx - 90, cy + 235)
    body_path.cubicTo(cx - 95, cy + 135, cx - 68, cy + 82, cx - 40, cy + 75)
    body_path.lineTo(cx + 40, cy + 75)
    body_path.cubicTo(cx + 68, cy + 82, cx + 95, cy + 135, cx + 90, cy + 235)
    body_path.closeSubpath()
    p.drawPath(body_path)

    # Red casual stripes on sweater chest & cuffs
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(sweater_red)
    p.drawRoundedRect(QRectF(cx - 72, cy + 148, 144, 22), 8, 8)
    p.drawRoundedRect(QRectF(cx - 76, cy + 184, 152, 12), 6, 6)

    # Subtle knit rib lines
    p.setPen(QPen(QColor("#DCE1EC"), 2.0))
    for offset in (-45, -15, 15, 45):
        p.drawLine(QPointF(cx + offset, cy + 115), QPointF(cx + offset, cy + 230))

    # 3. Elf Ears (Telinga peri panjang khas Frieren)
    p.setPen(pen_outline)
    p.setBrush(skin_color)
    left_ear = QPainterPath()
    left_ear.moveTo(cx - 68, cy - 8)
    left_ear.cubicTo(cx - 125, cy - 28, cx - 148, cy - 18, cx - 154, cy - 6)
    left_ear.cubicTo(cx - 135, cy + 16, cx - 100, cy + 20, cx - 64, cy + 16)
    left_ear.closeSubpath()
    p.drawPath(left_ear)

    right_ear = QPainterPath()
    right_ear.moveTo(cx + 68, cy - 8)
    right_ear.cubicTo(cx + 125, cy - 28, cx + 148, cy - 18, cx + 154, cy - 6)
    right_ear.cubicTo(cx + 135, cy + 16, cx + 100, cy + 20, cx + 64, cy + 16)
    right_ear.closeSubpath()
    p.drawPath(right_ear)

    # 4. Red round earrings (Anting bulat merah)
    p.setPen(QPen( QColor("#7A1C24"), 2.2))
    p.setBrush(QColor("#E32636"))
    p.drawLine(QPointF(cx - 76, cy + 16), QPointF(cx - 76, cy + 28))
    p.drawEllipse(QPointF(cx - 76, cy + 35), 9, 9)
    p.drawLine(QPointF(cx + 76, cy + 16), QPointF(cx + 76, cy + 28))
    p.drawEllipse(QPointF(cx + 76, cy + 35), 9, 9)
    # Earring specular highlight
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 190))
    p.drawEllipse(QPointF(cx - 79, cy + 32), 3, 3)
    p.drawEllipse(QPointF(cx + 73, cy + 32), 3, 3)

    # 5. Head & Face
    p.setPen(pen_outline)
    p.setBrush(skin_color)
    face_rect = QRectF(cx - 72, cy - 82, 144, 142)
    p.drawRoundedRect(face_rect, 56, 58)

    # Cheeks blush
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(blush_color)
    p.drawEllipse(QPointF(cx - 42, cy + 14), 16, 9)
    p.drawEllipse(QPointF(cx + 42, cy + 14), 16, 9)

    # 6. Eyes & Facial Expression per State
    eye_green = QColor("#4FA886")
    eye_dark = QColor("#254E41")

    if state == "pleased":
        # Happy closed-eye arches (^ ^)
        p.setPen(QPen(hair_outline, 3.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        left_eye = QPainterPath()
        left_eye.moveTo(cx - 48, cy - 4)
        left_eye.quadTo(cx - 32, cy - 20, cx - 16, cy - 4)
        p.drawPath(left_eye)

        right_eye = QPainterPath()
        right_eye.moveTo(cx + 16, cy - 4)
        right_eye.quadTo(cx + 32, cy - 20, cx + 48, cy - 4)
        p.drawPath(right_eye)
    else:
        # Anime eyes (emerald green typical of Frieren)
        look_dx = 4 if state == "thinking" else 0
        look_dy = -5 if state == "thinking" else 0
        for sign in (-1, 1):
            ex = cx + sign * 32
            ey = cy - 6
            # Upper lash
            p.setPen(QPen(hair_outline, 3.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(QColor("#FFFFFF"))
            p.drawEllipse(QPointF(ex, ey), 15, 17)

            # Iris
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(eye_green)
            p.drawEllipse(QPointF(ex + look_dx, ey + 1 + look_dy), 11, 13)
            p.setBrush(eye_dark)
            p.drawEllipse(QPointF(ex + look_dx, ey + 2 + look_dy), 6, 7)

            # Starlight highlights
            p.setBrush(QColor("#FFFFFF"))
            p.drawEllipse(QPointF(ex - 4 + look_dx, ey - 5 + look_dy), 4.2, 4.2)
            p.drawEllipse(QPointF(ex + 4 + look_dx, ey + 4 + look_dy), 2.3, 2.3)

    # Eyebrows
    p.setPen(QPen(hair_outline, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    brow_dy = -4 if state == "thinking" else 0
    p.drawLine(QPointF(cx - 46, cy - 28 + brow_dy), QPointF(cx - 20, cy - 26))
    p.drawLine(QPointF(cx + 20, cy - 26), QPointF(cx + 46, cy - 28 - brow_dy))

    # Mouth per state
    p.setPen(QPen(hair_outline, 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    if state == "idle":
        mouth = QPainterPath()
        mouth.moveTo(cx - 10, cy + 28)
        mouth.quadTo(cx, cy + 34, cx + 10, cy + 28)
        p.drawPath(mouth)
    elif state == "thinking":
        # Cute small 'o' / 'w' pensive mouth
        p.setBrush(QColor("#E58B94"))
        p.drawEllipse(QPointF(cx + 2, cy + 30), 4.5, 4.5)
    elif state == "talking":
        # Open warm speaking mouth
        p.setBrush(QColor("#DF6E7B"))
        p.drawRoundedRect(QRectF(cx - 11, cy + 23, 22, 15), 7, 7)
    elif state == "pleased":
        # Warm cat-like ':3' or wide happy smile
        mouth = QPainterPath()
        mouth.moveTo(cx - 14, cy + 26)
        mouth.quadTo(cx - 7, cy + 34, cx, cy + 28)
        mouth.quadTo(cx + 7, cy + 34, cx + 14, cy + 26)
        p.drawPath(mouth)

    # 7. Front Silver Hair Bangs
    p.setPen(pen_outline)
    bang_grad = QLinearGradient(cx, cy - 98, cx, cy + 10)
    bang_grad.setColorAt(0.0, hair_base)
    bang_grad.setColorAt(1.0, hair_shade)
    p.setBrush(bang_grad)

    bangs = QPainterPath()
    bangs.moveTo(cx - 76, cy - 25)
    bangs.cubicTo(cx - 82, cy - 88, cx - 35, cy - 102, cx, cy - 98)
    bangs.cubicTo(cx + 35, cy - 102, cx + 82, cy - 88, cx + 76, cy - 25)
    # Center parted bangs strands
    bangs.cubicTo(cx + 58, cy - 48, cx + 38, cy - 14, cx + 22, cy - 38)
    bangs.cubicTo(cx + 10, cy - 12, cx - 10, cy - 12, cx - 22, cy - 38)
    bangs.cubicTo(cx - 38, cy - 14, cx - 58, cy - 48, cx - 76, cy - 25)
    bangs.closeSubpath()
    p.drawPath(bangs)

    # 8. Warm Red Scarf (Syal merah hangat) wrapped cozily around neck
    p.setPen(pen_outline)
    scarf_grad = QLinearGradient(cx - 70, cy + 50, cx + 70, cy + 125)
    scarf_grad.setColorAt(0.0, scarf_red)
    scarf_grad.setColorAt(1.0, scarf_dark)
    p.setBrush(scarf_grad)

    p.drawRoundedRect(QRectF(cx - 64, cy + 52, 128, 42), 18, 18)
    # Scarf hanging tail
    scarf_tail = QPainterPath()
    scarf_tail.moveTo(cx + 14, cy + 84)
    scarf_tail.lineTo(cx + 50, cy + 84)
    scarf_tail.lineTo(cx + 58, cy + 162)
    scarf_tail.lineTo(cx + 10, cy + 162)
    scarf_tail.closeSubpath()
    p.drawPath(scarf_tail)

    # State indicator badge (thinking dots / sparkles for pleased)
    if state == "thinking":
        p.setPen(pen_outline)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QPointF(cx + 95, cy - 65), 7, 7)
        p.drawEllipse(QPointF(cx + 112, cy - 82), 11, 11)
        p.drawRoundedRect(QRectF(cx + 115, cy - 130, 56, 36), 14, 14)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#6E7894"))
        for dx in (130, 143, 156):
            p.drawEllipse(QPointF(cx + dx, cy - 112), 3.5, 3.5)
    elif state == "pleased":
        # Sparkles around head
        p.setPen(QPen(QColor("#FFD166"), 2.5))
        p.setBrush(QColor("#FFF3B0"))
        for sx, sy, r in ((cx - 105, cy - 75, 12), (cx + 108, cy - 70, 14), (cx + 98, cy + 15, 9)):
            star = QPolygonF(
                [
                    QPointF(sx, sy - r),
                    QPointF(sx + r * 0.3, sy - r * 0.3),
                    QPointF(sx + r, sy),
                    QPointF(sx + r * 0.3, sy + r * 0.3),
                    QPointF(sx, sy + r),
                    QPointF(sx - r * 0.3, sy + r * 0.3),
                    QPointF(sx - r, sy),
                    QPointF(sx - r * 0.3, sy - r * 0.3),
                ]
            )
            p.drawPolygon(star)

    p.end()
    return pixmap
