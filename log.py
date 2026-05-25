"""Minimal stderr logging with flush."""

from __future__ import annotations

import sys

_verbose = True


def set_quiet(quiet: bool) -> None:
    global _verbose
    _verbose = not quiet


def info(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def warn(msg: str) -> None:
    print(f"Warning: {msg}", file=sys.stderr, flush=True)


def error(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr, flush=True)


def verbose(msg: str) -> None:
    if _verbose:
        info(msg)
