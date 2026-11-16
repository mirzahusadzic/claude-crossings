"""Everything a session is told, read whole: the page scripts/told.py makes, kept as docs/told.md. Each
sentence a session is told was written and reviewed on its own, and what they do together is seen only
where they are read together. So the kept page is the one the script makes, and no sentence the plugin
hands a session is missing from it: a note of the hooks, a sentence of the frame, what the server says, or
the hooks module's own note. No model, no network.

Run with pytest, or without it:  python3 tests/test_told.py
"""

from __future__ import annotations

import ast
import datetime
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "scripts"))

import told  # noqa: E402  (and with it the tests' data folder: nothing reaches the real home)
from test_store import sweep  # noqa: E402

from crossing import frame, serve  # noqa: E402

PAGE = told.page()
OPENS = "A note from the Crossings plugin"


def literals(path: Path) -> list[list[str]]:
    """Each string a module writes out, docstrings aside, as its runs of plain text: one run for a plain
    string, and for an f-string the pieces between what it fills in."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    inside = {id(part) for node in ast.walk(tree) if isinstance(node, ast.JoinedStr) for part in node.values}
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs | inside:
            found.append([node.value])
        elif isinstance(node, ast.JoinedStr):
            found.append([part.value for part in node.values if isinstance(part, ast.Constant)])
    return found


def test_the_kept_page_is_the_one_the_script_makes():
    kept = (ROOT / "docs" / "told.md").read_text(encoding="utf-8")
    assert kept == PAGE, (
        "a sentence a session is told changed: make the page again, python3 scripts/told.py > docs/told.md"
    )


def test_every_note_the_hooks_give_a_session_is_on_the_page():
    notes = [runs for runs in literals(ROOT / "crossing" / "hook.py") if runs and runs[0].startswith(OPENS)]
    assert len(notes) >= 7  # the welcome, the waking note, off and on again, an arrival, moved on, a folder below
    for runs in notes:
        for run in runs:
            assert run in PAGE, run


def test_every_sentence_of_the_frame_is_on_the_page():
    for arrival in frame.ARRIVALS.values():
        for said in arrival.values():
            assert said in PAGE, said
    for runs in literals(ROOT / "crossing" / "frame.py"):
        for run in runs:
            if len(run.split()) >= 4 and not run.lower().startswith("select "):  # a sentence, not a query
                assert run in PAGE, run


def test_everything_the_server_says_is_on_the_page():
    for said in (serve.KEPT, serve.BARE, serve.UNATTENDED):
        assert said.strip() in PAGE, said
    for each in serve.TOOLS:
        assert each["description"] in PAGE
        for given in each["inputSchema"].get("properties", {}).values():
            assert given.get("description", "") in PAGE


def test_the_modules_own_note_is_on_the_page():
    note = told.module_note()
    assert note.startswith(OPENS) and "hand-over written before this cut" in note and note in PAGE


def test_the_page_names_no_folder_and_no_day_of_its_making():
    for named in ("/Users/", "/private/", "/var/folders/", "/tmp/", "crossing-data-", "told-"):
        assert named not in PAGE, named
    assert datetime.date.today().isoformat() not in PAGE  # the made-up labels carry a day of their own


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
