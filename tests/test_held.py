"""What the home's lock holds, what a mark decides from, and what is let go of a small file once the
person was told it. No model, no network.

Run with pytest, or without it:  python3 tests/test_held.py
"""

from __future__ import annotations

import contextlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_store import D, E, home, row, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import store  # noqa: E402


@contextlib.contextmanager
def held_elsewhere(crossings: Path):
    """The home's lock, held by another act (an archive, a mark, a strike) for as long as the test
    needs it, with a short wait for any act that asks for it meanwhile."""
    wait, store.WAIT = store.WAIT, 0.2
    held = store._locked(crossings)
    try:
        yield
    finally:
        store._unlocked(crossings, held)
        store.WAIT = wait


def test_a_reading_of_a_session_no_person_sat_in_waits_for_the_homes_lock(tmp_path):
    crossings, _ = home(tmp_path)
    headless = tmp_path / "session-0002.jsonl"
    headless.write_text(json.dumps(row("user", "12345678", 6, "A prompt of a run no person sits in.")) + "\n")
    with held_elsewhere(crossings):
        assert store.unattended(headless, crossings) == 0  # nothing read, and no marker moved under another's act
        assert not [name for name in store.markers(crossings) if name.endswith("#unattended")]
    assert store.unattended(headless, crossings) == 1  # let go, the next reading keeps its id
    assert "12345678-0000-4000-8000-000000000000" in store.unheld(crossings)


def test_a_signing_waits_for_the_homes_lock(tmp_path):
    crossings, _ = home(tmp_path)
    key = store.mark(crossings, "work", "session", "The hull is grey.", [D])["id"]
    with held_elsewhere(crossings):
        assert not store.sign(crossings, key, "The hull is grey.", "made-up-model")  # nothing signed meanwhile
    assert (key, store.digest("The hull is grey.")) not in store.models(crossings)
    assert store.sign(crossings, key, "The hull is grey.", "made-up-model")
    assert store.listed(crossings, ids=(key,))["labels"][0]["model"] == "made-up-model"


def test_a_mark_over_labels_decides_from_the_pages_as_they_stand(tmp_path):
    crossings, _ = home(tmp_path)
    one = store.mark(crossings, "work", "session", "The hull is grey.", [D])["id"]
    two = store.mark(crossings, "work", "session", "The reminder is for March.", [E])["id"]
    stack = store.mark(crossings, "work", "session", "The hull and its reminder.", [one, two])["id"]
    page = next((crossings / "labels").glob("*.md"))
    as_marked = page.read_text(encoding="utf-8")
    page.write_text(as_marked.replace("The hull is grey.", "The hull is pale grey."), encoding="utf-8")
    store.build(crossings)  # a line written again by hand: its stack no longer stands for it
    assert store.listed(crossings, ids=(stack,))["labels"][0]["state"] == "misaligned"
    page.write_text(as_marked, encoding="utf-8")  # and put back as it was, with no build since
    out = store.mark(crossings, "work", "session", "A new stack over the hull.", [one], persons=False)
    assert not out["written"] and stack not in store.struck(crossings)  # the stack stands again, and is not struck
    assert store.listed(crossings, ids=(stack,))["labels"][0]["state"] == "carried"
    (crossings / "store.db").unlink()  # and where there is no index, the mark reads the pages as a read does
    assert not store.mark(crossings, "work", "session", "Another stack over the hull.", [one], persons=False)["written"]
    assert stack not in store.struck(crossings)


def test_a_mark_whose_sentence_holds_no_text_writes_nothing(tmp_path):
    crossings, _ = home(tmp_path)
    pages = sorted((crossings / "labels").glob("*.md"))
    for sentence, anchors in (("The hull is \udcff grey.", [D]), ("The hull is grey.", [D, "\udcff"])):
        out = store.mark(crossings, "work", "session", sentence, anchors)
        assert not out["written"] and "is none" in out["why"]
    assert sorted((crossings / "labels").glob("*.md")) == pages  # no page left holding its heading alone
    out = store.mark(crossings, "work", "session", "The hull is grey.", [D], model="made-\udcffmodel")
    assert out["written"] and store.listed(crossings, ids=(out["id"],))["labels"][0]["model"] == ""


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
