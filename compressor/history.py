
"""BL19 - Store recent compression and decompression history in JSON."""

import json
from datetime import datetime, timezone
from pathlib import Path


MAX_HISTORY_ENTRIES = 100
DEFAULT_HISTORY_FILE = Path.home() / ".file_compression_tool" / "history.json"


class CompressionHistory:
    """Manage a JSON history of compression and decompression operations."""

    def __init__(self, history_file=DEFAULT_HISTORY_FILE, max_entries=MAX_HISTORY_ENTRIES):
        if not isinstance(max_entries, int) or isinstance(max_entries, bool):
            raise TypeError("max_entries must be an integer.")
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1.")

        self.history_file = Path(history_file)
        self.max_entries = max_entries

    def get_history(self):
        """Return history entries, safely handling missing or damaged JSON."""
        try:
            with self.history_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(data, list):
            return []

        return [
            entry for entry in data
            if isinstance(entry, dict)
        ][-self.max_entries:]

    def add_entry(self, operation, input_file, output_file, **details):
        """Record an operation and return the saved entry."""
        if operation not in ("compression", "decompression"):
            raise ValueError(
                "operation must be 'compression' or 'decompression'."
            )

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "input_file": str(input_file),
            "output_file": str(output_file),
            **details,
        }

        # Keep metadata JSON-serializable and reject invalid values safely.
        try:
            json.dumps(entry)
        except (TypeError, ValueError) as error:
            raise ValueError("History details must be JSON-serializable.") from error

        entries = self.get_history()
        entries.append(entry)
        entries = entries[-self.max_entries:]

        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = self.history_file.with_suffix(
            self.history_file.suffix + ".tmp"
        )

        try:
            with temporary_file.open("w", encoding="utf-8") as file:
                json.dump(entries, file, indent=2, ensure_ascii=False)
            temporary_file.replace(self.history_file)
        finally:
            if temporary_file.exists():
                temporary_file.unlink()

        return entry

    def clear_history(self):
        """Clear saved history."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text("[]", encoding="utf-8")
