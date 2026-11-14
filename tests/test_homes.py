"""Where a project's home lies, and the person's switch: a home outside the repository for a
project with no crossings/ folder of its own, the one rule every piece finds it by, and a
project where Crossing was never switched on, in which nothing is kept. No model, no network.

Run with pytest, or without it:  python3 tests/test_homes.py
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import ran, set_to, through  # noqa: E402
from test_serve import said  # noqa: E402
from test_store import ROWS, A, D, E, home, in_person, own_folder, row, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import hook, record, second, serve, show, store, transcript  # noqa: E402

ON = "Crossings is on for this project.\n"
OFF = (
    "Crossings is off for this project: no cut is counted, noted or answered, and nothing said from now until it is "
    "switched on again will be kept.\n"
)
AGAIN = (
    "Crossings is on again for this project: what is said from now on is kept, and nothing said while it was off "
    "was kept.\n"
)  # where switching on closed a span the switching off opened
NEVER = "Crossings was never switched on for this project.\n"
NOT_ON = "Crossings is not switched on for this project."
BARE = [".git", "README.md", "src"]  # all that the made-up repository holds, before and after


def public(folder: Path) -> tuple[Path, Path, Path]:
    """A project as a public one would be: a repository with files of its own and no crossings/
    folder. With it come the home it would have outside it, and a session's transcript."""
    project = folder / "tern"
    (project / ".git").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "README.md").write_text("# Tern\n", encoding="utf-8")
    path = folder / "abcdef01-4444.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in ROWS), encoding="utf-8")
    return project, record.outside(project.resolve()), path


def inside(folder: Path) -> list[str]:
    """Everything under a folder, by its path from there."""
    return sorted(str(p.relative_to(folder)) for p in folder.rglob("*"))


def more(path: Path, uid: str, minute: int, text: str) -> None:
    """One more message of the person's at the end of a transcript."""
    path.write_text(
        path.read_text(encoding="utf-8") + json.dumps(row("user", uid, minute, text)) + "\n", encoding="utf-8"
    )


# --- where a home lies ------------------------------------------------------------------------


def test_a_project_with_no_folder_of_its_own_has_its_home_outside_the_repository(tmp_path):
    project, outside, _ = public(tmp_path)
    assert record.home(project) == outside == store.here(project / "src")  # one home, from any folder inside
    assert outside.parent == record.homes() and project.resolve() not in outside.parents
    slug = re.sub(r"[^A-Za-z0-9]+", "-", str(project.resolve())).strip(
        "-"
    )  # the path, and eight characters of its digest
    assert outside.name == f"{slug}-{hashlib.sha256(str(project.resolve()).encode('utf-8')).hexdigest()[:8]}"
    assert record.place(project / "src") == (outside, project.resolve())  # and the project it belongs to
    loose = tmp_path / "loose" / "deep"  # in no repository: the folder itself names the home
    loose.mkdir(parents=True)
    assert record.place(loose) == (record.outside(loose.resolve()), loose.resolve())
    assert record.home(loose.parent) != record.home(loose)
    assert record.outside(Path("/")).name.startswith("project-")  # a path with no letter in it still names one
    with set_to(CLAUDE_PLUGIN_DATA=str(tmp_path / "data")):  # the plugin's data folder is for its logs alone
        assert record.home(project) == outside
    assert not outside.exists() and inside(project) == BARE  # and looking made nothing


def test_the_homes_lie_under_the_persons_own_home_unless_a_folder_is_named_for_them(tmp_path):
    project, _, _ = public(tmp_path)
    house = tmp_path / "house"
    house.mkdir()
    with set_to(CROSSING_HOMES=None), own_folder(house):
        found = record.home(project)
    assert found.parent == house / ".claude" / "crossing" / "homes" and inside(house) == []
    with set_to(CROSSING_HOMES=str(tmp_path / "named")):
        assert record.home(project).parent == tmp_path / "named"


