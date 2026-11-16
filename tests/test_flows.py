"""What flows from a transcript into the home and out of it again, at its edges: a row the parser cannot take
whole, a paste or a queued prompt of an odd shape, the frame's words and its size, the hooks' logs and
sidecars, the cuts on record, the reader, and where the second copy stages. No model, no network.

Run with pytest, or without it:  python3 tests/test_flows.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_store import home, row, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import count, store, transcript  # noqa: E402


def appended(path: Path, *lines: str) -> None:
    """Lines added to a transcript as the harness adds them, each a row of its own."""
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("".join(line + "\n" for line in lines))


def pages(crossings: Path) -> list[str]:
    """The archive's pages, each read as UTF-8 strictly: a page that holds a byte that is no text fails here."""
    return [page.read_bytes().decode("utf-8") for page in sorted((crossings / "said").glob("*.jsonl"))]


# --- a row the parser cannot take whole ---------------------------------------------------------------


def test_a_row_that_holds_half_a_character_is_kept_and_stops_no_later_reading(tmp_path):
    """A harness that cuts a character of two surrogates in two writes the half as an escape of its own, which the
    parser takes as it is: no text, which no file takes. The row is kept with the mark for a character that cannot be
    told in its place, and what was said after it is kept too, by this reading and by every one after it."""
    crossings, path = home(tmp_path)
    halved = json.dumps(row("user", "a1a1a1a1", 6, "Half a star: HALF, and the rest of it.")).replace("HALF", "\\ud83d")
    appended(path, halved, json.dumps(row("user", "b2b2b2b2", 7, "The mooring rope is new.")))
    assert store.archive(path, crossings) == 2
    assert store.archive(path, crossings) == 0, "kept once, and the marker moved past it"
    kept = "".join(pages(crossings))
    assert "Half a star: �, and the rest of it." in kept and "The mooring rope is new." in kept
    store.build(crossings)
    assert {"a1a1a1a1", "b2b2b2b2"} <= {each["id"] for each in store.find(crossings, "star rope")["said"]}
    # and a summary that holds such a half is counted all the same, its runs kept as digests
    summary = "The person said the mooring rope is new, and half a star \ud83d came with it."
    assert count.count(path, summary, pending=True, key=bytes(16))["summary_runs"]


def test_a_row_nested_deeper_than_the_parser_reads_is_passed_over_and_the_rest_is_kept(tmp_path):
    """A row nested past what the parser can follow is a line that is not a row, as one cut short is: it is passed
    over, and what was said before and after it is kept and counted."""
    crossings, path = home(tmp_path)
    appended(
        path,
        '{"type": "user", "uuid": "c3c3c3c3-0000", "toolUseResult": ' + "[" * 5000 + "]" * 5000 + "}",
        json.dumps(row("user", "d4d4d4d4", 8, "The new rope is blue.")),
    )
    assert store.archive(path, crossings) == 1
    assert "The new rope is blue." in "".join(pages(crossings))
    assert str(list(transcript.rows(path))[-1][1]["uuid"]).startswith("d4d4d4d4"), "and the reading goes on past it"
    assert count.count(path, "The person said the new rope is blue, and so it is.", pending=True)["traced"]


def test_a_tool_result_nested_deep_is_measured_by_its_length_as_any_other(tmp_path):
    """Tool traffic is measured by its length alone, however deep its result is nested."""
    _, path = home(tmp_path)
    deep = "[" * 600 + '"x"' + "]" * 600
    appended(
        path,
        '{"type": "user", "uuid": "e5e5e5e5-0000", "toolUseResult": "r", '
        '"message": {"content": [{"type": "tool_result", "content": ' + deep + "}]}}",
    )
    assert transcript.tool_traffic(list(transcript.rows(path))[-1][1]) == (0, 1)
    assert count.count(path, "The person said the hull is grey, and so it is.", pending=True)["traced"]


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
