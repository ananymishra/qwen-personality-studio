"""Allow ``python -m qwen_steering``."""

from .cli import main

if __name__ == "__main__":
    import sys

    sys.exit(main())
