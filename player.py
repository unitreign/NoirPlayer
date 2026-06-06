import sys
import os
import json
import threading
import platform
from pathlib import Path

# ---------------------------------------------------------------------------
# Platform-aware mpv setup
# ---------------------------------------------------------------------------
MPV_DIR = Path(__file__).parent / "mpv"
NOIR_IMG = Path(__file__).parent / "noir.png"

_SYS = platform.system()  # "Windows" | "Linux" | "Darwin"

if _SYS == "Windows":
    _MPV_DLL = MPV_DIR / "mpv-2.dll"
    if not _MPV_DLL.exists():
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            _app = QApplication(sys.argv)
            QMessageBox.critical(
                None, "NoirPlayer – Missing mpv",
                "mpv-2.dll not found in the mpv\\ folder.\n\n"
                "See README for setup instructions."
            )
        except Exception:
            pass
        sys.exit(1)
    os.environ["PATH"] = str(MPV_DIR) + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(MPV_DIR))

import mpv  # type: ignore  # noqa: E402

# ---------------------------------------------------------------------------
# Fonts folder
# ---------------------------------------------------------------------------
FONTS_DIR = Path(__file__).parent / "fonts"
FONTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Dev logger (activated by NOIRPLAYER_DEV=1 env var)
# ---------------------------------------------------------------------------
_FLOG = Path(__file__).parent / "dev.log"
_DEV  = os.environ.get("NOIRPLAYER_DEV") == "1"

def flog(msg: str):
    if not _DEV:
        return
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    try:
        with open(_FLOG, "a", encoding="utf-8") as f:
            f.write(f"{ts}  {msg}\n")
    except Exception:
        pass