def test_a_project_reached_through_a_link_has_the_one_home(tmp_path):
    """The door is told a path with its links followed and a hook the path as the shell had
    it. Named by either, a project with its home outside it would have two."""
    project, outside, _ = public(tmp_path)
    (tmp_path / "link").symlink_to(project, target_is_directory=True)
    assert record.home(tmp_path / "link") == outside == record.home(tmp_path / "link" / "src")
    crossings, _ = home(tmp_path / "kept")
    (crossings.parent / ".git").mkdir()  # a repository: the folder is looked for up to its top
    (tmp_path / "other").symlink_to(crossings.parent, target_is_directory=True)
    assert (
        store.here(tmp_path / "other") == crossings.resolve() == store.here(tmp_path / "other" / "crossings" / "said")
    )


# --- the person's switch ------------------------------------------------------------------------


def test_the_door_says_where_a_projects_home_is_and_makes_none_by_looking(tmp_path):
    project, outside, _ = public(tmp_path)
    assert through("home", "--cwd", str(project)) == (1, "")  # none yet, and nothing is said
    assert not outside.exists() and inside(project) == BARE
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    assert through("home", "--cwd", str(project)) == (0, f"{outside}\n")
    assert through("home", "--cwd", str(project / "src")) == (0, f"{outside}\n")
    assert through("switch", "off", "--cwd", str(project)) == (0, OFF)
    assert through("home", "--cwd", str(project)) == (0, f"{outside}\n")  # switched off, it is still the home
    crossings, _ = home(tmp_path / "kept")  # a project with a folder of its own, in a repository
    (crossings.parent / ".git").mkdir()
    assert through("home", "--cwd", str(crossings / "said")) == (0, f"{crossings.resolve()}\n")
    alone = ran("door.py", "home", "--cwd", str(project))  # as a process of its own, the way the hooks module starts it
    assert (alone.returncode, alone.stdout, alone.stderr) == (0, f"{outside}\n", "")


def test_switching_on_makes_the_home_outside_and_says_which_project_it_belongs_to(tmp_path):
    project, outside, _ = public(tmp_path)
    assert through("switch", "off", "--cwd", str(project)) == (0, NEVER)  # nothing to switch off, and nothing is made
    assert not outside.exists()
    assert through("switch", "on", "--cwd", str(project / "src")) == (0, ON)
    assert {p.name: p.read_text(encoding="utf-8") for p in outside.iterdir()} == {
        "archive.lock": "",  # the home's lock, which the switch holds as it turns
        "switch": "on\n",
        "mode": "beside\n",
        "carry": "note\n",
        "project": f"{project.resolve()}\n",
    }
    assert inside(project) == BARE
    assert through("switch", "off", "--cwd", str(project)) == (0, OFF)
    assert (outside / "switch").read_text(encoding="utf-8") == "off\n"
    assert through("switch", "toggle", "--cwd", str(project)) == (0, AGAIN)
    assert through("switch", "toggle", "--cwd", str(project)) == (0, OFF)
    (outside / "mode").write_text("own\n", encoding="utf-8")  # as the person set it since
    assert through("switch", "ON", "--cwd", str(project)) == (0, AGAIN)
    assert (outside / "mode").read_text(encoding="utf-8") == "own\n"  # a home that is there is only switched
    wren = tmp_path / "wren"  # a project with no home is off, so turning the switch over switches it on
    wren.mkdir()
    assert through("switch", "toggle", "--cwd", str(wren)) == (0, ON)
    assert (record.outside(wren.resolve()) / "project").read_text(encoding="utf-8") == f"{wren.resolve()}\n"
    for wrong in (["sideways"], [], ["on", "off"]):  # a word that is none of the three changes nothing
        assert through("switch", *wrong, "--cwd", str(project)) == (
            2,
            "switch takes one word: on, off, toggle or adopt.\n",
        )
    assert (outside / "switch").read_text(encoding="utf-8") == "on\n" and inside(project) == BARE


