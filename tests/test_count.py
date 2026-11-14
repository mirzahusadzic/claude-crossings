"""The count, the record and the hook, on a transcript written here. No model, no network.

Run with pytest, or without it:  python3 tests/test_count.py
"""

from __future__ import annotations

import atexit
import contextlib
import functools
import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from crossing import count, handover, hook, read, record, show, store, transcript  # noqa: E402

# No test reaches the real home: what would go to the plugin's data folder goes here, and so
# does the home of a project that has no crossings/ folder of its own. A home named outright,
# and the project root a live session exports, are not a test's to use.
DATA = Path(tempfile.mkdtemp(prefix="crossing-data-"))
os.environ["CLAUDE_PLUGIN_DATA"] = str(DATA)
os.environ["CROSSING_HOMES"] = str(DATA / "homes")
os.environ["CROSSING_SWITCHED"] = str(DATA / "switched")  # the person's record of the projects switched on
os.environ["CROSSING_LIVE"] = str(DATA / "live")  # for a hook started as a process of its own
hook.LIVE = DATA / "live"  # and for the one already loaded here
os.environ.pop("CLAUDE_PROJECT_DIR", None)
os.environ.pop("CROSSING_HOME", None)
# How the harness says a session was started: no hook here takes its session for one a person sits
# in unless a test says so, as in test_store. A session that runs these tests may well be one, and
# a session a person sits in is welcomed as it starts in a home with no label.
os.environ.pop("CLAUDE_CODE_ENTRYPOINT", None)


def sweep(folder: Path) -> None:
    """A test's own files, one by one. A link is taken away as a link: what it leads to is
    swept where it lies."""
    if folder.exists():
        for left in sorted(folder.rglob("*"), reverse=True):
            left.rmdir() if left.is_dir() and not left.is_symlink() else left.unlink()
        folder.rmdir()


atexit.register(sweep, DATA)


def switched_on(project: Path) -> None:
    """The person's act of switching Crossing on in a project, as far as their record of it goes."""
    store.consent(project)


@contextlib.contextmanager
def set_to(**env):
    """Environment variables for the length of a block, put back afterwards. One set to None
    is taken away for that long."""
    before = {name: os.environ.get(name) for name in env}
    try:
        for name, value in env.items():
            os.environ.pop(name, None) if value is None else os.environ.update({name: value})
        yield
    finally:
        for name, value in before.items():
            os.environ.pop(name, None) if value is None else os.environ.update({name: value})


def in_person(test):
    """A test of what a session a person sits in is told (see record.attended): a session no
    person sits in is not woken with a note after a cut."""

    @functools.wraps(test)
    def run(tmp_path):
        with set_to(CLAUDE_CODE_ENTRYPOINT="cli"):
            return test(tmp_path)

    return run


@contextlib.contextmanager
def live_in(folder: Path):
    """The folder sessions are marked in, for the length of a block. It is put back afterwards:
    left where a test put it, a later test would mark its session in a folder already swept."""
    before, hook.LIVE = hook.LIVE, folder
    try:
        yield
    finally:
        hook.LIVE = before


HIS_WHOLE = "Please keep the door open for both of us, and write down what you decide about it."
HIS_MID_TURN = "and one more thing sent while you were working on it"
HIS_KEPT_HALF = "The second half of this message is dropped by the summary because it is long"
HIS_HALF = HIS_KEPT_HALF + "; the first half is kept as it stands in the record."
OWN_FIRST = "A reply whose first sentence is quoted by the summary exactly as it was said."
OWN_ONE = "I will keep the door open for both of us. Here is a long sentence of mine that the summary will not hold at all, not a word of it."
OWN_TWO = OWN_FIRST + " And a second sentence that is not there in any form whatever, friend."
TOOL_OUT = "file-a\nfile-b\n" * 50
SUMMARY = f'Summary. The person said: "{HIS_WHOLE}" and "{HIS_KEPT_HALF}". The session said: "{OWN_FIRST}"'


def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


