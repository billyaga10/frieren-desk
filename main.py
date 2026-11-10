#!/usr/bin/env python3
"""
Frieren 2D Interactive Desktop Companion & Codex Agent (macOS)
Ultra-lightweight transparent borderless window for MacBook Air 2015 (8GB RAM).

Features:
- Borderless, transparent, always-on-top window docked at bottom-right above macOS Dock.
- Dynamic click-through outside Frieren's sprite, speech bubble, and input bar.
- 4 2D expression states (`idle`, `thinking`, `talking`, `pleased`) with smooth 2D cross-fade.
- Custom lightweight 2D Loading Spinner with live Codex command status while thinking.
- Motion typing (typewriter) with toggleable soft anime sound effects (native ObjC NSSound).
- Scrollable Chat History (`📜`) AND Scrollable/Copyable Codex CLI Output Drawer (`💻`).
- Long-Term Memory (`long_term_memory.json` + `frieren_notes.md`) synced to selectable Google Drive.
- Toggleable Agent Execution Mode (`⚡` - open web/URLs, run shell/code via `gpt-6-luna`).
- Minimize Mode (`—` button: collapses to tiny floating orb or hides to Menu Bar without quitting).
"""

from __future__ import annotations

import ctypes
import ctypes.util
import html
import math
import random
import re
import struct
import subprocess
import sys
import wave
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import (
    Property,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QCursor,
    QGuiApplication,
    QIcon,
    QKeySequence,
    QPainter,
    QPen,
    QPixmap,
    QRegion,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from codex_backend import CodexBackend, CodexResult
from needs_manager import NeedsManager
from sprite_helper import IDLE_POSES, PLEASED_POSES, TALKING_POSES, THINKING_POSES, ensure_sprites


# ---------------------------------------------------------------------------
# Natural & Cozy Emotion / Feeling System (No negative/punitive mechanics)
# ---------------------------------------------------------------------------
EMOTION_CATALOG: Dict[str, tuple[str, str]] = {
    "tenang": ("🌿 Tenang", "Damai & rileks menemanimu di meja kerja"),
    "hangat": ("☕ Hangat", "Nyaman sekali memakai syal merah kesayangan"),
    "senang": ("🌸 Senang", "Bahagia bisa mengobrol dan membantumu hari ini"),
    "ceria": ("🎶 Ceria", "Hati sedang riang sambil bersenandung kecil ♪"),
    "antusias": ("✨ Antusias", "Bersemangat mencari tahu & merapal sihir untukmu!"),
    "penasaran": ("🔍 Penasaran", "Tertarik mempelajari hal baru bersamamu"),
    "fokus": ("📖 Fokus", "Konsentrasi penuh membaca grimoire & catatan"),
    "tersentuh": ("🤍 Tersentuh", "Merasa disayangi & dihargai olehmu"),
    "nostalgia": ("💭 Nostalgia", "Terkenang petualangan indah di masa lalu"),
    "mengantuk": ("💤 Mengantuk Manja", "Mata agak berat karena suasananya terlalu nyaman~"),
}

STATE_DEFAULT_EMOTION: Dict[str, str] = {
    "idle": "tenang",
    "idle_cozy": "hangat",
    "idle_sleepy": "mengantuk",
    "idle_reading": "fokus",
    "idle_dancing": "ceria",
    "idle_tea": "hangat",
    "thinking": "fokus",
    "thinking_lookup": "nostalgia",
    "thinking_tilt": "penasaran",
    "thinking_hmmm": "penasaran",
    "action_laptop": "antusias",
    "action_magic": "antusias",
    "talking": "senang",
    "talking_explain": "antusias",
    "pleased": "tersentuh",
    "pleased_wave": "ceria",
    "needs_tea": "hangat",
    "needs_hungry": "penasaran",
    "needs_sleepy": "mengantuk",
    "needs_stretch": "antusias",
}


# ---------------------------------------------------------------------------
# Cute Thinking Statuses & 36 Varied Tap/Click Dialogues for Frieren
# ---------------------------------------------------------------------------
CUTE_THINKING_LINES = [
    "Hmm, tunggu sebentar ya, lagi kupikirkan... ✦",
    "Sedang membolak-balik halaman grimoire... ♪",
    "Emm... lagi merangkai kata-kata yang pas buatmu~",
    "Sebentar ya, Frieren lagi mikir keras nih... (・ω・)",
    "Lagi mengingat-ingat mantra yang cocok... ✦",
    "Hmm... menarik, coba kupikirkan dulu ya~",
    "Tunggu sebentar, telinga elfku lagi fokus... ♪",
    "Sedang merapikan catatan sihir sebentar... ✦",
    "Ehehe, sabar ya, lagi kucari jawabannya~",
    "Hmm... kira-kira gimana ya bagusnya... ♪",
]

PET_QUOTES = [
    "Hehe... terima kasih sudah menyapaku. Syal merah ini hangat sekali, semangat ya kerjanya hari ini!",
    "Hmm? Kamu memanggilku? Aku selalu di sini kok menemanimu.",
    "Jangan lupa minum air putih ya. Perjalanan panjang butuh tubuh yang sehat.",
    "Kepang rambutku rapi kan hari ini? Aku butuh waktu agak lama menyisirnya tadi pagi.",
    "Kalau lelah, istirahat sebentar tidak apa-apa. Bahkan petualang pun butuh duduk di dekat api unggun.",
    "Ada mantra sederhana untuk membuat teh terasa lebih hangat... mau kubuatkan?",
    "Telinga elfku bisa mendengar suara ketikan keyboardmu, ritmenya menenangkan sekali.",
    "Jangan begadang terlalu malam ya... nanti susah bangun pagi sepertiku, hehe.",
    "Himmel dulu pernah bilang, hal kecil yang dikerjakan hari ini akan jadi kenangan berharga nanti.",
    "Sweter rajut ini nyaman sekali... rasanya jadi agak mengantuk kalau udaranya sejuk begini.",
    "Kalau ada kode atau pekerjaan yang rumit, ceritakan saja padaku. Kita urai pelan-pelan bersama.",
    "Ehehe... geli tahu kalau diklik terus, tapi aku senang kamu memperhatikanku ♪",
    "Sedang sibuk ya? Aku duduk tenang di pojok sini sambil membaca grimoire kok.",
    "Kadang berhenti sejenak dan menarik napas dalam-dalam itu bagian dari sihir penenang terbaik.",
    "Aku suka suasana meja kerjamu hari ini. Rasanya damai dan fokus.",
    "Jangan lupa regangkan bahu dan punggungmu sebentar ya, sudah cukup lama kamu menatap layar.",
    "Waktu seribu tahun itu singkat bagi elf, tapi waktumu hari ini sangat berharga. Semangat ya!",
    "Kalau menemukan grimoire langka atau ide baru, jangan lupa catat di memoriku ya.",
    "Hmm... kira-kira camilan manis apa yang enak untuk menemani kerja sore ini ya?",
    "Fern pasti akan mengomeliku kalau tahu aku sempat mengantuk di pojok layarmu, hehe...",
    "Sihir favoritku? Sihir yang menumbuhkan padang bunga... dan sihir kecil untuk membantumu bekerja.",
    "Pelan-pelan saja mengerjakannya, satu langkah kecil tetap membawamu lebih dekat ke tujuan.",
    "Anting merah ini? Ini salah satu benda kesayanganku, cocok kan dengan syalku?",
    "Kamu sudah bekerja keras hari ini. Aku bangga melihat ketekunanmu dari sini ✦",
    "Kalau butuh membuka web atau mencari sesuatu, tinggal panggil aku dengan Cmd+Shift+Space ya!",
    "Udara di sekitar sini terasa hangat... mungkin karena kamu sedang semangat bekerja.",
    "Hmm~ tadi aku hampir tertidur sambil memeluk syal, untung kamu menyapaku.",
    "Tidak semua hal harus selesai dalam satu kedipan mata. Nikmati prosesnya ya.",
    "Kalau kepalamu mulai penuh, coba tulis hal pentingnya agar aku yang menyimpannya untukmu.",
    "Lihat deh, aku bisa ganti-ganti gaya duduk kalau lagi santai... perhatikan ya ♪",
    "Semoga hari ini berjalan lancar tanpa bug yang menyebalkan untukmu!",
    "Hati-hati jangan sampai terhisap mimic ya... eh, maksudku jangan sampai terdistraksi hal aneh, hehe.",
    "Senang rasanya punya teman ngobrol di meja kerja seperti ini.",
    "Aku sudah siap kapan pun kamu butuh bantuan. Panggil saja namaku ya!",
    "Bintang-bintang di luar sana indah, tapi cahaya layarmu juga penuh dengan karya yang keren.",
    "Tarik napas pelan... hembuskan... nah, sekarang ayo kita lanjutkan dengan hati tenang ✦",
]


# ---------------------------------------------------------------------------
# macOS Carbon Global Hotkey (Cmd + Shift + Space) - Zero CPU Polling
# ---------------------------------------------------------------------------
kEventClassKeyboard = 0x6B657962  # 'keyb'
kEventHotKeyPressed = 5
cmdKey = 1 << 8
shiftKey = 1 << 9
kVK_Space = 0x31


class EventTypeSpec(ctypes.Structure):
    _fields_ = [("eventClass", ctypes.c_uint32), ("eventKind", ctypes.c_uint32)]


class EventHotKeyID(ctypes.Structure):
    _fields_ = [("signature", ctypes.c_uint32), ("id", ctypes.c_uint32)]


EventHandlerProcPtr = ctypes.CFUNCTYPE(
    ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
)


class MacGlobalHotKey:
    """Registers a native macOS Carbon global hotkey (Cmd+Shift+Space)."""

    def __init__(self, callback) -> None:
        self.callback = callback
        self._handler_ref = None
        self._hotkey_ref = ctypes.c_void_p()
        self._c_callback = None
        self._install()

    def _install(self) -> None:
        if sys.platform != "darwin":
            return
        try:
            carbon_path = ctypes.util.find_library("Carbon")
            if not carbon_path:
                return
            self.carbon = ctypes.cdll.LoadLibrary(carbon_path)

            def _handler(next_handler, event, user_data):
                QTimer.singleShot(0, self.callback)
                return 0

            self._c_callback = EventHandlerProcPtr(_handler)
            spec = EventTypeSpec(kEventClassKeyboard, kEventHotKeyPressed)

            self.carbon.GetApplicationEventTarget.restype = ctypes.c_void_p
            target = self.carbon.GetApplicationEventTarget()

            handler_ref = ctypes.c_void_p()
            self.carbon.InstallEventHandler(
                ctypes.c_void_p(target),
                self._c_callback,
                1,
                ctypes.byref(spec),
                None,
                ctypes.byref(handler_ref),
            )
            self._handler_ref = handler_ref

            hk_id = EventHotKeyID(0x46524E31, 1)  # 'FRN1'
            self.carbon.RegisterEventHotKey(
                ctypes.c_uint32(kVK_Space),
                ctypes.c_uint32(cmdKey | shiftKey),
                hk_id,
                ctypes.c_void_p(target),
                ctypes.c_uint32(0),
                ctypes.byref(self._hotkey_ref),
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Ultra-lightweight Soft Anime Typing Sound Synthesizer & Player (Native ObjC)
# ---------------------------------------------------------------------------
class TypingSoundPlayer:
    """Generates tiny 3KB soft sine-chime WAVs and plays them via native ObjC NSSound."""

    def __init__(self, assets_dir: Path, enabled: bool = True) -> None:
        self.enabled = enabled
        self.sounds_dir = assets_dir / "sounds"
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        self.effects: list[int] = []
        self._idx = 0
        self._objc = None
        self._sel_is_playing = None
        self._sel_stop = None
        self._sel_play = None
        self._init_sounds()

    def _init_sounds(self) -> None:
        freqs = (587.33, 659.25, 783.99)
        for i, freq in enumerate(freqs):
            wav_path = self.sounds_dir / f"blip_{i}.wav"
            if not wav_path.exists():
                self._write_blip_wav(wav_path, freq)

        if sys.platform == "win32":
            # Native Windows winsound player support
            try:
                import winsound
                self._winsound = winsound
            except Exception:
                pass
            return

        if sys.platform != "darwin":
            return
        try:
            objc_path = ctypes.util.find_library("objc")
            appkit_path = ctypes.util.find_library("AppKit")
            if not objc_path or not appkit_path:
                return
            ctypes.cdll.LoadLibrary(appkit_path)
            objc = ctypes.cdll.LoadLibrary(objc_path)

            objc.objc_getClass.restype = ctypes.c_void_p
            objc.objc_getClass.argtypes = [ctypes.c_char_p]
            objc.sel_registerName.restype = ctypes.c_void_p
            objc.sel_registerName.argtypes = [ctypes.c_char_p]

            msg = objc.objc_msgSend
            self._objc = objc

            ns_string_cls = objc.objc_getClass(b"NSString")
            ns_sound_cls = objc.objc_getClass(b"NSSound")
            sel_str_utf8 = objc.sel_registerName(b"stringWithUTF8String:")
            sel_alloc = objc.sel_registerName(b"alloc")
            sel_init_file = objc.sel_registerName(b"initWithContentsOfFile:byReference:")
            sel_set_vol = objc.sel_registerName(b"setVolume:")
            self._sel_is_playing = objc.sel_registerName(b"isPlaying")
            self._sel_stop = objc.sel_registerName(b"stop")
            self._sel_play = objc.sel_registerName(b"play")

            for i in range(len(freqs)):
                wav_bytes = str(self.sounds_dir / f"blip_{i}.wav").encode("utf-8")
                msg.restype = ctypes.c_void_p
                msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p]
                ns_path = msg(ns_string_cls, sel_str_utf8, wav_bytes)

                msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                snd_alloc = msg(ns_sound_cls, sel_alloc)

                msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool]
                snd = msg(snd_alloc, sel_init_file, ns_path, True)
                if snd:
                    msg.restype = None
                    msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float]
                    msg(snd, sel_set_vol, 0.28)
                    self.effects.append(snd)
        except Exception:
            pass

    @staticmethod
    def _write_blip_wav(path: Path, freq: float, duration_ms: int = 34, sample_rate: int = 22050) -> None:
        n_samples = int(sample_rate * (duration_ms / 1000.0))
        frames = bytearray()
        for s in range(n_samples):
            t = s / sample_rate
            progress = s / max(1, n_samples - 1)
            env = math.sin(math.pi * progress) * ((1.0 - progress) ** 0.7)
            val = math.sin(2.0 * math.pi * freq * t) * 0.45 * env
            sample_i16 = max(-32767, min(32767, int(val * 32767)))
            frames.extend(struct.pack("<h", sample_i16))

        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(bytes(frames))

    def play_tick(self) -> None:
        if not self.enabled:
            return
        if sys.platform == "win32" and hasattr(self, "_winsound"):
            try:
                wav_file = str(self.sounds_dir / f"blip_{self._idx % 3}.wav")
                self._idx += 1
                self._winsound.PlaySound(wav_file, self._winsound.SND_FILENAME | self._winsound.SND_ASYNC)
            except Exception:
                pass
            return

        if not self.effects or not self._objc:
            return
        try:
            snd = self.effects[self._idx % len(self.effects)]
            self._idx += 1
            msg = self._objc.objc_msgSend
            msg.restype = ctypes.c_bool
            msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            if msg(snd, self._sel_is_playing):
                msg(snd, self._sel_stop)
            msg(snd, self._sel_play)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Lightweight 2D Loading Spinner Widget (for `thinking` state)
