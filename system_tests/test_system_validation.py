"""System validation tests for the File Compression Tool.

These tests exercise the finished product from the outside, the way a user
does: they start the real command line program (``python main.py ...``) in a
separate process, give it real files, and check the exit code, the messages
printed, and the files left on disk.

Each test is named ``test_sys_NN_...`` and maps to a system test case
(SYS-NN) in docs/Test_Cases.pdf and docs/System_Validation_Report.pdf.

Run from the project root:

    python -m pytest system_tests -v
"""

import ast
import hashlib
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "main.py"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

@pytest.fixture
def work(tmp_path):
    """A private working folder (also used as HOME so history stays isolated)."""
    return tmp_path


def run_cli(work, *args):
    """Run the CLI in a new process and return (exit_code, stdout, stderr)."""
    env = dict(os.environ)
    env["HOME"] = str(work / "home")
    env["USERPROFILE"] = str(work / "home")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    done = subprocess.run(
        [sys.executable, str(MAIN), *map(str, args)],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return done.returncode, done.stdout, done.stderr


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sample_text(size):
    base = b"The quick brown fox jumps over the lazy dog. Huffman coding. "
    return (base * (size // len(base) + 1))[:size]


def round_trip(work, name, data):
    """Compress then decompress `data` through the CLI; return the results."""
    src = work / name
    src.write_bytes(data)
    c_code, c_out, c_err = run_cli(work, "compress", src)
    hfc = Path(str(src) + ".hfc")
    restored = work / ("restored_" + name)
    d_code, d_out, d_err = run_cli(work, "decompress", hfc, "-o", restored)
    return c_code, d_code, hfc, restored, (c_out, c_err, d_out, d_err)


# --------------------------------------------------------------------------
# Lossless round trips (FR-1..FR-7, NFR-3, NFR-4, SR-4)
# --------------------------------------------------------------------------

def test_sys_01_text_file_round_trip(work):
    data = sample_text(10_000)
    c, d, hfc, restored, _ = round_trip(work, "sample.txt", data)
    assert (c, d) == (0, 0)
    assert hfc.exists() and hfc.read_bytes()[:4] == b"HFC1"
    assert restored.read_bytes() == data


def test_sys_02_binary_random_file_round_trip(work):
    data = os.urandom(200_000)
    c, d, _, restored, _ = round_trip(work, "random.bin", data)
    assert (c, d) == (0, 0)
    assert restored.read_bytes() == data


def test_sys_03_all_256_byte_values_round_trip(work):
    data = bytes(range(256)) * 40
    c, d, _, restored, _ = round_trip(work, "allbytes.bin", data)
    assert (c, d) == (0, 0)
    assert restored.read_bytes() == data


def test_sys_04_single_symbol_file_round_trip(work):
    data = b"A" * 5000
    c, d, _, restored, _ = round_trip(work, "same.txt", data)
    assert (c, d) == (0, 0)
    assert restored.read_bytes() == data


def test_sys_05_one_byte_file_round_trip(work):
    c, d, _, restored, _ = round_trip(work, "one.txt", b"Z")
    assert (c, d) == (0, 0)
    assert restored.read_bytes() == b"Z"


def test_sys_06_file_name_with_spaces_and_unicode(work):
    data = sample_text(3000)
    c, d, _, restored, _ = round_trip(work, "my résumé final.txt", data)
    assert (c, d) == (0, 0)
    assert restored.read_bytes() == data


def test_sys_07_compress_with_verify_flag(work):
    src = work / "v.txt"
    src.write_bytes(sample_text(4000))
    code, out, _ = run_cli(work, "compress", src, "--verify")
    assert code == 0
    assert "Verification passed" in out


def test_sys_08_verify_command_ok_and_mismatch(work):
    a = work / "a.txt"
    b = work / "b.txt"
    a.write_bytes(sample_text(2000))
    b.write_bytes(sample_text(2000) + b"!")
    run_cli(work, "compress", a)
    code_ok, out_ok, _ = run_cli(work, "verify", a, str(a) + ".hfc")
    code_bad, _, err_bad = run_cli(work, "verify", b, str(a) + ".hfc")
    assert code_ok == 0 and "OK" in out_ok
    assert code_bad == 6 and "Error" in err_bad


def test_sys_09_compression_is_deterministic(work):
    src = work / "d.txt"
    src.write_bytes(sample_text(8000))
    run_cli(work, "compress", src)
    first = (work / "d.txt.hfc").read_bytes()
    run_cli(work, "compress", src, "--overwrite")
    assert (work / "d.txt.hfc").read_bytes() == first


# --------------------------------------------------------------------------
# Statistics, code table, tree, timing (FR-8, FR-10, NFR-2)
# --------------------------------------------------------------------------

def test_sys_10_statistics_are_displayed(work):
    src = work / "s.txt"
    src.write_bytes(sample_text(20_000))
    code, out, _ = run_cli(work, "compress", src)
    assert code == 0
    for label in ("Original size", "Compressed size", "Space saved",
                  "Space saved percentage", "Compression ratio"):
        assert label in out
    assert "Original size: 20000 bytes" in out


def test_sys_11_repetitive_data_is_smaller(work):
    src = work / "rep.txt"
    src.write_bytes(sample_text(100_000))
    run_cli(work, "compress", src)
    # NFR-2: repeated text must shrink to at most 75 % of its original size
    assert (work / "rep.txt.hfc").stat().st_size <= 0.75 * src.stat().st_size


def test_sys_12_small_file_can_grow_and_stats_still_shown(work):
    """Known, documented behaviour: header+table overhead on tiny inputs."""
    src = work / "tiny.txt"
    src.write_bytes(b"AAAABBBCCD")
    code, out, _ = run_cli(work, "compress", src)
    assert code == 0
    assert (work / "tiny.txt.hfc").stat().st_size == 42
    assert "Compressed size: 42 bytes" in out
    assert "Space saved percentage: -320.00%" in out


def test_sys_13_code_table_and_tree_are_displayed(work):
    src = work / "t.txt"
    src.write_bytes(b"AAAABBBCCD")
    code, out, _ = run_cli(work, "compress", src, "--table", "--tree")
    assert code == 0
    assert "Huffman Code Table" in out and "Huffman Tree" in out
    assert "'code': '0'" in out          # A gets code 0
    assert "'A' (4)" in out and "(10)" in out


def test_sys_14_performance_report(work):
    src = work / "p.txt"
    src.write_bytes(sample_text(50_000))
    code, out, _ = run_cli(work, "compress", src, "--time")
    assert code == 0
    assert re.search(r"Time: \d+\.\d{3} s \| Speed: [\d.]+ MB/s", out)
    assert "Peak memory" in out


def test_sys_15_performance_one_megabyte_within_limit(work):
    """NFR-1: a 1 MB file is compressed and decompressed in <= 5 s each."""
    src = work / "big.txt"
    src.write_bytes(sample_text(1_000_000))
    t0 = time.perf_counter()
    c_code, _, _ = run_cli(work, "compress", src)
    t_compress = time.perf_counter() - t0
    t0 = time.perf_counter()
    d_code, _, _ = run_cli(work, "decompress", str(src) + ".hfc",
                           "-o", work / "big_out.txt")
    t_decompress = time.perf_counter() - t0
    assert (c_code, d_code) == (0, 0)
    assert t_compress <= 5 and t_decompress <= 5
    assert (work / "big_out.txt").read_bytes() == src.read_bytes()


def test_sys_16_files_of_different_sizes(work):
    """NFR-6: sizes from 1 byte to 2 MB all round-trip."""
    for size in (1, 100, 10_000, 500_000, 2_000_000):
        data = sample_text(size)
        c, d, _, restored, _ = round_trip(work, f"size{size}.txt", data)
        assert (c, d) == (0, 0), size
        assert restored.read_bytes() == data, size


# --------------------------------------------------------------------------
# Invalid and corrupt input (FR-9, SR-1, SR-2, SR-5, SR-8)
# --------------------------------------------------------------------------

def test_sys_17_missing_input_file(work):
    code, out, err = run_cli(work, "compress", "missing.txt")
    assert code == 2
    assert "File not found" in err
    assert "Traceback" not in err
    assert not (work / "missing.txt.hfc").exists()


def test_sys_18_folder_given_as_input(work):
    (work / "folder").mkdir()
    code, _, err = run_cli(work, "compress", "folder")
    assert code == 2 and "folder" in err and "Traceback" not in err


def test_sys_19_empty_file_is_rejected_safely(work):
    (work / "empty.txt").write_bytes(b"")
    code, _, err = run_cli(work, "compress", "empty.txt")
    assert code == 2 and "empty" in err and "Traceback" not in err
    assert not (work / "empty.txt.hfc").exists()


def test_sys_20_non_hfc_file_is_rejected(work):
    (work / "plain.hfc").write_bytes(b"this is not a compressed file at all")
    code, _, err = run_cli(work, "decompress", "plain.hfc")
    assert code == 4 and "Traceback" not in err
    assert not (work / "plain_restored").exists()


def test_sys_21_truncated_compressed_file(work):
    src = work / "tr.txt"
    src.write_bytes(sample_text(5000))
    run_cli(work, "compress", src)
    hfc = work / "tr.txt.hfc"
    hfc.write_bytes(hfc.read_bytes()[:-5])
    code, _, err = run_cli(work, "decompress", hfc, "-o", work / "tr_out.txt")
    assert code == 4 and "Traceback" not in err
    assert not (work / "tr_out.txt").exists()


def test_sys_22_bit_flipped_compressed_file(work):
    src = work / "bf.txt"
    src.write_bytes(sample_text(5000))
    run_cli(work, "compress", src)
    hfc = work / "bf.txt.hfc"
    raw = bytearray(hfc.read_bytes())
    raw[-3] ^= 0x01
    hfc.write_bytes(bytes(raw))
    code, _, err = run_cli(work, "decompress", hfc, "-o", work / "bf_out.txt")
    assert code == 4 and "Traceback" not in err
    assert not (work / "bf_out.txt").exists()


def test_sys_23_random_damage_never_crashes(work):
    """30 different damaged files: every one is reported, none crashes."""
    import random
    rng = random.Random(7)
    src = work / "fz.txt"
    src.write_bytes(sample_text(3000))
    run_cli(work, "compress", src)
    good = (work / "fz.txt.hfc").read_bytes()
    for i in range(30):
        damaged = bytearray(good)
        for _ in range(rng.choice([1, 2, 5])):
            damaged[rng.randrange(len(damaged))] = rng.randrange(256)
        if i % 3 == 0:
            damaged = damaged[:rng.randrange(1, len(damaged))]
        path = work / f"fz{i}.hfc"
        path.write_bytes(bytes(damaged))
        code, _, err = run_cli(work, "decompress", path, "-o", work / f"o{i}")
        assert code in (0, 4), (i, code, err)
        assert "Traceback" not in err and "Unexpected" not in err
        if bytes(damaged) != good:
            assert code == 4 or (work / f"o{i}").read_bytes() == sample_text(3000)


# --------------------------------------------------------------------------
# Output and overwrite protection (SR-3, SR-7, SR-10)
# --------------------------------------------------------------------------

def test_sys_24_existing_output_is_protected(work):
    src = work / "o.txt"
    src.write_bytes(sample_text(2000))
    out = work / "o.hfc"
    out.write_bytes(b"IMPORTANT EXISTING DATA")
    code, _, err = run_cli(work, "compress", src, "-o", out)
    assert code == 5 and "already exists" in err
    assert out.read_bytes() == b"IMPORTANT EXISTING DATA"


def test_sys_25_overwrite_flag_allows_replacement(work):
    src = work / "o2.txt"
    src.write_bytes(sample_text(2000))
    out = work / "o2.hfc"
    out.write_bytes(b"OLD")
    code, _, _ = run_cli(work, "compress", src, "-o", out, "--overwrite")
    assert code == 0 and out.read_bytes()[:4] == b"HFC1"


def test_sys_26_decompress_protects_existing_file(work):
    src = work / "r.txt"
    src.write_bytes(sample_text(2000))
    run_cli(work, "compress", src)
    target = work / "r_out.txt"
    target.write_bytes(b"KEEP ME")
    code, _, err = run_cli(work, "decompress", work / "r.txt.hfc", "-o", target)
    assert code == 5 and target.read_bytes() == b"KEEP ME"


def test_sys_27_missing_output_folder(work):
    src = work / "m.txt"
    src.write_bytes(sample_text(2000))
    code, _, err = run_cli(work, "compress", src, "-o",
                           work / "no_such_dir" / "m.hfc")
    assert code == 3 and "directory does not exist" in err
    assert "Traceback" not in err


@pytest.mark.skipif(not os.path.exists("/dev/full"),
                    reason="needs /dev/full (Linux) to simulate a full disk")
def test_sys_28_write_failure_is_reported(work):
    """SR-10: a failed write is an error, never a silent success."""
    src = work / "full.txt"
    src.write_bytes(sample_text(2000))
    code, out, err = run_cli(work, "compress", src, "-o", "/dev/full",
                             "--overwrite")
    assert code == 3 and "Could not write" in err
    assert "Compressed:" not in out


def test_sys_29_unrelated_files_untouched(work):
    other = work / "other.txt"
    other.write_bytes(b"unrelated data")
    before = sha(other)
    src = work / "u.txt"
    src.write_bytes(sample_text(3000))
    run_cli(work, "compress", src)
    run_cli(work, "decompress", work / "u.txt.hfc", "-o", work / "u_out.txt")
    assert sha(other) == before and sha(src) == hashlib.sha256(
        sample_text(3000)).hexdigest()


def test_sys_30_default_output_names(work):
    src = work / "report.txt"
    src.write_bytes(sample_text(3000))
    run_cli(work, "compress", src)
    assert (work / "report.txt.hfc").exists()
    code, _, _ = run_cli(work, "decompress", work / "report.txt.hfc")
    assert code == 0
    assert (work / "report_restored.txt").read_bytes() == sample_text(3000)


# --------------------------------------------------------------------------
# History (FR-13)
# --------------------------------------------------------------------------

def test_sys_31_history_lists_and_clears(work):
    src = work / "h.txt"
    src.write_bytes(sample_text(2000))
    run_cli(work, "compress", src)
    run_cli(work, "decompress", work / "h.txt.hfc", "-o", work / "h_out.txt")
    code, out, _ = run_cli(work, "history")
    assert code == 0 and "compression" in out and "decompression" in out
    code, out, _ = run_cli(work, "history", "--clear")
    assert code == 0 and "History cleared" in out
    code, out, _ = run_cli(work, "history")
    assert "No history available" in out


# --------------------------------------------------------------------------
# Command line behaviour
# --------------------------------------------------------------------------

def test_sys_32_help_and_bad_command(work):
    code, out, _ = run_cli(work, "--help")
    assert code == 0 and "compress" in out and "decompress" in out
    code, _, err = run_cli(work, "bogus")
    assert code == 2 and "usage" in err.lower()


# --------------------------------------------------------------------------
# Security and design constraints checked on the source (SR-9, NFR-7, NFR-8)
# --------------------------------------------------------------------------

def _imports(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return found


def test_sys_33_no_network_modules_used():
    """SR-9: no source file imports any networking library."""
    banned = {"socket", "urllib", "http", "requests", "ftplib", "smtplib",
              "xmlrpc", "asyncio", "ssl", "telnetlib"}
    files = list((ROOT / "compressor").glob("*.py")) + [ROOT / "gui.py",
                                                        ROOT / "main.py"]
    for path in files:
        assert not (_imports(path) & banned), path.name


def test_sys_34_only_standard_library_dependencies():
    """NFR-7: the tool runs on any Python 3 install with no extra packages."""
    stdlib = set(sys.stdlib_module_names)
    files = list((ROOT / "compressor").glob("*.py")) + [ROOT / "gui.py",
                                                        ROOT / "main.py"]
    local = {"compressor"}
    for path in files:
        for name in _imports(path):
            assert name in stdlib or name in local, (path.name, name)


def test_sys_35_modular_structure():
    """NFR-8: separate modules for each major operation."""
    expected = ["frequency", "min_heap", "huffman_tree", "huffman_codes",
                "file_format", "decompressor", "file_validation",
                "output_protection", "error_handler", "verification"]
    for name in expected:
        assert (ROOT / "compressor" / f"{name}.py").is_file(), name


def test_sys_36_gui_source_is_valid_and_complete():
    """FR-1/NFR-5 (static part): the GUI compiles and defines its 5 tabs.

    The GUI itself needs a display, so its behaviour is checked manually
    (see System Validation Report, section on manual checks).
    """
    source = (ROOT / "gui.py").read_text(encoding="utf-8")
    compile(source, "gui.py", "exec")
    for tab in ("Compress File", "Decompress File", "Huffman Explorer",
                "Statistics & Performance", "Compression History"):
        assert tab in source


def test_sys_37_size_limit_is_enforced(monkeypatch):
    """SR-6: data above the configured limit is refused, not processed."""
    sys.path.insert(0, str(ROOT))
    from compressor import file_format
    from compressor.errors import FileCreationError
    monkeypatch.setattr(file_format, "MAX_FILE_SIZE", 10)
    with pytest.raises(FileCreationError):
        file_format.build_compressed_bytes(b"x" * 11, {120: 11}, {120: "0"})