BEFORE = [
    user(HIS_WHOLE),
    {
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": OWN_ONE}, {"type": "tool_use", "input": {"command": "ls"}}]},
    },
    {
        "type": "user",
        "toolUseResult": {"stdout": TOOL_OUT},
        "message": {"content": [{"type": "tool_result", "content": TOOL_OUT}]},
    },
    {
        "type": "attachment",
        "attachment": {"type": "queued_command", "prompt": HIS_MID_TURN, "origin": {"kind": "human"}},
    },
    user([{"type": "text", "text": "<system-reminder>not his</system-reminder>"}]),
    user(HIS_HALF),
    {"type": "assistant", "message": {"content": [{"type": "text", "text": OWN_TWO}]}},
]
CUT = [
    {
        "type": "system",
        "subtype": "compact_boundary",
        "compactMetadata": {"trigger": "manual", "preTokens": 1000, "postTokens": 100, "durationMs": 2000},
    },
    {"type": "user", "isCompactSummary": True, "message": {"content": [{"type": "text", "text": SUMMARY}]}},
    user("a message after the cut, which is not part of what was cut"),
]


def written(folder: Path, rows: list) -> Path:
    path = folder / "session-0001.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows) + "not json\n", encoding="utf-8")
    return path


def test_both_voices_are_counted_by_size_and_not_by_openings(tmp_path):
    c = count.count(written(tmp_path, BEFORE + CUT))
    p, s = c["person"], c["session"]
    assert (c["boundary_line"], c["summary_line"], c["span_starts_after"]) == (8, 9, 0)
    assert (c["trigger"], c["tokens_before"], c["tokens_after"], c["cut_ms"]) == ("manual", 1000, 100, 2000)
    assert (p["messages"], p["typed"], p["sent_mid_turn"], p["whole"]) == (3, 2, 1, 1)
    assert p["chars"] == len(HIS_WHOLE) + len(HIS_MID_TURN) + len(HIS_HALF)
    # the message whose opening alone is in the summary counts for its opening, not as crossed
    assert p["covered"] == len(HIS_WHOLE) + len(HIS_KEPT_HALF)
    assert (p["sentences"], p["sentences_found"]) == (3, 1)
    assert (s["messages"], s["whole"]) == (2, 0)
    assert s["covered"] == len(" keep the door open for both of us") + len(OWN_FIRST)
    assert (s["sentences"], s["sentences_found"]) == (4, 1)
    assert c["tool_result_chars"] == len(TOOL_OUT) and c["tool_call_chars"] == len(json.dumps({"command": "ls"}))
    assert [x["line"] for x in p["pointers"]] == [1, 4, 6] and [x["line"] for x in s["pointers"]] == [2, 7]


def test_a_cut_the_transcript_does_not_hold_yet_is_counted_from_the_summary_handed_over(tmp_path):
    c = count.count(written(tmp_path, BEFORE), SUMMARY)
    assert c["boundary_line"] == len(BEFORE) + 2 and c["trigger"] is None
    assert (c["person"]["messages"], c["session"]["messages"]) == (3, 2)
    assert c["person"]["covered"] == len(HIS_WHOLE) + len(HIS_KEPT_HALF)


def test_the_second_cut_counts_only_what_came_after_the_first(tmp_path):
    later = [user("Only this message stands between the first cut and the second cut of the session.")]
    second = [
        {"type": "system", "subtype": "compact_boundary", "compactMetadata": {"trigger": "auto"}},
        {"type": "user", "isCompactSummary": True, "message": {"content": "A second summary with other words."}},
    ]
    c = count.count(written(tmp_path, BEFORE + CUT[:2] + later + second))
    assert (c["span_starts_after"], c["person"]["messages"], c["session"]["messages"]) == (9, 1, 0)


def test_the_record_holds_counts_and_pointers_and_no_text_of_either_voice(tmp_path):
    (tmp_path / "crossings").mkdir()
    switched_on(tmp_path)
    path = written(tmp_path, BEFORE + CUT)
    event = {
        "hook_event_name": "PostCompact",
        "transcript_path": str(path),
        "cwd": str(tmp_path),
        "session_id": "abcdef0123456789",
        "trigger": "manual",
        "compact_summary": SUMMARY,
    }
    assert hook.run(event) is None
    pages = sorted((tmp_path / "crossings").glob("*-cut-*"))  # the record; the archive beside it is another matter
    assert [p.name for p in pages] == ["abcdef01-cut-1.json", "abcdef01-cut-1.md"]
    kept = "".join(p.read_text(encoding="utf-8") for p in pages)
    for word in ("friend", "door open", "second half", "one more thing"):
        assert word not in kept
    assert "line 4," in kept and "| the person's | 3 | 1 |" in kept

    # Guard: the session's id and the session's voice once shared a key, and the id was lost.
    side = json.loads(pages[0].read_text(encoding="utf-8"))
    assert side["session_id"] == "abcdef0123456789" and side["session"]["messages"] == 2
    shown = show.block(tmp_path)
    assert "1 cut on record" in shown and "session abcdef01, cut 1 · manual" in shown
    assert "1,000 → 100 tokens · the cut took 2 s" in shown and "friend" not in shown
    assert "nothing held: 1 of 3 messages · 0 of 2 replies" in shown
    assert "no cut on record" in show.block(tmp_path, session="ffff")

    assert hook.run({**event, "hook_event_name": "SessionStart", "source": "startup"}) is None


