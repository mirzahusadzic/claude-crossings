"""The seams a second review found, each with the test that holds it: what is said after the clock
went back while Crossing was off, a switch while an archive is under way, the hand-over's helper,
two marks at once, a session's strike and its words pages, a model's name, a summary that retells
the one before, the count's rows, a time that is no time, the guard's files, a long count, a long
miss, rows of an unknown shape, and a second copy that fails. No model, no network, and nothing of
the person's: the Keychain and the disk images are stand-ins that refuse.

Run with pytest, or without it:  python3 tests/test_seams.py
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import threading
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_checks import ON  # noqa: E402
from test_count import set_to  # noqa: E402
from test_edges import ran, through, words_script  # noqa: E402
from test_homes import public  # noqa: E402
from test_off import says  # noqa: E402
from test_serve import said  # noqa: E402
from test_store import DATA, at_terminal, home, row, started_by  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import count, door, handover, hook, off, store  # noqa: E402

# No test here reaches a disk image either: a stand-in for macOS's hdiutil comes first on the path,
# beside the one for the Keychain, and refuses. A test of a disk image's own use puts its own first.
(DATA / "bin" / "hdiutil").write_text("#!/bin/sh\necho 'no test makes a disk image' >&2\nexit 52\n", encoding="utf-8")
(DATA / "bin" / "hdiutil").chmod(0o755)


def kept_texts(folder: Path) -> list[str]:
    return [said["text"] for said in store._archived(folder)]


# --- what is said after the clock went back while Crossing was off ---------------------------------------


def off_and_on_with_the_clock_set_back(folder: Path, steady_on: float) -> tuple[Path, Path, Path]:
    """A project switched on, then off at ten, and on again after the clock was set back by half a
    minute, with `steady_on` the steady clock's reading then (it read 1000 as it was switched off).
    One message was said before switching off, one while off before the clock went back, and one
    while off after it; none of them is archived yet."""
    project, home_, path = public(folder)
    path.write_text("", encoding="utf-8")
    says(path, "10000001", "Said on the record before switching off.", at="2026-11-11T09:58:00.000Z")
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    clock, steady = {"now": "2026-11-11T10:00:00.000000+00:00"}, {"at": 1000.0}
    was_now, was_steady = off.now, off.steady
    off.now, off.steady = (lambda: clock["now"]), (lambda: steady["at"])
    try:
        assert through("switch", "off", "--cwd", str(project))[0] == 0
        says(path, "10000002", "Said while off, before the clock went back.", at="2026-11-11T10:00:05.000Z")
        says(path, "10000003", "Said while off, after the clock went back.", at="2026-11-11T09:59:35.000Z")
        clock["now"], steady["at"] = "2026-11-11T09:59:40.000000+00:00", steady_on
        assert through("switch", "on", "--cwd", str(project)) == (0, door.SWITCHED["again"] + "\n")
    finally:
        off.now, off.steady = was_now, was_steady
    return project, home_, path


def test_what_is_said_after_the_clock_went_back_while_off_is_kept_off_too(tmp_path):
    """What was said before the clock went back and what was said after it are both off the
    record, whether the steady clock can tell how long it was off or not."""
    for steady_on, known in (
        (1040.0, True),
        (5.0, False),
    ):  # 40 seconds by the steady clock; or a computer started again
        project, home_, path = off_and_on_with_the_clock_set_back(tmp_path / str(known), steady_on)
        assert through("build", "--transcript", str(path), "--cwd", str(project))[0] == 0
        kept = kept_texts(home_)
        assert "Said while off, before the clock went back." not in kept, known
        assert "Said while off, after the clock went back." not in kept, known
        # Where the steady clock tells how long it was off, what was said before that stays on the record.
        assert ("Said on the record before switching off." in kept) is known, (known, kept)
        spans, unread = off.spans(home_)
        assert unread == 0 and len(spans) == 2 and not store.lost(home_), spans


# --- a switch while an archive is under way ---------------------------------------------------------------


def test_what_is_said_after_switching_off_is_not_kept_by_an_archive_already_under_way(tmp_path):
    """A hook's archive has begun when the person switches off, and the session speaks the moment
    the switch has answered. The archive was made to pause just after it read the spans, so that
    the switch comes in between, as it may when two things happen at once."""
    project, home_, path = public(tmp_path)
    path.write_text("", encoding="utf-8")
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    event = {"hook_event_name": "PreToolUse", "tool_name": "mcp__plugin_crossing_door__find", "cwd": str(project)}
    event.update(transcript_path=str(path), session_id=path.stem)
    entered, release, answers = threading.Event(), threading.Event(), []
    real = off.spans

    def paused(folder: Path):
        found = real(folder)
        entered.set()
        release.wait(timeout=20)
        return found

    def switching() -> None:
        answers.append(through("switch", "off", "--cwd", str(project)))

    said = "Said the moment the switch was turned off."
    with started_by("cli"):
        off.spans = paused
        try:
            archiving = threading.Thread(target=hook.run, args=(event,))
            archiving.start()
            assert entered.wait(timeout=20)
            switch = threading.Thread(target=switching)
            switch.start()
            switch.join(timeout=1.0)
            spoken = not switch.is_alive()  # the switch answered while the archive was still under way
            if spoken:
                says(path, "20000001", said)
            release.set()
            switch.join(timeout=20)
            archiving.join(timeout=20)
        finally:
            off.spans = real
            release.set()
        if not spoken:  # the switch waited for the archive: the session speaks once it has answered
            says(path, "20000001", said)
        assert answers == [(0, door.SWITCHED["off"] + "\n")]
        assert hook.run(event) is None  # and the next reading
    assert said not in kept_texts(home_)


# --- the hand-over's helper ---------------------------------------------------------------------------


# What the helper says, as the person reads it: written out here, so that the words are held too.
UNBELIEVED = "This page lies in no home Crossings was switched on for, so nothing was written."
HELPERS = "This is the person's to run, from their own terminal, so nothing was written."


def a_page_and_its_transcript(folder: Path, crossings: Path) -> tuple[Path, Path]:
    """A hand-over page in `crossings` that names one message, and a transcript that holds it."""
    path = folder / "session-0009.jsonl"
    path.write_text(json.dumps(row("user", "aaaaaaaa", 1, "Words a helper must not copy.")) + "\n", encoding="utf-8")
    page = crossings / "hand-over.md"
    page.write_text("| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n| R1 | A line. | his | `aaaaaaaa` |\n")
    return path, page


def helper_at_a_terminal(*argv: str) -> tuple[int, str]:
    """The hand-over's words script as the person runs it from their own terminal, in this process:
    its answer's status and what it says on its error stream."""
    out, was = io.StringIO(), sys.argv
    sys.argv = ["handover.py", *argv]
    try:
        with at_terminal(), contextlib.redirect_stderr(out):
            code = handover.main()
    finally:
        sys.argv = was
    return code, out.getvalue()


