"""``python -m system_integration`` dispatch (ADR-0038)."""

import sys

from system_integration.cli import main

if __name__ == "__main__":
    sys.exit(main())