# ---------------------------------------------------------------------------
class LoadingSpinnerWidget(QWidget):
    """Smooth 2D arc spinner drawn with QPainter (zero external assets)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(45)
        self._timer.timeout.connect(self._step)

    def start(self) -> None:
        self._angle = 0
        self.show()
        if not self._timer.isActive():
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _step(self) -> None:
        self._angle = (self._angle + 24) % 360
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(3.0, 3.0, self.width() - 6.0, self.height() - 6.0)

        bg_pen = QPen(QColor(255, 214, 220, 45), 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(bg_pen)
        p.drawEllipse(rect)

        arc_pen = QPen(QColor("#FF758F"), 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(arc_pen)
        p.drawArc(rect, -self._angle * 16, 110 * 16)
        p.end()


# ---------------------------------------------------------------------------
# Background Worker Thread for Non-Interactive Codex CLI (`gpt-6-luna`)
# ---------------------------------------------------------------------------
class CodexWorker(QThread):
    finished_result = Signal(object)
    status_update = Signal(str)

    def __init__(
        self,
        backend: CodexBackend,
        message: str,
        attachments: Optional[List[str]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.backend = backend
        self.message = message
        self.attachments = list(attachments or [])

    def run(self) -> None:
        res = self.backend.ask(
            self.message,
            on_status=self.status_update.emit,
            attachments=self.attachments,
        )
        self.finished_result.emit(res)


# ---------------------------------------------------------------------------
# Custom Input LineEdit Supporting Image Paste (Cmd+V) & File/Image Drag-Drop
# ---------------------------------------------------------------------------
class ChatInputBox(QLineEdit):
    imagePasted = Signal(object)
    filesDropped = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.StandardKey.Paste):
            cb = QGuiApplication.clipboard()
            md = cb.mimeData()
            if md:
                if md.hasImage():
                    img = cb.image()
                    if not img.isNull():
                        self.imagePasted.emit(img)
                        event.accept()
                        return
                if md.hasUrls():
                    local_paths = [u.toLocalFile() for u in md.urls() if u.isLocalFile()]
                    if local_paths:
                        self.filesDropped.emit(local_paths)
                        event.accept()
                        return
        super().keyPressEvent(self, event) if False else super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        md = event.mimeData()
        if md and (md.hasUrls() or md.hasImage() or md.hasText()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        md = event.mimeData()
        if md:
            if md.hasImage():
                img = md.imageData()
                if img is not None:
                    self.imagePasted.emit(img)
                    event.acceptProposedAction()
                    return
            if md.hasUrls():
                local_paths = [u.toLocalFile() for u in md.urls() if u.isLocalFile()]
                if local_paths:
                    self.filesDropped.emit(local_paths)
                    event.acceptProposedAction()
                    return
        super().dropEvent(event)


# ---------------------------------------------------------------------------
# 2D Cross-Fade Sprite Widget (Supports normal & minimized badge mode)
# ---------------------------------------------------------------------------
class FrierenSpriteWidget(QWidget):
    clicked = Signal()

    def __init__(self, sprites: Dict[str, Path], fade_ms: int = 220, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._base_normal_size = (235, 245)
        self._base_mini_size = (88, 92)
        self._scale_factor: float = 1.0
        self.is_minimized = False
        self.setFixedSize(*self._base_normal_size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._raw_pixmaps: Dict[str, QPixmap] = {
            state: QPixmap(str(path)) for state, path in sprites.items()
        }
        self.pixmaps: Dict[str, QPixmap] = {}
        self.alpha_masks: Dict[str, QRegion] = {}
        self._rebuild_scaled_sprites()

        self.current_state = "idle"
        self.previous_state = "idle"
        self._fade_progress: float = 1.0
        self._sway_phase: float = 0.0

        self.fade_anim = QPropertyAnimation(self, b"fadeProgress", self)
        self.fade_anim.setDuration(fade_ms)

        self.sway_timer = QTimer(self)
        self.sway_timer.setInterval(55)
        self.sway_timer.timeout.connect(self._on_sway_tick)

    def _on_sway_tick(self) -> None:
        self._sway_phase += 0.22
        self.update()

    def _apply_geometry_and_rebuild(self) -> None:
        base_w, base_h = self._base_mini_size if self.is_minimized else self._base_normal_size
        w = max(64, int(base_w * self._scale_factor))
        h = max(68, int(base_h * self._scale_factor))
        self.setFixedSize(w, h)
        self._rebuild_scaled_sprites()
        self.update()

    def set_scale_factor(self, scale: float) -> None:
        self._scale_factor = max(0.65, min(1.55, float(scale)))
        self._apply_geometry_and_rebuild()

    def _rebuild_scaled_sprites(self) -> None:
        self.pixmaps.clear()
        self.alpha_masks.clear()
        for state, raw_pix in self._raw_pixmaps.items():
            pix = raw_pix.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.pixmaps[state] = pix
            mask = pix.mask()
            self.alpha_masks[state] = QRegion(mask) if not mask.isNull() else QRegion(self.rect())

    def set_minimized_mode(self, minimized: bool) -> None:
        if self.is_minimized == minimized:
            return
        self.is_minimized = minimized
        self._apply_geometry_and_rebuild()

    def get_fade_progress(self) -> float:
        return self._fade_progress

    def set_fade_progress(self, val: float) -> None:
        self._fade_progress = float(val)
        self.update()

    fadeProgress = Property(float, get_fade_progress, set_fade_progress)

    def set_state(self, state: str) -> None:
        if state not in self.pixmaps or state == self.current_state:
            return
        self.previous_state = self.current_state
        self.current_state = state
        if state in ("idle_dancing", "action_laptop", "action_magic", "pleased"):
            self._sway_phase = 0.0
            if not self.sway_timer.isActive():
                self.sway_timer.start()
        else:
            self.sway_timer.stop()
            self._sway_phase = 0.0
        self.fade_anim.stop()
        self._fade_progress = 0.0
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def opaque_region(self) -> QRegion:
        return self.alpha_masks.get(self.current_state, QRegion(self.rect()))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        dx, dy = 0, 0
        if self.sway_timer.isActive():
            if self.current_state == "idle_dancing":
                dx = int(math.sin(self._sway_phase) * 4.0)
                dy = int(abs(math.cos(self._sway_phase * 2.0)) * -3.5)
            else:
                dy = int(math.sin(self._sway_phase * 1.3) * 2.2)

        if self._fade_progress < 1.0 and self.previous_state in self.pixmaps:
            painter.setOpacity(1.0 - self._fade_progress)
            prev_pix = self.pixmaps[self.previous_state]
            px = (self.width() - prev_pix.width()) // 2
            py = self.height() - prev_pix.height()
            painter.drawPixmap(px, py, prev_pix)

        painter.setOpacity(self._fade_progress)
        curr_pix = self.pixmaps[self.current_state]
        cx = (self.width() - curr_pix.width()) // 2 + dx
        cy = max(0, self.height() - curr_pix.height() + dy)
        painter.drawPixmap(cx, cy, curr_pix)
        painter.end()


# ---------------------------------------------------------------------------
# Speech Bubble Widget (Spinner + Motion Typing + History + Codex Output + Minimize)
# ---------------------------------------------------------------------------
class SpeechBubble(QFrame):
    soundToggled = Signal(bool)
    historyToggled = Signal(bool)
    outputToggled = Signal(bool)
    agentToggled = Signal(bool)
    needsToggled = Signal(bool)
    needReplenishRequested = Signal(str)
    careAllRequested = Signal()
    minimizeRequested = Signal()
    typingFinished = Signal()
    bubbleDragDeltaY = Signal(int)
    bubbleDragFinished = Signal()

    def __init__(
        self,
        sound_player: TypingSoundPlayer,
        typing_interval_ms: int = 26,
        history_enabled: bool = False,
        output_enabled: bool = False,
        agent_enabled: bool = True,
        needs_enabled: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("speechBubble")
        self.setFixedWidth(336)

        self.sound_player = sound_player
        self.typing_interval_ms = max(12, typing_interval_ms)
        self.history_enabled = history_enabled
        self.output_enabled = output_enabled
        self.agent_enabled = agent_enabled
        self.needs_enabled = needs_enabled
        self._bubble_drag_last_y: Optional[int] = None

        self._full_text = ""
        self._typed_index = 0
        self._char_tick_counter = 0

        self.typing_timer = QTimer(self)
        self.typing_timer.setInterval(self.typing_interval_ms)
        self.typing_timer.timeout.connect(self._on_typing_step)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 10)
        layout.setSpacing(6)

        # Header Row: Name + Emotion/State + Collapsible Quick Action Toolbar + Minimize
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)

        self.name_label = QLabel("✦ Frieren")
        self.name_label.setObjectName("bubbleTitle")
        self.name_label.setCursor(Qt.CursorShape.SizeVerCursor)
        self.name_label.setToolTip("Geser (Drag) naik/turun untuk mengatur jarak Bubble dengan Frieren")
        self.name_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.current_emotion_key = "tenang"
        self.current_state_key = "idle"
        self.emotion_badge = QLabel("🌿 Tenang")
        self.emotion_badge.setObjectName("emotionBadge")
        self.emotion_badge.setCursor(Qt.CursorShape.SizeVerCursor)
        self.emotion_badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.emotion_badge.setToolTip("Perasaan Frieren saat ini: Damai & rileks menemanimu di meja kerja")
        self.state_badge = QLabel("· santai")
        self.state_badge.setObjectName("stateBadge")
        self.state_badge.setMinimumWidth(0)
        self.state_badge.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        # Collapsible Tools Container (hidden/collapsed by default so emotion & status are clearly visible!)
        self.tools_expanded = False
        self.tools_panel = QWidget(self)
        tools_layout = QHBoxLayout(self.tools_panel)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(3)

        # 1. Agent Execution Toggle Button (⚡)
        self.agent_btn = QPushButton("⚡", self.tools_panel)
        self.agent_btn.setObjectName("iconToggleBtn")
        self.agent_btn.setCheckable(True)
        self.agent_btn.setChecked(self.agent_enabled)
        self.agent_btn.setFixedSize(22, 20)
        self.agent_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.agent_btn.setToolTip("Mode Eksekusi Codex (Buka Web / Jalankan Perintah)")
        self.agent_btn.clicked.connect(self._on_agent_btn_clicked)

        # 2. Codex CLI Output Drawer Button (💻)
        self.output_btn = QPushButton("💻", self.tools_panel)
        self.output_btn.setObjectName("iconToggleBtn")
        self.output_btn.setCheckable(True)
        self.output_btn.setChecked(self.output_enabled)
        self.output_btn.setFixedSize(22, 20)
        self.output_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.output_btn.setToolTip("Panel Output / Log Eksekusi Codex CLI")
        self.output_btn.clicked.connect(self._on_output_btn_clicked)

        # 3. Scrollable Chat History Button (📜)
        self.history_btn = QPushButton("📜", self.tools_panel)
        self.history_btn.setObjectName("iconToggleBtn")
        self.history_btn.setCheckable(True)
        self.history_btn.setChecked(self.history_enabled)
        self.history_btn.setFixedSize(22, 20)
        self.history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.history_btn.setToolTip("Tampilkan / Sembunyikan Riwayat Chat (Scrollable)")
        self.history_btn.clicked.connect(self._on_history_btn_clicked)

        # 4. Sound Toggle Button (🔊 / 🔇)
        self.sound_btn = QPushButton("🔊" if self.sound_player.enabled else "🔇", self.tools_panel)
        self.sound_btn.setObjectName("iconToggleBtn")
        self.sound_btn.setCheckable(True)
        self.sound_btn.setChecked(self.sound_player.enabled)
        self.sound_btn.setFixedSize(22, 20)
        self.sound_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sound_btn.setToolTip("Aktifkan / Nonaktifkan Suara Ketikan Frieren")
        self.sound_btn.clicked.connect(self._on_sound_btn_clicked)

        # 5. Needs & Wellness Drawer Button (🍵)
        self.needs_btn = QPushButton("🍵", self.tools_panel)
        self.needs_btn.setObjectName("iconToggleBtn")
        self.needs_btn.setCheckable(True)
        self.needs_btn.setChecked(self.needs_enabled)
        self.needs_btn.setFixedSize(22, 20)
        self.needs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.needs_btn.setToolTip("Tampilkan / Sembunyikan Status Kebutuhan & Perhatian Frieren (🍵)")
        self.needs_btn.clicked.connect(self._on_needs_btn_clicked)

        tools_layout.addWidget(self.needs_btn)
        tools_layout.addWidget(self.agent_btn)
        tools_layout.addWidget(self.output_btn)
        tools_layout.addWidget(self.history_btn)
        tools_layout.addWidget(self.sound_btn)
        self.tools_panel.setVisible(False)

        # Toggle Button to Expand/Collapse Action Buttons (◂ / ▸)
        self.tools_toggle_btn = QPushButton("◂")
        self.tools_toggle_btn.setObjectName("iconToggleBtn")
        self.tools_toggle_btn.setCheckable(True)
        self.tools_toggle_btn.setChecked(False)
        self.tools_toggle_btn.setFixedSize(20, 20)
        self.tools_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tools_toggle_btn.setToolTip("Buka / Collapse Tombol Pengaturan Cepat (🍵 ⚡ 💻 📜 🔊)")
        self.tools_toggle_btn.clicked.connect(self._on_tools_toggle_clicked)

        # 5. Minimize Bubble Button (—)
        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("iconToggleBtn")
        self.min_btn.setFixedSize(20, 20)
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setToolTip("Sembunyikan Bubble Chat (Klik Frieren atau Cmd+Shift+Space untuk memunculkan lagi)")
        self.min_btn.clicked.connect(self.minimizeRequested.emit)

        header.addWidget(self.name_label)
        header.addWidget(self.emotion_badge)
        header.addWidget(self.state_badge, 1)
        header.addWidget(self.tools_panel)
        header.addWidget(self.tools_toggle_btn)
        header.addWidget(self.min_btn)
        layout.addLayout(header)

        # Scrollable Chat History Area
        self.history_scroll = QScrollArea(self)
        self.history_scroll.setObjectName("historyScroll")
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_scroll.setFixedHeight(105)

        self.history_content = QWidget()
        self.history_content.setObjectName("historyContent")
        self.history_layout = QVBoxLayout(self.history_content)
        self.history_layout.setContentsMargins(4, 4, 6, 4)
        self.history_layout.setSpacing(5)
        self.history_layout.addStretch(1)
        self.history_scroll.setWidget(self.history_content)
        self.history_scroll.setVisible(self.history_enabled)
        layout.addWidget(self.history_scroll)

        # Scrollable & Copyable Codex CLI Output Drawer (💻)
        self.output_box = QPlainTextEdit(self)
        self.output_box.setObjectName("codexOutputBox")
        self.output_box.setReadOnly(True)
        self.output_box.setPlaceholderText("Log perintah & output Codex CLI akan tampil di sini...")
        self.output_box.setFixedHeight(105)
        self.output_box.setVisible(self.output_enabled)
        layout.addWidget(self.output_box)

        # Interactive Needs & Wellness Panel (🍵)
        self.needs_panel = QFrame(self)
        self.needs_panel.setObjectName("needsPanel")
        needs_panel_layout = QVBoxLayout(self.needs_panel)
        needs_panel_layout.setContentsMargins(8, 8, 8, 8)
        needs_panel_layout.setSpacing(6)

        needs_header = QHBoxLayout()
        needs_title = QLabel("🍵 Kebutuhan Frieren", self.needs_panel)
        needs_title.setObjectName("needsTitle")
        care_all_btn = QPushButton("✨ Care All", self.needs_panel)
        care_all_btn.setObjectName("needsCareAllBtn")
        care_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        care_all_btn.setToolTip("Penuhi semua kebutuhan Frieren sekaligus")
        care_all_btn.clicked.connect(self.careAllRequested.emit)
        needs_header.addWidget(needs_title)
        needs_header.addStretch(1)
        needs_header.addWidget(care_all_btn)
        needs_panel_layout.addLayout(needs_header)

        self.needs_bars: Dict[str, QProgressBar] = {}
        items_def = [
            ("thirst", "☕ Haus", "#64B5F6", "+ Teh"),
            ("hunger", "🍰 Lapar", "#FFB74D", "+ Makan"),
            ("energy", "💤 Energi", "#BA68C8", "+ Tidur"),
            ("freshness", "🌿 Segar", "#81C784", "+ Regang"),
        ]
        for key, label_txt, color_hex, btn_txt in items_def:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel(label_txt, self.needs_panel)
            lbl.setFixedWidth(56)
            lbl.setObjectName("needsRowLabel")

            bar = QProgressBar(self.needs_panel)
            bar.setRange(0, 100)
            bar.setValue(80)
            bar.setTextVisible(True)
            bar.setFormat("80%")
            bar.setFixedHeight(14)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: rgba(255, 255, 255, 20);
                    border: 1px solid rgba(255, 255, 255, 30);
                    border-radius: 6px;
                    text-align: center;
                    color: #FFFFFF;
                    font-size: 9.5px;
                    font-weight: 600;
                }}
                QProgressBar::chunk {{
                    background-color: {color_hex};
                    border-radius: 5px;
                }}
            """)
            self.needs_bars[key] = bar

            action_btn = QPushButton(btn_txt, self.needs_panel)
            action_btn.setObjectName("needsActionBtn")
            action_btn.setFixedSize(54, 18)
            action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            action_btn.clicked.connect(lambda checked=False, k=key: self.needReplenishRequested.emit(k))

            row.addWidget(lbl)
            row.addWidget(bar, 1)
            row.addWidget(action_btn)
            needs_panel_layout.addLayout(row)

        self.needs_panel.setVisible(self.needs_enabled)
        layout.addWidget(self.needs_panel)

        # Loading Spinner Row (shown only while `thinking`)
        self.loading_row = QWidget(self)
        loading_layout = QHBoxLayout(self.loading_row)
        loading_layout.setContentsMargins(2, 4, 2, 4)
        loading_layout.setSpacing(8)
        self.spinner = LoadingSpinnerWidget(self.loading_row)
        self.loading_label = QLabel("Sedang memproses permintaanmu...")
        self.loading_label.setObjectName("loadingLabel")
        self.loading_label.setWordWrap(True)
        loading_layout.addWidget(self.spinner)
        loading_layout.addWidget(self.loading_label, 1)
        self.loading_row.setVisible(False)
        layout.addWidget(self.loading_row)

        # Scrollable Current Active Message Area (prevents clipping & supports clickable links)
        self.msg_scroll = QScrollArea(self)
        self.msg_scroll.setObjectName("msgScroll")
        self.msg_scroll.setWidgetResizable(True)
        self.msg_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.msg_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.msg_scroll.setMinimumHeight(54)
        self.msg_scroll.setMaximumHeight(135)
        self.msg_scroll.setVisible(not self.history_enabled)

        self.text_label = QLabel(
            "Halo... Aku sudah duduk nyaman di pojok layarmu. "
            "Aku bisa mengingat hal penting, membuka web, dan membantu pekerjaanmu kapan saja!"
        )
        self.text_label.setObjectName("bubbleText")
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.text_label.setTextFormat(Qt.TextFormat.RichText)
        self.text_label.setOpenExternalLinks(True)
        self.text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.msg_scroll.setWidget(self.text_label)
        layout.addWidget(self.msg_scroll)

    def _on_tools_toggle_clicked(self, checked: bool) -> None:
        self.tools_expanded = bool(checked)
        self.tools_panel.setVisible(self.tools_expanded)
        self.tools_toggle_btn.setText("▸" if self.tools_expanded else "◂")
        self._refresh_header_fit()

    def _refresh_header_fit(self) -> None:
        """Ensures `emotion_badge` is ALWAYS 100% readable even when resized down to 70%."""
        label, desc = EMOTION_CATALOG.get(self.current_emotion_key, ("🌸 Senang", ""))
        w = self.width()

        # When toolbar (🍵 ⚡ 💻 📜 🔊) is expanded on a compact bubble, shorten emotion to emoji or hide title
        if self.tools_expanded:
            self.state_badge.setVisible(False)
            if w < 320:
                # Show only emoji on compact width while tools are open
                emoji_only = label.split(" ")[0]
                self.emotion_badge.setText(emoji_only)
            else:
                self.emotion_badge.setText(label)
            return

        # Normal state (toolbar collapsed): ALWAYS show full emotion badge (`🔍 Penasaran`, etc.)!
        self.emotion_badge.setText(label)
        if w < 285:
            # On small/resized bubbles, hide secondary activity text so Emotion Badge has 100% room
            self.state_badge.setVisible(False)
        else:
            self.state_badge.setVisible(True)
            raw_state_txt = getattr(self, "_raw_state_text", "· santai")
            fm = self.state_badge.fontMetrics()
            avail = max(36, w - 215)
            self.state_badge.setText(fm.elidedText(raw_state_txt, Qt.TextElideMode.ElideRight, avail))

    def _on_sound_btn_clicked(self, checked: bool) -> None:
        self.set_sound_enabled(checked)
        self.soundToggled.emit(checked)

    def _on_history_btn_clicked(self, checked: bool) -> None:
        self.set_history_enabled(checked)
        self.historyToggled.emit(checked)

    def _on_output_btn_clicked(self, checked: bool) -> None:
        self.set_output_enabled(checked)
        self.outputToggled.emit(checked)

    def _on_agent_btn_clicked(self, checked: bool) -> None:
        self.set_agent_enabled(checked)
        self.agentToggled.emit(checked)

    def _on_needs_btn_clicked(self, checked: bool) -> None:
        self.set_needs_enabled(checked)
        self.needsToggled.emit(checked)

    def set_needs_enabled(self, enabled: bool) -> None:
        self.needs_enabled = enabled
        self.needs_btn.setChecked(enabled)
        self.needs_panel.setVisible(enabled)
        self.adjustSize()

    def update_needs_data(self, data: Dict[str, float]) -> None:
        """Update progress bars for all tracked needs in the drawer."""
        for key, bar in self.needs_bars.items():
            if key in data:
                val = int(round(data[key]))
                bar.setValue(val)
                bar.setFormat(f"{val}%")
        # Visual alert on the 🍵 button if any need is below 35%
        is_low = any(data.get(k, 100.0) < 35.0 for k in ("thirst", "hunger", "energy", "freshness"))
        if is_low and not self.needs_enabled:
            self.needs_btn.setStyleSheet("background-color: rgba(255, 152, 0, 160); border: 1px solid #FFD54F;")
        else:
            self.needs_btn.setStyleSheet("")

    def set_sound_enabled(self, enabled: bool) -> None:
        self.sound_player.enabled = enabled
        self.sound_btn.setChecked(enabled)
        self.sound_btn.setText("🔊" if enabled else "🔇")

    def set_history_enabled(self, enabled: bool) -> None:
        self.history_enabled = enabled
        self.history_btn.setChecked(enabled)
        self.history_scroll.setVisible(enabled)
        self.msg_scroll.setVisible(not enabled)
        self.adjustSize()
        if enabled:
            self.scroll_to_bottom()

    def set_output_enabled(self, enabled: bool) -> None:
        self.output_enabled = enabled
        self.output_btn.setChecked(enabled)
        self.output_box.setVisible(enabled)
        self.adjustSize()

    def set_agent_enabled(self, enabled: bool) -> None:
        self.agent_enabled = enabled
        self.agent_btn.setChecked(enabled)

    def set_cli_output(self, text: str) -> None:
        """Store CLI log in console box without forcing it open if user closed it."""
        self.output_box.setPlainText(text)
        sb = self.output_box.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

    @staticmethod
    def format_rich_text(raw: str) -> str:
        """Convert Markdown (bold, italic, inline code, lists, links) into clean HTML."""
        escaped = html.escape(raw)

        # 1. Extract inline code `code` into placeholders first so markdown inside code isn't altered
        code_slots: List[str] = []

        def _code_repl(m: re.Match) -> str:
            idx = len(code_slots)
            code_slots.append(
                f'<code style="background-color:rgba(255,255,255,24); color:#FFD6DC; '
                f'padding:1px 4px; border-radius:4px; font-family:Menlo,monospace; font-size:11.5px;">{m.group(1)}</code>'
            )
            return f"@@CODE_{idx}@@"

        text = re.sub(r"`([^`\n]+)`", _code_repl, escaped)

        # 2. Convert [label](url) markdown links (supports https, http, file, and local paths) into placeholders
        link_slots: List[str] = []

        def _md_repl(m: re.Match) -> str:
            idx = len(link_slots)
            label, url = m.group(1), m.group(2)
            href = url
            # Convert local filesystem absolute paths to file:// URI for native desktop opening
            if url.startswith("/") or re.match(r"^[a-zA-Z]:[\\/]", url):
                href = f"file://{url}"
            link_slots.append(f'<a href="{href}" style="color:#82AAFF; text-decoration:underline;">{label}</a>')
            return f"@@LINK_{idx}@@"

        text = re.sub(
            r"\[([^\]]+)\]\(((?:https?://|file://|/|[a-zA-Z]:[\\/])[^\s\)]+)\)",
            _md_repl,
            text,
        )

        # 3. Convert standalone https://... URLs
        def _url_repl(m: re.Match) -> str:
            idx = len(link_slots)
            url = m.group(1)
            link_slots.append(f'<a href="{url}" style="color:#82AAFF; text-decoration:underline;">{url}</a>')
            return f"@@LINK_{idx}@@"

        text = re.sub(r"(https?://[^\s<>\")]+)", _url_repl, text)

        # 4. Bold (**text** or __text__)
        text = re.sub(
            r"\*\*(.+?)\*\*",
            r'<b style="color:#FFF0F3; font-weight:700;">\1</b>',
            text,
            flags=re.S,
        )
        # Also gracefully close an unclosed ** at the end of a partial typing slice so `**` never flashes raw
        if text.count("**") % 2 == 1:
            text = re.sub(
                r"\*\*([^*]+)$",
                r'<b style="color:#FFF0F3; font-weight:700;">\1</b>',
                text,
            )
        text = re.sub(
            r"__(.+?)__",
            r'<b style="color:#FFF0F3; font-weight:700;">\1</b>',
            text,
            flags=re.S,
        )

        # 5. Italic (*text* or _text_) — avoid matching inside words or lone asterisks
        text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", text)
        text = re.sub(r"(?<![a-zA-Z0-9_])_([^_\n]+?)_(?![a-zA-Z0-9_])", r"<i>\1</i>", text)

        # 6. Strikethrough (~~text~~)
        text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)

        # 7. Clean bullet lists & headings at start of lines
        formatted_lines: List[str] = []
        for line in text.split("\n"):
            s_line = line.strip()
            if re.match(r"^#{1,4}\s+", s_line):
                head_txt = re.sub(r"^#{1,4}\s+", "", s_line)
                formatted_lines.append(f'<b style="color:#FFD6DC;">{head_txt}</b>')
            elif re.match(r"^[-*]\s+", s_line):
                item_txt = re.sub(r"^[-*]\s+", "", s_line)
                formatted_lines.append(f"• {item_txt}")
            else:
                formatted_lines.append(line)

        result = "<br>".join(formatted_lines)

        # Restore links and inline code slots
        for idx, html_link in enumerate(link_slots):
            result = result.replace(f"@@LINK_{idx}@@", html_link)
        for idx, html_code in enumerate(code_slots):
            result = result.replace(f"@@CODE_{idx}@@", html_code)

        return result

    def set_emotion(self, emotion_key: str) -> None:
        key = emotion_key.lower().strip()
        if key not in EMOTION_CATALOG:
            key = "senang"
        self.current_emotion_key = key
        label, desc = EMOTION_CATALOG[key]
        self.emotion_badge.setText(label)
        self.emotion_badge.setToolTip(f"Perasaan Frieren: {label} — {desc}")
        self._refresh_header_fit()

    def update_state_badge(self, state: str, emotion_override: Optional[str] = None) -> None:
        self.current_state_key = state
        badge_map = {
            "idle": "· santai",
            "idle_cozy": "· nyender ♪",
            "idle_sleepy": "· terkantuk~",
            "idle_reading": "· baca buku 📖",
            "idle_dancing": "· menari ♪",
            "idle_tea": "· minum teh ☕",
            "thinking": "· mikir...",
            "thinking_lookup": "· menerawang~",
            "thinking_tilt": "· memikir...",
            "thinking_hmmm": "· merenung...",
            "action_laptop": "· buka laptop 💻",
            "action_magic": "· merapal sihir ✦",
            "talking": "· berbicara",
            "talking_explain": "· menjelaskan ♪",
            "pleased": "· tersenyum ♪",
            "pleased_wave": "· menyapa 👋",
            "needs_tea": "· butuh teh ☕",
            "needs_hungry": "· lapar 🍰",
            "needs_sleepy": "· mengantuk 💤",
            "needs_stretch": "· peregangan 🌿",
        }
        self._raw_state_text = badge_map.get(state, f"· {state}")
        self.state_badge.setToolTip(f"Aktivitas saat ini: {self._raw_state_text.lstrip('· ')}")
        if emotion_override:
            self.set_emotion(emotion_override)
        elif state in STATE_DEFAULT_EMOTION:
            self.set_emotion(STATE_DEFAULT_EMOTION[state])
        else:
            self._refresh_header_fit()

    def show_loading(self, status_text: str = "Sedang memproses permintaanmu...") -> None:
        self.typing_timer.stop()
        self.update_state_badge("thinking")
        self.loading_label.setText(status_text)
        self.msg_scroll.setVisible(False)
        self.spinner.start()
        self.loading_row.setVisible(True)
        self.adjustSize()

    def update_loading_status(self, status_text: str) -> None:
        self.loading_label.setText(status_text)
        self.adjustSize()

    def show_message(
        self,
        text: str,
        state: str = "idle",
        animate: bool = False,
        emotion_override: Optional[str] = None,
    ) -> None:
        self.typing_timer.stop()
        self.spinner.stop()
        self.loading_row.setVisible(False)
        self.msg_scroll.setVisible(not self.history_enabled)
        self.update_state_badge(state, emotion_override=emotion_override)

        if not animate or not text:
            self._full_text = text
            self.text_label.setText(self.format_rich_text(text))
            self._update_msg_scroll_height()
            self.typingFinished.emit()
            return

        self._full_text = text
        self._typed_index = 0
        self._char_tick_counter = 0
        self.text_label.setText("")
        self._update_msg_scroll_height()
        self.typing_timer.start()

    def _update_msg_scroll_height(self) -> None:
        self.text_label.adjustSize()
        content_h = self.text_label.sizeHint().height() + 8
        target_h = max(48, min(135, content_h))
        self.msg_scroll.setFixedHeight(target_h)
        bar = self.msg_scroll.verticalScrollBar()
        if bar:
            bar.setValue(bar.maximum())
        self.adjustSize()

    def _on_typing_step(self) -> None:
        if self._typed_index >= len(self._full_text):
            self.typing_timer.stop()
            # Render final rich text with clickable links when typing finishes
            self.text_label.setText(self.format_rich_text(self._full_text))
            self._update_msg_scroll_height()
            self.typingFinished.emit()
            return

        self._typed_index += 1
        current_slice = self._full_text[: self._typed_index]
        last_char = self._full_text[self._typed_index - 1]
        self.text_label.setText(self.format_rich_text(current_slice))

        if not last_char.isspace():
            self._char_tick_counter += 1
            if self._char_tick_counter % 2 == 1:
                self.sound_player.play_tick()

        self._update_msg_scroll_height()

    def refresh_history(self, items: List[Dict[str, str]], ltm_count: int = 0) -> None:
        while self.history_layout.count() > 1:
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if ltm_count > 0:
            ltm_badge = QLabel(f"✦ {ltm_count} catatan memori tersimpan (Lokal & GDrive)")
            ltm_badge.setObjectName("ltmBadge")
            self.history_layout.insertWidget(0, ltm_badge)

        if not items:
            empty_lbl = QLabel("Belum ada riwayat percakapan.")
            empty_lbl.setObjectName("historyEmpty")
            self.history_layout.insertWidget(self.history_layout.count() - 1, empty_lbl)
        else:
            for entry in items:
                role = entry.get("role", "user")
                text = entry.get("text", "")
                row_frame = QFrame()
                row_frame.setObjectName("historyItemUser" if role == "user" else "historyItemBot")
                row_layout = QVBoxLayout(row_frame)
                row_layout.setContentsMargins(8, 4, 8, 4)
                row_layout.setSpacing(2)

                who = "Kamu" if role == "user" else "✦ Frieren"
                rich_body = self.format_rich_text(text)
                lbl = QLabel(f"<b>{who}:</b> {rich_body}")
                lbl.setObjectName("historyItemText")
                lbl.setWordWrap(True)
                lbl.setTextFormat(Qt.TextFormat.RichText)
                lbl.setOpenExternalLinks(True)
                lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
                row_layout.addWidget(lbl)
                self.history_layout.insertWidget(self.history_layout.count() - 1, row_frame)

        QTimer.singleShot(20, self.scroll_to_bottom)

    def scroll_to_bottom(self) -> None:
        bar = self.history_scroll.verticalScrollBar()
        if bar:
            bar.setValue(bar.maximum())

    def mousePressEvent(self, event) -> None:
        # Allow dragging the top header area of the bubble vertically to adjust gap from Frieren
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 34:
            self._bubble_drag_last_y = int(event.globalPosition().y())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._bubble_drag_last_y is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            curr_y = int(event.globalPosition().y())
            dy = curr_y - self._bubble_drag_last_y
            if dy != 0:
                self._bubble_drag_last_y = curr_y
                # Dragging up (dy < 0) increases gap; dragging down (dy > 0) brings bubble closer
                self.bubbleDragDeltaY.emit(-dy)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._bubble_drag_last_y is not None:
            self._bubble_drag_last_y = None
            self.bubbleDragFinished.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)