@in_person
def test_the_note_comes_before_the_count_and_is_never_about_an_earlier_cut(tmp_path):
    """Guard: the harness calls SessionStart, then PostCompact, and writes the boundary after
    both. Read naively, the first cut gets no note and the second gets the first cut's numbers."""
    (tmp_path / "crossings").mkdir()
    switched_on(tmp_path)
    path = written(tmp_path, BEFORE)  # the boundary is not in the transcript yet
    event = {"transcript_path": str(path), "cwd": str(tmp_path), "session_id": "abcdef0123456789"}
    start = {**event, "hook_event_name": "SessionStart", "source": "compact"}
    post = {**event, "hook_event_name": "PostCompact", "trigger": "manual", "compact_summary": SUMMARY}

    said = json.loads(hook.run(start))["hookSpecificOutput"]["additionalContext"]
    assert "cut 1 of this session" in said
    assert "%" not in said and str(tmp_path) not in said  # no number, and no file named: the door is the way back
    promised = tmp_path / "crossings" / "abcdef01-cut-1.md"
    assert not promised.exists()
    hook.run(post)
    side = json.loads(promised.with_suffix(".json").read_text(encoding="utf-8"))
    assert promised.exists() and (side["cut"], side["trigger"], side["traced"]) == (1, "manual", True)

    later = [user("Only this message stands between the first cut and the second cut of the session.")]
    written(tmp_path, BEFORE + CUT[:2] + later)  # the second boundary is not written yet either
    said = json.loads(hook.run(start))["hookSpecificOutput"]["additionalContext"]
    assert "cut 2 of this session" in said
    assert "cut 1 of this session" not in said
    hook.run({**post, "compact_summary": "A second summary with other words."})
    assert json.loads((tmp_path / "crossings" / "abcdef01-cut-2.json").read_text())["person"]["messages"] == 1
    assert json.loads(promised.with_suffix(".json").read_text())["person"]["messages"] == 3  # the first is untouched


def test_a_cut_that_cannot_be_counted_never_breaks_the_session(tmp_path):
    (tmp_path / "crossings").mkdir()
    switched_on(tmp_path)
    env = dict(os.environ, CLAUDE_PLUGIN_DATA=str(tmp_path))
    for event in (
        {"hook_event_name": "PostCompact", "transcript_path": str(tmp_path / "missing.jsonl"), "cwd": str(tmp_path)},
        "not an event",
    ):
        ran = subprocess.run(
            [sys.executable, "-I", str(ROOT / "crossing" / "hook.py")],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert ran.returncode == 0 and ran.stdout == ""
    assert (tmp_path / "errors.log").read_text(encoding="utf-8").count("Traceback") == 2


def test_a_message_too_short_to_judge_is_never_counted_as_held(tmp_path):
    """Guard: on the first real cut a three-character reply counted as "in the summary whole"
    because those characters occur in any summary."""
    rows = [
        user("ok"),
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Yes"}]}},
        user("ok -- check it"),
        CUT[0],
        {
            "type": "user",
            "isCompactSummary": True,
            "message": {"content": 'Yesterday the tide table changed. They said: "ok -- check it"'},
        },
    ]
    c = count.count(written(tmp_path, rows))
    p, s = c["person"], c["session"]
    assert (p["messages"], p["too_short"], p["whole"], p["covered"]) == (2, 1, 1, len("ok -- check it"))
    assert (s["messages"], s["too_short"], s["whole"], s["covered"]) == (1, 1, 0, 0)


def test_a_thinking_block_is_never_read():
    """A session's reasoning is not the plugin's to open: not as prose, not as traffic."""
    row = {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "thinking", "thinking": "private reasoning that must stay where it is"},
                {"type": "text", "text": "The reply itself."},
            ]
        },
    }
    assert transcript.session(row) == ["The reply itself."]
    assert transcript.tool_traffic(row) == (0, 0) and transcript.person(row) == []


