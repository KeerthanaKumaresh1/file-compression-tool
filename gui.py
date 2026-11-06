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
"""

import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from compressor.frequency import calculate_frequencies
from compressor.huffman_tree import build_huffman_tree
from compressor.huffman_codes import generate_huffman_codes
from compressor.file_format import build_compressed_bytes
from compressor.decompressor import decompress_bytes
from compressor.tree_visualizer import render_tree
from compressor.huffman_code_table import build_huffman_code_table
from compressor.compression_stats import calculate_statistics, format_statistics


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
    def _write_new_file(path, data):
        """Create a new output without replacing an existing file."""
        with open(path, "xb") as file:
            file.write(data)

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

        actions = tk.Frame(self.compress_tab, bg=COLORS["surface"])
        actions.pack(fill="x", padx=23, pady=(4, 16))

        self._button(
            actions, "Compress Selected File", self.compress_file
        ).pack(side="left")

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

    def choose_compress_file(self):
        path = filedialog.askopenfilename(title="Choose a file to compress")
        if path:
            self.compress_path.set(path)
            self.status.set(f"Selected: {os.path.basename(path)}")

    def compress_file(self):
        source = self.compress_path.get().strip()

        if not source:
            messagebox.showwarning("Select a file", "Choose a file first.")
            return
        if not os.path.isfile(source):
            messagebox.showerror("Invalid file", "The selected file does not exist.")
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

            self._write_new_file(output, compressed)

            stats = calculate_statistics(len(data), len(compressed))
            stats_text = format_statistics(stats)
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
                f"{stats_text}\n\n"
                "The original file was not modified.",
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
                "Compression failed", f"The file could not be compressed.\n\n{error}"
            )
            self.status.set("Compression failed.")

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

        output = filedialog.asksaveasfilename(
            title="Save restored file",
            initialfile=os.path.basename(source)[:-4] if source.lower().endswith(".hfc")
            else os.path.basename(source) + "_restored",
            filetypes=[("All files", "*.*")],
        )
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

            # Exclusive creation protects an existing destination.
            self._write_new_file(output, restored)

            self._set_text(
                self.decompress_output,
                "DECOMPRESSION SUCCESSFUL\n"
                "════════════════════════════════════════════\n\n"
                f"Compressed file : {source}\n"
                f"Restored file   : {output}\n\n"
                f"Compressed size : {len(raw):,} bytes\n"
                f"Restored size   : {len(restored):,} bytes\n"
                f"Elapsed time    : {elapsed:.6f} seconds\n\n"
                "The decoder completed without reporting a format or "
                "integrity error.",
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
                f"The file could not be decompressed.\n\n{error}",
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
                "Analysis failed", f"Could not analyse this file.\n\n{error}"
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
            if item["operation"] == "Compression":
                stats = calculate_statistics(
                    item["input_size"], item["output_size"]
                )
                output.extend(
                    [
                        "",
                        "COMPRESSION STATISTICS",
                        "────────────────────────────────────────────",
                        str(format_statistics(stats)),
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
    root.mainloop()


if __name__ == "__main__":
    main()
