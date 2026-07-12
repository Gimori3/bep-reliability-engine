"""Module entry point: ``python -m bayesian_reliability_updating``."""

from __future__ import annotations

import sys

from bayesian_reliability_updating.cli import main

if __name__ == "__main__":
    sys.exit(main())
