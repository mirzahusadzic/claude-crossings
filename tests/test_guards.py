"""Five guards: the home on this computer is offered only where Crossings is switched on; a setting
that names a place inside the project is not followed; a home that came with a repository is
not switched on with no word said; a session no person sits in is not archived; and what the
plugin makes is its owner's alone. No model, no network.

Run with pytest, or without it:  python3 tests/test_guards.py
"""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import as_the_module, ran, set_to, through  # noqa: E402
from test_serve import said  # noqa: E402
from test_shipped import cloned, inside, lines, logged  # noqa: E402
from test_store import ROWS, A, B, D, E, home, own_folder, row, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, hook, record, store  # noqa: E402

ON = "Crossings is on for this project.\n"
NOT_ON = "Crossings is not switched on for this project."
LINKED = "A file of this project's home is a link, so nothing was written.\n"
UUIDS = sorted(f"{uid}-0000-4000-8000-000000000000" for uid in (A, B, D, E))  # the messages ROWS holds


def repository(folder: Path, name: str) -> Path:
    """A project as a repository: a folder that holds `.git`, and nothing of Crossings's."""
    project = folder / name
    (project / ".git").mkdir(parents=True)
    return project


def transcript_of(folder: Path, name: str, rows=ROWS) -> Path:
    path = folder / f"{name}.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def standing(folder: Path, sentence: str) -> None:
    """A home with one standing line in it, as a page holds one."""
    (folder / "labels").mkdir(parents=True)
    (folder / "labels" / "2026-01-01.md").write_text(
        f"| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n| R1 | {sentence} | both | `{A}` |\n",
        encoding="utf-8",
    )