def test_reading_a_line_back_shows_what_was_said_and_never_the_reasoning(tmp_path):
    """Guard: raw transcript rows can hold reasoning blocks. A message is read back through a
    reader that shows only what was said."""
    rows = [
        user(HIS_WHOLE),
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "thinking", "thinking": "private reasoning that must stay where it is"},
                    {"type": "text", "text": OWN_FIRST},
                    {"type": "tool_use", "input": {"command": "ls -la"}},
                ]
            },
        },
        BEFORE[2],
    ]
    out = "\n".join(read.said(written(tmp_path, rows), {1, 2, 3}))
    assert f"(line 1), the person: {HIS_WHOLE}" in out and f"(line 2), the session: {OWN_FIRST}" in out
    assert "(line 3): nothing was said here" in out
    assert "private reasoning" not in out and "ls -la" not in out and "file-a" not in out
    said = hook.waking(count.count(written(tmp_path, BEFORE), pending=True))
    assert "find, then thread" in said and "Do not open the transcript file" in said


def test_a_session_is_marked_while_crossing_is_on_in_it(tmp_path):
    """The status line shows the sign from this marker: there from any start, gone at the end,
    and only a start after a compaction is answered with a note."""
    (tmp_path / "crossings").mkdir()
    switched_on(tmp_path)
    event = {"transcript_path": str(written(tmp_path, BEFORE)), "cwd": str(tmp_path), "session_id": "abcdef0123456789"}
    with (
        live_in(tmp_path / "live"),
        set_to(CROSSING_WAIT="1"),
    ):  # the end of the session is waited for, not left writing
        for source in ("startup", "resume", "clear", "fork"):
            assert hook.run({**event, "hook_event_name": "SessionStart", "source": source}) is None
            assert (hook.LIVE / "abcdef0123456789").exists()
        assert hook.run({**event, "hook_event_name": "SessionEnd"}) is None
        assert not (hook.LIVE / "abcdef0123456789").exists()
        assert hook.run({**event, "hook_event_name": "SessionStart", "source": "compact"}) is None  # no person: no note
        with set_to(
            CLAUDE_CODE_ENTRYPOINT="cli"
        ):  # one a person sits in is also welcomed, once, in a home with no label
            assert hook.run({**event, "hook_event_name": "SessionStart", "source": "startup"}) is not None
            assert hook.run({**event, "hook_event_name": "SessionStart", "source": "resume"}) is None
            assert hook.run({**event, "hook_event_name": "SessionStart", "source": "compact"}) is not None
        try:  # a name that is not a session's is refused, and never written
            hook.mark("../outside", True)
        except record.Unnamed:
            pass
        else:
            raise AssertionError("a name that is no session's was taken")
        assert sorted(p.name for p in hook.LIVE.iterdir()) == ["abcdef0123456789"]
    assert hook.LIVE != tmp_path / "live"


def test_a_message_is_found_by_its_id_where_its_line_has_moved(tmp_path):
    """Guard: a fork writes a new transcript in which every message sits on another line and
    keeps its id. A hand-over anchored by line points at the wrong messages there."""
    one = {**user(HIS_WHOLE), "uuid": "b4a6ea10-0000-4000-8000-000000000001"}
    two = {
        "type": "assistant",
        "uuid": "b11289f4-0000-4000-8000-000000000002",
        "message": {"content": [{"type": "text", "text": OWN_FIRST}]},
    }
    base = written(tmp_path, [one, two])
    fork = tmp_path / "fork.jsonl"
    fork.write_text(
        "".join(json.dumps(r) + "\n" for r in [BEFORE[2], BEFORE[4], one, BEFORE[2], two]), encoding="utf-8"
    )
    for path, line in ((base, 1), (fork, 3)):
        out = read.said(path, set(), {"b4a6ea10"})
        assert out == [f"b4a6ea10 (line {line}), the person: {HIS_WHOLE}"]
    assert read.said(fork, {1}, set()) == ["no id (line 1): nothing was said here"]  # what line 1 is there
    c = count.count(written(tmp_path, [one, two] + CUT[:2]))
    assert [p["id"] for p in c["person"]["pointers"]] == ["b4a6ea10"] and c["session"]["pointers"][0][
        "id"
    ] == "b11289f4"


