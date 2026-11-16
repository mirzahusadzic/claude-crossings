"""A session started in a folder below another home's: found on the way up, that home is not taken in
silence. Nothing said there is kept, and nothing of that home is read, until the person answers once
for that folder: /crossings join shares the home, /crossings here gives the folder a home of its own.
No model, no network.

Run with pytest, or without it:  python3 tests/test_below.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to, through  # noqa: E402
from test_store import ROWS, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, hook, record, store  # noqa: E402

ON = door.SWITCHED["on"] + "\n"


def project(folder: Path, own_home: bool = True) -> tuple[Path, Path]:
    """A repository switched on at its top, with a home of its own there or none; and a folder deep below it."""
    top = folder / "tern"
    (top / ".git").mkdir(parents=True)
    if own_home:
        (top / "crossings").mkdir()
        assert through("switch", "on", "--cwd", str(top)) == (0, ON)
    paper = top / "papers" / "paper"
    paper.mkdir(parents=True)
    return Path(store.spelled(top)), Path(store.spelled(paper))  # as the door names them: the disk's own spelling


def told(cwd: Path, name: str = "SessionStart", transcript: Path | None = None) -> str | None:
    """A hook, as the harness calls it for a session a person sits in that stands in `cwd`."""
    event = {"hook_event_name": name, "cwd": str(cwd), "session_id": "below-0001", "source": "startup"}
    if transcript is not None:
        event.update(transcript_path=str(transcript), tool_name="mcp__plugin_crossings_door__look", tool_input={})
    with started_by("cli"):
        return hook.run(event)


def talk(folder: Path) -> Path:
    path = folder / "below-0001.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in ROWS), encoding="utf-8")
    return path


def test_a_session_below_another_home_keeps_nothing_until_the_person_answers(tmp_path):
    top, paper = project(tmp_path)
    shared = store.kept(top)
    assert shared is not None and store.kept(paper) is None and store.waiting(paper) == shared
    out = json.loads(told(paper))  # the session is told in one sentence, and the person is shown the two words
    assert "below another project's home" in out["hookSpecificOutput"]["additionalContext"]
    assert str(top) in out["systemMessage"] and "/crossings join" in out["systemMessage"]
    assert told(paper, "PreToolUse", talk(tmp_path)) is None and not store._archived(shared)
    assert through("status", "--cwd", str(paper)) == (1, door.BELOW.format(top) + "\n")
    # a session's shell, or the server, is told without the folder's name
    assert through("look", "--bare", "--cwd", str(paper)) == (1, door.BELOW_BARE + "\n")
    assert through("home", "--cwd", str(paper)) == (0, f"{shared}\n")  # the guard is still told where that home lies
    for word in ("on", "off", "toggle", "adopt"):  # nothing of that home is switched from here
        assert through("switch", word, "--cwd", str(paper)) == (1, door.BELOW.format(top) + "\n")
    assert store.active(shared)
    projects = store.consented()
    assert through("switch", "join", "--cwd", str(paper)) == (0, door.SWITCHED["joined"] + "\n")
    assert store.kept(paper) == shared and store.waiting(paper) is None
    told(paper, "PreToolUse", talk(tmp_path))
    assert store._archived(shared)  # what is said there is kept in the home it shares from now on
    assert through("switch", "join", "--cwd", str(paper)) == (0, door.SWITCHED["joined"] + "\n")  # once is enough
    store.join(paper, shared)  # and a second join at the same moment, past the first one's check, writes nothing
    lines = store.switched().read_text(encoding="utf-8").splitlines()
    assert sum(json.loads(line).get("joined") == str(paper) for line in lines) == 1
    started = told(paper)  # a session that starts there now is welcomed as in any home, and told nothing of below
    assert started is None or "below another" not in started
    assert store.consented() == projects  # the line that joins names no project: it switches nothing on


def test_here_gives_a_folder_below_a_home_of_its_own_outside_the_project(tmp_path):
    top, paper = project(tmp_path)
    shared = store.kept(top)
    assert through("switch", "here", "--cwd", str(paper)) == (0, ON)
    own = store.kept(paper)
    assert own == record.outside(Path(store.spelled(paper))) and own != shared
    assert (own / "project").read_text(encoding="utf-8") == f"{store.spelled(paper)}\n"  # named by the folder's path
    assert store.kept(top) == shared and store.waiting(paper) is None  # the home above is left as it was
    told(paper, "PreToolUse", talk(tmp_path))
    assert store._archived(own) and not store._archived(shared)
    assert through("switch", "here", "--cwd", str(paper)) == (0, ON)  # asked again, it stands as it is
    assert through("switch", "join", "--cwd", str(paper)) == (1, door.SWITCHED["alone"] + "\n")
    assert through("switch", "here", "--cwd", str(top)) == (0, ON)  # at its home's own folder, here is on


def test_a_folder_whose_own_home_holds_what_was_never_switched_on_is_not_given_it(tmp_path):
    top, paper = project(tmp_path)
    made = record.outside(Path(store.spelled(paper)))
    made.mkdir(parents=True)
    (made / "notes.txt").write_text("made by hand\n", encoding="utf-8")
    assert through("switch", "here", "--cwd", str(paper)) == (1, door.SWITCHED["occupied"] + "\n")
    assert store.kept(paper) is None and sorted(p.name for p in made.iterdir()) == ["notes.txt"]


def test_switching_on_from_a_folder_below_makes_the_projects_home_and_shares_it_from_there(tmp_path):
    top, paper = project(tmp_path, own_home=False)
    assert through("switch", "join", "--cwd", str(paper)) == (0, door.SWITCHED["never"] + "\n")  # as `off` is
    assert through("switch", "on", "--cwd", str(paper)) == (0, ON)
    shared = record.outside(top)
    assert store.kept(top) == shared and store.kept(paper) == shared and store.joined(paper, shared)
    assert through("switch", "join", "--cwd", str(top)) == (1, door.SWITCHED["alone"] + "\n")


def test_a_folder_joined_by_another_spelling_is_joined(tmp_path):
    top, paper = project(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(paper)
    line = {"home": str(store.kept(top)), "joined": str(alias)}  # as a hand or an older spelling wrote it
    record.add(store.switched(), json.dumps(line) + "\n")
    assert store.kept(paper) == store.kept(top)
    nul = {"home": str(store.kept(top)), "joined": str(paper) + "\0"}  # a line that names no folder is passed over
    record.add(store.switched(), json.dumps(nul) + "\n")
    assert store.kept(paper) == store.kept(top)


def test_a_home_named_outright_is_never_below(tmp_path):
    named = tmp_path / "named"
    top, paper = project(tmp_path, own_home=False)
    with set_to(CROSSING_HOME=str(named)):
        assert through("switch", "here", "--cwd", str(paper)) == (0, ON)  # here is on, for the home the setting names
        assert store.kept(paper) == named and store.waiting(paper) is None
    assert os.environ.get("CROSSING_HOME") is None


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
