"""What flows from a transcript into the home and out of it again, at its edges: a row the parser cannot take
whole, a paste or a queued prompt of an odd shape, the frame's words and its size, the hooks' logs and
sidecars, the cuts on record, the reader, and where the second copy stages. No model, no network.

Run with pytest, or without it:  python3 tests/test_flows.py
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import ran  # noqa: E402
from test_store import A, D, home, row, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import count, frame, record, show, store, transcript  # noqa: E402


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


# --- a paste, and a prompt sent while a turn ran ------------------------------------------------------


# A pasted text that holds the tags itself, as a pasted session's log or a program's source holds them.
HOLDS_TAGS = 'A log: <pasted_content id="9">inner</pasted_content> and the rest of the log, which goes on.'


def test_a_paste_ends_only_at_the_closing_tag_of_its_own_id(tmp_path):
    """The harness wraps a paste in a pair of tags that carry one id. A closing tag of another id, or of none,
    inside the pasted text is the text's own, and the paste runs on to the closing tag of its id: none of it is
    taken for the person's words."""
    sent = f'Please look at this. <pasted_content id="1">{HOLDS_TAGS}</pasted_content id="1">'
    said = {"type": "user", "uuid": "f6f6f6f6-0000", "message": {"content": sent}}
    assert transcript.person(said) == ["Please look at this."]
    typed, pastes = transcript.unpasted(sent)
    assert typed == f"Please look at this. [pasted: {len(HOLDS_TAGS)} characters]" and pastes == [HOLDS_TAGS]
    # and a pair whose closing tag carries no id, or whose opening tag carries none, ends as it always did
    assert transcript.unpasted('Two: <pasted_content id="2">a text</pasted_content> and so on.')[1] == ["a text"]
    assert transcript.unpasted("Three: <pasted_content>b text</pasted_content> and on.")[1] == ["b text"]


def queued(prompt: str) -> dict:
    """A prompt the person sent while a turn ran, as the harness keeps it."""
    held = {"type": "queued_command", "prompt": prompt, "origin": {"kind": "human"}}
    return {"type": "attachment", "uuid": "a7a7a7a7-0000", "attachment": held}


def test_a_prompt_sent_while_a_turn_ran_is_read_as_one_typed_at_the_prompt(tmp_path):
    """What the harness puts into the person's turn is not their words, and what they pasted is not counted as
    theirs, whether the turn was typed at the prompt or sent while the session was still at work."""
    for harness in (
        "<command-name>/compact</command-name>\n<command-message>compact</command-message>",
        "<system-reminder>a note of the harness</system-reminder>",
        "Caveat: The messages below were generated by the user while running local commands.",
    ):
        typed = {"type": "user", "uuid": "b8b8b8b8-0000", "message": {"content": harness}}
        assert transcript.person(typed) == [] and transcript.person(queued(harness)) == [], harness
        assert transcript.person(queued(harness), whole=True) == []
    sent = 'And this. <pasted_content id="4">A long text someone else wrote.</pasted_content id="4">'
    assert transcript.person(queued(sent)) == ["And this."], "a paste is not counted as the person's"
    assert transcript.person(queued(sent), whole=True) == [sent], "and is kept in the message's line as it was sent"
    only = '<pasted_content id="5">Only a paste.</pasted_content id="5">'
    assert transcript.person(queued(only)) == [] and transcript.person(queued(only), whole=True) == [only]
    assert transcript.person(queued("  Plain words, sent early.  ")) == ["Plain words, sent early."]


# --- the frame ----------------------------------------------------------------------------------------


def labelled(crossings: Path, *rows: str, day: str = "2026-11-12") -> None:
    """A page of labels written by hand (or brought by a pull), and the index built from it."""
    (crossings / "labels").mkdir(exist_ok=True)
    (crossings / "labels" / f"{day}.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n" + "".join(each + "\n" for each in rows),
        encoding="utf-8",
    )
    store.build(crossings)


# A key no mark gives, as a page written by hand or brought by a pull can hold one.
LONG = "9" * 1200


def test_the_frame_stays_within_what_a_hook_may_carry_whatever_length_a_key_has(tmp_path):
    """The frame never exceeds what a hook may carry, whatever its lines hold: also where the keys of the labels it
    names outside their own lines (marked after the line at the door, not fitted, resting on nothing held) are longer
    than any mark gives. Those sentences then say how many labels they are about, and `labels` names them."""
    crossings, _ = home(tmp_path)
    labelled(
        crossings,
        "| N1 | " + "The line at the door runs on. " * 400 + f"| session | `{D}` |",
        f"| W{LONG}1 | Work marked after the line. | both | `{D}` |",
        *(f"| R{n} | " + "The person keeps the quay in mind. " * 40 + f"| his | `{A}` |" for n in range(2, 7)),
        *(f"| R{LONG}{n} | A standing line of a long key. | his | `{A}` |" for n in range(2)),
        *(f"| W{LONG}{n} | Resting on what the archive never held. | both | `0a0a0a0a` |" for n in range(2, 9)),
    )
    for size in (frame.LEAST, frame.SIZE, frame.MOST):
        for new in (False, True):
            composed = frame.compose(crossings, size, new=new)
            assert len(composed) <= frame.MOST, (size, new, len(composed))
            assert "The line at the door runs on." in composed and "`labels` gives them." in composed, (size, new)
    composed = frame.compose(crossings, frame.MOST)
    assert "Marked after this line: 8 work labels." in composed and "7 labels rest on what the archive" in composed
    # and a frame of keys of the usual length names them, as it always did
    crossings, _ = home(tmp_path / "usual")
    labelled(
        crossings, "| N1 | The mooring is next. | session | `{D}` |".replace("{D}", D), f"| W2 | Done. | both | `{D}` |"
    )
    assert "Marked after this line: W2." in frame.compose(crossings)