def test_a_project_with_a_folder_of_its_own_keeps_it_and_is_switched_there(tmp_path):
    crossings, _ = home(tmp_path)
    project, before = crossings.parent, inside(crossings)
    assert through("switch", "off", "--cwd", str(project)) == (0, OFF)
    assert (crossings / "switch").read_text(encoding="utf-8") == "off\n"
    assert through("switch", "toggle", "--cwd", str(project)) == (0, AGAIN)
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    # no mode, no carry, no project file: it is set as it was, with the span the switching off opened and the on closed
    assert inside(crossings) == sorted({*before, "archive.lock", "off.txt", "switch"})  # and the lock the switch holds
    assert not record.outside(project.resolve()).exists()
    empty = tmp_path / "empty"  # a crossings/ folder with nothing in it is a home once the person switches it on
    (empty / "crossings").mkdir(parents=True)
    assert store.kept(empty) is None and through("switch", "toggle", "--cwd", str(empty)) == (0, ON)
    assert store.active(store.kept(empty)) and through("switch", "toggle", "--cwd", str(empty)) == (0, OFF)
    assert not store.active(store.kept(empty)) and inside(empty) == [
        "crossings",
        "crossings/archive.lock",
        "crossings/off.txt",
        "crossings/switch",
    ]


def test_a_home_named_outright_is_switched_like_any_other_and_names_no_project(tmp_path):
    named = tmp_path / "named"
    with set_to(CROSSING_HOME=str(named)):
        assert through("home") == (1, "") and through("status") == (1, NOT_ON + "\n")
        assert through("switch", "off") == (0, NEVER) and not named.exists()
        assert through("switch", "on") == (0, ON)
        assert sorted(p.name for p in named.iterdir()) == ["archive.lock", "carry", "mode", "switch"]
        assert through("home") == (0, f"{named}\n")
        assert "holds 0 messages of the person's" in through("status")[1]


# --- never switched on ----------------------------------------------------------------------------


