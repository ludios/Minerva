#!/bin/sh
# On NixOS (without nix-ld), the manylinux `ruff` and `ty` binaries that uv
# installs into .venv can't find the glibc dynamic linker.  Point them at the
# same one the venv's (Nix-provided) Python uses.  Run after `uv sync`.
set -eu
cd "$(dirname "$0")/.."
interpreter=$(patchelf --print-interpreter "$(readlink -f .venv/bin/python)")
for bin in .venv/bin/ruff .venv/bin/ty; do
    patchelf --set-interpreter "$interpreter" "$bin"
done
