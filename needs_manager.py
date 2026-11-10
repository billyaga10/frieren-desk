"""
Frieren Needs & Wellness System
Lightweight, non-punitive body-double companion tracker:
- Thirst (0-100): Decreases ~20 per hour.
- Hunger (0-100): Decreases ~15 per hour.
- Energy (0-100): Decreases ~12 per hour (faster at night >22:00).
- Freshness/Cozy (0-100): Decreases ~25 per hour of continuous typing/activity.

Provides gentle wellness reminders for the user as well.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


class NeedsManager:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.needs_path = self.base_dir / "needs.json"
        self.data: Dict[str, float] = {
            "thirst": 85.0,
            "hunger": 80.0,
            "energy": 90.0,
            "freshness": 85.0,
        }
        self.last_update_ts: str = datetime.now().isoformat(timespec="seconds")
        self._load()

    def _load(self) -> None:
        if self.needs_path.exists():
            try:
                raw = json.loads(self.needs_path.read_text(encoding="utf-8"))
                for k in ("thirst", "hunger", "energy", "freshness"):
                    if k in raw:
                        self.data[k] = max(0.0, min(100.0, float(raw[k])))
                self.last_update_ts = raw.get("last_update_ts", datetime.now().isoformat(timespec="seconds"))
            except Exception:
                pass

    def save(self) -> None:
        try:
            payload = {
                **self.data,
                "last_update_ts": self.last_update_ts,
            }
            self.needs_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def tick(self, elapsed_seconds: float = 60.0) -> Optional[Tuple[str, str, str]]:
        """
        Simulates natural decay over elapsed_seconds.
        Returns Optional[(need_key, reminder_text, target_pose)] if any need is low and needs attention.
        """
        hours = elapsed_seconds / 3600.0
        now = datetime.now()

        # Decay rates per hour
        thirst_decay = 20.0 * hours
        hunger_decay = 15.0 * hours
        # Energy drains a bit faster at night (22:00 - 06:00)
        is_night = now.hour >= 22 or now.hour < 6
        energy_decay = (18.0 if is_night else 10.0) * hours
        freshness_decay = 20.0 * hours

        self.data["thirst"] = max(10.0, min(100.0, self.data["thirst"] - thirst_decay))
        self.data["hunger"] = max(10.0, min(100.0, self.data["hunger"] - hunger_decay))
        self.data["energy"] = max(10.0, min(100.0, self.data["energy"] - energy_decay))
        self.data["freshness"] = max(10.0, min(100.0, self.data["freshness"] - freshness_decay))

        self.last_update_ts = now.isoformat(timespec="seconds")
        self.save()

        # Check for gentle reminders (non-intrusive)
        if self.data["thirst"] < 35.0:
            return (
                "thirst",
                "Hmm... tenggorokanku agak haus. Ada teh hangat atau air putih? Kamu juga jangan lupa minum ya ☕",
                "needs_tea",
            )
        if self.data["hunger"] < 30.0:
            return (
                "hunger",
                "Perutku mulai bersuara kecil... kira-kira camilan manis atau makanan enak apa ya? Jangan lupa makan ya 🍰",
                "needs_hungry",
            )
        if self.data["energy"] < 30.0:
            return (
                "energy",
                "Uwah... mataku agak berat dan mengantuk. Kalau lelah, istirahat sejenak tidak apa-apa kok 💤",
                "needs_sleepy",
            )
        if self.data["freshness"] < 30.0:
            return (
                "freshness",
                "Sudah cukup lama kamu menatap layar. Ayo regangkan kedua tangan dan punggungmu sebentar 🌿",
                "needs_stretch",
            )
        return None

    def replenish(self, need_key: str, amount: float = 40.0) -> str:
        """Replenishes a specific need when user feeds/waters/rests Frieren."""
        if need_key not in self.data:
            return "Kebutuhan tidak dikenal."
        self.data[need_key] = min(100.0, self.data[need_key] + amount)
        self.save()

        responses = {
            "thirst": "Segar sekali... terima kasih tehnya! Tubuh terasa lebih hangat sekarang ☕♪",
            "hunger": "Wah, hamburg steak / kuenya enak sekali! Enerjiku sudah kembali 🍰✦",
            "energy": "Hooam... setelah tidur sebentar, kepalaku jadi jernih lagi. Semangat! 💤✨",
            "freshness": "Tarik napas dalam-dalam... regangkan badan. Rasanya segar sekali 🌿♪",
        }
        return responses.get(need_key, "Terima kasih sudah memperhatikanku ✦")

    def replenish_all(self) -> str:
        for k in self.data:
            self.data[k] = 100.0
        self.save()
        return "Semua kebutuhan Frieren sudah terpenuhi! Siap menemani petualangan dan kerjamu ✦"
