#!/usr/bin/env python3
"""
Build Minerva's JavaScript: regenerate js_minerva/deps.js, and compile the
standalone client (minerva-client.js), xdrframe.js, and the demos (into
src/minerva/demos/static/) with Closure Compiler.

This needs an old Closure Library and Closure Compiler (the JavaScript uses
APIs that were removed long ago), and a Coreweb checkout:

    CLOSURE_LIBRARY_HOME   default: ../closure-library
    CLOSURE_COMPILER_HOME  default: ../closure-compiler (with the compiler's jar,
                           and any jars it depends on, in build/)
    COREWEB_HOME           default: ../Coreweb
    CLOSURE_PYTHON         the Python for Closure Library's (Python 2-era)
                           closurebuilder.py and depswriter.py; default: python2
    CLOSURE_COMPILER_JAVA  the command to run Java; default: java

Usage: scripts/build_js.py [deps|compile|demos|all]
"""

import os
import shlex
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)

CLOSURE_LIBRARY = os.environ.get("CLOSURE_LIBRARY_HOME", "../closure-library")
CLOSURE_COMPILER = os.environ.get("CLOSURE_COMPILER_HOME", "../closure-compiler")
COREWEB = os.environ.get("COREWEB_HOME", "../Coreweb")
CLOSURE_PYTHON = shlex.split(os.environ.get("CLOSURE_PYTHON", "python2"))
JAVA = shlex.split(os.environ.get("CLOSURE_COMPILER_JAVA", "java"))

COMPILED = "src/minerva/compiled_client"
DEMOS_STATIC = "src/minerva/demos/static"
ROOTS = [f"{COREWEB}/js_coreweb", "js_minerva"]
STANDALONE_EXTERNS = ["js_minerva/externs/standalone-client.js"]
# For applications that compile the client in with their own code.
NORMAL_EXTERNS = ["js_minerva/externs/normal-client.js"]
COMPILER_FLAGS = [
    "--compilation_level=ADVANCED_OPTIMIZATIONS",
    "--warning_level=VERBOSE",
    "--formatting=PRETTY_PRINT",
    "--jscomp_warning=missingProperties",
    "--jscomp_warning=undefinedVars",
    "--jscomp_warning=checkTypes",
    "--summary_detail_level=3",
    f"--js={CLOSURE_LIBRARY}/closure/goog/deps.js",
    f"--js={CLOSURE_LIBRARY}/third_party/closure/goog/deps.js",
]


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"{args[0]} exited with {result.returncode}:\n{result.stderr}")
    return result


def git_rev(directory: str) -> str:
    result = subprocess.run(
        ["git", "-C", directory, "log", "-1", "--date=short", "--pretty=%H | %ad | %s"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"(not a git checkout: {directory})"
    return result.stdout.strip()


def build_deps() -> None:
    """
    Regenerate js_minerva/deps.js, which tells the uncompiled Closure code
    where to find Minerva's modules.  The prefix is relative to base.js.
    """
    depswriter = f"{CLOSURE_LIBRARY}/closure/bin/build/depswriter.py"
    deps = run(
        [
            *CLOSURE_PYTHON,
            depswriter,
            "--root_with_prefix=js_minerva ../../../js_minerva",
        ]
    )
    Path("js_minerva/deps.js").write_text(deps.stdout.replace("\r\n", "\n"))
    print("Wrote js_minerva/deps.js")


def compile_js(
    namespaces: list[str],
    output: str,
    defines: dict[str, str] | None = None,
    externs: list[str] = STANDALONE_EXTERNS,
) -> None:
    print(f"Compiling {output}")
    closurebuilder = f"{CLOSURE_LIBRARY}/closure/bin/build/closurebuilder.py"
    sources = run(
        [
            *CLOSURE_PYTHON,
            closurebuilder,
            *(f"--root={root}" for root in [CLOSURE_LIBRARY, *ROOTS]),
            *(f"--namespace={namespace}" for namespace in namespaces),
        ]
    ).stdout.splitlines()

    args = [
        *COMPILER_FLAGS,
        *(f"--define={k}={v}" for k, v in (defines or {}).items()),
        *(f"--externs={e}" for e in externs),
        *(f"--js={root}/deps.js" for root in ROOTS),
        *(f"--js={source}" for source in sources),
    ]
    jar = f"{CLOSURE_COMPILER}/build/compiler.jar"
    result = run(
        [*JAVA, "-cp", jar, "com.google.javascript.jscomp.CommandLineRunner", *args]
    )

    Path(output).write_text(f"(function() {{\n{result.stdout}}})();\n")
    Path(f"{output}.log").write_text(
        f"Compiling with the following arguments: {args!r}\n"
        + result.stderr.replace("\r\n", "\n")
        + f"Used closure-compiler {git_rev(CLOSURE_COMPILER)}\n"
        + f"Used closure-library {git_rev(CLOSURE_LIBRARY)}\n"
        + f"Used Coreweb {git_rev(COREWEB)}\n"
    )


def build_compiled() -> None:
    compile_js(["cw.net.setupXDRFrame", "cw.net.XHRSlave"], f"{COMPILED}/xdrframe.js")
    compile_js(
        ["minerva_client"],
        f"{COMPILED}/minerva-client.js",
        defines={"cw.net.STANDALONE_CLIENT_BUILD_": "true"},
    )


def build_demos() -> None:
    for demo in ["whiteboard", "bskystream"]:
        compile_js([demo], f"{DEMOS_STATIC}/{demo}.js", externs=NORMAL_EXTERNS)


def main() -> None:
    match sys.argv[1:]:
        case [] | ["all"]:
            build_deps()
            build_compiled()
            build_demos()
        case ["deps"]:
            build_deps()
        case ["compile"]:
            build_compiled()
        case ["demos"]:
            build_demos()
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main()
