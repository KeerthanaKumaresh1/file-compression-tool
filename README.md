# File Compression Tool

A lossless file compressor built on **Huffman coding**, written in Python (standard library only) with a command-line interface and a five-tab Tkinter GUI. Software Engineering mini-project by **Keerthana Kumaresh, Rishitha Radhae and Kanishka Sarraf**.

## Features

* Compress any non-empty file to a self-contained `.hfc` file and restore it byte-for-byte
* Statistics: original/compressed size, ratio, space saved
* Huffman code table and tree view
* Lossless verification (SHA-256), CRC-32 damage detection, corrupt-file rejection
* Output/overwrite protection, operation history, timing and memory report

## Quick start

```bash
python main.py compress notes.txt --table --tree --time
python main.py decompress notes.txt.hfc -o notes\_restored.txt
python main.py verify notes.txt notes.txt.hfc
python main.py history
python gui.py            # graphical interface (needs Tkinter)
```

Exit codes: 0 ok, 2 invalid input, 3 cannot write, 4 corrupted file, 5 output exists (use `--overwrite`), 6 verification failed.

## Repository structure

```text
file-compression-tool/
├── main.py, gui.py              entry points (CLI / GUI)
├── compressor/                  the implementation
├── tests/                       unit + integration tests (147)
├── system\_tests/                end-to-end system validation tests (37)
├── documents/                   Part-1 documents (user stories, use cases, security, first SRS, original test cases)
│   └── docs/                    final documents and generated reports (PDF)
├── .github/workflows/ci.yml     GitHub Actions: runs all tests + coverage on every push / pull request
└── requirements-dev.txt         pytest, pytest-cov
```

## Documents

### Part-1 documents (`documents/`)

|Document|Content|
|-|-|
|SRS\_document.pdf|First Software Requirements Specification|
|Security\_Requirements.pdf|First security requirements|
|User\_Stories.pdf|User stories|
|Use\_Case\_Flow.pdf|Use case flow|
|Test\_Cases\_original.pdf|First set of test cases|

### Final documents and reports (`documents/Docs/`)

|Document|Standard|
|-|-|
|SRS\_IEEE.pdf - Software Requirements Specification|IEEE 830 / 29148|
|SAD.pdf - Software Architecture Document|IEEE 1016|
|Test\_Plan.pdf|IEEE 829|
|Test\_Cases\_Extended.pdf - test cases updated after Sprint 2|IEEE 829|
|Unit\_Test\_Report.pdf|IEEE 829|
|System\_Validation\_Report.pdf|IEEE 829|
|Code\_Coverage\_Report.pdf|IEEE 829|
|Branch\_Coverage\_Report.pdf|IEEE 829|

Known deviations from the first SRS/SAD are listed in SRS Appendix D.

## Running the tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests --cov=compressor --cov-branch --cov-report=term-missing
python -m pytest system\_tests -v
```

## Team

Keerthana Kumaresh (repository owner), Rishitha Radhae, Kanishka Sarraf