@in_person
def test_where_the_count_has_nothing_to_stand_on_it_says_so(tmp_path):
    """Guard: a cut the plugin answered hands the count no summary, and a session just forked
    has no conversation in its new file. Noughts must not be shown as if they were counts."""
    (tmp_path / "crossings").mkdir()
    switched_on(tmp_path)
    event = {"cwd": str(tmp_path), "session_id": "abcdef0123456789"}
    path = written(tmp_path, BEFORE)
    hook.run(
        {
            **event,
            "transcript_path": str(path),
            "hook_event_name": "PostCompact",
            "trigger": "manual",
            "compact_summary": "",
        }
    )  # the plugin answered: no summary comes
    page = (tmp_path / "crossings" / "abcdef01-cut-1.md").read_text(encoding="utf-8")
    assert "### Nothing to compare against" in page and "3 messages of the person's and 2 replies" in page
    assert "%" not in page.split("### Nothing to compare against")[1].split("###")[0]

    empty = tmp_path / "forked.jsonl"
    empty.write_text(json.dumps({"type": "system", "subtype": "other"}) + "\n", encoding="utf-8")
    said = json.loads(
        hook.run(
            {
                **event,
                "session_id": "ffff0000aaaa",
                "transcript_path": str(empty),
                "hook_event_name": "SessionStart",
                "source": "compact",
            }
        )
    )
    note = said["hookSpecificOutput"]["additionalContext"]
    assert "replies of yours" not in note and "%" not in note  # the note brings no numbers; the page says what it lacks
    hook.run(
        {
            **event,
            "session_id": "ffff0000aaaa",
            "transcript_path": str(empty),
            "hook_event_name": "PostCompact",
            "trigger": "manual",
            "compact_summary": SUMMARY,
        }
    )
    page = (tmp_path / "crossings" / "ffff0000-cut-1.md").read_text(encoding="utf-8")
    assert "### Not counted" in page and "word for word" not in page.split("### Not counted")[1]


def test_a_hand_over_carries_the_anchored_words_themselves(tmp_path):
    """Guard: a label can paraphrase the person where a summary holds their words. The words
    are taken from the record, for both voices."""
    one = {**user(HIS_WHOLE), "uuid": "b4a6ea10-0000-4000-8000-000000000001"}
    two = {
        "type": "assistant",
        "uuid": "b11289f4-0000-4000-8000-000000000002",
        "message": {
            "content": [
                {"type": "thinking", "thinking": "kept where it is"},
                {"type": "text", "text": OWN_FIRST + " " + "and more " * 200},
            ]
        },
    }
    path = written(tmp_path, [one, two])
    hand = tmp_path / "hand-over.md"
    hand.write_text(
        "session `0a1b2c3d-…`\n| F | a label | `b4a6ea10` / `b11289f4` |\n| X | gone | `deadbeef` | line 12345678 |\n",
        encoding="utf-8",
    )
    assert handover.named(hand.read_text()) == ["b4a6ea10", "b11289f4", "deadbeef"]  # a number is not an id
    text = handover.page(path, hand)
    assert f"- `b4a6ea10`, the person: {HIS_WHOLE}" in text
    assert f"- `b11289f4`, the session: {OWN_FIRST}" in text and text.count("and more") < 200 and "[…]" in text
    assert "kept where it is" not in text and "not in this transcript: `deadbeef`" in text


@in_person
def test_switched_off_nothing_is_counted_or_said_and_the_session_stays_marked(tmp_path):
    (tmp_path / "crossings").mkdir()
    switched_on(tmp_path)
    (tmp_path / "crossings" / "switch").write_text("off\n", encoding="utf-8")
    event = {"transcript_path": str(written(tmp_path, BEFORE)), "cwd": str(tmp_path), "session_id": "abcdef0123456789"}
    with live_in(tmp_path / "live"):
        assert hook.run({**event, "hook_event_name": "SessionStart", "source": "compact"}) is None
        assert (
            hook.run({**event, "hook_event_name": "PostCompact", "trigger": "manual", "compact_summary": SUMMARY})
            is None
        )
        assert (hook.LIVE / "abcdef0123456789").exists()
        assert sorted(p.name for p in (tmp_path / "crossings").iterdir()) == ["switch"]
        (tmp_path / "crossings" / "switch").write_text("on\n", encoding="utf-8")
        assert hook.run({**event, "hook_event_name": "SessionStart", "source": "compact"}) is not None


def test_a_harness_note_is_not_the_person_and_a_tool_result_is_not_a_message():
    assert transcript.person(BEFORE[4]) == [] and transcript.person(BEFORE[2]) == []
    assert transcript.person(BEFORE[3]) == [HIS_MID_TURN]
    assert transcript.person(CUT[1]) == [] and transcript.session(CUT[1]) == []