if _DEV:
    try:
        _FLOG.write_text(f"=== NoirPlayer dev.log  platform={_SYS} ===\n", encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Qt
# ---------------------------------------------------------------------------
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QComboBox, QFrame, QSizePolicy,
    QMessageBox, QLineEdit, QDialog, QSlider, QGroupBox, QTabWidget,
    QColorDialog, QCheckBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread, QUrl
from PyQt6.QtGui import (
    QKeyEvent, QDragEnterEvent, QDropEvent, QKeySequence, QColor,
    QPainter, QFont, QPainterPath, QPen, QFontDatabase, QDesktopServices,
    QCursor, QPixmap, QLinearGradient,
)

# ---------------------------------------------------------------------------
# Load bundled fonts
# ---------------------------------------------------------------------------
def _load_fonts_dir() -> dict[str, str]:
    loaded: dict[str, str] = {}
    for ext in ("*.ttf", "*.otf", "*.TTF", "*.OTF"):
        for f in FONTS_DIR.glob(ext):
            fid = QFontDatabase.addApplicationFont(str(f))
            if fid >= 0:
                for fam in QFontDatabase.applicationFontFamilies(fid):
                    loaded[fam] = str(f)
    return loaded

_BUNDLED_FONTS: dict[str, str] = {}

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
SETTINGS_PATH = Path(__file__).parent / "settings.json"
APP_VERSION   = "1.0"

DEFAULT_SETTINGS: dict = {
    # keybindings
    "key_swap":        "Tab",
    "key_swap_alt":    "S",
    "key_pause":       "Space",
    "key_seek_back":   "Left",
    "key_seek_fwd":    "Right",
    "key_fullscreen":  "F",
    "key_quit":        "Escape",
    # font
    "sub_font_mode":   "default",
    "sub_font":        "",
    "sub_font_path":   "",
    # subtitle appearance
    "sub_font_size":   40,
    "sub_pos":         90,
    "sub_color":       "#FFFFFF",
    "sub_border":      2.5,
    "sub_bold":        False,
    "sub_italic":      False,
    "sub_shadow":      1,
}

def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            return {**DEFAULT_SETTINGS, **json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)

def save_settings(s: dict):
    try:
        SETTINGS_PATH.write_text(json.dumps(s, indent=2), encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Colour scheme
# ---------------------------------------------------------------------------
DARK_BG    = "#0c0c0c"
DARK_CARD  = "#191919"
ACCENT     = "#b8b8b8"
ACCENT_HI  = "#e0e0e0"
TEXT       = "#dcdcdc"
DIM_TEXT   = "#5a5a5a"
BTN_BG     = "#202020"
BTN_HOVER  = "#2a2a2a"
BORDER_CLR = "#2e2e2e"

STYLESHEET = f"""
QWidget {{
    background-color: {DARK_BG};
    color: {TEXT};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QLabel {{ background-color: transparent; }}
QFrame#card {{
    background-color: {DARK_CARD};
    border: 1px solid {BORDER_CLR};
    border-radius: 8px;
}}
QGroupBox {{
    background-color: {DARK_CARD};
    border: 1px solid {BORDER_CLR};
    border-radius: 8px;
    margin-top: 20px;
    padding: 12px 8px 8px 8px;
    color: {ACCENT};
    font-weight: bold;
    letter-spacing: 1px;
    font-size: 11px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; }}
QTabWidget::pane {{
    border: 1px solid {BORDER_CLR};
    background: {DARK_BG};
    border-radius: 0 4px 4px 4px;
}}
QTabBar::tab {{
    background: {BTN_BG};
    color: {DIM_TEXT};
    padding: 8px 22px;
    border: 1px solid {BORDER_CLR};
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {DARK_CARD};
    color: {ACCENT_HI};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{ background: {BTN_HOVER}; color: {TEXT}; }}
QPushButton {{
    background-color: {BTN_BG};
    color: {TEXT};
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 7px 16px;
}}
QPushButton:hover {{ background-color: {BTN_HOVER}; border-color: {ACCENT}; }}
QPushButton:disabled {{ color: #383838; border-color: #252525; }}
QPushButton#accent {{
    background-color: {ACCENT};
    color: #0c0c0c;
    font-weight: bold;
    border: none;
    letter-spacing: 1px;
}}
QPushButton#accent:hover {{ background-color: {ACCENT_HI}; }}
QPushButton#accent:disabled {{ background-color: #383838; color: #555; }}
QPushButton#keycap {{
    background-color: #141414;
    color: {ACCENT};
    border: 1px solid {ACCENT};
    border-radius: 6px;
    padding: 6px 16px;
    font-family: 'Consolas', monospace;
    font-weight: bold;
    min-width: 90px;
}}
QPushButton#keycap:checked {{ background-color: {ACCENT}; color: #0c0c0c; }}
QPushButton#swatch {{
    border-radius: 4px;
    border: 2px solid #444;
    min-width: 52px; max-width: 52px;
    min-height: 22px; max-height: 22px;
}}
QComboBox {{
    background-color: {BTN_BG};
    color: {TEXT};
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 5px 10px;
    combobox-popup: 0;
}}
QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background-color: {DARK_CARD};
    color: {TEXT};
    selection-background-color: #2e2e2e;
    border: 1px solid {BORDER_CLR};
}}
QLineEdit {{
    background-color: {BTN_BG};
    color: {TEXT};
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 6px 10px;
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QSlider::groove:horizontal {{
    height: 3px; background: #333; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT}; width: 13px; height: 13px;
    margin: -5px 0; border-radius: 7px;
}}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 15px; height: 15px;
    border: 1px solid #484848;
    border-radius: 3px;
    background: {BTN_BG};
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QLabel#title {{
    color: {ACCENT_HI};
    font-size: 26px;
    font-weight: bold;
    letter-spacing: 6px;
}}
QLabel#subtitle  {{ color: {DIM_TEXT}; font-size: 10px; letter-spacing: 3px; }}
QLabel#sectionhead {{ color: {ACCENT}; font-size: 10px; font-weight: bold; letter-spacing: 1px; }}
QLabel#filepath  {{ color: {DIM_TEXT}; font-size: 11px; }}
QLabel#dimtext   {{ color: {DIM_TEXT}; font-size: 11px; }}
QLabel#val       {{ color: {ACCENT}; font-size: 11px; font-family: Consolas; min-width: 44px; }}
QLabel#fontname  {{
    color: {TEXT};
    background: {BTN_BG};
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}}
QLabel#srtname   {{
    color: {DIM_TEXT};
    font-size: 11px;
    font-style: italic;
}}
"""

def make_card() -> QFrame:
    f = QFrame(); f.setObjectName("card"); return f

# ---------------------------------------------------------------------------
# BCP-47 language expansion
# ---------------------------------------------------------------------------
_LANG = {
    "af":"Afrikaans","ar":"Arabic","az":"Azerbaijani","be":"Belarusian",
    "bg":"Bulgarian","bn":"Bengali","bs":"Bosnian","ca":"Catalan",
    "cs":"Czech","cy":"Welsh","da":"Danish","de":"German","el":"Greek",
    "en":"English","eo":"Esperanto","es":"Spanish","et":"Estonian",
    "eu":"Basque","fa":"Persian","fi":"Finnish","fil":"Filipino",
    "fr":"French","ga":"Irish","gl":"Galician","gu":"Gujarati",
    "he":"Hebrew","hi":"Hindi","hr":"Croatian","hu":"Hungarian",
    "hy":"Armenian","id":"Indonesian","is":"Icelandic","it":"Italian",
    "ja":"Japanese","ka":"Georgian","kk":"Kazakh","km":"Khmer",
    "kn":"Kannada","ko":"Korean","lt":"Lithuanian","lv":"Latvian",
    "mk":"Macedonian","ml":"Malayalam","mn":"Mongolian","mr":"Marathi",
    "ms":"Malay","mt":"Maltese","my":"Burmese","nb":"Norwegian",
    "ne":"Nepali","nl":"Dutch","pa":"Punjabi","pl":"Polish",
    "pt":"Portuguese","ro":"Romanian","ru":"Russian","si":"Sinhala",
    "sk":"Slovak","sl":"Slovenian","sq":"Albanian","sr":"Serbian",
    "sv":"Swedish","sw":"Swahili","ta":"Tamil","te":"Telugu",
    "th":"Thai","tr":"Turkish","uk":"Ukrainian","ur":"Urdu",
    "uz":"Uzbek","vi":"Vietnamese","zh":"Chinese","zu":"Zulu",
}
_REGION = {
    "419":"Latin Am.","BR":"Brazilian","CA":"Canadian","Hans":"Simplified",
    "Hant":"Traditional","US":"US","GB":"British","AU":"Australian",
}

def lang_display(tag: str) -> str:
    if not tag: return "Unknown"
    parts = tag.replace("_", "-").split("-")
    name  = _LANG.get(parts[0].lower(), parts[0].upper())
    return f"{name} ({_REGION.get(parts[1], parts[1])})" if len(parts) > 1 else name

# ---------------------------------------------------------------------------
# Keyword matching
# ---------------------------------------------------------------------------
def keyword_score(label: str, kws: list[str]) -> int:
    lo = label.lower()
    return sum(1 for kw in kws if kw and kw in lo)

def auto_select_track(tracks: list[dict], kws: list[str]) -> int | None:
    if not kws or not tracks: return None
    scored = [(keyword_score(t["label"], kws), i) for i, t in enumerate(tracks)]
    best, idx = max(scored)
    return (idx + 1) if best > 0 else None

# ---------------------------------------------------------------------------
# mpv subtitle probe
# ---------------------------------------------------------------------------
def _probe_via_mpv(filepath: str) -> list[dict]:
    tracks = []
    flog(f"[PROBE] start {filepath!r}")
    try:
        ready  = threading.Event()
        player = mpv.MPV(vo="null", ao="null")
        flog("[PROBE] mpv created")

        @player.event_callback("file-loaded")
        def _l(_e): flog("[PROBE] file-loaded"); ready.set()
        @player.event_callback("end-file")
        def _e(_e): flog("[PROBE] end-file"); ready.set()

        player.play(filepath)
        ready.wait(timeout=8.0)
        flog("[PROBE] wait done")

        for t in (player.track_list or []):
            if t.get("type") != "sub": continue
            idx   = t.get("id", "?")
            lang  = t.get("lang") or ""
            title = t.get("title") or ""
            name  = lang_display(lang)
            label = f"{name}  – {title}" if title else name
            tracks.append({"id": idx, "label": label})
            flog(f"[PROBE]   {idx}: {label!r}")

        player.terminate()
        flog(f"[PROBE] done  {len(tracks)} tracks")
    except Exception as e:
        flog(f"[PROBE] EXCEPTION: {e}")
    return tracks


class ProbeWorker(QObject):
    finished = pyqtSignal(list)
    error    = pyqtSignal(str)
    def __init__(self, filepath):
        super().__init__(); self.filepath = filepath
    def run(self):
        try:
            self.finished.emit(_probe_via_mpv(self.filepath))
        except Exception as e:
            self.error.emit(str(e))

# ---------------------------------------------------------------------------
# Subtitle preview widget
# ---------------------------------------------------------------------------
PREVIEW_TEXT = "The city never sleeps. Neither do I."

class SubPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(150)
        self.setMinimumWidth(300)
        self._fam    = ""
        self._size   = 40
        self._bold   = False
        self._italic = False
        self._color  = QColor("#FFFFFF")
        self._border = 2.5
        self._pos    = 90

    def apply(self, s: dict):
        mode         = s.get("sub_font_mode", "default")
        self._fam    = s.get("sub_font", "") if mode == "custom" else ""
        self._size   = s.get("sub_font_size", 40)
        self._bold   = s.get("sub_bold", False)
        self._italic = s.get("sub_italic", False)
        self._color  = QColor(s.get("sub_color", "#FFFFFF"))
        self._border = float(s.get("sub_border", 2.5))
        self._pos    = int(s.get("sub_pos", 90))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.fillRect(self.rect(), QColor("#0d0d0d"))
        p.setPen(QPen(QColor("#2a2a2a"), 1))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        p.setPen(QColor("#2a2a2a"))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(self.rect().adjusted(6, 4, 0, 0),
                   Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, "PREVIEW")

        scale   = self.height() / 720.0
        px_size = max(10, int(self._size * scale * 2.8))
        font    = QFont(self._fam if self._fam else "Segoe UI")
        font.setPixelSize(px_size)
        font.setBold(self._bold)
        font.setItalic(self._italic)
        p.setFont(font)

        fm     = p.fontMetrics()
        text_w = fm.horizontalAdvance(PREVIEW_TEXT)
        x      = max(8, (self.width() - text_w) // 2)
        usable = self.height() - fm.height() - 20
        y      = 10 + int(usable * self._pos / 100) + fm.ascent()

        border_px = self._border * scale * 3.0
        if border_px > 0.3:
            path = QPainterPath()
            path.addText(x, y, font, PREVIEW_TEXT)
            pen = QPen(QColor("#000000"), border_px * 2)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.strokePath(path, pen)
            p.fillPath(path, self._color)
        else:
            p.setPen(self._color)
            p.drawText(x, y, PREVIEW_TEXT)
        p.end()

# ---------------------------------------------------------------------------
# Key capture button
# ---------------------------------------------------------------------------
class KeyCaptureButton(QPushButton):
    key_captured = pyqtSignal(str)

    def __init__(self, key_name: str, parent=None):
        super().__init__(key_name, parent)
        self.setObjectName("keycap")
        self.setCheckable(True)
        self._key_name = key_name
        self.clicked.connect(self._on_click)

    def _on_click(self):
        if self.isChecked():
            self.setText("Press a key…")
            self.grabKeyboard()
        else:
            self.releaseKeyboard()
            self.setText(self._key_name)

    def keyPressEvent(self, e: QKeyEvent):
        if not self.isChecked():
            return super().keyPressEvent(e)
        k = e.key()
        if k in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return
        self._key_name = QKeySequence(k).toString()
        self.setText(self._key_name)
        self.setChecked(False)
        self.releaseKeyboard()
        self.key_captured.emit(self._key_name)

    @property
    def key_name(self): return self._key_name

# ---------------------------------------------------------------------------
# Settings dialog
# ---------------------------------------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(540)
        self._s = dict(settings)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(12)

        tabs = QTabWidget()
        root.addWidget(tabs)
        tabs.addTab(self._make_keys_tab(),  "Key Bindings")
        tabs.addTab(self._make_subs_tab(),  "Subtitles")
        tabs.addTab(self._make_about_tab(), "About")

        btns = QHBoxLayout(); btns.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        save   = QPushButton("  Save  "); save.setObjectName("accent")
        save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save)
        root.addLayout(btns)

    # ── Keys tab ─────────────────────────────────────────────────────────
    def _make_keys_tab(self) -> QWidget:
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        note = QLabel("Click a button, then press any key to rebind.")
        note.setObjectName("dimtext")
        lay.addWidget(note)

        # Switch group
        switch_grp = QGroupBox("SWITCH VERSIONS")
        sg = QVBoxLayout(switch_grp); sg.setSpacing(8)
        self._key_swap     = self._keybind_row(sg, "Primary:",   "key_swap")
        self._key_swap_alt = self._keybind_row(sg, "Alternate:", "key_swap_alt")
        lay.addWidget(switch_grp)

        # Playback group
        play_grp = QGroupBox("PLAYBACK")
        pg = QVBoxLayout(play_grp); pg.setSpacing(8)
        self._key_pause      = self._keybind_row(pg, "Play / Pause:", "key_pause")
        self._key_seek_back  = self._keybind_row(pg, "Seek Back:",    "key_seek_back")
        self._key_seek_fwd   = self._keybind_row(pg, "Seek Forward:", "key_seek_fwd")
        self._key_fullscreen = self._keybind_row(pg, "Fullscreen:",   "key_fullscreen")
        self._key_quit       = self._keybind_row(pg, "Quit / Exit:",  "key_quit")
        lay.addWidget(play_grp)

        lay.addStretch()
        return w

    def _keybind_row(self, layout, label: str, setting_key: str) -> KeyCaptureButton:
        row = QHBoxLayout()
        lbl = QLabel(label); lbl.setFixedWidth(110)
        btn = KeyCaptureButton(self._s.get(setting_key, ""))
        btn.key_captured.connect(lambda k, sk=setting_key: self._s.update({sk: k}))
        row.addWidget(lbl); row.addWidget(btn); row.addStretch()
        layout.addLayout(row)
        return btn

    # ── Subtitles tab ────────────────────────────────────────────────────
    def _make_subs_tab(self) -> QWidget:
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        self._preview = SubPreviewWidget()
        self._preview.apply(self._s)
        lay.addWidget(self._preview)

        grp = QGroupBox("APPEARANCE")
        g   = QVBoxLayout(grp); g.setSpacing(10)

        # Font sub-group
        font_grp = QGroupBox("FONT")
        fg = QVBoxLayout(font_grp); fg.setSpacing(8)

        self._font_name_lbl = QLabel(self._font_label())
        self._font_name_lbl.setObjectName("fontname")
        fg.addWidget(self._font_name_lbl)

        font_btns = QHBoxLayout(); font_btns.setSpacing(8)
        for text, slot in [("Default", self._font_use_default),
                            ("Browse TTF / OTF…", self._font_browse),
                            ("Reset", self._font_use_default)]:
            b = QPushButton(text); b.clicked.connect(slot)
            font_btns.addWidget(b)
        font_btns.addStretch()
        fg.addLayout(font_btns)

        note = QLabel("Fonts in the fonts/ folder are loaded automatically on startup.")
        note.setObjectName("dimtext"); note.setWordWrap(True)
        fg.addWidget(note)
        g.addWidget(font_grp)

        # Style checkboxes
        style_row = QHBoxLayout()
        self._bold_chk = QCheckBox("Bold")
        self._bold_chk.setChecked(self._s.get("sub_bold", False))
        self._bold_chk.toggled.connect(lambda v: (self._s.update({"sub_bold": v}), self._refresh()))
        self._italic_chk = QCheckBox("Italic")
        self._italic_chk.setChecked(self._s.get("sub_italic", False))
        self._italic_chk.toggled.connect(lambda v: (self._s.update({"sub_italic": v}), self._refresh()))
        style_row.addWidget(self._bold_chk); style_row.addWidget(self._italic_chk)
        style_row.addStretch()
        g.addLayout(style_row)

        # Sliders
        self._add_slider(g, "Size",     "sub_font_size", 16,  80)
        self._add_slider(g, "Position", "sub_pos",        0, 100,
                         hint="0 = top   100 = bottom")
        self._add_slider(g, "Outline",  "_border",        0,  20, scale=0.5)

        # Color
        crow = QHBoxLayout()
        crow.addWidget(QLabel("Color:"))
        self._swatch = QPushButton(); self._swatch.setObjectName("swatch")
        self._set_swatch(self._s.get("sub_color", "#FFFFFF"))
        self._swatch.clicked.connect(self._pick_color)
        crow.addWidget(self._swatch); crow.addStretch()
        g.addLayout(crow)

        lay.addWidget(grp); lay.addStretch()
        return w

    def _add_slider(self, layout, label, key, lo, hi, scale=1.0, hint=""):
        raw = int(self._s.get("sub_border", 2.5) * 2) if key == "_border" \
              else int(self._s.get(key, lo))
        row = QHBoxLayout()
        lbl_text = label + (f"  {hint}" if hint else "")
        lbl = QLabel(lbl_text); lbl.setObjectName("dimtext"); lbl.setFixedWidth(150)
        val_lbl = QLabel(self._fmt(raw, scale)); val_lbl.setObjectName("val")
        sl = QSlider(Qt.Orientation.Horizontal); sl.setRange(lo, hi); sl.setValue(raw)

        def on_ch(v, k=key, vl=val_lbl, sc=scale):
            if k == "_border":
                self._s["sub_border"] = v * sc
            else:
                self._s[k] = v
            vl.setText(self._fmt(v, sc))
            self._refresh()

        sl.valueChanged.connect(on_ch)
        row.addWidget(lbl); row.addWidget(sl, 1); row.addWidget(val_lbl)
        layout.addLayout(row)

    def _fmt(self, v, scale):
        r = v * scale
        return str(int(r)) if r == int(r) else f"{r:.1f}"

    def _font_label(self) -> str:
        if self._s.get("sub_font_mode") == "custom" and self._s.get("sub_font"):
            return f"Custom  —  {self._s['sub_font']}"
        return "Default  (mpv built-in)"

    def _font_use_default(self):
        self._s.update({"sub_font_mode": "default", "sub_font": "", "sub_font_path": ""})
        self._font_name_lbl.setText(self._font_label())
        self._refresh()

    def _font_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Font File", "",
            "Font Files (*.ttf *.otf *.TTF *.OTF);;All Files (*)"
        )
        if not path: return
        fid = QFontDatabase.addApplicationFont(path)
        if fid < 0:
            QMessageBox.warning(self, "Font Error", "Could not load this font file.")
            return
        families = QFontDatabase.applicationFontFamilies(fid)
        if not families: return
        self._s.update({
            "sub_font_mode": "custom",
            "sub_font":      families[0],
            "sub_font_path": path,
        })
        self._font_name_lbl.setText(self._font_label())
        self._refresh()

    def _set_swatch(self, color: str):
        self._s["sub_color"] = color
        self._swatch.setStyleSheet(
            f"QPushButton#swatch{{background-color:{color};"
            f"border:2px solid #555;border-radius:4px;"
            f"min-width:52px;max-height:22px;}}"
        )

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._s.get("sub_color", "#FFFFFF")), self)
        if c.isValid():
            self._set_swatch(c.name()); self._refresh()

    def _refresh(self):
        self._preview.apply(self._s)

    # ── About tab ─────────────────────────────────────────────────────────
    def _make_about_tab(self) -> QWidget:
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(30, 30, 30, 30); lay.setSpacing(16)
        lay.addStretch()

        title = QLabel("NOIR PLAYER"); title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(title)

        ver = QLabel(f"Version {APP_VERSION}"); ver.setObjectName("subtitle")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(ver)
        lay.addSpacing(8)

        desc = QLabel(
            "Dual-video player for watching films or series that exist\n"
            "in two versions — switch between them in real time."
        )
        desc.setObjectName("dimtext"); desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True); lay.addWidget(desc)
        lay.addSpacing(16)

        kofi = QPushButton("Support on Ko-fi")
        kofi.setObjectName("accent"); kofi.setFixedWidth(200)
        kofi.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://ko-fi.com/U7U41U5JQ")))
        row = QHBoxLayout(); row.addStretch(); row.addWidget(kofi); row.addStretch()
        lay.addLayout(row)
        lay.addStretch()
        return w

    def _save(self):
        # Flush key capture button states
        for attr in ("_key_swap", "_key_swap_alt", "_key_pause",
                     "_key_seek_back", "_key_seek_fwd", "_key_fullscreen", "_key_quit"):
            btn  = getattr(self, attr)
            skey = attr.lstrip("_")
            self._s[skey] = btn.key_name
        save_settings(self._s)
        self.accept()

    @property
    def result_settings(self): return self._s