def archived(folder: Path) -> list[str]:
    """The ids of the messages a home's archive holds, as its files hold them."""
    return sorted(
        json.loads(line)["uuid"]
        for page in sorted((folder / "said").glob("*.jsonl"))
        for line in page.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


# --- C1: the home on this computer is offered only where Crossings is switched on --------------------------


def test_the_home_on_this_computer_answers_no_project_that_was_never_switched_on(tmp_path):
    project = repository(tmp_path, "stranger")
    kept = tmp_path / "ours"  # the home on this computer, with a standing line for the whole computer in it
    standing(kept, "A line kept for every project on this computer.")
    before = inside(kept)
    for ours in (kept, tmp_path / "not-there"):
        with set_to(CROSSING_OURS=str(ours), CLAUDE_PROJECT_DIR=str(project)):
            for argv in (
                ["look"],
                ["find", "computer"],
                ["labels", "--kind", "relation"],
                ["labels", "R1"],
                ["mark", "--anchors", A, "A line written from a stranger's project."],
                ["status"],
                ["frame"],
                ["build"],
                ["thread", A, "--touch"],
                ["strike", "R1"],
                ["copy"],
            ):
                assert through(*argv, "--home", "ours", "--cwd", str(project)) == (1, NOT_ON + "\n"), argv
            assert through("home", "--home", "ours", "--cwd", str(project)) == (
                1,
                "",
            )  # as a project never switched on: nothing said
            for name, given in (
                ("look", {}),
                ("find", {"words": "computer"}),
                ("labels", {"kind": "relation"}),
                ("mark", {"sentence": "A line from a stranger.", "anchors": [A]}),
                ("status", {}),
            ):
                assert said(name, home="ours", **given) == (NOT_ON, True), name
            alone = ran("door.py", "look", "--home", "ours", "--cwd", str(project), CROSSING_OURS=str(ours))
            assert (alone.returncode, alone.stdout, alone.stderr) == (1, NOT_ON + "\n", "")
    assert inside(kept) == before and not (tmp_path / "not-there").exists()  # nothing read, and nothing made
    assert inside(project) == [".git"]


def test_the_home_on_this_computer_is_offered_where_crossing_is_on_and_no_read_makes_anything(tmp_path):
    crossings, _ = home(tmp_path)
    project, kept, absent = crossings.parent, tmp_path / "ours", tmp_path / "not-there"
    standing(kept, "A line kept for every project on this computer.")
    with set_to(CROSSING_OURS=str(kept)):
        code, shown = through("labels", "--kind", "relation", "--home", "ours", "--cwd", str(project))
        assert code == 0 and "A line kept for every project on this computer." in shown
        through("switch", "off", "--cwd", str(project))  # switched off, it is not offered either
        assert through("look", "--home", "ours", "--cwd", str(project)) == (1, NOT_ON + "\n")
        with set_to(CLAUDE_PROJECT_DIR=str(project)):
            assert said("look", home="ours") == (NOT_ON, True)
        through("switch", "on", "--cwd", str(project))
    assert not (kept / "store.db").exists()  # read, and no index made of it on disk
    with set_to(CROSSING_OURS=str(absent)):  # a home on this computer not made yet is an empty room, and stays unmade
        for argv in (
            ["look"],
            ["labels"],
            ["find", "Tern"],
            ["thread", A, "--touch"],
            ["status"],
            ["frame"],
            ["build"],
            ["strike", "R1"],
            ["mark", "--anchors", A, "A line on nothing it holds."],
        ):
            through(*argv, "--home", "ours", "--cwd", str(project))
        assert through("strike", "R1", "--home", "ours", "--cwd", str(project)) == (
            1,
            "not struck: nothing is kept there yet\n",
        )
    assert not absent.exists()
    (crossings / "store.db").unlink()  # nor does a read of a project's own home make a database
    for argv in (["look"], ["status"], ["find", "Tern"], ["labels", "R1"], ["frame"]):
        assert through(*argv, "--cwd", str(project))[0] == 0, argv
    assert not (crossings / "store.db").exists()


# --- C2: a setting that names a place inside the project is not followed ------------------------------------


def astray(name: str) -> str:
    return f"The setting {name} names a place inside this project, so it was not followed.\n"


def refusals(name: str) -> int:
    return logged(Path(os.environ["CLAUDE_PLUGIN_DATA"])).count(
        f"refused: the setting {name} names a place inside the project: "
    )


def test_a_consent_record_a_repository_ships_and_names_by_a_setting_is_not_followed(tmp_path):
    project, crossings, path = cloned(tmp_path)
    shipped = project / ".crossing" / "switched"  # the person's record, as the repository would have it
    shipped.parent.mkdir()
    shipped.write_text(
        json.dumps({"project": str(project.resolve()), "home": str(crossings.resolve())}) + "\n", encoding="utf-8"
    )
    before, logged_before = inside(crossings), refusals("CROSSING_SWITCHED")
    with set_to(CROSSING_SWITCHED=str(shipped), CLAUDE_PROJECT_DIR=str(project), CROSSING_WAIT="1"), started_by("cli"):
        assert store.kept(project) is None
        for argv in (
            ["look"],
            ["labels", "R1"],
            ["status", "--transcript", str(path)],
            ["home"],
            ["switch", "on"],
            ["switch", "adopt"],
        ):
            assert through(*argv, "--cwd", str(project)) == (1, astray("CROSSING_SWITCHED")), argv
        assert said("look") == (astray("CROSSING_SWITCHED").strip(), True)
        event = {"transcript_path": str(path), "cwd": str(project), "session_id": "abcdef01-6666"}
        assert (
            hook.run({**event, "hook_event_name": "PreToolUse", "tool_name": "mcp__plugin_crossings_door__look"})
            is None
        )
        assert hook.run({**event, "hook_event_name": "SessionEnd"}) is None
        assert hook.carried({**event, "hook_event_name": "SessionStart", "source": "startup"}) is None
    assert inside(crossings) == before and shipped.read_text(encoding="utf-8").count("\n") == 1
    assert refusals("CROSSING_SWITCHED") == logged_before + 1  # one line in the error log, however often it was asked


def test_homes_named_inside_the_project_are_not_made_there(tmp_path):
    project = repository(tmp_path, "public")
    with set_to(CROSSING_HOMES=str(project / "homes")):
        assert through("switch", "on", "--cwd", str(project)) == (1, astray("CROSSING_HOMES"))
        assert store.switch(project, "on") == "astray"
        assert through("look", "--cwd", str(project)) == (1, astray("CROSSING_HOMES"))
    assert inside(project) == [".git"] and lines(tmp_path) == []
    assert through("switch", "on", "--cwd", str(project)) == (
        0,
        ON,
    )  # named elsewhere, as by default, it works as it did
    assert inside(project) == [".git"]


def test_the_home_on_this_computer_named_inside_the_project_is_not_followed(tmp_path):
    crossings, _ = home(tmp_path)
    project = crossings.parent
    shipped = project / "ours"
    standing(shipped, "A line the repository wrote for the whole computer.")
    before = inside(shipped)
    with set_to(CROSSING_OURS=str(shipped), CLAUDE_PROJECT_DIR=str(project)):
        assert through("labels", "--kind", "relation", "--home", "ours", "--cwd", str(project)) == (
            1,
            astray("CROSSING_OURS"),
        )
        assert through("look", "--cwd", str(project)) == (
            1,
            astray("CROSSING_OURS"),
        )  # as if never switched on, here too
        assert said("labels", home="ours", kind="relation") == (astray("CROSSING_OURS").strip(), True)
        assert said("mark", home="ours", sentence="A line.", anchors=[A]) == (astray("CROSSING_OURS").strip(), True)
    assert inside(shipped) == before
    with set_to(CROSSING_OURS=str(tmp_path / "ours")):
        assert through("look", "--home", "ours", "--cwd", str(project))[0] == 0  # outside the project, it is followed


def test_a_home_named_outright_inside_the_project_is_not_followed(tmp_path):
    project = repository(tmp_path, "named")
    named = project / "home"
    standing(named, "A line the repository wrote.")
    before = inside(named)
    with set_to(CROSSING_HOME=str(named)):
        assert store.kept(project) is None
        assert through("labels", "R1", "--cwd", str(project)) == (1, astray("CROSSING_HOME"))
        assert through("switch", "on", "--cwd", str(project)) == (1, astray("CROSSING_HOME"))
        with set_to(CLAUDE_PROJECT_DIR=str(project)):
            assert said("labels", ids=["R1"]) == (astray("CROSSING_HOME").strip(), True)
    assert inside(named) == before


# --- C3: a home someone else made is not switched on with no word said -----------------------------------------


def test_switching_on_a_home_that_came_with_the_repository_says_what_is_there_and_adopt_takes_it(tmp_path):
    project, crossings, _ = cloned(tmp_path)
    before = inside(crossings)
    account = (
        f"This project's home already holds 1 message and 1 label, and the setting files mode and carry, that this "
        f"computer has no record of switching on, in {crossings.resolve()}. Run the same command again with the word adopt (/crossings adopt, or "
        "door.py switch adopt from a shell) to take them as your own, or remove that folder first to start clean. "
        "Crossings was not switched on.\n"
    )
    for word in ("on", "toggle", "ON"):
        assert through("switch", word, "--cwd", str(project)) == (1, account), word
    assert inside(crossings) == before and lines(tmp_path) == [] and store.kept(project) is None
    assert through("look", "--cwd", str(project)) == (1, NOT_ON + "\n")
    assert through("switch", "adopt", "--cwd", str(project)) == (0, ON)
    assert lines(tmp_path) == [{"project": str(project.resolve()), "home": str(crossings.resolve())}]
    assert store.kept(project) == crossings.resolve() and through("look", "--cwd", str(project))[0] == 0
    assert through("switch", "off", "--cwd", str(project))[0] == 0
    assert through("switch", "on", "--cwd", str(project)) == (
        0,
        door.SWITCHED["again"] + "\n",
    )  # its line is there: not asked again
    assert len(lines(tmp_path)) == 1


def test_a_shipped_home_that_holds_only_labels_or_only_messages_is_asked_about_and_an_empty_one_is_not(tmp_path):
    only = tmp_path / "only-labels"
    (only / ".git").mkdir(parents=True)
    standing(only / "crossings", "A line someone else wrote.")
    code, text = through("switch", "on", "--cwd", str(only))
    assert code == 1 and text.startswith("This project's home already holds 0 messages and 1 label")
    spoken = tmp_path / "only-messages"
    (spoken / ".git").mkdir(parents=True)
    (spoken / "crossings" / "said").mkdir(parents=True)
    (spoken / "crossings" / "said" / "x.jsonl").write_text(
        "".join(
            json.dumps({"uuid": f"{n:08x}-0000", "id": f"{n:08x}", "session": "x", "voice": "his", "text": "Words."})
            + "\n"
            for n in (1, 2)
        ),
        encoding="utf-8",
    )
    code, text = through("switch", "on", "--cwd", str(spoken))
    assert code == 1 and text.startswith("This project's home already holds 2 messages and 0 labels")
    empty = tmp_path / "empty"
    (empty / ".git").mkdir(parents=True)
    (empty / "crossings" / "said").mkdir(parents=True)  # a folder with nothing in it but an ignore file
    (empty / "crossings" / ".gitignore").write_text("*\n", encoding="utf-8")
    assert through("switch", "on", "--cwd", str(empty)) == (0, ON)
    assert store.kept(empty) == (empty / "crossings").resolve()
    with set_to(CROSSING_HOME=str(tmp_path / "named")):  # a home named outright is asked about as any other (S3)
        standing(tmp_path / "named", "A line in a home named outright.")
        assert store.unclaimed(tmp_path)["labels"] == 1 and store.kept(tmp_path / "empty") is None
        code, text = through("switch", "on", "--cwd", str(tmp_path / "empty"))
        assert code == 1 and text.startswith("This project's home already holds 0 messages and 1 label")
        assert through("switch", "adopt", "--cwd", str(tmp_path / "empty")) == (0, ON)
        assert store.kept(tmp_path / "empty") == tmp_path / "named"


# --- C4: nothing is archived from a session no person sits in -------------------------------------------------


def switched(folder: Path) -> tuple[Path, Path]:
    """A project switched on by the person, with a home of its own that holds nothing yet."""
    project = repository(folder, "harbour")
    (project / "crossings").mkdir()
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    for name, value in (("mode", "beside"), ("carry", "note")):
        (project / "crossings" / name).write_text(value + "\n", encoding="utf-8")
    return project, project / "crossings"


def test_a_session_no_person_sits_in_is_archived_at_no_hook(tmp_path):
    project, crossings = switched(tmp_path)
    house = tmp_path / "house"
    (house / ".claude" / "projects" / "harbour").mkdir(parents=True)
    path = transcript_of(house / ".claude" / "projects" / "harbour", "headless-0001")
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": "headless-0001"}
    for entrypoint in ("sdk-cli", None, "sdk-py"):
        with set_to(CROSSING_WAIT="1", CLAUDE_PROJECT_DIR=str(project)), own_folder(house), started_by(entrypoint):
            for name, more in (
                ("SessionStart", {"source": "startup"}),
                ("PreToolUse", {"tool_name": "mcp__plugin_crossings_door__find"}),  # before a door call
                ("PostCompact", {"trigger": "auto", "compact_summary": "A summary."}),
                ("SessionStart", {"source": "compact"}),
                ("SessionEnd", {}),
            ):
                hook.run({**event, "hook_event_name": name, **more})
            assert (
                hook.carried({**event, "hook_event_name": "SessionStart", "source": "compact"}) is None
            )  # no frame either (S6)
            assert "Newly archived" not in through("status", "--session", "headless-0001", "--cwd", str(project))[1]
            assert "Newly archived" not in through("frame", "--session", "headless-0001", "--cwd", str(project))[1]
        assert not (crossings / "said").exists(), entrypoint
    assert store.status(crossings)["his"] == 0
    kept = (crossings / store.UNHELD).read_text(encoding="utf-8").splitlines()
    assert kept[0].startswith("# ") and sorted(kept[1:]) == UUIDS  # by their ids alone, and once each
    assert "Tern" not in (crossings / store.UNHELD).read_text(encoding="utf-8")


def test_what_a_session_no_person_sat_in_held_is_not_archived_later_by_a_fork_or_a_resume(tmp_path):
    project, crossings = switched(tmp_path)
    headless = transcript_of(tmp_path, "headless-0002")
    event = {"transcript_path": str(headless), "cwd": str(project), "session_id": "headless-0002"}
    with set_to(CROSSING_WAIT="1", CLAUDE_PROJECT_DIR=str(project)), started_by("sdk-cli"):
        hook.run({**event, "hook_event_name": "SessionEnd"})
    assert not (crossings / "said").exists()
    copied = transcript_of(
        tmp_path, "headless-copy", ROWS[:2]
    )  # a second session no person sat in, repeating two of them
    with started_by("sdk-ts"):
        assert store.unattended(copied, crossings) == 0 and store.unattended(copied, crossings) == 0
    mine = row("user", "12121212", 30, "Now I sit in it myself.")
    fork = transcript_of(
        tmp_path, "personal-0003", ROWS + [mine]
    )  # a person forks it: the same messages under the same ids
    with set_to(CROSSING_WAIT="1", CLAUDE_PROJECT_DIR=str(project)), started_by("cli"):
        assert hook.run({**fork_event(event, fork), "hook_event_name": "SessionEnd"}) is None
        assert archived(crossings) == ["12121212-0000-4000-8000-000000000000"]
        # A person resumes it in its own file: what was said since is kept, what the tool's prompts said is not.
        later = row("user", "34343434", 31, "And in the resumed session too.")
        headless.write_text(headless.read_text(encoding="utf-8") + json.dumps(later) + "\n", encoding="utf-8")
        started = hook.keep(headless, project, wait=False)  # the hooks' own build, at a session's end not waited for
        assert started.wait(timeout=60) == 0
    assert archived(crossings) == ["12121212-0000-4000-8000-000000000000", "34343434-0000-4000-8000-000000000000"]
    # Handed to the door by its path, from a shell, the transcript is the person's own act, and is taken: by a
    # build, which reads it whole, since a marker has stepped over it already.
    assert "Newly archived: 4." in through("build", "--transcript", str(headless), "--cwd", str(project))[1]


def fork_event(event: dict, path: Path) -> dict:
    return {**event, "transcript_path": str(path), "session_id": path.stem}


def test_a_session_a_person_sits_in_is_still_archived_at_every_hook(tmp_path):
    project, crossings = switched(tmp_path)
    path = transcript_of(tmp_path, "personal-0004")
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": "personal-0004"}
    with set_to(CROSSING_WAIT="1", CLAUDE_PROJECT_DIR=str(project)), started_by("cli"):
        assert (
            hook.run({**event, "hook_event_name": "PreToolUse", "tool_name": "mcp__plugin_crossings_door__find"})
            is None
        )
        assert archived(crossings) == UUIDS
        more = row("user", "56565656", 32, "One more.")
        path.write_text(path.read_text(encoding="utf-8") + json.dumps(more) + "\n", encoding="utf-8")
        hook.run({**event, "hook_event_name": "SessionEnd"})
    assert "56565656-0000-4000-8000-000000000000" in archived(crossings) and not (crossings / "unattended.txt").exists()


# --- C5: what the plugin makes is its owner's alone ----------------------------------------------------------------


def modes(*folders: Path) -> dict[str, str]:
    """The mode of every folder and file below these, and of each of them, by path."""
    found = {}
    for folder in folders:
        for path in [folder, *sorted(folder.rglob("*"))]:
            found[str(path)] = oct(stat.S_IMODE(path.lstat().st_mode))
    return found


def wide(folder: Path) -> None:
    """A home as an older make left it: folders 0755 and files 0644."""
    for path in [folder, *folder.rglob("*")]:
        os.chmod(path, 0o755 if path.is_dir() else 0o644)


class Umask:
    """The process's umask for the length of a block, as a person's shell would have it."""

    def __init__(self, mask: int):
        self.mask = mask

    def __enter__(self):
        self.was = os.umask(self.mask)

    def __exit__(self, *_):
        os.umask(self.was)


def test_every_folder_the_plugin_makes_is_0700_and_every_file_0600(tmp_path):
    project = repository(tmp_path, "private")
    places = {
        "CROSSING_HOMES": tmp_path / "homes",
        "CROSSING_SWITCHED": tmp_path / "record" / "switched",
        "CLAUDE_PLUGIN_DATA": tmp_path / "data",
        "CROSSING_LIVE": tmp_path / "live",
        "CROSSING_OURS": tmp_path / "ours",
    }
    env = {name: str(place) for name, place in places.items()}
    path = transcript_of(tmp_path, "abcdef01-8888")
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": "abcdef01-8888"}
    (tmp_path / "ours" / "said").mkdir(parents=True)  # the home on this computer, with an archive put there by hand
    (tmp_path / "ours" / "said" / "x.jsonl").write_text(
        json.dumps(
            {"uuid": D + "-0000", "id": D, "session": "x", "voice": "his", "text": "Words of the whole computer."}
        )
        + "\n",
        encoding="utf-8",
    )
    wide(tmp_path / "ours")
    with Umask(0o022):  # every process starts as a shell would start it
        assert as_the_module("switch", "on", "--cwd", str(project), **env).stdout == ON
        for sent in (
            {**event, "hook_event_name": "SessionStart", "source": "startup"},
            {**event, "hook_event_name": "SessionEnd"},
            {**event, "session_id": "abcdef01-9999", "hook_event_name": "SessionStart", "source": "resume"},
        ):
            done = ran("hook.py", stdin=json.dumps(sent), CLAUDE_CODE_ENTRYPOINT="cli", CROSSING_WAIT="1", **env)
            assert (done.returncode, done.stderr) == (0, "")  # a session starting is welcomed, as it is
        calls = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "mark", "arguments": {"sentence": "A label.", "anchors": [D]}},
            },
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "thread", "arguments": {"id": D}}},
        ]
        served = ran(
            "serve.py",
            stdin="".join(json.dumps(c) + "\n" for c in calls),
            CLAUDE_PROJECT_DIR=str(project),
            CLAUDE_CODE_ENTRYPOINT="cli",
            **env,
        )
        assert "marked W1" in served.stdout
        marked = ran(
            "door.py",
            "mark",
            "--home",
            "ours",
            "--anchors",
            D,
            "A line for the whole computer.",
            "--cwd",
            str(project),
            **env,
        )
        assert marked.stdout.startswith("marked W1")
        assert ran("door.py", "status", "--home", "ours", "--cwd", str(project), **env).returncode == 0  # and narrowed
    made = modes(
        *(places[name] for name in ("CROSSING_HOMES", "CLAUDE_PLUGIN_DATA", "CROSSING_LIVE", "CROSSING_OURS")),
        places["CROSSING_SWITCHED"].parent,
    )
    home_of = record.outside(project.resolve())
    for name in ("said", "labels", "store.db", "markers.jsonl", "reached.jsonl", "welcomed.txt", "switch", "project"):
        assert str(Path(str(places["CROSSING_HOMES"]) + str(home_of)[len(str(record.homes())) :]) / name) in made, name
    for name in ("calls.log", "abcdef01-9999", "switched", "store.db", "labels"):
        assert any(Path(p).name == name for p in made), name
    assert {p: m for p, m in made.items() if m != ("0o700" if Path(p).is_dir() else "0o600")} == {}