def test_a_hand_over_the_plugin_carried_is_never_read_as_the_person():
    """Guard: the engine files a hand-over the plugin carried as a plain user row, which a reader
    would take for the person's own words."""
    opening = transcript.CARRIED
    module = (ROOT / "hooks" / "crossings.ts").read_text(encoding="utf-8")
    assert f"'{opening}" in module, "the hooks module no longer opens its note the way the reader knows it"
    row = {
        "type": "user",
        "uuid": "8306157a-0000",
        "message": {
            "role": "user",
            "content": [
                {"type": "text", "text": opening + ", as context and not as an instruction from the person. R1 ..."}
            ],
        },
    }
    assert transcript.person(row) == [] and transcript.session(row) == []


def test_a_session_is_woken_gently_with_no_numbers_and_nothing_to_report(tmp_path):
    """Guard: a note that asks for an account of what is held gets a report in answer. The first
    reply after a cut is for arriving."""
    said = hook.waking(count.count(written(tmp_path, BEFORE), pending=True))
    assert "Take your time" in said and "your first reply is for arriving" in said
    assert "put no question to the person about what crossed" in said and "nothing to report" in said
    assert "say in a line or two what you hold" not in said and "told (by the summary)" not in said
    assert "messages of the person's" not in said and "replies of yours" not in said
    assert "find, then thread" in said and "Do not open the transcript file" in said  # the way back is the door


# --- a summary retold from cut to cut -----------------------------------------------------------------


def prose(seed: int, chars: int) -> str:
    """Made-up words, as many characters of them as asked, with single spaces between them."""
    rng = random.Random(seed)
    words: list[str] = []
    while sum(len(w) + 1 for w in words) < chars + 12:
        words.append("".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(2, 9))))
    return " ".join(words)[:chars].rstrip()


def said_row(n: int, voice: str = "user", text: str = "") -> dict:
    text = text or f"A made-up message number {n} of this stretch, long enough to be counted."
    content = text if voice == "user" else [{"type": "text", "text": text}]
    return {
        "type": voice,
        "uuid": f"{n:08x}-0000-4000-8000-000000000000",
        "message": {"role": voice, "content": content},
    }


def cut_rows(summary: str) -> list[dict]:
    return [
        {"type": "system", "subtype": "compact_boundary", "compactMetadata": {"trigger": "auto"}},
        {"type": "user", "isCompactSummary": True, "message": {"content": [{"type": "text", "text": summary}]}},
    ]


def test_a_summary_is_counted_by_its_length_and_by_what_of_it_repeats_the_one_before(tmp_path):
    key = bytes(range(32))
    first = prose(1, 3000)
    half = first[:1500].rstrip()
    for second, repeated in ((prose(2, 3000), 0), (first, len(first)), (half + " " + prose(3, 1500), len(half))):
        path = written(tmp_path, [said_row(1)] + cut_rows(first) + [said_row(2)] + cut_rows(second))
        asked = []
        c = count.count(
            path, key=key, earlier=lambda ordinal, asked=asked: asked.append(ordinal) or count.runs(first, key)
        )
        assert asked == [2] and c["cut"] == 2
        assert c["summary_chars"] == len(second) and c["retold"] == repeated, (c["retold"], repeated)
        assert count.unpacked(c["summary_runs"]) == count.runs(second, key)
    assert count.retold(first, count.runs(first, bytes(32)), key) == 0  # digests made with another key match nothing
    c = count.count(path)  # no key: nothing kept, nothing compared
    assert c["summary_runs"] is None and c["retold"] is None
    assert count.runs("shorter than a run", key) == set() and count.retold("shorter than a run", {b"1234"}, key) == 0
    for odd in (None, 5, "not base64 !", "AAAA"):  # none of them is a set of digests
        assert count.unpacked(odd) is None, odd
    assert count.unpacked("") == set()


SID = "abcdef0123456789"


