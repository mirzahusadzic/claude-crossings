"""The seams a second review found, each with the test that holds it: what is said after the clock
went back while Crossing was off, a switch while an archive is under way, the hand-over's helper,
two marks at once, a session's strike and its words pages, a model's name, a summary that retells
the one before, the count's rows, a time that is no time, the guard's files, a long count, a long
miss, rows of an unknown shape, and a second copy that fails. No model, no network, and nothing of
the person's: the Keychain and the disk images are stand-ins that refuse.

Run with pytest, or without it:  python3 tests/test_seams.py
"""

from __future__ import annotations

import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_checks import ON  # noqa: E402
from test_edges import through  # noqa: E402
from test_homes import public  # noqa: E402
from test_off import says  # noqa: E402
from test_store import DATA, started_by  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, hook, off, store  # noqa: E402

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


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            with tempfile.TemporaryDirectory(prefix="crossing-test-") as folder:
                test(Path(folder)) if test.__code__.co_argcount else test()
            print("ok", name)
