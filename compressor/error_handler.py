
"""BL17 - Centralized error handling."""
import sys

from .errors import (
    CompressionError,
    FileValidationError,
    FileCreationError,
    CorruptedFileError,
    OutputExistsError,
    VerificationError,
)


EXIT_CODES = {
    FileValidationError: 2,
    FileCreationError: 3,
    CorruptedFileError: 4,
    OutputExistsError: 5,
    VerificationError: 6,
}


def exit_code_for(error):
    """Return an appropriate process exit code for an error."""
    for error_type, code in EXIT_CODES.items():
        if isinstance(error, error_type):
            return code

    if isinstance(error, CompressionError):
        return 1

    return 1


def format_error(error):
    """Return a concise, user-friendly error message."""
    return f"Error: {error}"


def run_safely(func, *args, **kwargs):
    """Run a function and return an exit code instead of a traceback."""
    try:
        func(*args, **kwargs)
        return 0

    except CompressionError as error:
        print(format_error(error), file=sys.stderr)
        return exit_code_for(error)

    except KeyboardInterrupt:
        print("Cancelled by the user.", file=sys.stderr)
        return 130

    except MemoryError:
        print(
            "Error: not enough memory to process this file.",
            file=sys.stderr,
        )
        return 7

    except Exception as error:
        print(f"Unexpected error: {error}", file=sys.stderr)
        return 1