# ---------------------------------------------------------------------------
# Main Transparent Desktop Companion Window
# ---------------------------------------------------------------------------
class FrierenDeskWindow(QWidget):
    def __init__(self, base_dir: Path) -> None:
        super().__init__()
        self.base_dir = base_dir
        self.backend = CodexBackend(base_dir)
        self.needs = NeedsManager(base_dir)
        self.config = self.backend.config

        win_cfg = self.config.get("window", {})
        self.base_win_w = int(win_cfg.get("width", 360))
        self.base_win_h = int(win_cfg.get("height", 620))
        self.margin_right = int(win_cfg.get("margin_right", 18))
        self.margin_bottom = int(win_cfg.get("margin_bottom", 12))

        anim_cfg = self.config.get("animation", {})
        self.fade_ms = int(anim_cfg.get("fade_duration_ms", 220))
        self.typing_interval_ms = int(anim_cfg.get("typing_interval_ms", 26))
        self.talking_hold_ms = int(anim_cfg.get("talking_hold_ms", 2200))
        self.pleased_hold_ms = int(anim_cfg.get("pleased_hold_ms", 4000))
        self.bubble_autohide_ms = int(anim_cfg.get("bubble_autohide_ms", 9000))

        ui_cfg = self.config.get("ui", {})
        sound_enabled = bool(ui_cfg.get("sound_enabled", True))
        history_enabled = bool(ui_cfg.get("history_enabled", False))
        output_enabled = bool(ui_cfg.get("output_enabled", False))
        needs_enabled = bool(ui_cfg.get("needs_enabled", False))
        self.is_minimized = bool(ui_cfg.get("minimized", False))
        self.auto_hide_bubble = bool(ui_cfg.get("auto_hide_bubble", True))
        self.scale_factor: float = float(ui_cfg.get("scale", 1.0))
        self.opacity_level: float = float(ui_cfg.get("opacity", 1.0))
        self.bubble_gap: int = int(ui_cfg.get("bubble_gap", 4))
        self._last_pet_idx: int = -1
        self._idle_pose_idx: int = 0

        self.sound_player = TypingSoundPlayer(self.base_dir / "assets", enabled=sound_enabled)

        self._drag_offset: Optional[QPoint] = None
        self._worker: Optional[CodexWorker] = None
        self.pending_attachments: List[str] = []
        self.clipboard_dir = self.base_dir / "assets" / "clipboard"
        self.clipboard_dir.mkdir(parents=True, exist_ok=True)
        self.setAcceptDrops(True)

        # Auto-hide timer for bubble & input bar when idle / not chatting
        self.bubble_hide_timer = QTimer(self)
        self.bubble_hide_timer.setSingleShot(True)
        self.bubble_hide_timer.timeout.connect(self._on_bubble_autohide_timeout)

        self._init_window_flags()
        self._init_ui(history_enabled=history_enabled, output_enabled=output_enabled, needs_enabled=needs_enabled)
        self._init_shortcuts_and_tray()
        self.apply_scale(self.scale_factor, save=False, redock=False)
        self.apply_opacity(self.opacity_level, save=False)
        self.apply_bubble_gap(self.bubble_gap, save=False)
        if self.is_minimized:
            self.set_minimized(True)
        else:
            self._schedule_bubble_autohide()
        self.dock_bottom_right()

        # Perform initial quiet Google Drive sync check
        self.backend.sync_to_gdrive()

        self.state_timer = QTimer(self)
        self.state_timer.setSingleShot(True)
        self.state_timer.timeout.connect(self._on_state_timer)
        self._next_scheduled_state = "idle"

        # Periodic Idle Pose Changer (rotates between idle, idle_cozy, idle_sleepy every 16s)
        self.idle_cycle_timer = QTimer(self)
        self.idle_cycle_timer.setInterval(16000)
        self.idle_cycle_timer.timeout.connect(self._cycle_idle_pose)
        self.idle_cycle_timer.start()

        # Needs & Wellness Tracker Timer (ticks every 60s)
        self.needs_timer = QTimer(self)
        self.needs_timer.setInterval(60000)
        self.needs_timer.timeout.connect(self._on_needs_tick)
        self.needs_timer.start()

        self.clickthrough_timer = QTimer(self)
        self.clickthrough_timer.setInterval(60)
        self.clickthrough_timer.timeout.connect(self._update_mask_and_clickthrough)
        self.clickthrough_timer.start()

    def _init_window_flags(self) -> None:
        self.setWindowTitle("Frieren Desk Companion")
        self.setFixedSize(self.base_win_w, self.base_win_h)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        if hasattr(Qt.WidgetAttribute, "WA_MacAlwaysShowToolWindow") and sys.platform == "darwin":
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)

    def _init_ui(self, history_enabled: bool, output_enabled: bool, needs_enabled: bool = False) -> None:
        sprites = ensure_sprites(self.base_dir / "assets" / "sprites")

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 10)
        root.setSpacing(4)

        # Top stretch pushes the speech bubble down so it sits right above Frieren's head!
        root.addStretch(1)

        self.bubble = SpeechBubble(
            sound_player=self.sound_player,
            typing_interval_ms=self.typing_interval_ms,
            history_enabled=history_enabled,
            output_enabled=output_enabled,
            agent_enabled=self.backend.agent_execution_enabled,
            needs_enabled=needs_enabled,
            parent=self,
        )
        self.bubble.soundToggled.connect(self._on_sound_toggled)
        self.bubble.historyToggled.connect(self._on_history_toggled)
        self.bubble.outputToggled.connect(self._on_output_toggled)
        self.bubble.agentToggled.connect(self._on_agent_toggled)
        self.bubble.needsToggled.connect(self._on_needs_toggled)
        self.bubble.needReplenishRequested.connect(self._fulfill_need)
        self.bubble.careAllRequested.connect(self._fulfill_all_needs)
        self.bubble.minimizeRequested.connect(self.minimize_bubble_only)
        self.bubble.typingFinished.connect(self._on_typing_finished)
        self.bubble.bubbleDragDeltaY.connect(self._on_bubble_drag_delta)
        self.bubble.bubbleDragFinished.connect(self._on_bubble_drag_finished)
        self._refresh_bubble_history()
        self.bubble.update_needs_data(self.needs.data)
        root.addWidget(self.bubble, alignment=Qt.AlignmentFlag.AlignRight)

        # Controlled gap widget between Bubble and Frieren (clamped 0..70px so it never goes too far)
        self.bubble_spacer = QWidget(self)
        self.bubble_spacer.setFixedHeight(max(0, min(70, self.bubble_gap)))
        self.bubble_spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        root.addWidget(self.bubble_spacer)

        self.sprite = FrierenSpriteWidget(sprites, fade_ms=self.fade_ms, parent=self)
        root.addWidget(self.sprite, alignment=Qt.AlignmentFlag.AlignRight)

        # Attachment Preview Bar (shown above input bar when user pastes/drops images or files)
        self.attachment_bar = QFrame(self)
        self.attachment_bar.setObjectName("attachmentBar")
        att_layout = QHBoxLayout(self.attachment_bar)
        att_layout.setContentsMargins(10, 4, 8, 4)
        att_layout.setSpacing(6)
        self.attachment_label = QLabel("")
        self.attachment_label.setObjectName("attachmentLabel")
        self.attachment_label.setWordWrap(False)
        self.attachment_clear_btn = QPushButton("✕")
        self.attachment_clear_btn.setObjectName("attachmentClearBtn")
        self.attachment_clear_btn.setFixedSize(18, 18)
        self.attachment_clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attachment_clear_btn.setToolTip("Hapus semua lampiran gambar/file")
        self.attachment_clear_btn.clicked.connect(self.clear_attachments)
        att_layout.addWidget(self.attachment_label, 1)
        att_layout.addWidget(self.attachment_clear_btn)
        self.attachment_bar.setVisible(False)
        root.addWidget(self.attachment_bar)

        self.input_container = QFrame(self)
        self.input_container.setObjectName("inputContainer")
        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(8, 6, 8, 6)
        input_layout.setSpacing(5)

        self.attach_btn = QPushButton("📎", self.input_container)
        self.attach_btn.setObjectName("attachButton")
        self.attach_btn.setFixedSize(26, 26)
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.setToolTip("Lampirkan Gambar / File (Atau langsung Cmd+V / Drag & Drop ke Frieren)")
        self.attach_btn.clicked.connect(self._pick_attachments_dialog)

        self.input_box = ChatInputBox(self.input_container)
        self.input_box.setObjectName("chatInput")
        self.input_box.setPlaceholderText("Ngobrol sama Frieren...")
        self.input_box.returnPressed.connect(self.send_message)
        self.input_box.imagePasted.connect(self._on_image_pasted)
        self.input_box.filesDropped.connect(self._on_files_dropped)

        self.send_btn = QPushButton("✦", self.input_container)
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setFixedSize(28, 28)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.attach_btn)
        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.send_btn)
        root.addWidget(self.input_container)

        self.setStyleSheet(
            """
            #speechBubble {
                background-color: rgba(25, 27, 38, 238);
                border: 1.5px solid rgba(216, 67, 82, 195);
                border-radius: 14px;
            }
            #bubbleTitle {
                color: #FFD6DC;
                font-size: 12px;
                font-weight: 700;
            }
            #emotionBadge {
                background-color: rgba(216, 67, 82, 55);
                border: 1px solid rgba(255, 182, 193, 95);
                border-radius: 7px;
                color: #FFEBF0;
                font-size: 10.5px;
                font-weight: 600;
                padding: 1px 6px;
            }
            #stateBadge {
                color: #AEB8D0;
                font-size: 10.5px;
                font-style: italic;
            }
            #iconToggleBtn {
                background-color: rgba(255, 255, 255, 18);
                border: 1px solid rgba(255, 255, 255, 35);
                border-radius: 6px;
                color: #F5F7FA;
                font-size: 11px;
                padding: 0px;
            }
            #iconToggleBtn:checked {
                background-color: rgba(209, 59, 73, 155);
                border: 1px solid rgba(255, 190, 200, 175);
            }
            #iconToggleBtn:hover {
                background-color: rgba(255, 255, 255, 45);
            }
            #historyScroll {
                background-color: rgba(16, 18, 26, 175);
                border: 1px solid rgba(255, 255, 255, 28);
                border-radius: 9px;
            }
            #msgScroll {
                background-color: transparent;
                border: none;
            }
            #bubbleText {
                background-color: rgba(25, 27, 38, 245);
                color: #F5F7FA;
                font-size: 12.5px;
                line-height: 1.35;
                padding-right: 4px;
            }
            #historyContent {
                background: transparent;
            }
            #codexOutputBox {
                background-color: rgba(12, 14, 20, 215);
                border: 1px solid rgba(130, 170, 255, 75);
                border-radius: 9px;
                color: #B9F27C;
                font-family: "SF Mono", Menlo, Monaco, monospace;
                font-size: 11px;
                padding: 5px;
                selection-background-color: #3D59A1;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 2px 1px 2px 1px;
            }
            QScrollBar::handle:vertical {
                background: rgba(216, 67, 82, 160);
                min-height: 18px;
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            #ltmBadge {
                color: #FFE082;
                font-size: 10.5px;
                font-weight: 600;
                padding: 2px 4px;
            }
            #historyItemUser {
                background-color: rgba(58, 66, 92, 145);
                border-radius: 7px;
            }
            #historyItemBot {
                background-color: rgba(120, 38, 52, 130);
                border-radius: 7px;
            }
            #historyItemText {
                color: #ECEFF6;
                font-size: 11.5px;
            }
            #historyEmpty {
                color: #8E96AA;
                font-size: 11px;
                font-style: italic;
                padding: 6px;
            }
            #loadingLabel {
                color: #FFD6DC;
                font-size: 11.5px;
                font-style: italic;
            }
            #needsPanel {
                background-color: rgba(16, 18, 26, 195);
                border: 1px solid rgba(255, 182, 193, 45);
                border-radius: 9px;
            }
            #needsTitle {
                color: #FFEBF0;
                font-size: 11.5px;
                font-weight: 700;
            }
            #needsCareAllBtn {
                background-color: rgba(216, 67, 82, 140);
                border: 1px solid rgba(255, 190, 200, 160);
                border-radius: 5px;
                color: #FFFFFF;
                font-size: 9.5px;
                font-weight: bold;
                padding: 1px 6px;
            }
            #needsCareAllBtn:hover {
                background-color: rgba(228, 84, 98, 210);
            }
            #needsRowLabel {
                color: #ECEFF6;
                font-size: 11px;
                font-weight: 500;
            }
            #needsActionBtn {
                background-color: rgba(255, 255, 255, 22);
                border: 1px solid rgba(255, 255, 255, 45);
                border-radius: 5px;
                color: #ECEFF6;
                font-size: 9.5px;
                font-weight: 600;
            }
            #needsActionBtn:hover {
                background-color: rgba(216, 67, 82, 155);
                border-color: rgba(255, 190, 200, 180);
            }
            #bubbleText {
                color: #F5F7FA;
                font-size: 12.5px;
                line-height: 1.35;
            }
            #inputContainer {
                background-color: rgba(24, 26, 36, 240);
                border: 1.5px solid rgba(236, 239, 246, 150);
                border-radius: 16px;
            }
            #attachmentBar {
                background-color: rgba(34, 38, 54, 238);
                border: 1px solid rgba(130, 170, 255, 145);
                border-radius: 11px;
            }
            #attachmentLabel {
                color: #D8E6FF;
                font-size: 11px;
                font-weight: 600;
            }
            #attachmentClearBtn {
                background-color: rgba(216, 67, 82, 140);
                border: none;
                border-radius: 9px;
                color: #FFFFFF;
                font-size: 10px;
                font-weight: bold;
            }
            #attachmentClearBtn:hover {
                background-color: rgba(228, 84, 98, 210);
            }
            #attachButton {
                background-color: rgba(255, 255, 255, 18);
                border: 1px solid rgba(255, 255, 255, 38);
                border-radius: 13px;
                color: #ECEFF6;
                font-size: 12px;
            }
            #attachButton:hover {
                background-color: rgba(255, 255, 255, 45);
            }
            #chatInput {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 12.5px;
                selection-background-color: #D13B49;
            }
            #sendButton {
                background-color: #D13B49;
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                font-weight: bold;
                font-size: 13px;
            }
            #sendButton:hover {
                background-color: #E45462;
            }
            #sendButton:disabled {
                background-color: #5A5F72;
            }
            """
        )

    def _init_shortcuts_and_tray(self) -> None:
        self.local_shortcut = QShortcut(QKeySequence("Meta+Shift+Space"), self)
        self.local_shortcut.activated.connect(self.toggle_input_bar)

        self.min_shortcut = QShortcut(QKeySequence("Meta+M"), self)
        self.min_shortcut.activated.connect(lambda: self.set_minimized(not self.is_minimized))

        self.zoom_in_shortcut = QShortcut(QKeySequence("Meta+="), self)
        self.zoom_in_shortcut.activated.connect(lambda: self.apply_scale(self.scale_factor + 0.12))
        self.zoom_in_shortcut2 = QShortcut(QKeySequence("Meta++"), self)
        self.zoom_in_shortcut2.activated.connect(lambda: self.apply_scale(self.scale_factor + 0.12))

        self.zoom_out_shortcut = QShortcut(QKeySequence("Meta+-"), self)
        self.zoom_out_shortcut.activated.connect(lambda: self.apply_scale(self.scale_factor - 0.12))

        self.zoom_reset_shortcut = QShortcut(QKeySequence("Meta+0"), self)
        self.zoom_reset_shortcut.activated.connect(lambda: self.apply_scale(1.0))

        self.esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.esc_shortcut.activated.connect(self.hide_input_bar)

        self.global_hotkey = MacGlobalHotKey(self.toggle_input_bar)

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self)
            tray_pix = self.sprite.pixmaps.get("idle")
            if tray_pix:
                self.tray.setIcon(QIcon(tray_pix))
            self.tray.setToolTip("Frieren Desk Companion (Cmd+Shift+Space)")

            menu = QMenu()
            act_toggle = QAction("Munculkan / Fokus Input (Cmd+Shift+Space)", self)
            act_toggle.triggered.connect(self.toggle_input_bar)
            menu.addAction(act_toggle)

            act_min_bubble = QAction("Sembunyikan Bubble Chat Saja (Biarkan Frieren)", self)
            act_min_bubble.triggered.connect(self.minimize_bubble_only)
            menu.addAction(act_min_bubble)

            self.act_autohide_bubble = QAction("Otomatis Minimize Bubble Saat Diam (Idle)", self)
            self.act_autohide_bubble.setCheckable(True)
            self.act_autohide_bubble.setChecked(self.auto_hide_bubble)
            self.act_autohide_bubble.triggered.connect(self._toggle_autohide_bubble)
            menu.addAction(self.act_autohide_bubble)

            self.act_minimize = QAction("Minimize Karakter ke Mode Mini (Cmd+M)", self)
            self.act_minimize.setCheckable(True)
            self.act_minimize.setChecked(self.is_minimized)
            self.act_minimize.triggered.connect(self.set_minimized)
            menu.addAction(self.act_minimize)

            self.act_hide_window = QAction("Sembunyikan ke Menu Bar Saja", self)
            self.act_hide_window.setCheckable(True)
            self.act_hide_window.setChecked(False)
            self.act_hide_window.triggered.connect(self._toggle_hide_to_tray)
            menu.addAction(self.act_hide_window)

            menu.addSeparator()

            # Submenu: AI Engine Selection (Codex vs Antigravity)
            engine_menu = menu.addMenu("🤖 Mesin AI (Codex vs Antigravity)")
            self.engine_group = QActionGroup(self)
            self.engine_group.setExclusive(True)

            act_eng_codex = QAction("OpenAI Codex CLI (gpt-6-luna)", self)
            act_eng_codex.setCheckable(True)
            act_eng_codex.setChecked(self.backend.active_engine == "codex")
            act_eng_codex.triggered.connect(lambda: self._switch_engine("codex"))
            self.engine_group.addAction(act_eng_codex)
            engine_menu.addAction(act_eng_codex)

            act_eng_agy = QAction("Google Antigravity CLI (gemini-3.8-flash-low)", self)
            act_eng_agy.setCheckable(True)
            act_eng_agy.setChecked(self.backend.active_engine == "antigravity")
            act_eng_agy.triggered.connect(lambda: self._switch_engine("antigravity"))
            self.engine_group.addAction(act_eng_agy)
            engine_menu.addAction(act_eng_agy)

            engine_menu.addSeparator()
            act_check_pre = QAction("Periksa Kesiapan Mesin (Login & Binary)", self)
            act_check_pre.triggered.connect(self._check_engine_status_dialog)
            engine_menu.addAction(act_check_pre)

            menu.addSeparator()

            self.act_agent = QAction("⚡ Izinkan Eksekusi Aksi / Buka Web (Agent Mode)", self)
            self.act_agent.setCheckable(True)
            self.act_agent.setChecked(self.backend.agent_execution_enabled)
            self.act_agent.triggered.connect(self._toggle_agent_from_menu)
            menu.addAction(self.act_agent)

            self.act_output = QAction("💻 Tampilkan Panel Output / Log Codex", self)
            self.act_output.setCheckable(True)
            self.act_output.setChecked(self.bubble.output_enabled)
            self.act_output.triggered.connect(self._toggle_output_from_menu)
            menu.addAction(self.act_output)

            self.act_history = QAction("📜 Tampilkan Riwayat Chat (Scrollable)", self)
            self.act_history.setCheckable(True)
            self.act_history.setChecked(self.bubble.history_enabled)
            self.act_history.triggered.connect(self._toggle_history_from_menu)
            menu.addAction(self.act_history)

            self.act_sound = QAction("🔊 Suara Ketikan (Motion Typing Sound)", self)
            self.act_sound.setCheckable(True)
            self.act_sound.setChecked(self.sound_player.enabled)
            self.act_sound.triggered.connect(self._toggle_sound_from_menu)
            menu.addAction(self.act_sound)

            # Submenu: Kebutuhan & Perhatian (Needs & Wellness System)
            needs_menu = menu.addMenu("🍵 Kebutuhan & Istirahat (Needs System)")

            self.act_status_needs = QAction("Tampilkan Panel Indikator Kebutuhan (🍵)", self)
            self.act_status_needs.setCheckable(True)
            self.act_status_needs.setChecked(self.bubble.needs_enabled)
            self.act_status_needs.triggered.connect(self._toggle_needs_from_menu)
            needs_menu.addAction(self.act_status_needs)
            needs_menu.addSeparator()

            act_feed_tea = QAction("🍵 Beri Teh Hangat (Thirst +40)", self)
            act_feed_tea.triggered.connect(lambda: self._fulfill_need("thirst"))
            needs_menu.addAction(act_feed_tea)

            act_feed_cake = QAction("🍰 Beri Camilan Manis (Hunger +40)", self)
            act_feed_cake.triggered.connect(lambda: self._fulfill_need("hunger"))
            needs_menu.addAction(act_feed_cake)

            act_rest = QAction("💤 Temani Istirahat Sejenak (Energy +40)", self)
            act_rest.triggered.connect(lambda: self._fulfill_need("energy"))
            needs_menu.addAction(act_rest)

            act_stretch = QAction("🌿 Peregangan Bersama (Freshness +40)", self)
            act_stretch.triggered.connect(lambda: self._fulfill_need("freshness"))
            needs_menu.addAction(act_stretch)

            needs_menu.addSeparator()
            act_care_all = QAction("✨ Penuhi Semua Kebutuhan (Care All)", self)
            act_care_all.triggered.connect(self._fulfill_all_needs)
            needs_menu.addAction(act_care_all)

            menu.addSeparator()

            # Submenu: Perasaan / Suasana Hati Frieren (Natural & Cozy)
            emotion_menu = menu.addMenu("🌸 Perasaan & Suasana Hati Frieren")
            lbl_emo = QAction("Perasaan Frieren mengalir alami (tanpa marah/ngambek):", self)
            lbl_emo.setEnabled(False)
            emotion_menu.addAction(lbl_emo)
            emotion_menu.addSeparator()
            for emo_key, (emo_label, emo_desc) in EMOTION_CATALOG.items():
                act_emo = QAction(f"{emo_label} — {emo_desc}", self)
                act_emo.triggered.connect(lambda checked=False, k=emo_key: self._set_manual_emotion(k))
                emotion_menu.addAction(act_emo)

            # Submenu: Resize / Ukuran Karakter & Window
            size_menu = menu.addMenu("📐 Ukuran Frieren (Resize / Cmd + Scroll)")
            self.size_group = QActionGroup(self)
            self.size_group.setExclusive(True)
            size_presets = [
                ("Kecil (80%)", 0.80),
                ("Normal (100% - Cmd+0)", 1.00),
                ("Besar (120%)", 1.20),
                ("Ekstra Besar (140%)", 1.40),
            ]
            self.size_actions: Dict[float, QAction] = {}
            for label, sc in size_presets:
                act_sz = QAction(label, self)
                act_sz.setCheckable(True)
                act_sz.setChecked(abs(self.scale_factor - sc) < 0.06)
                act_sz.triggered.connect(lambda checked, s=sc: self.apply_scale(s))
                self.size_group.addAction(act_sz)
                size_menu.addAction(act_sz)
                self.size_actions[sc] = act_sz

            size_menu.addSeparator()
            act_zin = QAction("Perbesar Sedikit (Cmd + =)", self)
            act_zin.triggered.connect(lambda: self.apply_scale(self.scale_factor + 0.10))
            size_menu.addAction(act_zin)

            act_zout = QAction("Perkecil Sedikit (Cmd + -)", self)
            act_zout.triggered.connect(lambda: self.apply_scale(self.scale_factor - 0.10))
            size_menu.addAction(act_zout)

            # Submenu: Opacity / Transparansi (Option + Scroll)
            opacity_menu = menu.addMenu("💧 Transparansi / Opacity (Option + Scroll)")
            self.opacity_group = QActionGroup(self)
            self.opacity_group.setExclusive(True)
            opacity_presets = [
                ("Solid (100%)", 1.00),
                ("Sedikit Transparan (85%)", 0.85),
                ("Lembut (70%)", 0.70),
                ("Samar (55%)", 0.55),
                ("Bayangan Tipis (40%)", 0.40),
            ]
            self.opacity_actions: Dict[float, QAction] = {}
            for label, op in opacity_presets:
                act_op = QAction(label, self)
                act_op.setCheckable(True)
                act_op.setChecked(abs(self.opacity_level - op) < 0.06)
                act_op.triggered.connect(lambda checked, o=op: self.apply_opacity(o))
                self.opacity_group.addAction(act_op)
                opacity_menu.addAction(act_op)
                self.opacity_actions[op] = act_op

            opacity_menu.addSeparator()
            act_opin = QAction("Lebih Jelas (+10%)", self)
            act_opin.triggered.connect(lambda: self.apply_opacity(self.opacity_level + 0.10))
            opacity_menu.addAction(act_opin)

            act_opout = QAction("Lebih Transparan (-10%)", self)
            act_opout.triggered.connect(lambda: self.apply_opacity(self.opacity_level - 0.10))
            opacity_menu.addAction(act_opout)

            # Submenu: Bubble Distance / Jarak Bubble ke Frieren (Drag Header / Shift + Scroll)
            gap_menu = menu.addMenu("💬 Jarak Bubble ke Frieren (Drag Header / Shift+Scroll)")
            self.gap_group = QActionGroup(self)
            self.gap_group.setExclusive(True)
            gap_presets = [
                ("Menempel Dekat (0 px)", 0),
                ("Dekat & Pas (4 px - Default)", 4),
                ("Sedang (16 px)", 16),
                ("Agak Atas (32 px)", 32),
                ("Batas Atas Maksimal (55 px)", 55),
            ]
            self.gap_actions: Dict[int, QAction] = {}
            for label, gp in gap_presets:
                act_gp = QAction(label, self)
                act_gp.setCheckable(True)
                act_gp.setChecked(abs(self.bubble_gap - gp) <= 3)
                act_gp.triggered.connect(lambda checked, g=gp: self.apply_bubble_gap(g))
                self.gap_group.addAction(act_gp)
                gap_menu.addAction(act_gp)
                self.gap_actions[gp] = act_gp

            gap_menu.addSeparator()
            act_gdown = QAction("Lebih Dekat ke Frieren (-6 px)", self)
            act_gdown.triggered.connect(lambda: self.apply_bubble_gap(self.bubble_gap - 6))
            gap_menu.addAction(act_gdown)

            act_gup = QAction("Agak Naik Sedikit (+6 px)", self)
            act_gup.triggered.connect(lambda: self.apply_bubble_gap(self.bubble_gap + 6))
            gap_menu.addAction(act_gup)

            menu.addSeparator()

            # Submenu: Memory & Google Drive Selection
            gdrive_menu = menu.addMenu("☁️ Memori & Sinkronisasi Google Drive")

            self.act_gdrive_sync = QAction("Aktifkan Auto-Sync ke Google Drive", self)
            self.act_gdrive_sync.setCheckable(True)
            self.act_gdrive_sync.setChecked(self.backend.gdrive_sync_enabled)
            self.act_gdrive_sync.triggered.connect(self.backend.set_gdrive_sync_enabled)
            gdrive_menu.addAction(self.act_gdrive_sync)

            gdrive_menu.addSeparator()
            lbl_acc = QAction("Pilih Akun Google Drive:", self)
            lbl_acc.setEnabled(False)
            gdrive_menu.addAction(lbl_acc)

            self.gdrive_group = QActionGroup(self)
            self.gdrive_group.setExclusive(True)
            for acc_name in self.backend.get_gdrive_accounts().keys():
                act_acc = QAction(f"• {acc_name}", self)
                act_acc.setCheckable(True)
                act_acc.setChecked(acc_name == self.backend.gdrive_account)
                act_acc.triggered.connect(lambda checked, a=acc_name: self._select_gdrive_account(a))
                self.gdrive_group.addAction(act_acc)
                gdrive_menu.addAction(act_acc)

            gdrive_menu.addSeparator()

            self.act_gdrive_plugin = QAction("Aktifkan Plugin Google Drive Codex (Cloud Search)", self)
            self.act_gdrive_plugin.setCheckable(True)
            self.act_gdrive_plugin.setChecked(self.backend.enable_gdrive_plugin)
            self.act_gdrive_plugin.triggered.connect(self.backend.set_enable_gdrive_plugin)
            gdrive_menu.addAction(self.act_gdrive_plugin)

            act_open_notes = QAction("Buka Catatan Grimoire (frieren_notes.md)", self)
            act_open_notes.triggered.connect(self._open_notes_file)
            gdrive_menu.addAction(act_open_notes)

            act_restore_gdrive = QAction("Muat Ulang Memori dari Google Drive", self)
            act_restore_gdrive.triggered.connect(self._restore_from_gdrive)
            gdrive_menu.addAction(act_restore_gdrive)

            menu.addSeparator()

            act_pleased = QAction("Sapa Frieren ♪", self)
            act_pleased.triggered.connect(self._pet_frieren)
            menu.addAction(act_pleased)

            act_reset = QAction("Bersihkan Riwayat Chat Sementara", self)
            act_reset.triggered.connect(lambda: self._clear_history(include_ltm=False))
            menu.addAction(act_reset)

            act_reset_all = QAction("Bersihkan Semua Memori (Termasuk LTM)", self)
            act_reset_all.triggered.connect(lambda: self._clear_history(include_ltm=True))
            menu.addAction(act_reset_all)

            act_dock = QAction("Kembalikan ke Pojok Kanan Bawah", self)
            act_dock.triggered.connect(self.dock_bottom_right)
            menu.addAction(act_dock)

            menu.addSeparator()
            act_quit = QAction("Keluar", self)
            act_quit.triggered.connect(QApplication.instance().quit)
            menu.addAction(act_quit)

            self.tray.setContextMenu(menu)
            self.tray.show()

    def _refresh_bubble_history(self) -> None:
        ltm_count = len(self.backend.load_ltm())
        self.bubble.refresh_history(self.backend.load_memory(), ltm_count=ltm_count)

    # ------------------------------------------------------------------
    # Resize / Scale & Idle Multi-Pose Controls
    # ------------------------------------------------------------------
    def apply_scale(self, new_scale: float, save: bool = True, redock: bool = True) -> None:
        self.scale_factor = max(0.70, min(1.50, round(float(new_scale), 2)))

        # Keep bottom-right corner anchored when resizing
        old_geo = self.geometry()
        new_w = int(self.base_win_w * self.scale_factor)
        new_h = int(self.base_win_h * self.scale_factor)
        self.setFixedSize(new_w, new_h)

        bubble_w = max(240, new_w - 22)
        self.bubble.setFixedWidth(bubble_w)
        self.bubble._refresh_header_fit()
        self.bubble._update_msg_scroll_height()
        self.sprite.set_scale_factor(self.scale_factor)

        if hasattr(self, "size_actions"):
            for sc, act in self.size_actions.items():
                act.setChecked(abs(self.scale_factor - sc) < 0.06)

        if redock and old_geo.width() > 0:
            new_x = old_geo.right() - new_w + 1
            new_y = old_geo.bottom() - new_h + 1
            self.move(new_x, new_y)

        if save:
            self.backend.save_ui_prefs(
                self.sound_player.enabled,
                self.bubble.history_enabled,
                output_enabled=self.bubble.output_enabled,
                minimized=self.is_minimized,
                scale=self.scale_factor,
                opacity=self.opacity_level,
            )

    def apply_opacity(self, new_opacity: float, save: bool = True) -> None:
        self.opacity_level = max(0.25, min(1.00, round(float(new_opacity), 2)))
        self.setWindowOpacity(self.opacity_level)
        if hasattr(self, "opacity_actions"):
            for op, act in self.opacity_actions.items():
                act.setChecked(abs(self.opacity_level - op) < 0.06)
        if save:
            self.backend.save_ui_prefs(
                self.sound_player.enabled,
                self.bubble.history_enabled,
                output_enabled=self.bubble.output_enabled,
                minimized=self.is_minimized,
                scale=self.scale_factor,
                opacity=self.opacity_level,
                bubble_gap=self.bubble_gap,
            )

    def apply_bubble_gap(self, new_gap: int, save: bool = True) -> None:
        # Clamp strictly within 0..65px so the bubble always stays close to Frieren!
        self.bubble_gap = max(0, min(65, int(new_gap)))
        if hasattr(self, "bubble_spacer"):
            self.bubble_spacer.setFixedHeight(self.bubble_gap)
        if hasattr(self, "gap_actions"):
            for gp, act in self.gap_actions.items():
                act.setChecked(abs(self.bubble_gap - gp) <= 3)
        if save:
            self.backend.save_ui_prefs(
                self.sound_player.enabled,
                self.bubble.history_enabled,
                output_enabled=self.bubble.output_enabled,
                minimized=self.is_minimized,
                scale=self.scale_factor,
                opacity=self.opacity_level,
                bubble_gap=self.bubble_gap,
            )

    def _on_bubble_drag_delta(self, dy: int) -> None:
        self.apply_bubble_gap(self.bubble_gap + dy, save=False)

    def _on_bubble_drag_finished(self) -> None:
        self.apply_bubble_gap(self.bubble_gap, save=True)

    def _cycle_idle_pose(self) -> None:
        """Gently cycles Frieren's idle pose between various cute expressions."""
        if self._worker and self._worker.isRunning():
            return
        # If Frieren is in a temporary needs pose or normal idle, cycle through normal idle poses
        if not self.sprite.current_state.startswith("idle") and not self.sprite.current_state.startswith("needs_"):
            return
        # Pick a different idle pose smoothly
        choices = [p for p in IDLE_POSES if p != self.sprite.current_state]
        next_pose = random.choice(choices) if choices else "idle"
        self.sprite.set_state(next_pose)
        self.bubble.update_state_badge(next_pose)

    # ------------------------------------------------------------------
    # Minimize & Auto-Hide Bubble Controls
    # ------------------------------------------------------------------
    def minimize_bubble_only(self) -> None:
        """Hides the speech bubble and input bar while keeping Frieren at normal size."""
        self.bubble_hide_timer.stop()
        self.input_box.clearFocus()
        self.bubble.setVisible(False)
        self.input_container.setVisible(False)

    def show_bubble(self) -> None:
        if not self.is_minimized and not self.bubble.isVisible():
            self.bubble.setVisible(True)

    def _toggle_autohide_bubble(self, checked: bool) -> None:
        self.auto_hide_bubble = bool(checked)
        self.config.setdefault("ui", {})["auto_hide_bubble"] = self.auto_hide_bubble
        self.backend.save_config()
        if self.auto_hide_bubble:
            self._schedule_bubble_autohide()
        else:
            self.bubble_hide_timer.stop()
            self.show_bubble()

    def _schedule_bubble_autohide(self) -> None:
        if not self.auto_hide_bubble:
            return
        self.bubble_hide_timer.start(self.bubble_autohide_ms)

    def _on_bubble_autohide_timeout(self) -> None:
        if not self.auto_hide_bubble or self.is_minimized or self._is_context_menu_open():
            if self._is_context_menu_open():
                self._schedule_bubble_autohide()
            return
        # Do not auto-hide if Codex is running, typing is active, input has focus/text, or cursor is inside bubble/input
        if self._worker and self._worker.isRunning():
            self._schedule_bubble_autohide()
            return
        if self.bubble.typing_timer.isActive():
            self._schedule_bubble_autohide()
            return
        if self.input_box.hasFocus() or self.input_box.text().strip() or self.pending_attachments:
            self._schedule_bubble_autohide()
            return
        if self.bubble.history_enabled or self.bubble.output_enabled or self.bubble.needs_enabled:
            self._schedule_bubble_autohide()
            return
        local_cursor = self.mapFromGlobal(QCursor.pos())
        if self.bubble.geometry().contains(local_cursor) or self.input_container.geometry().contains(local_cursor):
            self._schedule_bubble_autohide()
            return
        self.minimize_bubble_only()

    def set_minimized(self, minimized: bool) -> None:
        self.is_minimized = bool(minimized)
        if hasattr(self, "act_minimize"):
            self.act_minimize.setChecked(self.is_minimized)

        if self.is_minimized:
            self.bubble.setVisible(False)
            self.input_container.setVisible(False)
            self.sprite.set_minimized_mode(True)
        else:
            if not self.isVisible():
                self.show()
                if hasattr(self, "act_hide_window"):
                    self.act_hide_window.setChecked(False)
            self.sprite.set_minimized_mode(False)
            self.bubble.setVisible(True)
            self.input_container.setVisible(True)

        self.backend.save_ui_prefs(
            self.sound_player.enabled,
            self.bubble.history_enabled,
            output_enabled=self.bubble.output_enabled,
            minimized=self.is_minimized,
        )

    def _toggle_hide_to_tray(self, hidden: bool) -> None:
        if hidden:
            self.hide()
        else:
            self.show()
            self.raise_()

    # ------------------------------------------------------------------
    # Settings & Menu Callbacks
    # ------------------------------------------------------------------
    def _show_needs_status(self) -> None:
        d = self.needs.data
        status_msg = (
            f"Status Kebutuhan & Kesejahteraan:\n"
            f"• ☕ Kehausan (Thirst): {int(d['thirst'])}%\n"
            f"• 🍰 Kelaparan (Hunger): {int(d['hunger'])}%\n"
            f"• 💤 Energi (Energy): {int(d['energy'])}%\n"
            f"• 🌿 Kesegaran (Freshness): {int(d['freshness'])}%\n\n"
            f"Frieren selalu nyaman menemanimu bekerja ✦"
        )
        self.set_character_state("pleased", status_msg, animate_typing=True, emotion_override="hangat")

    def _fulfill_need(self, need_key: str) -> None:
        reply = self.needs.replenish(need_key)
        self.bubble.update_needs_data(self.needs.data)
        pose_map = {
            "thirst": "needs_tea",
            "hunger": "needs_hungry",
            "energy": "needs_sleepy",
            "freshness": "needs_stretch",
        }
        pose = pose_map.get(need_key, "pleased")
        self.set_character_state(pose, reply, animate_typing=True, emotion_override="senang")

    def _fulfill_all_needs(self) -> None:
        reply = self.needs.replenish_all()
        self.bubble.update_needs_data(self.needs.data)
        self.set_character_state("pleased_wave", reply, animate_typing=True, emotion_override="antusias")

    def _on_needs_tick(self) -> None:
        reminder = self.needs.tick(elapsed_seconds=60.0)
        self.bubble.update_needs_data(self.needs.data)
        # Only notify if Frieren is idle and not typing or chatting
        if reminder and not self.bubble.typing_timer.isActive():
            if not self._worker or not self._worker.isRunning():
                need_key, text, pose = reminder
                # Soft friendly reminder
                self.set_character_state(pose, text, animate_typing=True, emotion_override="penasaran")

    def _switch_engine(self, engine_name: str) -> None:
        self.backend.set_engine(engine_name)
        ok, reason = self.backend.check_engine_prerequisites()
        engine_label = "Antigravity CLI (gemini-3.8-flash)" if engine_name == "antigravity" else "OpenAI Codex CLI (gpt-6-luna)"
        if ok:
            msg = f"Mesin AI dialihkan ke {engine_label} ✦"
            emo = "antusias"
        else:
            msg = f"Beralih ke {engine_label}, namun ada catatan:\n{reason}"
            emo = "tenang"
        self.set_character_state("pleased", msg, animate_typing=True, emotion_override=emo)

    def _check_engine_status_dialog(self) -> None:
        ok, reason = self.backend.check_engine_prerequisites()
        engine_label = "Antigravity CLI" if self.backend.active_engine == "antigravity" else "OpenAI Codex CLI"
        status_txt = f"[{engine_label}]\n{reason}"
        self.set_character_state("pleased", status_txt, animate_typing=True, emotion_override="fokus" if ok else "penasaran")

    def _on_sound_toggled(self, enabled: bool) -> None:
        if hasattr(self, "act_sound"):
            self.act_sound.setChecked(enabled)
        self.backend.save_ui_prefs(enabled, self.bubble.history_enabled, self.bubble.output_enabled, self.is_minimized)

    def _on_history_toggled(self, enabled: bool) -> None:
        if hasattr(self, "act_history"):
            self.act_history.setChecked(enabled)
        if enabled:
            self._refresh_bubble_history()
        self.backend.save_ui_prefs(self.sound_player.enabled, enabled, self.bubble.output_enabled, self.is_minimized)

    def _on_output_toggled(self, enabled: bool) -> None:
        if hasattr(self, "act_output"):
            self.act_output.setChecked(enabled)
        self.backend.save_ui_prefs(self.sound_player.enabled, self.bubble.history_enabled, enabled, self.is_minimized)

    def _on_needs_toggled(self, enabled: bool) -> None:
        if hasattr(self, "act_status_needs"):
            self.act_status_needs.setChecked(enabled)
        if enabled:
            self.bubble.update_needs_data(self.needs.data)
        self.config.setdefault("ui", {})["needs_enabled"] = bool(enabled)
        self.backend.save_config()

    def _on_agent_toggled(self, enabled: bool) -> None:
        if hasattr(self, "act_agent"):
            self.act_agent.setChecked(enabled)
        self.backend.set_agent_execution_enabled(enabled)
        mode_msg = (
            "Mode Eksekusi Codex (⚡) diaktifkan. Aku sekarang bisa membuka web dan menjalankan perintah untukmu."
            if enabled
            else "Mode Eksekusi Codex (⚡) dimatikan (Read-Only). Aku hanya akan mengobrol dan menganalisis dengan aman."
        )
        self.set_character_state("pleased", mode_msg, animate_typing=True)

    def _toggle_sound_from_menu(self, checked: bool) -> None:
        self.bubble.set_sound_enabled(checked)
        self._on_sound_toggled(checked)

    def _toggle_history_from_menu(self, checked: bool) -> None:
        if checked:
            self._refresh_bubble_history()
        self.bubble.set_history_enabled(checked)
        self._on_history_toggled(checked)

    def _toggle_output_from_menu(self, checked: bool) -> None:
        self.bubble.set_output_enabled(checked)
        self._on_output_toggled(checked)

    def _toggle_agent_from_menu(self, checked: bool) -> None:
        self.bubble.set_agent_enabled(checked)
        self._on_agent_toggled(checked)

    def _toggle_needs_from_menu(self, checked: bool) -> None:
        self.bubble.set_needs_enabled(checked)
        self._on_needs_toggled(checked)

    def _select_gdrive_account(self, account: str) -> None:
        status = self.backend.set_gdrive_account(account)
        if self.is_minimized:
            self.set_minimized(False)
        self.set_character_state("pleased", f"Akun Google Drive diatur ke {account}. ({status})", animate_typing=True)

    def _open_notes_file(self) -> None:
        if not self.backend.notes_path.exists():
            self.backend._write_markdown_notes(self.backend.load_ltm())
        if sys.platform == "win32":
            os.startfile(str(self.backend.notes_path))
        else:
            subprocess.Popen(["open", str(self.backend.notes_path)])

    def _restore_from_gdrive(self) -> None:
        status = self.backend.restore_from_gdrive()
        self._refresh_bubble_history()
        if self.is_minimized:
            self.set_minimized(False)
        self.set_character_state("pleased", status, animate_typing=True)

    # ------------------------------------------------------------------
    # Window Positioning & Dynamic Click-Through
    # ------------------------------------------------------------------
    def dock_bottom_right(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        avail: QRect = screen.availableGeometry()
        x = avail.right() - self.width() - self.margin_right
        y = avail.bottom() - self.height() - self.margin_bottom
        self.move(x, y)

    def _interactive_region(self) -> QRegion:
        region = QRegion()
        if self.bubble.isVisible():
            region = region.united(QRegion(self.bubble.geometry()))
        if self.attachment_bar.isVisible():
            region = region.united(QRegion(self.attachment_bar.geometry()))
        if self.input_container.isVisible():
            region = region.united(QRegion(self.input_container.geometry()))

        sprite_reg = self.sprite.opaque_region().translated(self.sprite.pos())
        region = region.united(sprite_reg)
        return region

    def _is_context_menu_open(self) -> bool:
        if QApplication.activePopupWidget() is not None:
            return True
        if hasattr(self, "tray") and self.tray.contextMenu() and self.tray.contextMenu().isVisible():
            return True
        return False

    def _update_mask_and_clickthrough(self) -> None:
        if not self.isVisible():
            return
        # Never toggle window flags while a right-click popup menu is open (otherwise self.show() closes the menu!)
        if self._is_context_menu_open():
            return
        region = self._interactive_region()
        local_cursor = self.mapFromGlobal(QCursor.pos())
        inside_interactive = region.contains(local_cursor)

        transparent_for_input = bool(self.windowFlags() & Qt.WindowType.WindowTransparentForInput)
        if not inside_interactive and not self.input_box.hasFocus():
            if not transparent_for_input:
                self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, True)
                self.show()
        else:
            if transparent_for_input:
                self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
                self.show()

    def _set_manual_emotion(self, emotion_key: str) -> None:
        self.bubble.set_emotion(emotion_key)
        pose_for_emotion = {
            "tenang": "idle",
            "hangat": "idle_cozy",
            "senang": "pleased",
            "ceria": "idle_dancing",
            "antusias": "pleased_wave",
            "penasaran": "thinking_tilt",
            "fokus": "idle_reading",
            "tersentuh": "pleased",
            "nostalgia": "thinking_lookup",
            "mengantuk": "idle_sleepy",
        }.get(emotion_key, "idle")
        self.sprite.set_state(pose_for_emotion)
        self.bubble.update_state_badge(pose_for_emotion, emotion_override=emotion_key)
        self.show_bubble()
        self._schedule_bubble_autohide()

    def set_character_state(
        self,
        state: str,
        message: Optional[str] = None,
        animate_typing: bool = False,
        emotion_override: Optional[str] = None,
    ) -> None:
        self.sprite.set_state(state)
        if state == "thinking" and message is None:
            self.show_bubble()
            self.bubble_hide_timer.stop()
            self.bubble.show_loading()
        elif message is not None:
            self.show_bubble()
            self.bubble_hide_timer.stop()
            self.bubble.show_message(
                message,
                state=state,
                animate=animate_typing,
                emotion_override=emotion_override,
            )
        else:
            self.bubble.update_state_badge(state, emotion_override=emotion_override)

    def _on_typing_finished(self) -> None:
        if (
            self.sprite.current_state in TALKING_POSES
            or self.sprite.current_state.startswith("talking")
            or self.sprite.current_state.startswith("needs_")
        ):
            self._next_scheduled_state = "pleased"
            self.state_timer.start(self.talking_hold_ms)
        else:
            self._schedule_bubble_autohide()

    def _on_state_timer(self) -> None:
        if self._next_scheduled_state == "pleased":
            pleased_pose = random.choice(PLEASED_POSES)
            # Keep the current conversation emotion while holding the pleased smile after talking
            self.set_character_state(pleased_pose, emotion_override=self.bubble.current_emotion_key)
            self._next_scheduled_state = "idle"
            self.state_timer.start(self.pleased_hold_ms)
        else:
            idle_pose = random.choice(IDLE_POSES)
            self.set_character_state(idle_pose)
            self._schedule_bubble_autohide()

    def toggle_input_bar(self) -> None:
        if not self.isVisible():
            self._toggle_hide_to_tray(False)
        if self.is_minimized:
            self.set_minimized(False)
            self.show_input_bar()
            return
        if self.input_container.isVisible() and self.input_box.hasFocus():
            self.hide_input_bar()
        else:
            self.show_bubble()
            self.show_input_bar()

    def show_input_bar(self) -> None:
        if bool(self.windowFlags() & Qt.WindowType.WindowTransparentForInput):
            self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
            self.show()
        self.show_bubble()
        self.bubble_hide_timer.stop()
        self.input_container.setVisible(True)
        self.raise_()
        self.activateWindow()
        self.input_box.setFocus()

    def hide_input_bar(self) -> None:
        self.input_box.clearFocus()
        self.input_container.setVisible(False)
        self._schedule_bubble_autohide()

    def _pet_frieren(self) -> None:
        if self.is_minimized:
            self.set_minimized(False)
            return
        self.state_timer.stop()
        # Pick a random line from 36 varied quotes (never repeating the same one twice in a row)
        candidates = [i for i in range(len(PET_QUOTES)) if i != self._last_pet_idx]
        idx = random.choice(candidates)
        self._last_pet_idx = idx
        quote = PET_QUOTES[idx]

        # Pick a varied happy/cozy pose & warm emotion when clicked
        pose = random.choice(PLEASED_POSES)
        pet_emotion = random.choice(("senang", "tersentuh", "hangat", "ceria"))
        self.set_character_state(
            pose,
            quote,
            animate_typing=True,
            emotion_override=pet_emotion,
        )
        self._next_scheduled_state = "idle"
        self.state_timer.start(self.pleased_hold_ms)

    def _clear_history(self, include_ltm: bool = False) -> None:
        self.backend.clear_memory(include_ltm=include_ltm)
        self._refresh_bubble_history()
        msg = (
            "Semua riwayat chat dan catatan grimoire jangka panjang sudah kubersihkan."
            if include_ltm
            else "Riwayat chat sementara sudah kubersihkan, tapi catatan pentingmu tetap tersimpan aman."
        )
        self.set_character_state("pleased", msg, animate_typing=True)
        self._next_scheduled_state = "idle"
        self.state_timer.start(self.pleased_hold_ms)

    # ------------------------------------------------------------------
    # Image Clipboard Paste (Cmd+V) & File/Image Drag-and-Drop Support
    # ------------------------------------------------------------------
    def _refresh_attachment_bar(self) -> None:
        if not self.pending_attachments:
            self.attachment_bar.setVisible(False)
            return
        chips: List[str] = []
        for p in self.pending_attachments:
            path_obj = Path(p)
            icon = "🖼️" if self.backend._is_image_path(p) else "📄"
            name = path_obj.name
            if len(name) > 20:
                name = name[:17] + "..."
            chips.append(f"{icon} {name}")
        summary = " · ".join(chips)
        self.attachment_label.setText(summary)
        self.attachment_label.setToolTip("Lampiran siap dikirim:\n" + "\n".join(self.pending_attachments))
        self.attachment_bar.setVisible(True)

    def clear_attachments(self) -> None:
        self.pending_attachments.clear()
        self._refresh_attachment_bar()

    def _add_attachment_path(self, path_str: str) -> None:
        clean = path_str.strip()
        if not clean or not Path(clean).exists():
            return
        if clean not in self.pending_attachments:
            self.pending_attachments.append(clean)
        self.show_input_bar()
        self._refresh_attachment_bar()

    def _on_image_pasted(self, img_obj) -> None:
        """Saves a pasted QImage/QPixmap from macOS clipboard into a PNG file and attaches it quietly."""
        try:
            from datetime import datetime as _dt

            ts = _dt.now().strftime("%Y%m%d_%H%M%S_%f")
            out_file = self.clipboard_dir / f"gambar_{ts}.png"
            saved = img_obj.save(str(out_file), "PNG")
            if saved and out_file.exists():
                self._add_attachment_path(str(out_file))
        except Exception:
            pass

    def _on_files_dropped(self, paths: list) -> None:
        for raw_p in paths:
            p_str = str(raw_p).strip()
            if p_str and Path(p_str).exists():
                self._add_attachment_path(p_str)

    def _pick_attachments_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Pilih Gambar atau File untuk Frieren",
            str(Path.home()),
            "Semua File (*.*);;Gambar (*.png *.jpg *.jpeg *.webp *.gif)",
        )
        if files:
            self._on_files_dropped(files)

    def dragEnterEvent(self, event) -> None:
        md = event.mimeData()
        if md and (md.hasUrls() or md.hasImage()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        md = event.mimeData()
        if md:
            if md.hasImage():
                img = md.imageData()
                if img is not None:
                    self._on_image_pasted(img)
                    event.acceptProposedAction()
                    return
            if md.hasUrls():
                local_paths = [u.toLocalFile() for u in md.urls() if u.isLocalFile()]
                if local_paths:
                    self._on_files_dropped(local_paths)
                    event.acceptProposedAction()
                    return
        super().dropEvent(event)

    def send_message(self) -> None:
        text = self.input_box.text().strip()
        attachments = list(self.pending_attachments)

        # Also support raw pasted file paths inside the text box (e.g. `/Users/user/file.png`)
        for token in re.findall(r"(/Users/[^\s\"']+)", text):
            if Path(token).exists() and token not in attachments:
                attachments.append(token)

        if not text and not attachments:
            return
        if self._worker and self._worker.isRunning():
            return

        self.input_box.clear()
        self.clear_attachments()
        self.input_box.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.attach_btn.setEnabled(False)
        self.state_timer.stop()

        # Determine initial activity status & sprite pose:
        # Normal questions/greetings ONLY use soft thinking poses (`thinking`, `thinking_lookup`, `thinking_tilt`, `thinking_hmmm`).
        # `action_laptop` and `action_magic` are strictly reserved for explicit web/search or CLI/file/attachment execution!
        low = text.lower()
        has_image_att = any(self.backend._is_image_path(a) for a in attachments)
        has_file_att = bool(attachments) and not has_image_att
        is_web_request = bool(
            re.search(r"\b(https?://|www\.|buka\s+web|bukakan|cari\s+di\s+web|search|browsing|situs|website)\b", low)
        )
        is_agent_cli_request = bool(
            re.search(r"\b(cek\s+file|cek\s+folder|baca\s+file|git\s+|jalankan|eksekusi|terminal|script|coding|buatkan\s+file)\b", low)
        )

        if has_image_att:
            init_status = "Sedang mengamati gambar yang kamu kirimkan... 🖼️✦"
            init_pose = "thinking_tilt"
        elif has_file_att:
            init_status = "Sedang membuka grimoire untuk memeriksa filemu... 📄✦"
            init_pose = "action_magic"
        elif is_web_request:
            init_status = "Sedang membuka laptop & menelusuri web untukmu... 💻"
            init_pose = "action_laptop"
        elif is_agent_cli_request:
            init_status = "Sedang membuka buku grimoire & tongkat sihir... ✦"
            init_pose = "action_magic"
        else:
            init_status = random.choice(CUTE_THINKING_LINES)
            init_pose = random.choice(THINKING_POSES)

        self.sprite.set_state(init_pose)
        self.bubble.show_loading(init_status)
        self.bubble.update_state_badge(init_pose)

        self._worker = CodexWorker(self.backend, text, attachments=attachments, parent=self)
        self._worker.status_update.connect(self._on_worker_status_update)
        self._worker.finished_result.connect(self._on_codex_result)
        self._worker.start()

    def _on_worker_status_update(self, status_text: str) -> None:
        self.bubble.update_loading_status(status_text)
        s_low = status_text.lower()
        if any(k in s_low for k in ("membuka web", "membaca halaman", "mengintip halaman web", "mengambil data dari web")):
            self.sprite.set_state("action_laptop")
            self.bubble.update_state_badge("action_laptop")
        elif any(k in s_low for k in ("melihat isi folder", "membaca isi file", "memeriksa repositori", "menjalankan proses", "mencari file", "memproses:")):
            self.sprite.set_state("action_magic")
            self.bubble.update_state_badge("action_magic")
        else:
            # Normal reasoning/thinking step -> rotate among soft thinking poses only
            if not self.sprite.current_state.startswith("action_"):
                pose = random.choice(THINKING_POSES)
                self.sprite.set_state(pose)
                self.bubble.update_state_badge(pose)

    @staticmethod
    def _infer_emotion_from_text(speech: str) -> str:
        low = speech.lower()
        if any(w in low for w in ("ulang tahun", "terima kasih", "makasih", "sayang", "bangga", "🤍", "senang bisa")):
            return "tersentuh"
        if any(w in low for w in ("hehe", "♪", "asyik", "hore", "selamat")):
            return "ceria"
        if any(w in low for w in ("himmel", "dulu", "ribuan tahun", "kenangan", "masa lalu")):
            return "nostalgia"
        if any(w in low for w in ("teh", "hangat", "syal", "istirahat", "nyaman", "santai")):
            return "hangat"
        if any(w in low for w in ("kantuk", "tidur", "malas", "lelah")):
            return "mengantuk"
        if any(w in low for w in ("sudah kubukakan", "berhasil", "selesai", "siap", "ayo")):
            return "antusias"
        if any(w in low for w in ("menarik", "kira-kira", "coba kita", "penasaran")):
            return "penasaran"
        return "senang"

    def _on_codex_result(self, result: CodexResult) -> None:
        self.input_box.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.attach_btn.setEnabled(True)
        if self.input_container.isVisible():
            self.input_box.setFocus()

        self._refresh_bubble_history()

        # Update console output in background; ONLY visible if user toggled 💻 open
        self.bubble.set_cli_output(result.cli_output)

        emotion = result.emotion or self._infer_emotion_from_text(result.speech)
        talk_pose = random.choice(("talking", "talking_explain"))
        self.set_character_state(
            talk_pose,
            result.speech,
            animate_typing=True,
            emotion_override=emotion,
        )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._press_pos = event.globalPosition().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            if hasattr(self, "tray") and self.tray.contextMenu():
                self.tray.contextMenu().popup(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_offset is not None:
            dist = (event.globalPosition().toPoint() - self._press_pos).manhattanLength()
            self._drag_offset = None
            if dist < 6 and self.sprite.geometry().contains(event.position().toPoint()):
                self._pet_frieren()

    def wheelEvent(self, event) -> None:
        """Hold Cmd + Scroll to resize, or Option (Alt) + Scroll to adjust Opacity."""
        mods = event.modifiers()
        delta = event.angleDelta().y()
        if mods & Qt.KeyboardModifier.ControlModifier:  # Command key on macOS Qt
            if delta > 0:
                self.apply_scale(self.scale_factor + 0.06)
            elif delta < 0:
                self.apply_scale(self.scale_factor - 0.06)
            event.accept()
            return
        if mods & Qt.KeyboardModifier.AltModifier:  # Option key on macOS Qt
            if delta > 0:
                self.apply_opacity(self.opacity_level + 0.06)
            elif delta < 0:
                self.apply_opacity(self.opacity_level - 0.06)
            event.accept()
            return
        if mods & Qt.KeyboardModifier.ShiftModifier:  # Shift + Scroll adjusts Bubble Gap
            if delta > 0:
                self.apply_bubble_gap(self.bubble_gap + 4)
            elif delta < 0:
                self.apply_bubble_gap(self.bubble_gap - 4)
            event.accept()
            return
        super().wheelEvent(event)


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    app = QApplication(sys.argv)
    app.setApplicationName("Frieren Desk")
    app.setQuitOnLastWindowClosed(False)

    window = FrierenDeskWindow(base_dir)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