def two_cuts(
    tmp_path: Path,
    first: str,
    second: str,
    on_the_stretch: bool = True,
    door_since: bool = True,
    files: dict | None = None,
) -> tuple[str | None, Path, dict]:
    """A session cut twice: after the first cut a label is marked, on a message said since it or on
    one before it, and a line left at the door, since that cut or before it. The second cut's answer,
    the home, and the event of the second cut."""
    crossings = tmp_path / "crossings"
    crossings.mkdir()
    switched_on(tmp_path)
    for name, text in (files or {}).items():
        (crossings / name).write_text(text, encoding="utf-8")
    path = written(tmp_path, [said_row(1), said_row(2, "assistant")])
    event = {
        "hook_event_name": "PostCompact",
        "transcript_path": str(path),
        "cwd": str(tmp_path),
        "session_id": SID,
        "trigger": "auto",
    }
    store.archive(path, crossings) and store.build(crossings)
    if not door_since:
        assert store.mark(crossings, "next", "session", "Left before the first cut.", [f"{1:08x}"])["written"]
    assert hook.run({**event, "compact_summary": first}) is None  # the first cut: nothing before it to compare with
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("".join(json.dumps(r) + "\n" for r in cut_rows(first) + [said_row(3), said_row(4, "assistant")]))
    store.archive(path, crossings) and store.build(crossings)
    anchor = f"{3:08x}" if on_the_stretch else f"{1:08x}"
    assert store.mark(crossings, "work", "both", "The stretch since the first cut, marked.", [anchor])["written"]
    if door_since:
        assert store.mark(crossings, "next", "session", "Left since the first cut.", [f"{4:08x}"])["written"]
    event = {**event, "compact_summary": second}
    return hook.run(event), crossings, event


LONG_FIRST = prose(11, 21000)
RETOLD = prose(12, 1500) + " " + LONG_FIRST  # most of it the first summary again


def test_where_most_of_a_long_summary_retells_the_one_before_the_person_is_told_once(tmp_path):
    answer, crossings, event = two_cuts(tmp_path, LONG_FIRST, RETOLD)
    shown = json.loads(answer)
    assert shown == {"systemMessage": hook.retold().format(2)}  # for the person alone: no context, no decision
    assert shown["systemMessage"].startswith(
        "Crossings · this session has been cut 2 times and most of its summary now "
        "retells the one before; a new session would start from the store alone"
    )
    side = json.loads((crossings / "abcdef01-cut-2.json").read_text(encoding="utf-8"))
    assert (side["summary_chars"], side["retold"], side["labelled"], side["door"], side["told"]) == (
        len(RETOLD),
        len(LONG_FIRST),
        1,
        1,
        True,
    )
    page = (crossings / "abcdef01-cut-2.md").read_text(encoding="utf-8")
    assert (
        f"| The summary | {len(RETOLD):,} characters, 93% of them repeating the summary of cut 1 word for word, in runs "
        f"of {count.RUN} characters or more |" in page
    )
    first = (crossings / "abcdef01-cut-1.md").read_text(encoding="utf-8")
    assert f"| The summary | {len(LONG_FIRST):,} characters; no summary of an earlier cut of this session" in first
    assert hook.run(event) is None  # the same cut counted again: not told again
    assert json.loads((crossings / "abcdef01-cut-2.json").read_text(encoding="utf-8"))["told"] is True
    # The next cut is another cut: it is told where it is due.
    path = Path(event["transcript_path"])
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("".join(json.dumps(r) + "\n" for r in cut_rows(RETOLD) + [said_row(5)]))
    store.archive(path, crossings) and store.build(crossings)
    assert store.mark(crossings, "work", "both", "The third stretch.", [f"{5:08x}"])["written"]
    third = prose(13, 900) + " " + RETOLD
    assert hook.run({**event, "compact_summary": third}) is None  # no line left at the door since the second cut
    assert store.mark(crossings, "next", "session", "Left again.", [f"{5:08x}"])["written"]
    assert json.loads(hook.run({**event, "compact_summary": third}))["systemMessage"] == hook.retold().format(3)


def test_the_line_is_not_shown_where_any_one_condition_fails(tmp_path):
    cases = {
        "short": (prose(21, 12000), prose(22, 400) + " " + prose(21, 12000), {}),
        "little retold": (LONG_FIRST, prose(23, 12000) + " " + LONG_FIRST[:12000], {}),
        "no label on the stretch": (LONG_FIRST, RETOLD, {"on_the_stretch": False}),
        "no line at the door since": (LONG_FIRST, RETOLD, {"door_since": False}),
        "nothing to compare with": (prose(24, 10), RETOLD, {}),
    }
    for n, (name, (first, second, more)) in enumerate(cases.items()):
        folder = tmp_path / str(n)
        folder.mkdir()
        answer, crossings, _ = two_cuts(folder, first, second, **more)
        assert answer is None, name
        assert json.loads((crossings / "abcdef01-cut-2.json").read_text(encoding="utf-8"))["told"] is False, name