def test_the_helper_writes_no_words_page_in_a_project_never_switched_on(tmp_path):
    crossings = tmp_path / "project" / "crossings"
    crossings.mkdir(parents=True)  # a crossings/ folder a repository brought, and no switch
    path, page = a_page_and_its_transcript(tmp_path, crossings)
    assert helper_at_a_terminal(str(path), str(page)) == (1, UNBELIEVED + "\n")
    assert not (crossings / "hand-over.words.md").exists()


def test_the_helper_writes_nothing_through_a_projects_crossings_that_is_a_link(tmp_path):
    project, outside = tmp_path / "project", tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / "crossings").symlink_to(outside, target_is_directory=True)
    path, _ = a_page_and_its_transcript(tmp_path, outside)
    assert helper_at_a_terminal(str(path), str(project / "crossings" / "hand-over.md")) == (1, UNBELIEVED + "\n")
    assert not (outside / "hand-over.words.md").exists()


def test_the_helper_is_the_persons_to_run(tmp_path):
    crossings, path = home(tmp_path)  # a home the person switched on
    made = ran("handover.py", str(path), str(crossings / "hand-over.md"))  # a session's shell: no terminal, no flag
    assert (made.returncode, made.stderr) == (1, HELPERS + "\n"), made
    assert not (crossings / "hand-over.words.md").exists()
    assert words_script(str(path), str(crossings / "hand-over.md")).returncode == 0  # as the plugin's own module
    assert (crossings / "hand-over.words.md").exists()
    out = through("page", "--cwd", str(crossings.parent))
    assert out[0] == 0 and "My boat is called Tern." in out[1]  # and the door's page reads it, as before


# --- two marks at once --------------------------------------------------------------------------------


