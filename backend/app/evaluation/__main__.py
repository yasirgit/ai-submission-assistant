"""Offline golden-set command: python -m app.evaluation"""

import sys

from app.evaluation.runner import run_dataset
from app.evaluation.score import exit_code, format_report


def main() -> int:
    results = run_dataset()
    print(format_report(results))
    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
