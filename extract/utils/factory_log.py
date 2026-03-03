import json
import datetime
from pathlib import Path
from typing import Dict, Any


class ProductionLogger:
    """Gère le journal de bord de l'Usine à RFP."""

    def __init__(self, log_path: str = "data/production_log.json"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self._write_log([])

    def _read_log(self):
        with open(self.log_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_log(self, data):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def log_event(
        self, phase: str, event_type: str, message: str, details: Dict[str, Any] = None
    ):
        """Ajoute un événement au journal."""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "phase": phase,
            "type": event_type,
            "message": message,
            "details": details or {},
        }
        logs = self._read_log()
        logs.append(log_entry)
        self._write_log(logs)


# Instance globale
factory_logger = ProductionLogger()