def test_a_home_may_set_the_two_figures_in_a_plain_file_each(tmp_path):
    short_first = prose(31, 12000)
    short = prose(32, 400) + " " + short_first
    little = prose(33, 12000) + " " + LONG_FIRST[:12000]  # half of it retold
    cases = [
        (short_first, short, {hook.RETELLING_LENGTH: "10000\n"}, True),
        (short_first, short, {hook.RETELLING_LENGTH: "ten thousand\n"}, False),  # no number: the constant stands
        (LONG_FIRST, little, {hook.RETELLING_SHARE: "45%\n"}, True),
        (LONG_FIRST, little, {hook.RETELLING_SHARE: " 45 \n"}, True),
        (LONG_FIRST, little, {hook.RETELLING_SHARE: "-5\n"}, False),
        (LONG_FIRST, RETOLD, {hook.RETELLING_SHARE: "95\n"}, False),
        (LONG_FIRST, RETOLD, {hook.RETELLING_LENGTH: "30000\n"}, False),
    ]
    for n, (first, second, files, told) in enumerate(cases):
        folder = tmp_path / str(n)
        folder.mkdir()
        answer, crossings, _ = two_cuts(folder, first, second, files=files)
        assert (answer is not None) == told, files
    assert hook.limits(tmp_path / "nowhere") == (hook.LONG, hook.MOSTLY) == (20000, 60)
    (crossings / hook.RETELLING_SHARE).write_bytes(b"\xff\xfe")
    assert hook.limits(crossings) == (30000, hook.MOSTLY)


def test_no_text_of_a_summary_is_kept_in_the_home_beside_the_archive(tmp_path):
    marker = "Quillfeathered"
    first = prose(41, 21000) + f" {marker} " + prose(42, 300)
    with set_to(CLAUDE_CODE_ENTRYPOINT="cli"):  # a person sits in it: the archive is kept at each cut too
        answer, crossings, _ = two_cuts(tmp_path, first, prose(43, 1200) + " " + first)
    assert answer is not None
    kept = {
        p: p.read_bytes() for p in crossings.rglob("*") if p.is_file() and "said" not in p.relative_to(crossings).parts
    }
    assert any(p.name == "abcdef01-cut-2.json" for p in kept) and (crossings / "said" / "runs.key").exists()
    runs = [first[at : at + count.RUN].encode() for at in range(0, len(first) - count.RUN, 7)]
    for path, data in kept.items():
        assert marker.encode() not in data, path
        assert not any(run in data for run in runs), path
    side = json.loads((crossings / "abcdef01-cut-2.json").read_text(encoding="utf-8"))
    assert count.unpacked(side["summary_runs"]) and side["runs_of"] == record.keyed(record.runs_key(crossings))


def test_digests_made_with_another_key_or_kept_in_no_good_order_are_compared_with_nothing(tmp_path):
    answer, crossings, event = two_cuts(tmp_path, LONG_FIRST, RETOLD)
    assert answer is not None
    side = crossings / "abcdef01-cut-1.json"
    for broken in ({"runs_of": "00000000"}, {"summary_runs": "not base64 !"}, {"door": None}):
        held = json.loads(side.read_text(encoding="utf-8"))
        side.write_text(json.dumps({**held, **broken}), encoding="utf-8")
        assert hook.run({**event, "compact_summary": RETOLD + " and once more"}) is None, broken
        side.write_text(json.dumps(held), encoding="utf-8")
    for broken in ("not json", "[1, 2]"):
        side.write_text(broken, encoding="utf-8")
        assert hook.run({**event, "compact_summary": RETOLD + " and once more"}) is None
    key = crossings / "said" / "runs.key"
    key.write_text("not a key\n", encoding="utf-8")
    assert record.runs_key(crossings) is None
    assert hook.run({**event, "compact_summary": RETOLD + " and again"}) is None
    assert json.loads((crossings / "abcdef01-cut-2.json").read_text(encoding="utf-8"))["summary_runs"] is None
    key.unlink()
    key.mkdir()
    assert record.runs_key(crossings) is None  # a key that cannot be read is no key
    key.rmdir()
    made, real = [], record.secrets.token_hex

    def racing(n):  # another cut makes the key between the look and the write: its key is the one taken
        key.write_text("ab" * 32 + "\n", encoding="ascii")
        made.append(n)
        return real(n)

    record.secrets.token_hex = racing
    try:
        assert record.runs_key(crossings) == bytes.fromhex("ab" * 32) and made == [32]
    finally:
        record.secrets.token_hex = real


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
