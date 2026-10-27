"""Small helpers used by several modules (Step 0 - repo skeleton)."""


def format_size(num_bytes):
    """Turn a byte count into a readable string, e.g. 2048 -> '2.00 KB'."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.2f} {unit}"
        size /= 1024