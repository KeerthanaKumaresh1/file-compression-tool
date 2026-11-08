"""
File Compression Tool — Five-Tab Tkinter GUI
Huffman Coding / HFC1 format

Run from the project root:
    py gui.py

Tabs:
1. Compress File
2. Decompress File
3. Huffman Explorer
4. Statistics & Performance
5. Compression History

The GUI uses the project's compressor package. History and performance
measurements shown here are for the current GUI session; this GUI does not
claim persistent history or background benchmarking.

The Compress File tab also offers batch compression of several files at
once (US-10), and warns when a compressed file would not be smaller than
the original (use-case flow A2).
"""

import os
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def _find_compressor_package():
    """Find the folder that contains the project's `compressor` package.

    This file works wherever it is saved: next to the package, or in a
    folder that contains the project folder (for example
    Downloads\\GITHUB\\file-compression-tool-main).
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [here]
    try:
        for name in os.listdir(here):
            path = os.path.join(here, name)
            if os.path.isdir(path):
                candidates.append(path)
    except OSError:
        pass
    parent = here
    for _ in range(3):
        parent = os.path.dirname(parent)
        if parent:
            candidates.append(parent)
    for folder in candidates:
        if os.path.isdir(os.path.join(folder, "compressor")):
            return folder
    return None


_PKG_DIR = _find_compressor_package()
if _PKG_DIR is None:
    print(
        "ERROR: could not find the 'compressor' folder.\n"
        "Save this file in the project folder, next to main.py "
        "(the folder that contains the 'compressor' folder), "
        "then run it again.",
        file=sys.stderr,
    )
    _root = tk.Tk()
    _root.withdraw()
    messagebox.showerror(
        "compressor package not found",
        "This file needs the project's 'compressor' folder next to it.\n\n"
        "Save gui.py in the project folder, next to main.py\n"
        "(the folder that contains the 'compressor' folder),\n"
        "then run it again.",
    )
    sys.exit(1)
sys.path.insert(0, _PKG_DIR)

from compressor.batch_compression import compress_files
from compressor.errors import (
    CompressionError,
    CorruptedFileError,
    FileValidationError,
    OutputExistsError,
)
from compressor.frequency import calculate_frequencies
from compressor.huffman_tree import build_huffman_tree
from compressor.huffman_codes import generate_huffman_codes
from compressor.file_format import MAX_FILE_SIZE, build_compressed_bytes
from compressor.decompressor import decompress_bytes
from compressor.tree_visualizer import render_tree
from compressor.huffman_code_table import build_huffman_code_table
from compressor.compression_stats import calculate_statistics, format_statistics
from compressor.utils import format_size


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

COLORS = {
    "window": "#0B1220",
    "surface": "#111C2E",
    "panel": "#17263D",
    "panel_light": "#20334F",
    "input": "#0D1728",
    "accent": "#3B82F6",
    "accent_hover": "#2563EB",
    "accent_soft": "#193B70",
    "text": "#F8FAFC",
    "muted": "#A8B8CC",
    "subtle": "#71839B",
    "success": "#34D399",
    "border": "#2B3D57",
}


class FileCompressionGUI:
    """Five-tab desktop interface for the Huffman compression project."""

    def __init__(self, root):
        self.root = root
        self.root.title("File Compression Tool | Huffman Coding")
        self.root.geometry("1080x750")
        self.root.minsize(850, 620)
        self.root.configure(bg=COLORS["window"])

        self.history = []
        self.last_performance = None

        self.compress_path = tk.StringVar()
        self.status = tk.StringVar(value="Ready — choose an operation.")

        self._configure_styles()
        self._build_interface()

    # ------------------------------------------------------------------
    # Styling and shared UI helpers
    # ------------------------------------------------------------------

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "App.TNotebook",
            background=COLORS["window"],
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "App.TNotebook.Tab",
            background=COLORS["panel"],
            foreground=COLORS["muted"],
            padding=(15, 12),
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
        )
        style.map(
            "App.TNotebook.Tab",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", "#FFFFFF")],
        )
        style.configure(
            "App.Vertical.TScrollbar",
            background=COLORS["panel_light"],
            troughcolor=COLORS["input"],
            bordercolor=COLORS["input"],
            arrowcolor=COLORS["muted"],
        )
        style.configure(
            "App.Treeview",
            background=COLORS["input"],
            fieldbackground=COLORS["input"],
            foreground=COLORS["text"],
            rowheight=28,
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        style.configure(
            "App.Treeview.Heading",
            background=COLORS["panel_light"],
            foreground=COLORS["text"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
        )
        style.map(
            "App.Treeview",
            background=[("selected", COLORS["accent_soft"])],
            foreground=[("selected", COLORS["text"])],
        )

    def _build_interface(self):
        header = tk.Frame(self.root, bg=COLORS["window"])
        header.pack(fill="x", padx=26, pady=(20, 13))

        tk.Label(
            header,
            text="FILE COMPRESSION TOOL",
            font=("Segoe UI", 22, "bold"),
            fg=COLORS["text"],
            bg=COLORS["window"],
        ).pack(anchor="w")

        tk.Label(
            header,
            text="HUFFMAN CODING  •  COMPRESS  •  DECOMPRESS  •  EXPLORE",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["muted"],
            bg=COLORS["window"],
        ).pack(anchor="w", pady=(5, 0))

        self.tabs = ttk.Notebook(self.root, style="App.TNotebook")
        self.tabs.pack(fill="both", expand=True, padx=26, pady=(0, 13))

        self.compress_tab = tk.Frame(self.tabs, bg=COLORS["surface"])
        self.decompress_tab = tk.Frame(self.tabs, bg=COLORS["surface"])
        self.explorer_tab = tk.Frame(self.tabs, bg=COLORS["surface"])
        self.performance_tab = tk.Frame(self.tabs, bg=COLORS["surface"])
        self.history_tab = tk.Frame(self.tabs, bg=COLORS["surface"])

        self.tabs.add(self.compress_tab, text="  Compress File  ")
        self.tabs.add(self.decompress_tab, text="  Decompress File  ")
        self.tabs.add(self.explorer_tab, text="  Huffman Explorer  ")
        self.tabs.add(self.performance_tab, text="  Statistics & Performance  ")
        self.tabs.add(self.history_tab, text="  Compression History  ")

        self._build_compress_tab()
        self._build_decompress_tab()
        self._build_explorer_tab()
        self._build_performance_tab()
        self._build_history_tab()

        status_bar = tk.Frame(self.root, bg=COLORS["input"])
        status_bar.pack(fill="x", side="bottom")
        tk.Label(
            status_bar,
            textvariable=self.status,
            anchor="w",
            bg=COLORS["input"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            padx=15,
            pady=9,
        ).pack(fill="x")

    def _section_heading(self, parent, title, subtitle):
        block = tk.Frame(parent, bg=COLORS["surface"])
        block.pack(fill="x", padx=23, pady=(22, 17))

        tk.Label(
            block,
            text=title,
            font=("Segoe UI", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["surface"],
        ).pack(anchor="w")

        tk.Label(
            block,
            text=subtitle,
            font=("Segoe UI", 9),
            fg=COLORS["muted"],
            bg=COLORS["surface"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(5, 0))

    def _button(self, parent, text, command, secondary=False):
        background = COLORS["panel_light"] if secondary else COLORS["accent"]
        active = COLORS["border"] if secondary else COLORS["accent_hover"]
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=background,
            fg=COLORS["text"],
            activebackground=active,
            activeforeground=COLORS["text"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=15,
            pady=10,
            cursor="hand2",
            highlightthickness=0,
        )

    def _text_area(self, parent, wrap="word"):
        frame = tk.Frame(parent, bg=COLORS["input"])
        frame.pack(fill="both", expand=True, padx=23, pady=(0, 22))

        widget = tk.Text(
            frame,
            bg=COLORS["input"],
            fg="#DCE8F8",
            insertbackground=COLORS["text"],
            selectbackground=COLORS["accent_soft"],
            font=("Consolas", 10),
            relief="flat",
            bd=0,
            padx=13,
            pady=11,
            wrap=wrap,
            state="disabled",
        )
        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=widget.yview,
            style="App.Vertical.TScrollbar",
        )
        widget.configure(yscrollcommand=scrollbar.set)
        widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return widget

    @staticmethod
    def _set_text(widget, content):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", content)
        widget.configure(state="disabled")

    @staticmethod
    def _read_file(path):
        with open(path, "rb") as file:
            return file.read()

    @staticmethod
    def _friendly_error(error):
        """Turn an exception into a short message a user can act on.

        The project's own errors already carry plain messages, so they are
        shown as they are. Anything unexpected becomes one plain sentence
        instead of raw technical text (SR-8).
        """
        if isinstance(error, CompressionError):
            return str(error)
        if isinstance(error, FileNotFoundError):
            return "The file was not found."
        if isinstance(error, PermissionError):
            return "No permission to read or write that file."
        if isinstance(error, OSError):
            if error.errno == 28:  # No space left on device
                return "There is not enough free space to save the file."
            return ("The file could not be read or written. Check the file "
                    "and the folder, then try again.")
        return ("Something went wrong and the operation was stopped. "
                "No files were changed.")

    def _input_size_ok(self, path):
        """True when `path` is within the supported size limit (SR-6).

        Checked before the file is read, so an oversized file is refused
        without being loaded into memory first.
        """
        try:
            size = os.path.getsize(path)
        except OSError:
            messagebox.showerror(
                "Invalid file", "The selected file cannot be read."
            )
            return False
        if size > MAX_FILE_SIZE:
            messagebox.showerror(
                "File too large",
                f"This file is {format_size(size)}.\n"
                f"Files larger than {format_size(MAX_FILE_SIZE)} "
                "are not supported.",
            )
            return False
        return True

    @staticmethod
    def _format_stats_lines(stats):
        """Render the statistics dict from format_statistics as clean,
        aligned lines instead of a raw dict dump."""
        return "\n".join(
            f"{key:<24}: {value}" for key, value in stats.items()
        )

    @staticmethod
    def _write_new_file(path, data, overwrite=False):
        """Write an output file. Without overwrite, an existing file is
        never replaced (exclusive creation raises FileExistsError)."""
        mode = "wb" if overwrite else "xb"
        with open(path, mode) as file:
            file.write(data)

    def _write_with_overwrite_prompt(self, path, data, what="output",
                                     save_dialog=None):
        """Write `data` to `path`, asking before replacing an existing file.

        If the save fails (for example the disk is full), and `save_dialog`
        is given, the user is offered another location and the write is
        retried there (use-case flow A3).

        Returns (written, final_path): `written` is True when the file was
        written, and `final_path` is where it ended up.
        """
        current = path
        overwrite = False
        while True:
            try:
                self._write_new_file(current, data, overwrite=overwrite)
                return True, current
            except FileExistsError:
                if messagebox.askyesno(
                    "Output already exists",
                    f"'{os.path.basename(current)}' already exists.\n\n"
                    f"Overwrite it? (The existing {what} will be replaced.)",
                ):
                    overwrite = True
                    continue
                self.status.set(
                    f"Stopped — the existing {what} was not changed."
                )
                return False, None
            except OSError as error:
                if save_dialog is None:
                    raise
                if not messagebox.askyesno(
                    "Could not save the file",
                    f"{self._friendly_error(error)}\n\n"
                    "Choose another location?",
                ):
                    self.status.set("Save cancelled.")
                    return False, None
                new_path = save_dialog()
                if not new_path:
                    self.status.set("Save cancelled.")
                    return False, None
                current = new_path
                overwrite = False

    def _record_history(self, operation, source, output, input_size,
                        output_size, elapsed=None):
        self.history.insert(
            0,
            {
                "operation": operation,
                "source": os.path.basename(source),
                "output": os.path.basename(output),
                "input_size": input_size,
                "output_size": output_size,
                "elapsed": elapsed,
            },
        )
        self.refresh_history()

    # ------------------------------------------------------------------
    # Tab 1 — Compress File
    # ------------------------------------------------------------------

    def _build_compress_tab(self):
        self._section_heading(
            self.compress_tab,
            "Compress a file",
            "Choose a local file and create an HFC1 compressed output using "
            "the project's Huffman coding implementation.",
        )

        picker = tk.Frame(self.compress_tab, bg=COLORS["surface"])
        picker.pack(fill="x", padx=23, pady=(0, 12))

        tk.Entry(
            picker,
            textvariable=self.compress_path,
            bg=COLORS["input"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=("Segoe UI", 10),
            bd=0,
        ).pack(side="left", fill="x", expand=True, ipady=12, padx=(0, 9))

        self._button(
            picker, "Browse files", self.choose_compress_file, secondary=True
        ).pack(side="left")

        # Shown right under the file box, so it is visible however the
        # path got in there (Browse button, or typed/pasted by hand).
        self.selected_info = tk.Label(
            self.compress_tab,
            text="No file selected yet.",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.selected_info.pack(fill="x", padx=23, pady=(0, 2))
        self.compress_path.trace_add("write", self._on_compress_path_changed)

        actions = tk.Frame(self.compress_tab, bg=COLORS["surface"])
        actions.pack(fill="x", padx=23, pady=(4, 16))

        self._button(
            actions, "Compress Selected File", self.compress_file
        ).pack(side="left")

        self._button(
            actions, "Compress Multiple Files", self.compress_multiple_files,
            secondary=True
        ).pack(side="left", padx=(9, 0))

        tk.Label(
            actions,
            text="Output format: .hfc",
            bg=COLORS["surface"],
            fg=COLORS["subtle"],
            font=("Segoe UI", 9),
        ).pack(side="left", padx=13)

        self.compress_output = self._text_area(self.compress_tab)
        self._set_text(
            self.compress_output,
            "READY TO COMPRESS\n"
            "────────────────────────────────────────────\n\n"
            "1. Browse and select a non-empty file.\n"
            "2. Click Compress Selected File.\n"
            "3. Choose a destination for the .hfc file.\n\n"
            "The compression result and statistics will appear here.",
        )

    def _on_compress_path_changed(self, *_args):
        """Show the selected file's name and size however the path was
        entered (Browse button, or typed/pasted into the box)."""
        path = self.compress_path.get().strip()
        if not path:
            self.selected_info.configure(text="No file selected yet.")
            return
        if os.path.isfile(path):
            info = (
                f"Selected: {os.path.basename(path)} "
                f"({format_size(os.path.getsize(path))})"
            )
        else:
            info = f"Selected: {os.path.basename(path)} (file not found)"
        self.selected_info.configure(text=info)
        self.status.set(info)

    def choose_compress_file(self):
        path = filedialog.askopenfilename(title="Choose a file to compress")
        if path:
            self.compress_path.set(path)

    def compress_file(self):
        source = self.compress_path.get().strip()

        if not source:
            messagebox.showwarning("Select a file", "Choose a file first.")
            return
        if not os.path.isfile(source):
            messagebox.showerror("Invalid file", "The selected file does not exist.")
            return
        if not self._input_size_ok(source):
            return

        output = filedialog.asksaveasfilename(
            title="Save compressed file",
            initialfile=os.path.basename(source) + ".hfc",
            defaultextension=".hfc",
            filetypes=[("Huffman compressed files", "*.hfc"), ("All files", "*.*")],
        )
        if not output:
            self.status.set("Compression cancelled.")
            return
        if os.path.abspath(source) == os.path.abspath(output):
            messagebox.showerror(
                "Invalid output",
                "The compressed output cannot replace the original file.",
            )
            return

        try:
            data = self._read_file(source)
            if not data:
                messagebox.showwarning("Empty file", "Choose a non-empty file.")
                return

            self.status.set("Compressing file...")
            self.root.update_idletasks()
            start = time.perf_counter()

            frequencies = calculate_frequencies(data)
            tree = build_huffman_tree(frequencies)
            codes = generate_huffman_codes(tree)
            compressed = build_compressed_bytes(data, frequencies, codes)
            elapsed = time.perf_counter() - start

            # Use-case flow A2: warn when compression does not shrink the
            # file, and let the user keep it or cancel before anything is
            # written.
            kept_anyway = False
            if len(compressed) >= len(data):
                if not messagebox.askyesno(
                    "No size reduction",
                    f"The compressed file ({format_size(len(compressed))}) "
                    f"is not smaller than the original "
                    f"({format_size(len(data))}).\n\n"
                    "Keep the compressed file anyway?",
                ):
                    self.status.set(
                        "Compression cancelled — no size reduction achieved."
                    )
                    return
                kept_anyway = True

            written, output = self._write_with_overwrite_prompt(
                output,
                compressed,
                save_dialog=lambda: filedialog.asksaveasfilename(
                    title="Save compressed file",
                    initialfile=os.path.basename(source) + ".hfc",
                    defaultextension=".hfc",
                    filetypes=[("Huffman compressed files", "*.hfc"),
                               ("All files", "*.*")],
                ),
            )
            if not written:
                return

            stats = calculate_statistics(len(data), len(compressed))
            stats_text = self._format_stats_lines(format_statistics(stats))
            self._set_text(
                self.compress_output,
                "COMPRESSION SUCCESSFUL\n"
                "════════════════════════════════════════════\n\n"
                f"Input file      : {source}\n"
                f"Output file     : {output}\n\n"
                f"Original size   : {len(data):,} bytes\n"
                f"Compressed size : {len(compressed):,} bytes\n"
                f"Elapsed time    : {elapsed:.6f} seconds\n\n"
                "COMPRESSION STATISTICS\n"
                "────────────────────────────────────────────\n"
                f"{stats_text}\n"
                "Compression ratio (compressed ÷ original): "
                f"{len(compressed) / len(data):.2f}\n\n"
                + (
                    "Note: the compressed file is not smaller than the "
                    "original — kept at your choice.\n\n"
                    if kept_anyway else ""
                )
                + "The original file was not modified.",
            )

            self.last_performance = {
                "operation": "Compression",
                "source": os.path.basename(source),
                "input_size": len(data),
                "output_size": len(compressed),
                "elapsed": elapsed,
            }
            self._record_history(
                "Compression", source, output, len(data), len(compressed), elapsed
            )
            self.status.set("Compression completed successfully.")
            messagebox.showinfo("Compression complete", "Your file was compressed.")

        except FileExistsError:
            messagebox.showerror(
                "Output already exists",
                "Choose a different output name. The existing file was not changed.",
            )
            self.status.set("Compression stopped — output already exists.")
        except Exception as error:
            messagebox.showerror(
                "Compression failed", self._friendly_error(error)
            )
            self.status.set("Compression failed.")

    def compress_multiple_files(self):
        """Batch compression (US-10): compress several files at once."""
        paths = filedialog.askopenfilenames(title="Choose files to compress")
        if not paths:
            return

        output_dir = filedialog.askdirectory(
            title="Choose the folder for the .hfc files"
        )
        if not output_dir:
            self.status.set("Batch compression cancelled.")
            return

        for path in paths:
            if not self._input_size_ok(path):
                return

        self.status.set(f"Compressing {len(paths)} files...")
        self.root.update_idletasks()

        try:
            start = time.perf_counter()
            results = compress_files(paths, output_dir=output_dir)
            elapsed = time.perf_counter() - start
        except OutputExistsError as error:
            if messagebox.askyesno(
                "Output already exists",
                f"{error}\n\nOverwrite the existing output files?",
            ):
                try:
                    start = time.perf_counter()
                    results = compress_files(
                        paths, output_dir=output_dir, overwrite=True
                    )
                    elapsed = time.perf_counter() - start
                except Exception as error:
                    messagebox.showerror(
                        "Batch compression failed",
                        self._friendly_error(error),
                    )
                    self.status.set("Batch compression failed.")
                    return
            else:
                self.status.set(
                    "Batch compression stopped — existing files were not changed."
                )
                return
        except (ValueError, CompressionError) as error:
            messagebox.showerror(
                "Batch compression failed", self._friendly_error(error)
            )
            self.status.set("Batch compression failed.")
            return
        except OSError as error:
            # Use-case flow A3: a failed save offers another location.
            if not messagebox.askyesno(
                "Could not save the files",
                f"{self._friendly_error(error)}\n\n"
                "Choose another folder and try again?",
            ):
                self.status.set("Batch compression cancelled.")
                return
            new_dir = filedialog.askdirectory(
                title="Choose another folder for the .hfc files"
            )
            if not new_dir:
                self.status.set("Batch compression cancelled.")
                return
            try:
                start = time.perf_counter()
                results = compress_files(paths, output_dir=new_dir)
                elapsed = time.perf_counter() - start
            except Exception as error:
                messagebox.showerror(
                    "Batch compression failed", self._friendly_error(error)
                )
                self.status.set("Batch compression failed.")
                return
        except Exception as error:
            messagebox.showerror(
                "Batch compression failed", self._friendly_error(error)
            )
            self.status.set("Batch compression failed.")
            return

        total_in = sum(item["original_size"] for item in results)
        total_out = sum(item["compressed_size"] for item in results)
        lines = [
            "BATCH COMPRESSION SUCCESSFUL",
            "════════════════════════════════════════════",
            "",
            f"Files compressed: {len(results)}",
            f"Total original size:   {total_in:,} bytes",
            f"Total compressed size: {total_out:,} bytes",
            f"Elapsed time: {elapsed:.6f} seconds",
            "",
            "FILES",
            "────────────────────────────────────────────",
        ]
        for item in results:
            saved = item["original_size"] - item["compressed_size"]
            lines.append(
                f"{os.path.basename(item['input_path'])}: "
                f"{item['original_size']:,} → {item['compressed_size']:,} bytes "
                f"({saved:+,} bytes)"
            )
        lines.append("")
        lines.append(f"Outputs saved in: {output_dir}")
        lines.append("The original files were not modified.")
        self._set_text(self.compress_output, "\n".join(lines))

        self.last_performance = {
            "operation": "Batch compression",
            "source": f"{len(results)} files",
            "input_size": total_in,
            "output_size": total_out,
            "elapsed": elapsed,
        }
        for item in results:
            self._record_history(
                "Compression",
                item["input_path"],
                item["output_path"],
                item["original_size"],
                item["compressed_size"],
                elapsed,
            )
        self.status.set(f"Batch compression completed: {len(results)} files.")
        messagebox.showinfo(
            "Batch compression complete",
            f"{len(results)} file(s) compressed.",
        )

    # ------------------------------------------------------------------
    # Tab 2 — Decompress File
    # ------------------------------------------------------------------

    def _build_decompress_tab(self):
        self._section_heading(
            self.decompress_tab,
            "Decompress an HFC1 file",
            "Select a compressed .hfc file and restore its original bytes. "
            "The decoder validates the compressed data before writing output.",
        )

        actions = tk.Frame(self.decompress_tab, bg=COLORS["surface"])
        actions.pack(fill="x", padx=23, pady=(0, 15))

        self._button(
            actions, "Choose .hfc File and Decompress", self.decompress_file
        ).pack(side="left")

        self.decompress_output = self._text_area(self.decompress_tab)
        self._set_text(
            self.decompress_output,
            "READY TO DECOMPRESS\n"
            "────────────────────────────────────────────\n\n"
            "1. Click Choose .hfc File and Decompress.\n"
            "2. Select a valid HFC1 compressed file.\n"
            "3. Choose where to save the restored file.\n\n"
            "The result will be displayed here.",
        )

    def decompress_file(self):
        source = filedialog.askopenfilename(
            title="Choose a compressed HFC1 file",
            filetypes=[("Huffman compressed files", "*.hfc"), ("All files", "*.*")],
        )
        if not source:
            return
        if not self._input_size_ok(source):
            return

        def ask_output():
            return filedialog.asksaveasfilename(
                title="Save restored file",
                initialfile=os.path.basename(source)[:-4]
                if source.lower().endswith(".hfc")
                else os.path.basename(source) + "_restored",
                filetypes=[("All files", "*.*")],
            )

        output = ask_output()
        if not output:
            self.status.set("Decompression cancelled.")
            return

        if os.path.abspath(source) == os.path.abspath(output):
            messagebox.showerror(
                "Invalid output",
                "The restored file cannot overwrite the compressed input.",
            )
            return

        try:
            self.status.set("Decompressing and validating file...")
            self.root.update_idletasks()
            start = time.perf_counter()

            raw = self._read_file(source)
            restored = decompress_bytes(raw)
            elapsed = time.perf_counter() - start

            written, output = self._write_with_overwrite_prompt(
                output, restored, what="restored file",
                save_dialog=ask_output,
            )
            if not written:
                return

            self._set_text(
                self.decompress_output,
                "DECOMPRESSION SUCCESSFUL\n"
                "════════════════════════════════════════════\n\n"
                f"Compressed file : {source}\n"
                f"Restored file   : {output}\n\n"
                f"Compressed size : {len(raw):,} bytes\n"
                f"Restored size   : {len(restored):,} bytes\n"
                f"Elapsed time    : {elapsed:.6f} seconds\n\n"
                "LOSSLESS VERIFICATION: PASSED\n"
                "The decoder verified the CRC32 checksum stored in the "
                "compressed file, so the restored data is byte-for-byte "
                "identical to the original.",
            )

            self.last_performance = {
                "operation": "Decompression",
                "source": os.path.basename(source),
                "input_size": len(raw),
                "output_size": len(restored),
                "elapsed": elapsed,
            }
            self._record_history(
                "Decompression", source, output, len(raw), len(restored), elapsed
            )
            self.status.set("Decompression completed successfully.")
            messagebox.showinfo(
                "Decompression complete", "The file was restored successfully."
            )

        except FileExistsError:
            messagebox.showerror(
                "Output already exists",
                "Choose a different output name. The existing file was not changed.",
            )
            self.status.set("Decompression stopped — output already exists.")
        except Exception as error:
            messagebox.showerror(
                "Decompression failed",
                self._friendly_error(error),
            )
            self.status.set("Decompression failed — file may be invalid or corrupted.")

    # ------------------------------------------------------------------
    # Tab 3 — Huffman Explorer
    # ------------------------------------------------------------------

    def _build_explorer_tab(self):
        self._section_heading(
            self.explorer_tab,
            "Huffman Explorer",
            "Inspect byte frequencies, Huffman codes, and the tree generated "
            "for a selected file.",
        )

        toolbar = tk.Frame(self.explorer_tab, bg=COLORS["surface"])
        toolbar.pack(fill="x", padx=23, pady=(0, 13))

        self._button(
            toolbar, "Choose File and Explore", self.explore_file
        ).pack(side="left")

        tk.Label(
            toolbar,
            text="Analysis only — no output file is created.",
            bg=COLORS["surface"],
            fg=COLORS["subtle"],
            font=("Segoe UI", 9),
        ).pack(side="left", padx=13)

        self.explorer_output = self._text_area(self.explorer_tab, wrap="none")
        self._set_text(
            self.explorer_output,
            "Choose a file to display its Huffman code table and tree.",
        )

    def explore_file(self):
        source = filedialog.askopenfilename(title="Choose a file to analyse")
        if not source:
            return
        if not self._input_size_ok(source):
            return

        try:
            data = self._read_file(source)
            if not data:
                messagebox.showwarning("Empty file", "Choose a non-empty file.")
                return

            frequencies = calculate_frequencies(data)
            tree = build_huffman_tree(frequencies)
            codes = generate_huffman_codes(tree)
            table = build_huffman_code_table(frequencies, codes)

            lines = [
                "FILE INFORMATION",
                "════════════════════════════════════════════════════════════",
                f"File name          : {os.path.basename(source)}",
                f"File size          : {len(data):,} bytes",
                f"Distinct byte values: {len(frequencies)}",
                "",
                "HUFFMAN CODE TABLE",
                "────────────────────────────────────────────────────────────",
                f"{'BYTE':<18}{'FREQUENCY':>12}    HUFFMAN CODE",
                "────────────────────────────────────────────────────────────",
            ]
            for row in table:
                lines.append(
                    f"{row['display']:<18}{row['frequency']:>12}    {row['code']}"
                )

            lines.extend(
                [
                    "",
                    "HUFFMAN TREE",
                    "────────────────────────────────────────────────────────────",
                    render_tree(tree),
                ]
            )
            self._set_text(self.explorer_output, "\n".join(lines))
            self.status.set(f"Analysis completed: {os.path.basename(source)}")

        except Exception as error:
            messagebox.showerror(
                "Analysis failed", self._friendly_error(error)
            )
            self.status.set("Huffman analysis failed.")

    # ------------------------------------------------------------------
    # Tab 4 — Statistics & Performance
    # ------------------------------------------------------------------

    def _build_performance_tab(self):
        self._section_heading(
            self.performance_tab,
            "Statistics & Performance",
            "Review the most recent compression or decompression measurement. "
            "Elapsed time is measured during that operation on this computer.",
        )

        toolbar = tk.Frame(self.performance_tab, bg=COLORS["surface"])
        toolbar.pack(fill="x", padx=23, pady=(0, 13))

        self._button(
            toolbar, "Refresh Performance", self.refresh_performance,
            secondary=True
        ).pack(side="left")

        self.performance_output = self._text_area(self.performance_tab)
        self.refresh_performance()

    def refresh_performance(self):
        if not self.last_performance:
            content = (
                "NO PERFORMANCE MEASUREMENT YET\n"
                "────────────────────────────────────────────\n\n"
                "Complete a compression or decompression operation. "
                "Its elapsed time and file sizes will appear here."
            )
        else:
            item = self.last_performance
            elapsed = item["elapsed"]
            output = [
                "LATEST OPERATION MEASUREMENT",
                "════════════════════════════════════════════",
                f"Operation       : {item['operation']}",
                f"File            : {item['source']}",
                f"Input size      : {item['input_size']:,} bytes",
                f"Output size     : {item['output_size']:,} bytes",
                f"Elapsed time    : {elapsed:.6f} seconds",
            ]
            if elapsed > 0:
                throughput = item["input_size"] / elapsed
                output.append(f"Input throughput: {throughput:,.2f} bytes/second")
            if item["operation"] in ("Compression", "Batch compression"):
                stats = calculate_statistics(
                    item["input_size"], item["output_size"]
                )
                output.extend(
                    [
                        "",
                        "COMPRESSION STATISTICS",
                        "────────────────────────────────────────────",
                        self._format_stats_lines(format_statistics(stats)),
                        "Compression ratio (compressed ÷ original): "
                        f"{item['output_size'] / item['input_size']:.2f}",
                    ]
                )
            output.extend(
                [
                    "",
                    "NOTE",
                    "This is a single-operation timing, not a controlled benchmark. "
                    "Results depend on file contents, file size, and the computer.",
                ]
            )
            content = "\n".join(output)

        self._set_text(self.performance_output, content)

    # ------------------------------------------------------------------
    # Tab 5 — Compression History
    # ------------------------------------------------------------------

    def _build_history_tab(self):
        self._section_heading(
            self.history_tab,
            "Compression History",
            "Review compression and decompression operations completed "
            "during the current application session.",
        )

        toolbar = tk.Frame(self.history_tab, bg=COLORS["surface"])
        toolbar.pack(fill="x", padx=23, pady=(0, 13))

        self._button(
            toolbar, "Refresh History", self.refresh_history, secondary=True
        ).pack(side="left")
        self._button(
            toolbar, "Clear Session History", self.clear_history, secondary=True
        ).pack(side="left", padx=9)

        self.history_output = self._text_area(self.history_tab)
        self.refresh_history()

    def refresh_history(self):
        if not self.history:
            content = (
                "NO OPERATIONS RECORDED\n"
                "────────────────────────────────────────────\n\n"
                "Successful compression and decompression operations "
                "will appear here.\n\n"
                "Note: this history is held in memory and is cleared "
                "when the application closes."
            )
        else:
            lines = [
                f"SESSION HISTORY — {len(self.history)} OPERATION(S)",
                "════════════════════════════════════════════",
                "",
            ]
            for number, item in enumerate(self.history, start=1):
                lines.extend(
                    [
                        f"OPERATION {number} — {item['operation']}",
                        "────────────────────────────────────────────",
                        f"Input file      : {item['source']}",
                        f"Output file     : {item['output']}",
                        f"Input size      : {item['input_size']:,} bytes",
                        f"Output size     : {item['output_size']:,} bytes",
                        (
                            f"Elapsed time    : {item['elapsed']:.6f} seconds"
                            if item["elapsed"] is not None
                            else "Elapsed time    : Not measured"
                        ),
                        "",
                    ]
                )
            lines.append(
                "History is session-only and is cleared when the application closes."
            )
            content = "\n".join(lines)

        self._set_text(self.history_output, content)

    def clear_history(self):
        if not self.history:
            return
        if messagebox.askyesno(
            "Clear history",
            "Clear all operations recorded in this application session?",
        ):
            self.history.clear()
            self.refresh_history()
            self.status.set("Session history cleared.")


def main():
    root = tk.Tk()
    FileCompressionGUI(root)
    # Test hook: FCT_AUTOCLOSE_MS=2000 closes the window after 2 s.
    auto_close = os.environ.get("FCT_AUTOCLOSE_MS")
    if auto_close:
        root.after(int(auto_close), root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
