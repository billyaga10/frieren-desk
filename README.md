# ✦ Frieren Desk Companion

<div align="center">

![Frieren Desk Companion Banner](assets/sprites/idle.png)

**Sahabat Desktop Interaktif & AI Coding Assistant (macOS & Windows)**  
*Ultra-lightweight transparent borderless companion dengan Dual Engine (Codex & Antigravity), ekspresi responsif, Needs & Wellness tracker, dan memori percakapan.*

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20%28Qt6%29-41cd52?logo=qt)](https://www.qt.io/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-lightgrey)](#)
[![Engines](https://img.shields.io/badge/Dual%20Engine-Codex%20%7C%20Antigravity-orange)](#-pilihan-engine-ai)

</div>

---

## 🌟 Highlight Fitur

- 🪄 **Borderless & Zero-Flicker Transparent Window**: Tampil melayang rapi di pojok kanan bawah desktop (di atas Taskbar / Dock). Dilengkapi native OS level click-through di Windows (`WS_EX_TRANSPARENT`) & macOS tanpa kedipan.
- 🤖 **Dual AI Engine**:
  - **OpenAI Codex CLI** (`gpt-6-luna` / `codex`)
  - **Google Antigravity CLI** (`gemini-3.8-flash-low` / `agy`)
  - Ganti engine kapan saja langsung dari menu klik kanan.
- 🎭 **16 Ekspresi & Gerakan Sprite 2D**:
  - Pose santai dinamis (minum teh hangat, membaca grimoire sihir, merapatkan syal, bernyanyi & menari kecil).
  - Reaksi saat berpikir (`thinking`, `thinking_tilt`), bekerja (`action_laptop`, `action_magic`), dan gembira saat dielus/disapa (`pleased`, `pleased_wave`).
- 🍵 **Needs & Wellness System**: Frieren mengingatkanmu untuk minum air, makan camilan sehat, istirahat mata, peregangan tubuh, dan rehat tidur dengan visual drawer interaktif.
- 🎹 **Efek Suara Anime Lembut**: Audio chime keyboard synthesizer bawaan OS (native `winsound` di Windows & `NSSound` di macOS) tanpa lag.
- 📎 **Dukungan Vision & File Attachment**:
  - Tempel screenshot langsung dengan `Ctrl+V` (Windows) / `Cmd+V` (macOS).
  - Drag and drop file, folder, dokumen, atau gambar langsung ke Frieren.
- 🧠 **Dual Memory System**:
  - Riwayat sesi aktif (`memory.json`).
  - Catatan jangka panjang (`long_term_memory.json` & `frieren_notes.md`) dengan opsi sinkronisasi Google Drive.

---

## 📋 Persyaratan Sistem (Prerequisites)

Sebelum menjalankan Frieren Desk Companion, pastikan hal-hal berikut sudah terpasang di komputermu:

### 1. Python 3.11 atau Lebih Baru
- **Windows**: Download dari [python.org](https://www.python.org/downloads/).  
  *(⚠️ **PENTING**: Saat menginstall di Windows, pastikan kamu mencentang opsi **"Add python.exe to PATH"**).*
- **macOS**: Pasang via Homebrew: `brew install python@3.12`

### 2. Salah Satu (atau Kedua) AI Engine CLI:

Pilih engine yang ingin kamu gunakan:

#### A. Google Antigravity CLI (`agy`)
- Pastikan CLI `agy` sudah terpasang dan dapat dijalankan di terminal.
- Login dan verifikasi dengan mengetik:
  ```bash
  agy --version
  ```

#### B. OpenAI Codex CLI (`codex`)
- Pastikan `codex` CLI sudah terpasang di sistem.
- Login akun kamu terlebih dahulu:
  ```bash
  codex login
  ```

---

## 🚀 Panduan Instalasi & Menjalankan

### Cara Cepat (Windows) 🪟

1. Buka folder repositori `frieren-desk`.
2. Klik dua kali (double click) file **`run_windows.bat`**.
   - Script akan otomatis mengecek Python, membuat `.venv`, menginstall semua dependencies, dan menjalankan Frieren di background tanpa jendela hitam terminal CMD!

---

### Instalasi Manual (Windows / macOS) 💻

1. **Clone repositori:**
   ```bash
   git clone https://github.com/billyaga10/frieren-desk.git
   cd frieren-desk
   ```

2. **Buat dan aktifkan Virtual Environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Siapkan Konfigurasi:**
   Salin file `config.example.json` menjadi `config.json`:
   - **Windows:**
     ```powershell
     copy config.example.json config.json
     ```
   - **macOS:**
     ```bash
     cp config.example.json config.json
     ```

5. **Jalankan Aplikasi:**
   - **Windows (dengan Python bawaan venv):**
     ```powershell
     .\.venv\Scripts\pythonw.exe main.py
     ```
   - **macOS:**
     ```bash
     ./run.sh
     # atau
     python3 main.py
     ```

---

## 🎮 Cara Menggunakan & Kontrol Pintas

### 💬 Membuka Kolom Chat / Ngobrol
| Cara | Tindakan |
|---|---|
| **Shortcut Keyboard Global** | Tekan <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Space</kbd> (Windows) atau <kbd>Cmd</kbd> + <kbd>Shift</kbd> + <kbd>Space</kbd> (macOS) di mana saja. |
| **Klik Karakter** | Klik kiri langsung pada tubuh Frieren untuk menyapa/mengelus sekaligus memunculkan bubble chat. |
| **System Tray** | Klik kanan ikon Frieren di taskbar tray (dekat jam) ➜ pilih **"Munculkan / Fokus Input"**. |

### ⌨️ Daftar Shortcut Lengkap

| Shortcut (Windows) | Shortcut (macOS) | Fungsi |
|---|---|---|
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Space</kbd> | <kbd>Cmd</kbd> + <kbd>Shift</kbd> + <kbd>Space</kbd> | **Munculkan / Sembunyikan & Fokus Input Chat** |
| <kbd>Ctrl</kbd> + <kbd>M</kbd> | <kbd>Cmd</kbd> + <kbd>M</kbd> | **Minimize Frieren** menjadi avatar mini / pulihkan kembali |
| <kbd>Ctrl</kbd> + <kbd>=</kbd> / <kbd>+</kbd> | <kbd>Cmd</kbd> + <kbd>=</kbd> / <kbd>+</kbd> | Memperbesar ukuran karakter Frieren |
| <kbd>Ctrl</kbd> + <kbd>-</kbd> | <kbd>Cmd</kbd> + <kbd>-</kbd> | Memperkecil ukuran karakter Frieren |
| <kbd>Ctrl</kbd> + <kbd>0</kbd> | <kbd>Cmd</kbd> + <kbd>0</kbd> | Reset skala ukuran Frieren ke 100% |
| <kbd>Alt</kbd> + <kbd>Scroll Mouse</kbd> | <kbd>Option</kbd> + <kbd>Scroll Mouse</kbd> | Mengatur transparansi jendela (Opacity 25% – 100%) |
| <kbd>Shift</kbd> + <kbd>Scroll</kbd> | <kbd>Shift</kbd> + <kbd>Scroll</kbd> | Mengatur jarak balon obrolan dengan kepala Frieren (0 – 65px) |
| <kbd>Escape</kbd> | <kbd>Escape</kbd> | Menutup kolom input obrolan |
| <kbd>Ctrl</kbd> + <kbd>V</kbd> | <kbd>Cmd</kbd> + <kbd>V</kbd> | Menempelkan screenshot langsung dari clipboard |

---

## 🎛️ Menu Klik Kanan (Context Menu)

Klik kanan pada karakter Frieren atau ikon System Tray untuk mengakses:

1. **Ganti AI Engine**: Beralih antara **OpenAI Codex CLI** dan **Google Antigravity CLI**.
2. **Needs & Wellness Drawer (`🌱`)**: Cek status istirahat, minum, camilan, dan lakukan *"Rawat Semua"*.
3. **Pilih Mood / Suasana Hati Frieren**: Atur mood Frieren secara manual (*Tenang, Hangat, Ceria, Antusias, Fokus, dll.*).
4. **Google Drive Sync**: Hubungkan catatan memori jangka panjang ke akun Google Drive.
5. **Buka Catatan Frieren (`frieren_notes.md`)**: Lihat rangkuman fakta dan preferensimu yang diingat Frieren.
6. **Sembunyikan / Autohide Bubble Chat**: Mode santai agar balon percakapan otomatis sembunyi saat diam.
7. **Keluar**: Menutup aplikasi.

---

## 📂 Struktur Folder Proyek

```text
frieren-desk/
├── assets/
│   ├── sprites/          # 16 sprite ekspresi transparan Frieren
│   ├── sounds/           # File audio sintetis nada ketik
│   └── clipboard/       # Cache temporary gambar paste/attachment
├── config.example.json   # Template konfigurasi aplikasi
├── codex_backend.py      # Integrasi dual engine (Codex CLI & Antigravity CLI)
├── needs_manager.py      # Pengelola siklus Needs & Wellness
├── sprite_helper.py      # Helper pose & sprite generator
├── main.py               # Aplikasi utama GUI (PySide6 / Qt6)
├── run_windows.bat       # Launcher Windows (auto-detect Python & silent run)
├── run.sh                # Launcher macOS
└── requirements.txt      # Daftar dependensi Python
```

---

## ❓ FAQ & Solusi Masalah

> **T: Layar Frieren berkedip (flicker) saat mouse melintas?**  
> **J:** Versi terbaru telah diperbarui dengan integrasi native Win32 `WS_EX_TRANSPARENT`. Pastikan kamu menggunakan branch `main` terbaru, masalah flicker telah 100% tuntas.

> **T: Muncul pesan "Python belum terinstall atau belum ada di PATH"?**  
> **J:** Install Python dari [python.org](https://www.python.org/) dan pastikan opsi *"Add Python to PATH"* dicentang saat instalasi, lalu restart komputermu.

> **T: Bagaimana cara menghentikan Frieren yang berjalan di background?**  
> **J:** Klik kanan ikon Frieren di pojok kanan bawah taskbar (System Tray) lalu pilih **"Keluar"**, atau buka Task Manager dan matikan proses `pythonw.exe`.

---

<div align="center">
Dibuat dengan cinta untuk menemani hari-harimu di meja kerja 🌸
</div>