def test_two_marks_over_one_line_at_the_same_moment_give_one_stack(tmp_path):
    """Two sessions stack the same standing line in the same instant: one stack stands over it, and
    the other mark is refused in its sentence. The two were made to meet just before the lock."""
    crossings, _ = home(tmp_path)  # R1 and W1 on its hand-over page
    barrier, answers, real = threading.Barrier(2), [], store._locked

    def met(folder: Path):
        barrier.wait(timeout=20)
        return real(folder)

    def marking(sentence: str) -> None:
        answers.append(store.mark(crossings, "relation", "session", sentence, ["R1"], persons=False))

    store._locked = met
    try:
        both = [threading.Thread(target=marking, args=(each,)) for each in ("The first stack.", "The second stack.")]
        for each in both:
            each.start()
        for each in both:
            each.join(timeout=30)
    finally:
        store._locked = real
    # Each thread marks through the store itself: what the door prints goes to one stream for the whole process.
    assert sorted(out["written"] for out in answers) == [False, True], answers
    refused = next(out["why"] for out in answers if not out["written"])
    assert refused.startswith("R1 already stands beneath ") and refused.endswith(
        ", and a line stands beneath one stack alone"
    ), refused
    stacks = [label["id"] for label in store.labels(crossings) if any(key == "R1" for key, _ in label["beneath"])]
    assert len(stacks) == 1, stacks


# --- a session's strike and its words pages -------------------------------------------------------------


def test_a_sessions_strike_takes_every_words_page_whole_also_one_that_gives_what_was_not_archived_yet(tmp_path):
    project, home_, path = public(tmp_path)
    path.write_text("", encoding="utf-8")
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    says(path, "aaaaaaaa", "This first message was archived.")
    assert through("build", "--transcript", str(path), "--cwd", str(project))[0] == 0
    says(path, "bbbbbbbb", "This second message was never archived.")  # said since, and no hook has read it
    (home_ / "hand-over.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n| R1 | Both lines. | both | `aaaaaaaa`, `bbbbbbbb` |\n",
        encoding="utf-8",
    )
    assert words_script(str(path), str(home_ / "hand-over.md")).returncode == 0
    words = (home_ / "hand-over.words.md").read_text(encoding="utf-8")
    assert "This first message was archived." in words and "This second message was never archived." in words
    code, out = through("strike", f"session:{path.stem}", "--cwd", str(project))
    assert code == 0 and not (home_ / "hand-over.words.md").exists(), out
    assert (
        "The hand-over words page hand-over.words.md was removed whole, as a session's strike takes every one: the "
        "next hand-over makes it again from the record." in out
    ), out
    # A single message's strike still mends a page line by line.
    path = tmp_path / "fedcba98-5555.jsonl"  # another session, whose words were not struck
    says(path, "cccccccc", "A third message, of another session.")
    assert through("build", "--transcript", str(path), "--cwd", str(project))[0] == 0
    (home_ / "hand-over.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n| R2 | One. | both | `cccccccc` |\n"
    )
    assert words_script(str(path), str(home_ / "hand-over.md")).returncode == 0
    code, out = through("strike", "cccccccc", "--cwd", str(project))
    assert code == 0 and "Its words were taken out of hand-over.words.md." in out, out
    assert (home_ / "hand-over.words.md").exists()


# --- a model's name -------------------------------------------------------------------------------------


def test_a_transcripts_model_with_a_line_break_writes_no_line_of_its_own(tmp_path):
    """A session with a file tool can write what it likes into its transcript, a model's name with a
    line break included: the hook before a mark, the mark and the hook after it keep no model of it."""
    project, home_, path = public(tmp_path)
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    hostile = "made-up-model\nW1@ffffff other-made-up-model"
    spoken = row("assistant", "bbbbbbbb", 2, [{"type": "text", "text": "Grey noted."}])
    spoken["message"]["model"] = hostile
    path.write_text(json.dumps(row("user", "aaaaaaaa", 1, "The hull is grey.")) + "\n" + json.dumps(spoken) + "\n")
    given = {"sentence": "A plain label.", "anchors": ["bbbbbbbb"]}
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": path.stem}
    event.update(tool_name="mcp__plugin_crossing_door__mark", tool_input=given)
    with started_by("cli"):
        assert hook.run({**event, "hook_event_name": "PreToolUse"}) is None  # archived, and the model handed over
        assert through("mark", "--anchors", "bbbbbbbb", "--bare", "--cwd", str(project), "A plain label.")[0] == 0
        answered = {"content": [{"type": "text", "text": "marked W1"}]}
        assert hook.run({**event, "hook_event_name": "PostToolUse", "tool_response": answered}) is None
    for name in ("models.txt", "calling.txt"):
        written = (home_ / name).read_text(encoding="utf-8") if (home_ / name).exists() else ""
        assert "other-made-up-model" not in written and "made-up-model" not in written, (name, written)
    assert store.models(home_) == {}
    kept = [said for said in store._archived(home_) if said["id"] == "bbbbbbbb"]
    assert kept and "model" not in kept[0], kept


