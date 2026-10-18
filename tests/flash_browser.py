"""
Run pages in a browser that can still run Adobe Flash Player: Pale Moon, which
keeps NPAPI plugin support, on a virtual X display (Xvfb).

`nix-build scripts/flash-browser.nix -o ../flash-browser` makes one.  Set
MINERVA_FLASH_BROWSER to use another NPAPI browser (Pale Moon, Basilisk, or
Firefox <= 84) that can find a Flash plugin, e.g. through MOZ_PLUGIN_PATH.
Xvfb is looked for next to the browser, then on PATH.

These browsers have no remote-control protocol that we can use, so pages
report what they do to the server instead (see browser_server.py).
"""

import json
import os
import shutil
import signal
import subprocess
import tempfile
from collections.abc import Generator
from contextlib import contextmanager, suppress
from pathlib import Path

REPO = Path(__file__).parent.parent
BROWSER = Path(
    os.environ.get(
        "MINERVA_FLASH_BROWSER", REPO.parent / "flash-browser" / "bin" / "palemoon"
    )
)
XVFB = shutil.which("Xvfb", path=BROWSER.parent) or shutil.which("Xvfb")

# Run Flash without asking first, and skip the startup dialogs and update
# checks.
PREFS = {
    "plugin.state.flash": 2,
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.homepage_override.mstone": "ignore",
    "browser.sessionstore.resume_from_crash": False,
    "app.update.enabled": False,
    "extensions.update.enabled": False,
    "browser.search.update": False,
}


def available() -> bool:
    return os.access(BROWSER, os.X_OK) and XVFB is not None


@contextmanager
def virtual_display() -> Generator[str]:
    """
    Run Xvfb; yield its DISPLAY.
    """
    assert XVFB is not None
    read_fd, write_fd = os.pipe()
    command = [XVFB, "-displayfd", str(write_fd), "-screen", "0", "1024x768x24"]
    with subprocess.Popen(
        command, pass_fds=[write_fd], stderr=subprocess.DEVNULL
    ) as xvfb:
        os.close(write_fd)
        try:
            # Xvfb writes its display number once it's ready.
            with open(read_fd) as display:
                yield f":{display.readline().strip()}"
        finally:
            xvfb.terminate()


@contextmanager
def open_page(url: str, display: str) -> Generator[subprocess.Popen[bytes]]:
    """
    Open `url` in the Flash browser, with a new profile, on `display`.
    """
    # The browser and Flash Player also write to $HOME.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as home:
        profile = Path(home) / "profile"
        profile.mkdir()
        (profile / "user.js").write_text(
            "".join(
                f"user_pref({json.dumps(name)}, {json.dumps(value)});\n"
                for name, value in PREFS.items()
            )
        )
        env = os.environ | {"DISPLAY": display, "HOME": home}
        env.pop("WAYLAND_DISPLAY", None)
        command = [BROWSER, "-no-remote", "-profile", profile, url]
        with subprocess.Popen(
            command,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            # So that we can stop its plugin processes, too.
            start_new_session=True,
        ) as browser:
            try:
                yield browser
            finally:
                with suppress(ProcessLookupError):
                    os.killpg(browser.pid, signal.SIGTERM)