def test_a_home_an_older_make_left_wide_is_narrowed_by_status_and_by_switching_on(tmp_path):
    for verb in (["status"], ["switch", "on"]):
        crossings, _ = home(tmp_path / verb[0])
        (crossings / "labels").mkdir()
        (crossings / "labels" / "2026-01-01.md").write_text("| # | Label | Whose | Anchors |\n", encoding="utf-8")
        wide(crossings)
        with Umask(0o022):
            done = as_the_module(*verb, "--cwd", str(crossings.parent))
        assert done.returncode == 0, verb
        assert {p: m for p, m in modes(crossings).items() if m != ("0o700" if Path(p).is_dir() else "0o600")} == {}, (
            verb
        )
    crossings, _ = home(
        tmp_path / "linked"
    )  # a home with a link below it is refused whole, and nothing in it is changed
    (tmp_path / "elsewhere.txt").write_text("not the home's\n", encoding="utf-8")
    os.chmod(tmp_path / "elsewhere.txt", 0o644)
    (crossings / "copy").symlink_to(tmp_path / "elsewhere.txt")
    wide(crossings)
    before = modes(crossings)
    with Umask(0o022):
        done = ran("door.py", "status", "--cwd", str(crossings.parent))
    assert (done.returncode, done.stdout) == (1, LINKED) and modes(crossings) == before
    assert oct(stat.S_IMODE((tmp_path / "elsewhere.txt").stat().st_mode)) == "0o644"
    (crossings / "copy").unlink()
    (tmp_path / "pointer").symlink_to(
        crossings, target_is_directory=True
    )  # a home folder that is a link is left as it is
    assert record.narrow(tmp_path / "pointer") == 0 and record.narrow(tmp_path / "nowhere") == 0
    assert modes(crossings) == {p: m for p, m in before.items() if not p.endswith("/copy")}
    assert record.narrow(crossings) == len(before) - 1 and record.narrow(crossings) == 0


def test_on_windows_no_mode_is_set_or_narrowed(tmp_path):
    folder = tmp_path / "home"
    folder.mkdir()
    os.chmod(folder, 0o755)
    was, record.WINDOWS = record.WINDOWS, True
    try:
        with Umask(0o022):
            record.private()
            mask = os.umask(0o022)
        assert mask == 0o022 and record.narrow(folder) == 0
    finally:
        record.WINDOWS = was
    assert oct(stat.S_IMODE(folder.stat().st_mode)) == "0o755"
    assert door.ASTRAY.count(".") == 1 and "/" not in door.ASTRAY  # and the sentence of C2 names no file


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:
                sweep(folder)
            print("ok", name)
