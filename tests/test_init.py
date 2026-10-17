import subprocess
import sys

import minerva


def test_version() -> None:
    assert isinstance(minerva.__version__, str)
    assert "." in minerva.__version__


def test_public_api() -> None:
    for name in minerva.__all__:
        assert getattr(minerva, name) is not None


def test_import_is_lazy() -> None:
    """
    `import minerva` doesn't import Twisted until you use the API.
    """
    code = (
        "import sys, minerva\n"
        "assert 'twisted' not in sys.modules\n"
        "minerva.StreamTracker\n"
        "assert 'twisted' in sys.modules\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