# ---------------------------------------------------------------------------
# File picker row (used for both color and B&W in the launcher)
# ---------------------------------------------------------------------------
class FilePickerRow(QWidget):
    file_selected = pyqtSignal(str)
    tracks_ready  = pyqtSignal(list)

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self._filepath      = ""
        self._srt_path      = ""
        self._probe_thread  = None
        self._probe_worker  = None
        self._keywords: list[str] = []
        self.setAcceptDrops(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14); root.setSpacing(8)

        head = QLabel(label); head.setObjectName("sectionhead"); root.addWidget(head)

        # File row
        fr = QHBoxLayout(); fr.setSpacing(8)
        self.path_label = QLabel("No file selected  –  drag & drop here")
        self.path_label.setObjectName("filepath")
        self.path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.browse_btn = QPushButton("Browse…"); self.browse_btn.setFixedWidth(90)
        self.browse_btn.clicked.connect(self._browse)
        fr.addWidget(self.path_label); fr.addWidget(self.browse_btn)
        root.addLayout(fr)

        # Embedded subtitle row
        sr = QHBoxLayout(); sr.setSpacing(8)
        sr.addWidget(QLabel("Embedded sub:"))
        self.sub_combo = QComboBox(); self.sub_combo.setEnabled(False)
        self.sub_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.sub_combo.currentIndexChanged.connect(self._on_combo_changed)
        self.status_label = QLabel(""); self.status_label.setObjectName("filepath")
        sr.addWidget(self.sub_combo); sr.addWidget(self.status_label)
        root.addLayout(sr)

        # External SRT row
        er = QHBoxLayout(); er.setSpacing(8)
        er.addWidget(QLabel("External sub:"))
        self.srt_label = QLabel("None"); self.srt_label.setObjectName("srtname")
        self.srt_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.srt_btn = QPushButton("Browse SRT…"); self.srt_btn.setFixedWidth(110)
        self.srt_btn.clicked.connect(self._browse_srt)
        self.srt_clear_btn = QPushButton("Clear"); self.srt_clear_btn.setFixedWidth(60)
        self.srt_clear_btn.setEnabled(False); self.srt_clear_btn.clicked.connect(self._clear_srt)
        er.addWidget(self.srt_label); er.addWidget(self.srt_btn); er.addWidget(self.srt_clear_btn)
        root.addLayout(er)

    def set_keywords(self, kws: list[str]):
        self._keywords = kws

    # drag & drop
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls() and e.mimeData().urls()[0].isLocalFile():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        urls = e.mimeData().urls()
        if urls: self._load_file(urls[0].toLocalFile())

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "",
            "Video Files (*.mkv *.mp4 *.avi *.mov *.m2ts *.ts *.wmv *.webm *.flv);;All Files (*)"
        )
        if path: self._load_file(path)

    def _browse_srt(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Subtitle", "",
            "Subtitle Files (*.srt *.ass *.ssa *.sub);;All Files (*)"
        )
        if not path: return
        self._srt_path = path
        self.srt_label.setText(Path(path).name)
        self.srt_label.setToolTip(path)
        self.srt_clear_btn.setEnabled(True)
        # Dim combo to indicate external sub takes priority
        self.sub_combo.setEnabled(False)

    def _clear_srt(self):
        self._srt_path = ""
        self.srt_label.setText("None"); self.srt_label.setToolTip("")
        self.srt_clear_btn.setEnabled(False)
        self.sub_combo.setEnabled(bool(self._filepath))

    def _on_combo_changed(self, _):
        # If user picks an embedded track, clear external SRT
        if self.sub_combo.currentData() is not None and self._srt_path:
            self._clear_srt()

    def _load_file(self, path: str):
        self._filepath = path
        self.path_label.setText(Path(path).name)
        self.path_label.setToolTip(path)
        self.sub_combo.clear(); self.sub_combo.setEnabled(False)
        self.status_label.setText("Probing…")
        self.browse_btn.setEnabled(False)
        self.file_selected.emit(path)
        self._start_probe(path)

    def _start_probe(self, path: str):
        self._probe_thread = QThread()
        self._probe_worker = ProbeWorker(path)
        self._probe_worker.moveToThread(self._probe_thread)
        self._probe_thread.started.connect(self._probe_worker.run)
        self._probe_worker.finished.connect(self._on_tracks)
        self._probe_worker.error.connect(self._on_error)
        self._probe_worker.finished.connect(self._probe_thread.quit)
        self._probe_worker.error.connect(self._probe_thread.quit)
        self._probe_thread.finished.connect(self._probe_worker.deleteLater)
        self._probe_thread.start()

    def _on_tracks(self, tracks: list):
        self.browse_btn.setEnabled(True)
        if not self._srt_path:
            self.sub_combo.setEnabled(True)
        self.sub_combo.clear()
        self.sub_combo.addItem("None (no subtitles)", None)
        for t in tracks:
            self.sub_combo.addItem(t["label"], t["id"])
        idx = auto_select_track(tracks, self._keywords)
        if idx is not None:
            self.sub_combo.setCurrentIndex(idx)
            self.status_label.setText(f"Auto-selected  ·  {len(tracks)} tracks")
        else:
            self.status_label.setText(f"{len(tracks)} track{'s' if len(tracks)!=1 else ''}")
        self.tracks_ready.emit(tracks)

    def _on_error(self, msg: str):
        self.browse_btn.setEnabled(True)
        self.status_label.setText("Probe failed")
        flog(f"[PROBE ERROR] {msg}")

    @property
    def filepath(self):           return self._filepath
    @property
    def selected_sub_id(self):    return None if self._srt_path else self.sub_combo.currentData()
    @property
    def selected_srt_path(self):  return self._srt_path