# --- a summary that retells the one before --------------------------------------------------------------


def test_two_cuts_whose_summaries_open_alike_are_two_cuts(tmp_path):
    """The second cut's summary retells the first's, its first four hundred characters word for
    word, and something was said between: two pages, and the first left as it was."""
    project, home_, path = public(tmp_path)
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    rows = [row("user", "aaaaaaaa", 1, "The first stretch has this message.")]
    rows.append(row("assistant", "bbbbbbbb", 2, [{"type": "text", "text": "The first stretch has this reply."}]))
    path.write_text("".join(json.dumps(each) + "\n" for each in rows), encoding="utf-8")
    summary = "A summary that the next one retells, word for word, from its first sentence on. " * 8
    event = {"hook_event_name": "PostCompact", "transcript_path": str(path), "cwd": str(project), "trigger": "auto"}
    event.update(session_id=path.stem, compact_summary=summary)
    with started_by("cli"):
        assert hook.run(event) is None  # the first cut: its boundary is not written yet
        first = (home_ / "abcdef01-cut-1.json").read_text(encoding="utf-8")
        boundary = {"type": "system", "subtype": "compact_boundary", "compactMetadata": {"trigger": "auto"}}
        told = {"type": "user", "isCompactSummary": True, "message": {"content": [{"type": "text", "text": summary}]}}
        later = [row("user", "cccccccc", 3, "Said after the first cut."), row("user", "dddddddd", 4, "And this too.")]
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("".join(json.dumps(each) + "\n" for each in [boundary, told, *later]))
        again = summary[:400] + " And what was said since the first cut, told here at the end."
        assert hook.run({**event, "compact_summary": again}) is None  # the second cut
        assert hook.run({**event, "compact_summary": again}) is None  # and the same hook again, about it
    assert sorted(each.name for each in home_.glob("abcdef01-cut-*.json")) == [
        "abcdef01-cut-1.json",
        "abcdef01-cut-2.json",
    ]
    assert (home_ / "abcdef01-cut-1.json").read_text(encoding="utf-8") == first
    second = json.loads((home_ / "abcdef01-cut-2.json").read_text(encoding="utf-8"))
    assert (second["cut"], second["span_starts_after"], second["person"]["messages"]) == (2, 4, 2), second


# --- the count's rows -----------------------------------------------------------------------------------


def counted_cut(tmp_path: Path, rows: list) -> tuple[dict, Path]:
    """The sidecar a cut's hook writes for a transcript of these rows, in a project switched on."""
    project, home_, path = public(tmp_path)
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    path.write_text("".join(json.dumps(each) + "\n" for each in rows), encoding="utf-8")
    event = {"hook_event_name": "PostCompact", "transcript_path": str(path), "cwd": str(project), "trigger": "auto"}
    with started_by("cli"):
        assert hook.run({**event, "session_id": path.stem, "compact_summary": "A summary of the conversation."}) is None
    return json.loads((home_ / "abcdef01-cut-1.json").read_text(encoding="utf-8")), home_


def test_a_subagents_tool_traffic_is_not_counted(tmp_path):
    called = row("assistant", "33333333", 3, [{"type": "tool_use", "input": {"blob": "x" * 12345}}])
    answered = row("user", "44444444", 4, [{"type": "tool_result", "content": "y" * 6789}])
    own_call = row("assistant", "55555555", 5, [{"type": "tool_use", "input": {"blob": "z" * 100}}])
    rows = [row("user", "11111111", 1, "The main conversation's message."), {**called, "isSidechain": True}]
    side, _ = counted_cut(tmp_path, [*rows, {**answered, "isSidechain": True}, own_call])
    assert (side["tool_call_chars"], side["tool_result_chars"]) == (len(json.dumps({"blob": "z" * 100})), 0), side