# --- the hooks' logs and sidecars ---------------------------------------------------------------------


def door_call(crossings: Path, path: Path) -> str:
    """The event of a call of the door's own tool in a session a person sits in, as the harness hands it to a hook."""
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "mcp__plugin_crossings_door__look",
            "tool_input": {},
            "transcript_path": str(path),
            "session_id": "session-0001",
            "cwd": str(crossings.parent),
        }
    )


def test_a_log_of_calls_that_cannot_be_written_stops_no_hook(tmp_path):
    """The log of calls is a help to the plugin's own reading, and CROSSING_DEBUG turns it off: one that cannot be
    written holds nothing up, and what was said is kept all the same."""
    crossings, path = home(tmp_path)
    appended(path, json.dumps(row("user", "c9c9c9c9", 9, "The slip is free on Thursday.")))
    data = tmp_path / "data"
    data.mkdir()
    (data / "calls.log").write_text("", encoding="utf-8")
    (data / "calls.log").chmod(0o400)
    try:
        hooked = ran(
            "hook.py", stdin=door_call(crossings, path), CLAUDE_PLUGIN_DATA=str(data), CLAUDE_CODE_ENTRYPOINT="cli"
        )
    finally:
        (data / "calls.log").chmod(0o600)
    assert hooked.returncode == 0 and "The slip is free on Thursday." in "".join(pages(crossings))
    assert not (data / "errors.log").exists() or "calls.log" not in (data / "errors.log").read_text(encoding="utf-8")


def test_a_sidecar_cut_short_silences_no_note_at_a_sessions_start(tmp_path):
    """A cut's sidecar that a write left cut short is passed over where the waking note looks for it: the note is
    made from the count of the transcript, and the session is told what it is told at any start."""
    crossings, path = home(tmp_path)
    (crossings / "session--cut-1.json").write_text('{"cut": 1, "person": {"mess', encoding="utf-8")
    started = {
        "hook_event_name": "SessionStart",
        "source": "compact",
        "transcript_path": str(path),
        "session_id": "session-0001",
        "cwd": str(crossings.parent),
    }
    hooked = ran("hook.py", stdin=json.dumps(started), CLAUDE_CODE_ENTRYPOINT="cli")
    assert hooked.returncode == 0 and hooked.stdout.strip(), hooked.stderr
    told = json.loads(hooked.stdout)["hookSpecificOutput"]["additionalContext"]
    assert told.startswith(transcript.CARRIED)


# --- the cuts on record, and the reader ----------------------------------------------------------------


def test_a_sidecar_that_is_a_link_is_passed_over_in_one_line_and_the_others_are_shown(tmp_path):
    """No file of a home is read through a link: a cut's sidecar that is one is a record that cannot be read, named
    in one line, and the cuts beside it are shown as ever."""
    crossings, path = home(tmp_path)
    record.write(count.count(path, "A summary of the hull and the paint.", pending=True), crossings, "abcdef01", path)
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text("{}", encoding="utf-8")
    (crossings / "fedcba98-cut-1.json").symlink_to(elsewhere)
    shown = show.block(crossings.parent)
    assert "1 cut on record in this project" in shown and "session abcdef01, cut 1" in shown
    assert show.ODD.format("fedcba98-cut-1.json") in shown


def wide(script: str, *argv: str, **env: str) -> subprocess.CompletedProcess:
    """One of the plugin's scripts as the person starts it from a shell whose files are made readable to every
    account (a mask of 022, as many a shell has it)."""
    return subprocess.run(
        [sys.executable, "-I", str(ROOT / "crossing" / script), *argv],
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, **env},
        preexec_fn=lambda: os.umask(0o022),
    )


def test_the_cuts_on_record_and_the_reader_make_their_folder_for_its_owner_alone(tmp_path):
    """Every folder the plugin makes is its owner's alone, the data folder of its logs too, whichever of its scripts
    makes it first and whatever the shell it was started from would let others read."""
    crossings, path = home(tmp_path)
    (crossings / "abcdef01-cut-1.json").write_text("not json", encoding="utf-8")  # passed over, and logged
    data = tmp_path / "shown"
    assert wide("show.py", str(crossings.parent), CLAUDE_PLUGIN_DATA=str(data)).returncode == 0
    assert stat.S_IMODE(data.stat().st_mode) == 0o700 and stat.S_IMODE((data / "errors.log").stat().st_mode) == 0o600
    (crossings / "struck.txt").symlink_to(tmp_path / "nowhere")  # a link in the home: refused, and logged
    data = tmp_path / "read"
    read = wide(
        "read.py",
        str(path),
        "aaaaaaaa",
        "--cwd",
        str(crossings.parent),
        "--by-hook",
        CLAUDE_PLUGIN_DATA=str(data),
        CLAUDE_PLUGIN_ROOT=str(ROOT),
    )
    assert read.returncode == 1 and stat.S_IMODE(data.stat().st_mode) == 0o700, read.stderr


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