def test_where_crossing_was_never_switched_on_no_hook_keeps_anything(tmp_path):
    project, outside, path = public(tmp_path)
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": "abcdef01-4444"}
    cut = {**event, "hook_event_name": "SessionStart", "source": "compact"}
    counted = {**event, "hook_event_name": "PostCompact", "trigger": "manual", "compact_summary": "A summary."}
    with set_to(CROSSING_WAIT="1"):
        assert hook.run({**event, "hook_event_name": "SessionStart", "source": "startup"}) is None
        assert (hook.LIVE / "abcdef01-4444").exists()  # the session is marked as one the plugin is loaded in, as before
        assert hook.run(cut) is None  # no waking note
        assert hook.carried(cut) is None  # no frame
        assert (
            hook.run({**event, "hook_event_name": "PreToolUse", "tool_name": "mcp__plugin_crossing_door__find"}) is None
        )
        assert hook.run(counted) is None
        assert hook.keep(path, project, wait=True) is None and hook.keep(path, project, wait=False) is None
        assert hook.run({**event, "hook_event_name": "SessionEnd"}) is None
        assert not (hook.LIVE / "abcdef01-4444").exists()
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"}
    for argv, sent in (([], counted), ([], cut), (["frame"], cut)):  # and as the harness starts them
        done = subprocess.run(
            ["sh", str(ROOT / "hooks" / "run.sh"), *argv],
            input=json.dumps(sent),
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert (done.returncode, done.stdout, done.stderr) == (0, "", "")
    assert not outside.exists() and inside(project) == BARE
    assert inside(tmp_path) == ["abcdef01-4444.jsonl", "tern", "tern/.git", "tern/README.md", "tern/src"]


def test_the_door_keeps_nothing_and_says_so_where_crossing_was_never_switched_on(tmp_path):
    project, outside, path = public(tmp_path)
    handles = (
        ["look"],
        ["labels"],
        ["find", "Tern"],
        ["thread", A],
        ["mark", "--anchors", A, "A label."],
        ["status"],
        ["frame"],
        ["build"],
        ["strike", A],
        ["copy"],
        ["status", "--transcript", str(path)],
        ["look", "--bare"],
        ["thread", A, "--touch"],
    )
    for argv in handles:
        assert through(*argv, "--cwd", str(project)) == (1, NOT_ON + "\n"), argv
        assert through(*argv, "--cwd", str(project / "src")) == (1, NOT_ON + "\n"), argv
    alone = ran("door.py", "look", "--cwd", str(project))
    assert (alone.returncode, alone.stdout, alone.stderr) == (1, NOT_ON + "\n", "")
    assert not outside.exists() and inside(project) == BARE
    with set_to(CROSSING_OURS=str(tmp_path / "ours")):  # nor is the home on this computer offered to it
        assert through("look", "--home", "ours", "--cwd", str(project)) == (1, NOT_ON + "\n")
    assert not outside.exists() and inside(project) == BARE and not (tmp_path / "ours").exists()


def test_the_server_answers_in_one_sentence_and_names_no_folder_where_crossing_is_not_on(tmp_path):
    project, outside, _ = public(tmp_path)
    with set_to(CLAUDE_PROJECT_DIR=str(project), CROSSING_OURS=str(tmp_path / "ours")):
        for name, given in (
            ("look", {}),
            ("labels", {}),
            ("find", {"words": "Tern"}),
            ("find", {}),
            ("thread", {"id": A}),
            ("mark", {"sentence": "A label.", "anchors": [A]}),
            ("leave", {"sentence": "A line.", "anchors": [A]}),
            ("status", {}),
        ):
            assert said(name, **given) == (NOT_ON, True), name
        assert not outside.exists() and inside(project) == BARE
        assert said("look", home="ours") == (NOT_ON, True)  # nor the home on this computer, from here
        assert through("switch", "on", "--cwd", str(project)) == (0, ON)  # the person's own command; the server runs on
        assert said("status")[1] is False and said("status")[0].startswith("The store holds 0 messages of the person's")
        ours, failed = said("look", home="ours")  # switched on here, the home on this computer is offered
        assert failed is False and ours.startswith("The store in outline: 0 days") and not (tmp_path / "ours").exists()
    assert NOT_ON.count(".") == 1 and "/" not in NOT_ON and not re.search(r"\bask(s|ed|ing)?\b", NOT_ON, re.I)
    assert "home" not in serve.NAMES and "switch" not in serve.NAMES  # the switch is the person's, never a session's
    assert inside(project) == BARE


# --- switched on, in a home outside the repository ---------------------------------------------------


@in_person
def test_a_home_outside_holds_everything_a_projects_own_folder_would(tmp_path):
    project, outside, path = public(tmp_path)
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    (outside / "frame-size").write_text("2500\n", encoding="utf-8")
    event = {
        "transcript_path": str(path),
        "cwd": str(project / "src"),
        "session_id": "abcdef01-4444",
    }  # the shell stood deeper
    cut = {**event, "hook_event_name": "SessionStart", "source": "compact"}
    with set_to(CROSSING_WAIT="1", CLAUDE_PROJECT_DIR=str(project)):
        note = json.loads(hook.run(cut))["hookSpecificOutput"]["additionalContext"]
        assert "cut 1 of this session" in note and str(outside) not in note
        assert (
            hook.run({**event, "hook_event_name": "PostCompact", "trigger": "manual", "compact_summary": "A summary."})
            is None
        )
        assert store.status(outside)["his"] == 2
        more(path, "99999999", 30, "The mast is stepped in April.")
        assert (
            hook.run({**event, "hook_event_name": "PreToolUse", "tool_name": "mcp__plugin_crossing_door__find"}) is None
        )
        assert "`99999999` the person" in said("find", words="mast")[0]  # the server finds the same home
        assert said("mark", sentence="The hull is painted grey in spring.", anchors=[D, E], whose="both") == (
            "marked W1",
            False,
        )
        assert f"`{D}` the person" in said("thread", id=D)[0]
        more(path, "77777777", 31, "Said only to be struck again.")
        assert hook.run({**event, "hook_event_name": "SessionEnd"}) is None
        assert through("strike", "77777777", "--cwd", str(project))[1].startswith("struck 77777777: 1 line removed")
        framed = json.loads(hook.carried(cut))
        text = framed["hookSpecificOutput"]["additionalContext"]
        assert text.startswith(transcript.CARRIED) and "- W1 (both): The hull is painted grey in spring." in text
        assert len(text) <= 2500 and str(outside) not in text and str(project) not in text
    assert [re.sub(r"\d{4}-\d\d-\d\d", "the-day", name) for name in inside(outside)] == sorted(
        [
            "abcdef01-cut-1.json",
            "abcdef01-cut-1.md",
            "archive.lock",
            "carry",
            "frame-size",
            "labelled.txt",
            "labels",
            "labels/the-day.md",
            "last-carry.json",
            "markers.jsonl",
            "mode",
            "models-met.txt",
            "project",
            "reached.jsonl",
            "said",
            "said/abcdef01.jsonl",
            "store.db",
            "struck.txt",
            "switch",
            "welcomed.txt",
        ]
    )  # a person sits in it, and was welcomed once as it started again
    assert inside(project) == BARE  # and not one file of it lies in the repository
    shown = show.block(project)
    assert "1 cut on record in this project" in shown and f"    {outside / 'abcdef01-cut-1.md'}\n" in shown
    assert through("status", "--cwd", str(project / "src"))[1].startswith(
        f"The store at {outside} holds 3 messages of the person's"
    )
    if shutil.which("hdiutil") is None:
        return
    (outside / "copy").write_text(str(tmp_path / "cloud") + "\n", encoding="utf-8")
    with set_to(CROSSING_COPY_KEY="a passphrase for this test only"):
        code, copied = through("copy", "--cwd", str(project))
    assert (
        code == 0
        and "plain files, encrypted, to " in copied
        and b"Tern" not in (tmp_path / "cloud" / f"{second.named(project.resolve())}.dmg").read_bytes()
    )
    assert inside(project) == BARE


@in_person
def test_switched_off_a_home_is_read_and_nothing_is_added_to_it(tmp_path):
    project, outside, path = public(tmp_path)
    through("switch", "on", "--cwd", str(project))
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": "abcdef01-4444"}
    with set_to(CROSSING_WAIT="1", CLAUDE_PROJECT_DIR=str(project)):
        hook.run({**event, "hook_event_name": "PostCompact", "trigger": "manual", "compact_summary": "A summary."})
        assert through("switch", "off", "--cwd", str(project)) == (0, OFF)
        held, files = store.status(outside), inside(outside)
        time.sleep(0.005)  # said a moment after the switch was turned, by the transcript's own clock
        stamped = row("user", "88888888", 41, "Said while Crossing was switched off.")
        stamped["timestamp"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        path.write_text(path.read_text(encoding="utf-8") + json.dumps(stamped) + "\n", encoding="utf-8")
        time.sleep(0.005)
        cut = {**event, "hook_event_name": "SessionStart", "source": "compact"}
        assert hook.run(cut) is None and hook.carried(cut) is None
        assert (
            hook.run({**event, "hook_event_name": "PreToolUse", "tool_name": "mcp__plugin_crossing_door__find"}) is None
        )
        assert (
            hook.run({**event, "hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": "Another."})
            is None
        )
        assert hook.keep(path, project, wait=True) is None and hook.keep(path, project, wait=False) is None
        assert hook.run({**event, "hook_event_name": "SessionEnd"}) is None
        # The door still shows what the home holds, and adds nothing: no message, no label, no pull.
        shown = through("status", "--cwd", str(project), "--transcript", str(path))[1]
        assert "holds 2 messages of the person's" in shown and "Newly archived" not in shown
        assert f"`{A}` the person" in through("find", "Tern", "--cwd", str(project), "--transcript", str(path))[1]
        assert through("thread", A, "--touch", "--cwd", str(project))[0] == 0
        assert through("mark", "--anchors", A, "A label.", "--touch", "--cwd", str(project)) == (
            1,
            "not marked: Crossings is switched off for this project\n",
        )
        assert said("mark", sentence="A label.", anchors=[A]) == (
            "not marked: Crossings is switched off for this project",
            False,
        )
        assert (
            said("leave", sentence="A line.", anchors=[A])[0]
            == "not marked: Crossings is switched off for this project"
        )
        assert "88888888" not in said("find", words="switched")[0]
        assert store.status(outside) == held and inside(outside) == files
        # Switched on again, it keeps again from then on, and what was said while it was off is never kept.
        assert through("switch", "on", "--cwd", str(project)) == (0, AGAIN)
        assert "Newly archived" not in through("status", "--cwd", str(project), "--transcript", str(path))[1]
        assert "88888888" not in said("find", words="switched")[0]
        more(path, "77777777", 42, "Said once it was on again.")
        assert "Newly archived: 1." in through("status", "--cwd", str(project), "--transcript", str(path))[1]
    assert inside(project) == BARE


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:
                sweep(folder)
            print("ok", name)
