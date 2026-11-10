"""
Lightweight non-interactive Codex CLI (`gpt-6-luna`) wrapper with:
1. Short-Term Chat History (`memory.json`)
2. Long-Term Memory (`long_term_memory.json` & `frieren_notes.md`)
3. Selectable Google Drive Auto-Sync + optional Codex Google Drive plugin
4. Toggleable Agent Execution Mode (open web/apps, run shell commands, capture CLI output)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import random
from typing import Callable, Dict, List, Optional


@dataclass
class CodexResult:
    speech: str
    cli_output: str
    saved_memories: List[str]
    emotion: Optional[str] = None


class CodexBackend:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.config_path = self.base_dir / "config.json"
        self.persona_path = self.base_dir / "persona.txt"
        self.config = self._load_config()

        mem_cfg = self.config.get("memory", {})
        self.memory_path = self.base_dir / mem_cfg.get("file", "memory.json")
        self.ltm_path = self.base_dir / mem_cfg.get("ltm_file", "long_term_memory.json")
        self.notes_path = self.base_dir / mem_cfg.get("notes_file", "frieren_notes.md")
        self.max_messages: int = int(mem_cfg.get("max_messages", 10))

        codex_cfg = self.config.get("codex", {})
        configured_bin = codex_cfg.get("binary", "/Users/user/.local/bin/codex")
        self.codex_bin = (
            configured_bin
            if os.path.exists(configured_bin)
            else (shutil.which("codex") or configured_bin)
        )
        self.model: str = codex_cfg.get("model", "gpt-6-luna")
        self.reasoning_effort: str = codex_cfg.get("reasoning_effort", "low")
        self.timeout_seconds: int = int(codex_cfg.get("timeout_seconds", 90))

    def _load_config(self) -> dict:
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save_config(self) -> None:
        try:
            self.config_path.write_text(
                json.dumps(self.config, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass

    def save_ui_prefs(
        self,
        sound_enabled: bool,
        history_enabled: bool,
        output_enabled: Optional[bool] = None,
        minimized: Optional[bool] = None,
        scale: Optional[float] = None,
        opacity: Optional[float] = None,
        bubble_gap: Optional[int] = None,
    ) -> None:
        ui = self.config.setdefault("ui", {})
        ui["sound_enabled"] = bool(sound_enabled)
        ui["history_enabled"] = bool(history_enabled)
        if output_enabled is not None:
            ui["output_enabled"] = bool(output_enabled)
        if minimized is not None:
            ui["minimized"] = bool(minimized)
        if scale is not None:
            ui["scale"] = round(float(scale), 2)
        if opacity is not None:
            ui["opacity"] = round(float(opacity), 2)
        if bubble_gap is not None:
            ui["bubble_gap"] = int(bubble_gap)
        self.save_config()

    # ------------------------------------------------------------------
    # Settings Getters & Setters (Agent Mode & Google Drive Selection)
    # ------------------------------------------------------------------
    @property
    def agent_execution_enabled(self) -> bool:
        return bool(self.config.get("codex", {}).get("agent_execution_enabled", True))

    def set_agent_execution_enabled(self, enabled: bool) -> None:
        self.config.setdefault("codex", {})["agent_execution_enabled"] = bool(enabled)
        self.save_config()

    @property
    def gdrive_sync_enabled(self) -> bool:
        return bool(self.config.get("memory", {}).get("gdrive_sync_enabled", True))

    def set_gdrive_sync_enabled(self, enabled: bool) -> None:
        self.config.setdefault("memory", {})["gdrive_sync_enabled"] = bool(enabled)
        self.save_config()
        if enabled:
            self.sync_to_gdrive()

    @property
    def gdrive_account(self) -> str:
        return str(self.config.get("memory", {}).get("gdrive_account", "billbriework@gmail.com"))

    def get_gdrive_accounts(self) -> Dict[str, str]:
        return dict(self.config.get("memory", {}).get("gdrive_accounts", {}))

    def set_gdrive_account(self, account: str) -> str:
        self.config.setdefault("memory", {})["gdrive_account"] = account
        self.save_config()
        return self.sync_to_gdrive()

    @property
    def enable_gdrive_plugin(self) -> bool:
        return bool(self.config.get("codex", {}).get("enable_gdrive_plugin", False))

    def set_enable_gdrive_plugin(self, enabled: bool) -> None:
        self.config.setdefault("codex", {})["enable_gdrive_plugin"] = bool(enabled)
        self.save_config()

    # ------------------------------------------------------------------
    # Short-Term & Long-Term Memory + Google Drive Sync
    # ------------------------------------------------------------------
    def load_persona(self) -> str:
        if self.persona_path.exists():
            return self.persona_path.read_text(encoding="utf-8").strip()
        return "Kamu adalah Frieren. Jawab tenang, hangat, dan singkat dalam 2-3 kalimat."

    def load_memory(self) -> List[Dict[str, str]]:
        if not self.memory_path.exists():
            return []
        try:
            data = json.loads(self.memory_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data[-self.max_messages :]
        except Exception:
            pass
        return []

    def append_memory(self, role: str, text: str) -> List[Dict[str, str]]:
        history = self.load_memory()
        history.append(
            {
                "role": role,
                "text": text.strip(),
                "ts": datetime.now().isoformat(timespec="seconds"),
            }
        )
        history = history[-self.max_messages :]
        try:
            self.memory_path.write_text(
                json.dumps(history, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
        self.sync_to_gdrive()
        return history

    def load_ltm(self) -> List[Dict[str, str]]:
        if not self.ltm_path.exists():
            return []
        try:
            data = json.loads(self.ltm_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
        return []

    def add_ltm(self, fact: str) -> None:
        fact = fact.strip()
        if not fact:
            return
        facts = self.load_ltm()
        # Avoid exact duplicates
        if any(item.get("fact", "").lower() == fact.lower() for item in facts):
            return
        facts.append(
            {
                "fact": fact,
                "ts": datetime.now().isoformat(timespec="seconds"),
            }
        )
        facts = facts[-50:]  # Keep up to 50 core facts lightweight
        try:
            self.ltm_path.write_text(
                json.dumps(facts, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self._write_markdown_notes(facts)
        except Exception:
            pass
        self.sync_to_gdrive()

    def _write_markdown_notes(self, facts: List[Dict[str, str]]) -> None:
        lines = [
            "# ✦ Catatan Grimoire Frieren (Long-Term Memory)",
            f"_Terakhir diperbarui: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
            "",
            "## Fakta & Preferensi Pengguna",
        ]
        if not facts:
            lines.append("- _(Belum ada catatan khusus)_")
        else:
            for item in facts:
                lines.append(f"- **{item.get('ts', '')}**: {item.get('fact', '')}")
        self.notes_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def sync_to_gdrive(self) -> str:
        """Mirrors local memory files into the selected mounted Google Drive folder (0 token cost)."""
        if not self.gdrive_sync_enabled:
            return "Sync Google Drive nonaktif"
        accounts = self.get_gdrive_accounts()
        target_dir_str = accounts.get(self.gdrive_account)
        if not target_dir_str:
            return "Path Google Drive tidak ditemukan"
        target_dir = Path(target_dir_str)
        try:
            if not target_dir.parent.exists():
                return f"Folder Google Drive ({self.gdrive_account}) belum ter-mount"
            target_dir.mkdir(parents=True, exist_ok=True)
            for src in (self.memory_path, self.ltm_path, self.notes_path):
                if src.exists():
                    shutil.copy2(src, target_dir / src.name)
            return f"Tersinkron ke Google Drive ({self.gdrive_account})"
        except Exception as exc:
            return f"Gagal sync ke Google Drive: {exc}"

    def restore_from_gdrive(self) -> str:
        """Restores memory files from the selected Google Drive folder if present."""
        accounts = self.get_gdrive_accounts()
        target_dir_str = accounts.get(self.gdrive_account)
        if not target_dir_str:
            return "Akun Google Drive belum diatur"
        target_dir = Path(target_dir_str)
        if not target_dir.exists():
            return f"Belum ada folder backup di Google Drive ({self.gdrive_account})"
        restored = 0
        for dst in (self.memory_path, self.ltm_path, self.notes_path):
            src = target_dir / dst.name
            if src.exists():
                shutil.copy2(src, dst)
                restored += 1
        return f"Berhasil memuat {restored} file memori dari Google Drive ({self.gdrive_account})"

    def clear_memory(self, include_ltm: bool = False) -> None:
        try:
            self.memory_path.write_text("[]\n", encoding="utf-8")
            if include_ltm:
                self.ltm_path.write_text("[]\n", encoding="utf-8")
                self._write_markdown_notes([])
            self.sync_to_gdrive()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Zero-Token Instant Local Action Shortcut (e.g., "ingat ...", "buka https://...")
    # ------------------------------------------------------------------
    def _try_instant_local_command(self, user_message: str) -> Optional[CodexResult]:
        msg = user_message.strip()
        lower = msg.lower()

        # Instant memory save command: "ingat bahwa ..." / "tolong ingat ..."
        mem_match = re.match(r"^(?:frieren[, ]+)?(?:tolong\s+)?ingat(?:\s+ya|\s+bahwa|\s+kalau)?[:\s]+(.+)$", msg, re.I)
        if mem_match and len(msg) < 220:
            fact = mem_match.group(1).strip()
            self.add_ltm(fact)
            self.append_memory("user", user_message)
            reply = f"Baik, sudah kutulis di catatan grimoireku: \"{fact}\". Aku akan mengingatnya untukmu."
            self.append_memory("assistant", reply)
            sync_status = self.sync_to_gdrive()
            return CodexResult(
                speech=reply,
                cli_output=f"[LTM SAVED] {fact}\n[{sync_status}]",
                saved_memories=[fact],
                emotion="senang",
            )

        # Direct URL open without needing LLM tokens if message is just "buka <domain/url>"
        url_match = re.match(
            r"^(?:frieren[, ]+)?(?:tolong\s+)?(?:buka|bukakan|open)\s+(?:web(?:site)?\s+)?(https?://\S+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/\S*)?)$",
            msg,
            re.I,
        )
        if url_match and self.agent_execution_enabled:
            raw_url = url_match.group(1)
            url = raw_url if raw_url.startswith(("http://", "https://")) else f"https://{raw_url}"
            subprocess.Popen(["open", url])
            self.append_memory("user", user_message)
            reply = f"Sudah kubukakan `{url}` di browser untukmu. Semoga membantu pekerjaanmu ya."
            self.append_memory("assistant", reply)
            return CodexResult(
                speech=reply,
                cli_output=f"$ open {url}\n[Opened in default macOS browser - 0 token used]",
                saved_memories=[],
                emotion="antusias",
            )

        return None

    # ------------------------------------------------------------------
    # Prompt Builder & Non-Interactive `codex exec` (`gpt-6-luna`)
    # ------------------------------------------------------------------
    @staticmethod
    def _is_image_path(path_str: str) -> bool:
        ext = Path(path_str).suffix.lower()
        return ext in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

    def build_prompt(self, user_message: str, attachments: Optional[List[str]] = None) -> str:
        persona = self.load_persona()
        history = self.load_memory()
        ltm = self.load_ltm()
        attachments = attachments or []

        mode_desc = (
            "AKTIF (Kamu BISA menjalankan shell command seperti `open \"https://...\"` untuk membuka web/pencarian, "
            "membaca/menulis file, atau mengecek sistem jika diminta pengguna)."
            if self.agent_execution_enabled
            else "NONAKTIF / READ-ONLY (Jangan jalankan perintah modifikasi/buka aplikasi, cukup jawab atau analisis saja)."
        )

        lines = [
            "=== SYSTEM PERSONA ===",
            persona,
            f"\nStatus Mode Eksekusi Agent: {mode_desc}",
            "",
            "=== LONG-TERM MEMORY (CATATAN GRIMOIRE PENGGUNA) ===",
        ]
        if not ltm:
            lines.append("(Belum ada catatan jangka panjang)")
        else:
            for item in ltm[-15:]:
                lines.append(f"- {item.get('fact', '')}")

        lines.extend(["", "=== RIWAYAT CHAT TERAKHIR ==="])
        if not history:
            lines.append("(Belum ada percakapan sebelumnya)")
        else:
            for item in history[-self.max_messages :]:
                speaker = "User" if item.get("role") == "user" else "Frieren"
                lines.append(f"{speaker}: {item.get('text', '')}")

        if attachments:
            lines.extend(["", "=== LAMPIRAN FILE / GAMBAR DARI USER ==="])
            for idx, att in enumerate(attachments, 1):
                kind = "Gambar (juga dilampirkan ke vision -i)" if self._is_image_path(att) else "File / Path Lokal"
                lines.append(f"{idx}. [{kind}] `{att}`")
            lines.append(
                "Catatan: Jika berupa gambar, kamu bisa langsung melihatnya. Jika berupa file dokumen/kode/folder, "
                "kamu dapat membaca atau memeriksanya dari path di atas."
            )

        msg_clean = user_message.strip() or "Tolong lihat dan jelaskan lampiran gambar/file ini."
        lines.extend(
            [
                "",
                "=== PESAN / INSTRUKSI BARU DARI USER ===",
                f"User: {msg_clean}",
                "",
                "Instruksi Output:",
                "- Berikan ucapan Frieren (2-3 kalimat hangat).",
                "- Jika ada output perintah/kode/detail teknis, bungkus dalam blok ```output ... ```.",
                "- Jika ada fakta penting baru tentang user untuk diingat permanen, tambahkan [MEMORY_SAVE: fakta] di akhir.",
                "- Tambahkan suasana hatimu di akhir: [EMOTION: senang|hangat|antusias|penasaran|tenang|ceria|tersentuh|nostalgia|fokus|mengantuk].",
            ]
        )
        return "\n".join(lines)

    def ask(
        self,
        user_message: str,
        on_status: Optional[Callable[[str], None]] = None,
        attachments: Optional[List[str]] = None,
    ) -> CodexResult:
        attachments = [a for a in (attachments or []) if a and os.path.exists(a)]

        # 1. Check zero-token instant local handler first (only when no attachments)
        if not attachments:
            instant = self._try_instant_local_command(user_message)
            if instant is not None:
                return instant

        prompt = self.build_prompt(user_message, attachments=attachments)
        mem_user_text = user_message.strip()
        if attachments:
            att_names = ", ".join(Path(a).name for a in attachments)
            mem_user_text = f"{mem_user_text} [Lampiran: {att_names}]".strip()
        self.append_memory("user", mem_user_text)

        fd, out_path = tempfile.mkstemp(prefix="frieren_codex_", suffix=".txt")
        os.close(fd)

        try:
            cmd = [
                self.codex_bin,
                "exec",
                "-m",
                self.model,
                "-c",
                f'model_reasoning_effort="{self.reasoning_effort}"',
                "--skip-git-repo-check",
                "--ephemeral",
                "--color",
                "never",
                "--json",
            ]

            # Attach any image files via Codex native `-i` vision flag
            for att in attachments:
                if self._is_image_path(att):
                    cmd.extend(["-i", att])

            # Sandbox & execution permissions
            if self.agent_execution_enabled:
                cmd.append("--dangerously-bypass-approvals-and-sandbox")
            else:
                cmd.extend(["--sandbox", "read-only"])

            # Keep MCP fast unless user explicitly enabled Google Drive plugin
            if not self.enable_gdrive_plugin:
                cmd.extend(["-c", "mcp_servers={}"])

            cmd.extend(["-o", out_path, prompt])

            cli_logs: List[str] = ["$ codex exec"]
            proc = subprocess.Popen(
                cmd,
                cwd=str(Path.home()),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "NO_COLOR": "1"},
            )

            # Stream JSONL events to capture executed commands & tool calls live
            if proc.stdout:
                for raw_line in proc.stdout:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        evt = json.loads(line)
                        etype = evt.get("type", "")
                        item = evt.get("item", {})
                        if isinstance(item, dict):
                            itype = item.get("type", "")
                            if itype == "command_execution":
                                c_str = item.get("command", "")
                                if c_str and etype == "item.started":
                                    cli_logs.append(f"\n> {c_str}")
                                    if on_status:
                                        on_status(self._humanize_action(c_str))
                                elif etype == "item.completed":
                                    agg_out = (item.get("aggregated_output") or "").strip()
                                    exit_code = item.get("exit_code", 0)
                                    if agg_out:
                                        cli_logs.append(agg_out[:1500])
                                    cli_logs.append(f"[exit code: {exit_code}]")
                            elif itype in ("web_search_call", "web_search") and on_status:
                                q = item.get("query") or ""
                                on_status(f"Sedang mengintip halaman web{f' ({q[:24]})' if q else ''}... ✦")
                            elif itype in ("mcp_tool_call", "tool_call") and on_status:
                                tname = item.get("name") or item.get("tool_name") or "catatan"
                                on_status(f"Sedang membuka {tname}... ♪")
                            elif itype == "reasoning" and etype == "item.started" and on_status:
                                cute_thinks = [
                                    "Hmm, tunggu sebentar ya, lagi kupikirkan... ✦",
                                    "Sedang membolak-balik halaman grimoire... ♪",
                                    "Emm... lagi merangkai kata-kata yang pas buatmu~",
                                    "Sebentar ya, Frieren lagi mikir keras nih... (・ω・)",
                                    "Lagi mengingat-ingat mantra yang cocok... ✦",
                                ]
                                on_status(random.choice(cute_thinks))
                    except Exception:
                        pass

            proc.wait(timeout=self.timeout_seconds)

            raw_reply = ""
            if os.path.exists(out_path):
                raw_reply = Path(out_path).read_text(encoding="utf-8").strip()

            if not raw_reply:
                stderr_txt = (proc.stderr.read() if proc.stderr else "").strip()
                detail = stderr_txt.splitlines()[-1] if stderr_txt else f"exit code {proc.returncode}"
                return CodexResult(
                    speech=f"Hmm... catatan grimoire sedang sulit dibuka ({detail}). Coba sebentar lagi ya.",
                    cli_output="\n".join(cli_logs) + (f"\n[STDERR]\n{stderr_txt}" if stderr_txt else ""),
                    saved_memories=[],
                )

            speech, extracted_block, saved_memories, emotion = self._parse_response(raw_reply)
            for fact in saved_memories:
                self.add_ltm(fact)

            if extracted_block:
                cli_logs.append("\n=== CODEX OUTPUT ===\n" + extracted_block)
            else:
                cli_logs.append("\n=== RESPONSE ===\n" + speech)

            if saved_memories:
                cli_logs.append("\n=== MEMORY SAVED ===\n" + "\n".join(f"- {m}" for m in saved_memories))

            self.append_memory("assistant", speech)
            return CodexResult(
                speech=speech,
                cli_output="\n".join(cli_logs).strip(),
                saved_memories=saved_memories,
                emotion=emotion,
            )

        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
            return CodexResult(
                speech="Maaf ya, mantranya butuh waktu terlalu lama untuk dirapalkan. Ayo coba perintah yang lebih singkat.",
                cli_output="[Timeout setelah menunggu eksekusi Codex CLI]",
                saved_memories=[],
            )
        except Exception as exc:
            return CodexResult(
                speech=f"Ada gangguan sihir kecil saat menghubungi Codex: {exc}",
                cli_output=f"[Exception] {exc}",
                saved_memories=[],
            )
        finally:
            try:
                if os.path.exists(out_path):
                    os.remove(out_path)
            except OSError:
                pass

    @staticmethod
    def _parse_response(raw_text: str) -> tuple[str, str, List[str], Optional[str]]:
        text = raw_text.strip()
        if text.lower().startswith("frieren:"):
            text = text.split(":", 1)[1].strip()

        # 1. Extract [MEMORY_SAVE: ...] tags
        saved_memories: List[str] = []
        for match in re.finditer(r"\[MEMORY_SAVE:\s*(.+?)\]", text, flags=re.I | re.S):
            fact = match.group(1).strip()
            if fact:
                saved_memories.append(fact)
        text = re.sub(r"\[MEMORY_SAVE:\s*.+?\]", "", text, flags=re.I | re.S).strip()

        # 1b. Extract [EMOTION: ...] tag
        emotion: Optional[str] = None
        emo_match = re.search(r"\[EMOTION:\s*([a-zA-Z_-]+)\s*\]", text, flags=re.I)
        if emo_match:
            emotion = emo_match.group(1).strip().lower()
        text = re.sub(r"\[EMOTION:\s*[^\]]+\]", "", text, flags=re.I).strip()

        # 2. Extract ```output ... ``` or any fenced code blocks into Codex Output panel
        extracted_blocks: List[str] = []
        for match in re.finditer(r"```(?:output|[a-zA-Z0-9_-]*)\n(.*?)```", text, flags=re.S):
            block_content = match.group(1).strip()
            if block_content:
                extracted_blocks.append(block_content)

        speech = re.sub(r"```(?:output|[a-zA-Z0-9_-]*)\n.*?```", "", text, flags=re.S).strip()
        if not speech:
            speech = "Sudah selesai kupersiapkan. Kamu bisa melihat detail hasilnya di panel Output Codex (ikon 💻) ya."

        return speech, "\n\n".join(extracted_blocks), saved_memories, emotion

    @staticmethod
    def _humanize_action(cmd_str: str) -> str:
        """Translates a raw shell command into a friendly Indonesian activity status."""
        c = cmd_str.strip()
        # Strip shell wrapper if present (e.g., `/bin/zsh -lc "..."`)
        m_wrap = re.search(r'(?:zsh|bash|sh)\s+-l?c\s+[\'"]?(.+?)[\'"]?$', c)
        if m_wrap:
            c = m_wrap.group(1).strip()

        url_m = re.search(r'https?://([^\s\'"<>]+)', c)
        if re.search(r'\bopen\s+https?://', c) and url_m:
            return f"Sedang membuka web {url_m.group(1)[:28]}..."
        if re.search(r'\b(curl|wget|fetch|http)\b', c):
            if url_m:
                return f"Sedang membaca halaman {url_m.group(1)[:26]}..."
            return "Sedang mengambil data dari web..."
        if re.search(r'\bgit\s+(status|log|diff|branch)\b', c):
            return "Sedang memeriksa repositori Git..."
        if re.search(r'\b(rg|grep|find|fd)\b', c):
            return f"Sedang mencari file / kode ({c[:26]})..."
        if re.search(r'\b(ls|tree|stat)\b', c):
            return f"Sedang melihat isi folder ({c[:26]})..."
        if re.search(r'\b(cat|head|tail|sed|awk)\b', c):
            return f"Sedang membaca isi file ({c[:26]})..."
        if re.search(r'\b(python3?|node|npm|pytest|cargo)\b', c):
            return f"Sedang menjalankan proses ({c[:26]})..."
        return f"Sedang memproses: {c[:32]}..."