# ---------------------------------------------------------------------------
# Launcher
# ---------------------------------------------------------------------------
class LauncherWindow(QWidget):
    play_requested = pyqtSignal(dict, dict)  # color_info, bw_info

    def __init__(self, settings: dict):
        super().__init__()
        self._settings = settings
        self.setWindowTitle("NoirPlayer")
        self.setMinimumWidth(640)

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 28); root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        hdr = QHBoxLayout(); hdr.setContentsMargins(0, 0, 0, 0); hdr.setSpacing(0)

        # Left: title + subtitle, left-aligned
        title_col = QVBoxLayout(); title_col.setSpacing(2)
        title_lbl = QLabel("NOIR PLAYER"); title_lbl.setObjectName("title")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        sub_lbl   = QLabel("DUAL VIDEO COMPARISON"); sub_lbl.setObjectName("subtitle")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_col.addWidget(title_lbl); title_col.addWidget(sub_lbl)
        title_w = QWidget(); title_w.setLayout(title_col)

        # Centre: noir.png image, truly centred in window
        img_lbl = QLabel(); img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(str(NOIR_IMG))
        if not pix.isNull():
            pix = pix.scaledToHeight(68, Qt.TransformationMode.SmoothTransformation)
            img_lbl.setPixmap(pix)

        # Right: settings button, right-aligned
        settings_btn = QPushButton("Settings"); settings_btn.setFixedWidth(100)
        settings_btn.clicked.connect(self._open_settings)
        settings_w = QWidget()
        settings_lay = QHBoxLayout(settings_w); settings_lay.setContentsMargins(0,0,0,0)
        settings_lay.addStretch(); settings_lay.addWidget(settings_btn)

        hdr.addWidget(title_w,    1, Qt.AlignmentFlag.AlignVCenter)
        hdr.addWidget(img_lbl,    0, Qt.AlignmentFlag.AlignCenter)
        hdr.addWidget(settings_w, 1, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(hdr); root.addSpacing(22)

        # ── Keyword card ──────────────────────────────────────────────────
        kw = make_card(); kl = QVBoxLayout(kw); kl.setContentsMargins(16,12,16,12); kl.setSpacing(6)
        kh = QLabel("SUBTITLE AUTO-SELECT  –  keywords (comma-separated)")
        kh.setObjectName("sectionhead"); kl.addWidget(kh)
        self.kw_input = QLineEdit()
        self.kw_input.setPlaceholderText("e.g.  English, SDH  —  leave blank to show all")
        self.kw_input.textChanged.connect(self._on_kw)
        kl.addWidget(self.kw_input)
        root.addWidget(kw); root.addSpacing(10)

        # ── File pickers ──────────────────────────────────────────────────
        for attr, lbl in [("color_picker", "COLOR VERSION"),
                           ("bw_picker",   "BLACK & WHITE VERSION")]:
            card = make_card(); cl = QVBoxLayout(card); cl.setContentsMargins(0,0,0,0)
            picker = FilePickerRow(lbl); setattr(self, attr, picker); cl.addWidget(picker)
            root.addWidget(card); root.addSpacing(10)

        # ── Play button ───────────────────────────────────────────────────
        root.addSpacing(14)
        self.play_btn = QPushButton("  PLAY")
        self.play_btn.setObjectName("accent"); self.play_btn.setFixedHeight(46)
        self.play_btn.setEnabled(False); self.play_btn.clicked.connect(self._on_play)
        root.addWidget(self.play_btn)

        self.hint = QLabel(self._hint_text())
        self.hint.setObjectName("filepath"); self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addSpacing(8); root.addWidget(self.hint)

        self.color_picker.file_selected.connect(self._check_ready)
        self.bw_picker.file_selected.connect(self._check_ready)

    def _hint_text(self) -> str:
        s   = self._settings
        sw  = s.get("key_swap", "Tab"); sw2 = s.get("key_swap_alt", "S")
        pau = s.get("key_pause", "Space"); fs = s.get("key_fullscreen", "F")
        q   = s.get("key_quit", "Escape")
        return f"{sw} / {sw2}  switch   ·   {pau}  pause   ·   {fs}  fullscreen   ·   {q}  quit"

    def _open_settings(self):
        dlg = SettingsDialog(self._settings, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._settings.update(dlg.result_settings)
            self.hint.setText(self._hint_text())

    def _on_kw(self, text: str):
        kws = [k.strip().lower() for k in text.split(",") if k.strip()]
        self.color_picker.set_keywords(kws); self.bw_picker.set_keywords(kws)

    def _check_ready(self, _=None):
        self.play_btn.setEnabled(
            bool(self.color_picker.filepath and self.bw_picker.filepath))

    def _on_play(self):
        color_info = {
            "path": self.color_picker.filepath,
            "sid":  self.color_picker.selected_sub_id,
            "srt":  self.color_picker.selected_srt_path,
        }
        bw_info = {
            "path": self.bw_picker.filepath,
            "sid":  self.bw_picker.selected_sub_id,
            "srt":  self.bw_picker.selected_srt_path,
        }
        self.play_requested.emit(color_info, bw_info)

# ---------------------------------------------------------------------------
# Timeline overlay
# ---------------------------------------------------------------------------
class TimelineWidget(QWidget):
    seek_requested = pyqtSignal(float)

    _LABEL_W = 52
    _PAD     = 12
    _BAR_H   = 4
    _HEIGHT  = 46

    def __init__(self, parent=None):
        super().__init__(parent)
        # WA_NativeWindow is required so this widget stays on top of the
        # mpv VideoPanel native HWNDs in z-order.
        # WA_TranslucentBackground is intentionally NOT set here — combining
        # it with WA_NativeWindow on Windows makes the child window invisible
        # and prevents show() from restoring it.
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setFixedHeight(self._HEIGHT)
        self._pos      = 0.0
        self._dur      = 0.0
        self._dragging = False
        self.setMouseTracking(True)

    def set_position(self, pos: float, dur: float):
        if pos == self._pos and dur == self._dur: return
        self._pos = max(0.0, pos); self._dur = max(0.0, dur)
        self.update()

    def _fraction(self) -> float:
        return min(1.0, self._pos / self._dur) if self._dur > 0 else 0.0

    def _bar_x(self) -> int:
        return self._PAD + self._LABEL_W

    def _bar_w(self) -> int:
        return max(1, self.width() - 2 * self._PAD - 2 * self._LABEL_W)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Gradient background — dark at bottom, slightly lighter at top
        # (solid colours; alpha gradients don't work on WA_NativeWindow children on Windows)
        grad = QLinearGradient(0, 0, 0, self._HEIGHT)
        grad.setColorAt(0.0, QColor(28, 28, 28))
        grad.setColorAt(1.0, QColor(10, 10, 10))
        p.fillRect(self.rect(), grad)

        # Subtle top separator line
        p.setPen(QPen(QColor(50, 50, 50), 1))
        p.drawLine(0, 0, self.width(), 0)

        bx     = self._bar_x()
        bw     = self._bar_w()
        cy     = self._HEIGHT // 2 + 4
        filled = int(bw * self._fraction())

        # Track groove
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(55, 55, 55))
        p.drawRoundedRect(bx, cy - self._BAR_H // 2, bw, self._BAR_H, 2, 2)

        # Filled portion
        if filled > 0:
            p.setBrush(QColor(ACCENT))
            p.drawRoundedRect(bx, cy - self._BAR_H // 2, filled, self._BAR_H, 2, 2)

        # Scrubber handle
        hx = bx + filled
        p.setBrush(QColor(ACCENT_HI))
        p.setPen(QPen(QColor(20, 20, 20), 1))
        p.drawEllipse(hx - 6, cy - 6, 12, 12)

        # Time labels
        p.setFont(QFont("Consolas", 8))
        p.setPen(QColor(180, 180, 180))
        p.drawText(self._PAD, 0, self._LABEL_W, self._HEIGHT,
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   self._fmt(self._pos))
        p.drawText(self.width() - self._PAD - self._LABEL_W, 0,
                   self._LABEL_W, self._HEIGHT,
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                   self._fmt(self._dur))
        p.end()

    @staticmethod
    def _fmt(secs: float) -> str:
        s = int(secs); h, m, s = s // 3600, (s % 3600) // 60, s % 60
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    def _seek_from_x(self, mx: int) -> float:
        bx  = self._bar_x(); bw = self._bar_w()
        frac = max(0.0, min(1.0, (mx - bx) / bw))
        return frac * self._dur

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self.seek_requested.emit(self._seek_from_x(e.pos().x()))

    def mouseMoveEvent(self, e):
        if self._dragging:
            self.seek_requested.emit(self._seek_from_x(e.pos().x()))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

# ---------------------------------------------------------------------------
# Video panel
# ---------------------------------------------------------------------------
class VideoPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.setStyleSheet("background: black;")

# ---------------------------------------------------------------------------
# Player window
# ---------------------------------------------------------------------------
class PlayerWindow(QMainWindow):
    _HIDE_MS = 5000

    def __init__(self, color_info: dict, bw_info: dict, settings: dict):
        super().__init__()
        self.setWindowTitle("NoirPlayer")
        self.setStyleSheet("background: black;")

        self._color_path = color_info["path"]
        self._color_sid  = color_info["sid"]
        self._color_srt  = color_info.get("srt", "")
        self._bw_path    = bw_info["path"]
        self._bw_sid     = bw_info["sid"]
        self._bw_srt     = bw_info.get("srt", "")
        self._settings   = settings

        self._showing_color = True
        self._is_paused     = False
        self._fullscreen    = False
        self._ui_visible    = True
        self._keys          = self._resolve_keys()

        self._container = QWidget()
        self._container.setStyleSheet("background: black;")
        self.setCentralWidget(self._container)

        self._color_panel = VideoPanel(self._container)
        self._bw_panel    = VideoPanel(self._container)
        self._timeline    = TimelineWidget(self._container)
        self._timeline.seek_requested.connect(self._on_seek)

        self._color_mpv: mpv.MPV | None = None
        self._bw_mpv:    mpv.MPV | None = None

        self._sync_timer = QTimer(self); self._sync_timer.setInterval(2000)
        self._sync_timer.timeout.connect(self._drift_correct)

        self._tl_timer = QTimer(self); self._tl_timer.setInterval(300)
        self._tl_timer.timeout.connect(self._update_timeline)

        self._hide_timer = QTimer(self); self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(self._HIDE_MS)
        self._hide_timer.timeout.connect(self._hide_ui)

        self._poll_timer = QTimer(self); self._poll_timer.setInterval(100)
        self._poll_timer.timeout.connect(self._poll_cursor)
        self._last_cursor_pos = QCursor.pos()

        self.setMouseTracking(True)
        self._container.setMouseTracking(True)
        self._panels_ready = False

    # ── Key map ───────────────────────────────────────────────────────────
    def _resolve_keys(self) -> dict[int, str]:
        pairs = [
            ("key_swap",       "swap"),
            ("key_swap_alt",   "swap"),
            ("key_pause",      "pause"),
            ("key_seek_back",  "seek_back"),
            ("key_seek_fwd",   "seek_fwd"),
            ("key_fullscreen", "fullscreen"),
            ("key_quit",       "quit"),
        ]
        result: dict[int, str] = {}
        for setting_key, action in pairs:
            name = self._settings.get(setting_key, "")
            if not name: continue
            seq = QKeySequence(name)
            if not seq.isEmpty():
                result[seq[0].key()] = action
        return result

    # ── Lifecycle ─────────────────────────────────────────────────────────
    def showEvent(self, e):
        super().showEvent(e)
        if not self._panels_ready:
            self._panels_ready = True
            QTimer.singleShot(100, self._init_mpv)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._layout_panels()

    def keyPressEvent(self, e: QKeyEvent):
        action = self._keys.get(e.key())
        if action == "swap":         self._swap_panels()
        elif action == "pause":      self._toggle_pause()
        elif action == "seek_back":  self._seek(-5)
        elif action == "seek_fwd":   self._seek(5)
        elif action == "fullscreen": self._toggle_fullscreen()
        elif action == "quit":
            if self._fullscreen: self._toggle_fullscreen()
            else: self.close()
        else: super().keyPressEvent(e)

    def mousePressEvent(self, e):
        if e.button() in (Qt.MouseButton.BackButton, Qt.MouseButton.ForwardButton):
            self._swap_panels()
        else:
            super().mousePressEvent(e)

    def closeEvent(self, e):
        for t in (self._sync_timer, self._tl_timer, self._hide_timer, self._poll_timer):
            t.stop()
        self._show_ui()
        for p in (self._color_mpv, self._bw_mpv):
            if p:
                try: p.terminate()
                except Exception: pass
        super().closeEvent(e)

    # ── Layout ────────────────────────────────────────────────────────────
    def _layout_panels(self):
        r = self._container.rect()
        self._color_panel.setGeometry(r)
        self._bw_panel.setGeometry(r)
        self._timeline.setGeometry(0, r.height() - self._timeline.height(),
                                   r.width(), self._timeline.height())
        (self._color_panel if self._showing_color else self._bw_panel).raise_()
        self._timeline.raise_()

    # ── UI visibility ─────────────────────────────────────────────────────
    def _poll_cursor(self):
        pos = QCursor.pos()
        if pos != self._last_cursor_pos:
            self._last_cursor_pos = pos
            self._show_ui()
            self._hide_timer.start()

    def _show_ui(self):
        if not self._ui_visible:
            self._ui_visible = True
            self.unsetCursor()
        if not self._timeline.isVisible():
            self._timeline.show()
            self._timeline.raise_()

    def _hide_ui(self):
        self._ui_visible = False
        self.setCursor(Qt.CursorShape.BlankCursor)
        self._timeline.hide()

    # ── mpv init ──────────────────────────────────────────────────────────
    def _apply_sub_settings(self, player: mpv.MPV):
        s    = self._settings
        mode = s.get("sub_font_mode", "default")
        if mode == "custom" and s.get("sub_font"):
            player["sub-font"] = s["sub_font"]
            fp = s.get("sub_font_path", "")
            if fp:
                player["sub-fonts-dir"] = str(Path(fp).parent)
        player["sub-font-size"]     = int(s.get("sub_font_size", 40))
        player["sub-pos"]           = int(s.get("sub_pos", 90))
        player["sub-color"]         = s.get("sub_color", "#FFFFFF")
        player["sub-border-size"]   = float(s.get("sub_border", 2.5))
        player["sub-bold"]          = bool(s.get("sub_bold", False))
        player["sub-italic"]        = bool(s.get("sub_italic", False))
        player["sub-shadow-offset"] = int(s.get("sub_shadow", 1))

    def _make_mpv(self, wid: int, muted: bool, sid, srt_path: str = "") -> mpv.MPV:
        base_opts: dict = dict(
            wid=str(wid), vo="gpu", hwdec="auto",
            keep_open="yes", cache="yes", osc="no", border="no",
            input_default_bindings=False, input_vo_keyboard=False,
        )
        if _SYS == "Windows":
            base_opts["gpu_api"] = "d3d11"
        if srt_path:
            base_opts["sub_file"] = srt_path

        player = mpv.MPV(**base_opts)
        player["mute"] = muted

        if not srt_path:
            if sid is not None:
                player["sid"] = int(sid)
            else:
                player["sid"] = False

        self._apply_sub_settings(player)
        return player

    def _init_mpv(self):
        self._color_panel.winId(); self._bw_panel.winId()
        self._color_panel.raise_()
        try:
            self._color_mpv = self._make_mpv(
                int(self._color_panel.winId()), False,
                self._color_sid, self._color_srt)
            self._bw_mpv = self._make_mpv(
                int(self._bw_panel.winId()), True,
                self._bw_sid, self._bw_srt)
            self._color_mpv.play(self._color_path)
            self._bw_mpv.play(self._bw_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start playback:\n{e}")
            self.close(); return

        self._timeline.raise_()
        self._sync_timer.start()
        self._tl_timer.start()
        self._poll_timer.start()
        self._hide_timer.start()

    # ── Playback controls ─────────────────────────────────────────────────
    def _swap_panels(self):
        if not self._color_mpv: return
        self._showing_color = not self._showing_color
        if self._showing_color:
            self._color_mpv["mute"] = False; self._bw_mpv["mute"] = True
            self._color_panel.raise_()
        else:
            self._bw_mpv["mute"] = False; self._color_mpv["mute"] = True
            self._bw_panel.raise_()
        self._timeline.raise_()

    def _toggle_pause(self):
        if not self._color_mpv: return
        self._is_paused = not self._is_paused
        self._color_mpv["pause"] = self._is_paused
        self._bw_mpv["pause"]    = self._is_paused

    def _seek(self, secs: float):
        if not self._color_mpv: return
        try:
            self._color_mpv.seek(secs, "relative")
            self._bw_mpv.seek(secs, "relative")
        except Exception: pass

    def _on_seek(self, t: float):
        if not self._color_mpv: return
        try:
            self._color_mpv.seek(t, "absolute", "exact")
            self._bw_mpv.seek(t, "absolute", "exact")
        except Exception: pass

    def _toggle_fullscreen(self):
        self.showNormal() if self._fullscreen else self.showFullScreen()
        self._fullscreen = not self._fullscreen

    def _update_timeline(self):
        if not self._color_mpv: return
        try:
            pos = self._color_mpv.time_pos or 0.0
            dur = self._color_mpv.duration  or 0.0
            self._timeline.set_position(pos, dur)
        except Exception: pass

    def _drift_correct(self):
        if not self._color_mpv or not self._bw_mpv or self._is_paused: return
        try:
            ct = self._color_mpv.time_pos; bt = self._bw_mpv.time_pos
            if ct is None or bt is None: return
            drift = ct - bt
            if abs(drift) > 0.2:
                target = ct if drift > 0 else bt
                (self._bw_mpv if drift > 0 else self._color_mpv).seek(
                    target, "absolute", "exact")
        except Exception: pass

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
class App(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setStyle("Fusion")
        self.setStyleSheet(STYLESHEET)

        global _BUNDLED_FONTS
        _BUNDLED_FONTS = _load_fonts_dir()

        self._settings = load_settings()
        self._launcher = LauncherWindow(self._settings)
        self._player: PlayerWindow | None = None
        self._launcher.play_requested.connect(self._on_play)
        self._launcher.show()

    def _on_play(self, color_info: dict, bw_info: dict):
        self._launcher.hide()
        self._player = PlayerWindow(color_info, bw_info, self._settings)
        self._player.resize(1280, 720)
        self._player.show()


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    sys.exit(App(sys.argv).exec())


if __name__ == "__main__":
    main()