def test_a_message_of_two_text_blocks_is_one_message_of_the_count(tmp_path):
    two = [{"type": "text", "text": "The first part of one message."}, {"type": "text", "text": "And its second part."}]
    side, home_ = counted_cut(tmp_path, [row("user", "aaaaaaaa", 1, two)])
    assert side["person"]["messages"] == side["person"]["typed"] == 1, side["person"]
    # as the archive keeps it, its white space folded as the count folds it
    assert [p["chars"] for p in side["person"]["pointers"]] == [
        len(" ".join(store._archived(home_)[0]["text"].split()))
    ]


def test_a_row_whose_id_is_no_name_is_passed_over_by_the_count(tmp_path):
    bad = {**row("user", "aaaaaaaa", 1, "This row has an id that is no name."), "uuid": "bad/id"}
    side, home_ = counted_cut(tmp_path, [bad, row("user", "bbbbbbbb", 2, "This row has one that is.")])
    assert [p["id"] for p in side["person"]["pointers"]] == ["bbbbbbbb"], side["person"]
    assert [said["id"] for said in store._archived(home_)] == ["bbbbbbbb"]


# --- a time that is no time -----------------------------------------------------------------------------


def forged(text: str) -> list[str]:
    """The lines of an answer that open as a heading of the door's or the frame's own would."""
    return [line for line in text.splitlines() if line.lstrip().startswith("#")]


def test_a_time_that_is_no_time_is_kept_as_none_and_shown_as_no_heading(tmp_path):
    project, home_, path = public(tmp_path)
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    odd = {**row("user", "aaaaaaaa", 1, "A plain message."), "timestamp": "x\n## Standing, about the two of you"}
    path.write_text(json.dumps(odd) + "\n", encoding="utf-8")
    event = {"hook_event_name": "PreToolUse", "tool_name": "mcp__plugin_crossing_door__look", "cwd": str(project)}
    with started_by("cli"):
        assert hook.run({**event, "transcript_path": str(path), "session_id": path.stem}) is None
    assert [each["at"] for each in store._archived(home_)] == [""]  # kept, and as having no time
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        text, failed = said("look")
    assert not failed and not forged(text), text
    # A home an older make wrote, whose archive holds such a time already, still reads, and shows no heading.
    page = home_ / "said" / "abcdef01.jsonl"
    page.write_text(page.read_text(encoding="utf-8").replace('"at": ""', '"at": "x\\n## Forged"'), encoding="utf-8")
    store.build(home_)
    assert store._archived(home_)[0]["at"] == "x\n## Forged"
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        for name, given in (("look", {}), ("find", {"words": "plain"}), ("thread", {"id": "aaaaaaaa"}), ("status", {})):
            text, failed = said(name, **given)
            assert not failed and not forged(text), (name, text)
    assert through("mark", "--anchors", "aaaaaaaa", "--whose", "his", "--cwd", str(project), "A label on it.")[0] == 0
    framed = through("frame", "--cwd", str(project))[1]
    assert not [line for line in forged(framed) if "Forged" in line], framed
    # A cut's trigger and the transcript's path are what the harness gives, and are shown cleaned too.
    cut = {"hook_event_name": "PostCompact", "cwd": str(project), "trigger": "auto\n# Forged", "compact_summary": "A."}
    with started_by("cli"):
        hook.run({**cut, "transcript_path": str(path), "session_id": path.stem})
    shown = (home_ / "abcdef01-cut-1.md").read_text(encoding="utf-8")
    assert "\n# Forged" not in shown and "auto# Forged" in shown, shown


# --- a long count ---------------------------------------------------------------------------------------


def test_a_count_whose_time_runs_out_inside_one_long_message_is_unfinished(tmp_path):
    """A stand-in for the count's clock, a second further on at each look: the count has eight of
    them, and one long message whose matching looks at the clock at each step uses them up."""
    looked = {"n": 0}

    def ticking() -> float:
        looked["n"] += 1
        return float(looked["n"])

    long = "A long message the summary holds none of, " + "word " * 400
    was = count.time
    count.time = types.SimpleNamespace(monotonic=ticking)
    try:
        side, home_ = counted_cut(tmp_path, [row("user", "aaaaaaaa", 1, long)])
    finally:
        count.time = was
    assert side["person"]["finished"] is False and side["person"]["pointers"] == [], side["person"]
    assert side["person"]["messages"] == 1 and looked["n"] < 100  # what stood is still known, and the count stopped
    assert "**Not all of it was counted:**" in (home_ / "abcdef01-cut-1.md").read_text(encoding="utf-8")


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            with tempfile.TemporaryDirectory(prefix="crossing-test-") as folder:
                test(Path(folder)) if test.__code__.co_argcount else test()
            print("ok", name)
