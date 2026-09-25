"""Phase 1 smoke test: the package layout imports."""

import app


def test_package_imports() -> None:
    assert app.__version__ == "0.1.0"
