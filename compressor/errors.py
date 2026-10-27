"""Custom exceptions shared by every module (Step 0 - repo skeleton)."""


class CompressionError(Exception):
    """Base class for every error raised by the File Compression Tool."""


class FileValidationError(CompressionError):
    """The input file is missing, unreadable, empty or otherwise unusable."""


class FileCreationError(CompressionError):
    """An output file could not be written."""


class CorruptedFileError(CompressionError):
    """The compressed file is damaged or is not in the expected format."""


class OutputExistsError(CompressionError):
    """The output file already exists and overwriting was not allowed."""


class VerificationError(CompressionError):
    """The decompressed data does not match the original file."""