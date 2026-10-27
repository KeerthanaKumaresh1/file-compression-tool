
"""BL14 - Output & Overwrite Protection."""

import os

from .errors import FileCreationError, OutputExistsError
from .file_format import EXTENSION


def default_compressed_name(input_path):
    """Return the default compressed filename."""
    return os.fspath(input_path) + EXTENSION

def default_decompressed_name(compressed_path):
    """Return a restored filename without overwriting the source."""
    path = os.fspath(compressed_path)

    if path.endswith(EXTENSION):
        path = path[:-len(EXTENSION)]

    root, extension = os.path.splitext(path)
    return root + "_restored" + extension


def prepare_output_path(output_path, overwrite=False):
    """Validate an output path and protect existing files."""
    path = os.fspath(output_path)

    if not isinstance(overwrite, bool):
        raise TypeError("overwrite must be a boolean.")

    # Check directories before checking whether a path exists.
    if os.path.isdir(path):
        raise FileCreationError(
            f"Output path refers to a directory: '{path}'"
        )

    if os.path.exists(path) and not overwrite:
        raise OutputExistsError(
            f"Output file already exists: '{path}'. "
            "Choose another output path or enable overwrite."
        )

    parent = os.path.dirname(os.path.abspath(path))

    if not os.path.isdir(parent):
        raise FileCreationError(
            f"Output directory does not exist: '{parent}'"
        )

    return path


def write_output(output_path, data, overwrite=False):
    """Write bytes after checking overwrite protection.

    Returns the output path as a string.
    """
    path = prepare_output_path(output_path, overwrite=overwrite)

    try:
        # Exclusive creation prevents accidental replacement if the file
        # appears after the initial existence check.
        if overwrite:
            with open(path, "wb") as file:
                file.write(data)
        else:
            with open(path, "xb") as file:
                file.write(data)
    except FileExistsError as error:
        raise OutputExistsError(
            f"Output file already exists: '{path}'."
        ) from error
    except OSError as error:
        raise FileCreationError(
            f"Could not write output '{path}': {error}"
        ) from error

    return path
