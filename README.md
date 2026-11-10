# ✦ Frieren Desk Companion

Ultra-lightweight interactive 2D desktop companion and AI assistant for macOS, powered by **PySide6** and OpenAI Codex CLI (`gpt-6-luna`).

---

## ✨ Features

- **Borderless & Transparent Desktop Companion**:
  - Docks smoothly at the bottom-right corner of your screen above macOS Dock.
  - Dynamic click-through: clicking outside Frieren or her speech bubble interacts with background apps seamlessly.
- **Expressive 2D Sprites & Idle Animations**:
  - 16 transparent sprites covering states: `idle`, `thinking`, `talking`, `pleased`, plus special agent action poses (`action_laptop` and `action_magic`).
  - Periodic gentle idle pose rotation (drinking tea, reading grimoire, cozy scarf hold, dancing).
- **Natural Emotion & Mood System**:
  - Warm, non-punitive emotional feedback (`🌿 Tenang`, `☕ Hangat`, `🌸 Senang`, `🎶 Ceria`, `✨ Antusias`, `🔍 Penasaran`, `📖 Fokus`, `🤍 Tersentuh`, `💭 Nostalgia`, `💤 Mengantuk Manja`).
  - Adapts dynamically to conversation context or right-click manual selection.
- **Typewriter Motion & Soft Anime Sound**:
  - Smooth character typing effect with rich Markdown formatting (bold, italic, code pills, lists, clickable links).
  - Native macOS Objective-C `NSSound` chime ticks with mute toggle (`🔊` / `🔇`).
- **Collapsible Toolbar & Custom Positioning**:
  - Quick action toolbar (`⚡` Agent Mode, `💻` Codex Output drawer, `📜` Chat History, `🔊` Sound) collapsible via `◂` / `▸`.
  - Adjustable vertical bubble distance (`0` to `65px`) via drag, Shift + Scroll, or right-click menu.
  - Window Opacity adjustment via Option + Scroll (25% – 100%).
  - Window Resizing via Cmd + Scroll (70% – 150%).
  - Minimize character mode (`Cmd+M`) and hide-to-tray support.
- **Vision & File Attachments**:
  - Instant screenshot / image paste (`Cmd+V`).
  - Drag and drop images, documents, or file paths directly onto Frieren.
- **Codex CLI Integration & Dual Memory**:
  - Powered by local `codex exec` non-interactive runtime.
  - Short-term conversation history (`memory.json`).
  - Long-term memory notes (`long_term_memory.json` & `frieren_notes.md`) with optional Google Drive auto-sync.
- **Global Shortcut**:
  - Press `Cmd+Shift+Space` anywhere in macOS (Carbon zero-polling hotkey) to summon and focus the chat input bar.

---

## 🚀 Getting Started

### Prerequisites

- macOS (tested on macOS Monterey / Ventura / Sonoma)
- Python 3.11+
- Codex CLI (`codex`) installed in `~/.local/bin/codex` (or in `$PATH`)

### Installation

```bash
# Clone the repository
git clone https://github.com/billyaga10/frieren-desk.git
cd frieren-desk

# Create virtual environment & install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create your local config from example
cp config.example.json config.json
```

### Running the Companion

```bash
./run.sh
# or
.venv/bin/python3 main.py
```

---

## ⌨️ Shortcuts & Controls

| Shortcut / Action | Function |
|---|---|
| `Cmd + Shift + Space` | Toggle & focus Frieren's chat input bar |
| `Cmd + M` | Minimize Frieren into mini floating avatar |
| `Cmd + Scroll` / `Cmd + =/-` | Resize Frieren (Scale 70% – 150%) |
| `Option + Scroll` | Adjust transparency / Opacity (25% – 100%) |
| `Shift + Scroll` / Drag Header | Adjust distance between speech bubble and Frieren |
| `Left Click` on Frieren | Pet / sapa Frieren (36 varied voice lines) |
| `Right Click` | Context menu (Moods, Google Drive sync, reset history, quit) |
| `Cmd + V` in chat | Paste screenshot / image directly to attach |

---

## 📄 License

MIT License. Designed with care for cozy desktop companionship.
