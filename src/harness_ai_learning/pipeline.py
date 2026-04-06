"""Compatibility wrapper for previous import paths."""

from .runtime.defaults import analyze_path
from .application.analyze_material import UnsupportedFileTypeError

__all__ = ["UnsupportedFileTypeError", "analyze_path"]
