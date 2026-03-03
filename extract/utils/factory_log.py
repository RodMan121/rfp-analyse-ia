import json
import datetime
import os
from pathlib import Path

class ProductionLogger:
    """Système de log industriel optimisé pour les gros volumes."""
    def __init__(self, log_file: str = "data/factory_production.json"):
        self.log_path = Path(log_file)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._buffer = []
        self._buffer_limit = 20 # FIX P3.8 : Accumulation en mémoire

    def log_event(self, phase: str, status: str, message: str, details: dict = None):
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "phase": phase,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self._buffer.append(log_entry)
        
        # Flush si on dépasse la limite ou si c'est une erreur critique
        if len(self._buffer) >= self._buffer_limit or status == "ERROR":
            self.flush()

    def flush(self):
        """Écrit le buffer dans le fichier JSON de manière atomique."""
        if not self._buffer:
            return
            
        logs = self._read_log()
        logs.extend(self._buffer)
        self._write_log(logs)
        self._buffer = []

    def _read_log(self) -> list:
        if not self.log_path.exists():
            return []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_log(self, logs: list):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

# Instance unique
factory_logger = ProductionLogger()
