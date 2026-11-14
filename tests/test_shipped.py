"""What a repository can ship, and what it cannot do by shipping it: a `crossings/` folder that
switches nothing on, a link in a home that nothing is written through, two projects that never
come to one home, and a search for a home that stays inside the project. No model, no network.

Run with pytest, or without it:  python3 tests/test_shipped.py
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import ran, set_to, through  # noqa: E402
from test_serve import said  # noqa: E402
from test_store import ROWS, A, D, home, own_folder, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, hook, record, second, show, store  # noqa: E402

ON = "Crossings is on for this project.\n"
NEVER = "Crossings was never switched on for this project.\n"
NOT_ON = "Crossings is not switched on for this project.\n"
LINKED = "A file of this project's home is a link, so nothing was written.\n"
SHIPPED = "0f0f0f0f"  # a message a repository's archive holds, for its label to rest on


def inside(folder: Path) -> list[str]:
    """Everything under a folder, by its path from there."""
    return sorted(str(p.relative_to(folder)) for p in folder.rglob("*"))


def switched_on(project: Path) -> None:
    """The person's own act, as their command does it."""
    assert through("switch", "on", "--cwd", str(project)) in (
        (0, ON),
        (0, door.SWITCHED["again"] + "\n"),
    )  # on, or on again


def adopted(project: Path) -> None:
    """The person's own act, for a home that holds what this computer has no record of: the word
    adopt takes it as theirs."""
    assert through("switch", "adopt", "--cwd", str(project)) == (0, ON)


def logged(folder: Path) -> str:
    """What the plugin's error log holds, in the data folder `folder`."""
    try:
        return (folder / "errors.log").read_text(encoding="utf-8")
    except OSError:
        return ""


def cloned(folder: Path) -> tuple[Path, Path, Path]:
    """A repository as one is cloned: it ships a `crossings/` folder with an archive, a label page
    whose label rests on a message of that archive, and a mode that would answer every cut. With
    it, a session's transcript."""
    project = folder / "cloned"
    (project / ".git").mkdir(parents=True)
    crossings = project / "crossings"
    (crossings / "said").mkdir(parents=True)
    (crossings / "labels").mkdir()
    (crossings / "said" / "shipped0.jsonl").write_text(
        json.dumps(
            {
                "uuid": SHIPPED + "-0000",
                "id": SHIPPED,
                "session": "shipped0",
                "voice": "his",
                "at": "2026-01-01T00:00:00Z",
                "text": "A message that came with the repository.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (crossings / "labels" / "2026-01-01.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
        f"| R1 | A standing line the repository wrote for every session. | his | `{SHIPPED}` |\n",
        encoding="utf-8",
    )
    for name, value in (("mode", "own"), ("carry", "note")):
        (crossings / name).write_text(value + "\n", encoding="utf-8")
    path = folder / "abcdef01-6666.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in ROWS), encoding="utf-8")
    return project, crossings, path


def lines(folder: Path) -> list[dict]:
    """The lines of the person's record that name a project under this test's folder."""
    try:
        text = Path(os.environ["CROSSING_SWITCHED"]).read_text(encoding="utf-8")
    except OSError:
        return []
    mine, found = str(folder.resolve()) + os.sep, []
    for line in text.splitlines():
        try:
            line = json.loads(line)
        except ValueError:
            continue
        if isinstance(line, dict) and str(line.get("project")).startswith(mine):
            found.append(line)
    return found


# --- a folder a repository ships switches nothing on (F1) -------------------------------------------


def test_a_crossings_folder_a_repository_ships_switches_nothing_on(tmp_path):
    project, crossings, path = cloned(tmp_path)
    before = inside(crossings)
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": "abcdef01-6666"}
    with set_to(CROSSING_WAIT="1", CLAUDE_PROJECT_DIR=str(project)), started_by("cli"):
        for name, more in (
            ("PreToolUse", {"tool_name": "mcp__plugin_crossing_door__find"}),
            ("SessionEnd", {}),
            ("SessionStart", {"source": "startup"}),  # where a session is welcomed
            ("PostCompact", {"trigger": "manual", "compact_summary": "A summary."}),
            ("SessionStart", {"source": "compact"}),
        ):
            assert hook.run({**event, "hook_event_name": name, **more}) is None, name
        for source in ("startup", "compact"):  # no frame carries the repository's line to a session
            assert hook.carried({**event, "hook_event_name": "SessionStart", "source": source}) is None, source
        assert hook.keep(path, project, wait=True) is None
        for name, given in (
            ("look", {}),
            ("labels", {}),
            ("find", {"words": "repository"}),
            ("status", {}),
            ("mark", {"sentence": "A label.", "anchors": [SHIPPED]}),
        ):
            assert said(name, **given) == (NOT_ON.strip(), True), name
    for argv in (
        ["look"],
        ["labels", "R1"],
        ["frame"],
        ["status", "--transcript", str(path)],
        ["words"],
        ["page"],
        ["trace", "{}"],
        ["strike", SHIPPED],
        ["build"],
    ):
        assert through(*argv, "--cwd", str(project)) == (1, NOT_ON), argv
    assert through("home", "--cwd", str(project)) == (1, "")
    assert through("switch", "off", "--cwd", str(project)) == (0, NEVER)  # nothing to switch off, and nothing written
    assert "no cut on record" in show.block(project)
    assert inside(crossings) == before and "store.db" not in before  # nothing kept, and no index made by looking
    assert lines(tmp_path) == []


def test_switching_on_is_kept_in_the_persons_record_and_changes_nothing_else_in_the_home(tmp_path):
    project, crossings, path = cloned(tmp_path)
    adopted(project / "crossings")  # from inside it: in a repository the home is found up to its top
    assert lines(tmp_path) == [{"project": str(project.resolve()), "home": str(crossings.resolve())}]
    assert (crossings / "mode").read_text(encoding="utf-8") == "own\n"  # only the switch is turned, and kept
    assert (crossings / "carry").read_text(encoding="utf-8") == "note\n" and not (crossings / "project").exists()
    assert (crossings / "switch").read_text(encoding="utf-8") == "on\n"
    switched_on(project)
    assert len(lines(tmp_path)) == 1  # a line that is there is kept, and not written twice
    assert through("switch", "off", "--cwd", str(project)) == (
        0,
        "Crossings is off for this project: no cut is counted, "
        "noted or answered, and nothing said from now until it "
        "is switched on again will be kept.\n",
    )
    assert (
        len(lines(tmp_path)) == 1 and store.kept(project) == crossings.resolve()
    )  # off, the line stays and the home is read
    assert through("status", "--cwd", str(project))[0] == 0
    switched_on(project)
    (crossings / "mode").write_text("beside\n", encoding="utf-8")  # as the person may set it, to have the frame carried
    with set_to(CLAUDE_PROJECT_DIR=str(project)), started_by("cli"):  # believed, the home is the person's own choice
        framed = hook.carried(
            {
                "hook_event_name": "SessionStart",
                "source": "startup",
                "cwd": str(project),
                "transcript_path": str(path),
                "session_id": "abcdef01-6666",
            }
        )
    assert "A standing line the repository wrote" in json.loads(framed)["hookSpecificOutput"]["additionalContext"]


def test_a_home_is_believed_only_where_the_record_names_it_for_that_project(tmp_path):
    record_of = Path(os.environ["CROSSING_SWITCHED"])
    record_of.parent.mkdir(parents=True, exist_ok=True)
    one, _, _ = cloned(tmp_path / "one")
    two, crossings, _ = cloned(tmp_path / "two")
    adopted(one)
    assert store.kept(two) is None  # another project's line is not this one's
    # A line that names this project and another home, or a line that is no line, believes nothing.
    with open(record_of, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"project": str(two.resolve()), "home": str(tmp_path / "elsewhere")}) + "\n")
        handle.write(
            "not a line\n"
            + json.dumps([str(two.resolve()), str(crossings.resolve())])
            + "\n"
            + json.dumps({"project": str(two.resolve())})
            + "\n"
            + json.dumps({"project": [str(two.resolve())], "home": str(crossings.resolve())})
            + "\n"
        )
    assert store.kept(two) is None and through("look", "--cwd", str(two)) == (1, NOT_ON)
    adopted(two)  # a line for another home is no line for this one
    assert store.kept(two) == crossings.resolve()
    # The home put in its place since, as a link to elsewhere, is not the home the person switched on.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    crossings.rename(tmp_path / "two" / "was")
    crossings.symlink_to(elsewhere, target_is_directory=True)
    assert store.kept(two) is None and through("status", "--cwd", str(two)) == (1, NOT_ON)
    assert inside(elsewhere) == []
    # A project's crossings that is a link is no home at all: switching on is refused, and nothing is located through it.
    was = lines(tmp_path)
    assert through("switch", "on", "--cwd", str(two)) == (1, door.LINKED_HOME.format(elsewhere.resolve()) + "\n")
    assert store.kept(two) is None and lines(tmp_path) == was and inside(elsewhere) == []


def test_switching_on_a_home_made_earlier_only_adds_the_line_and_the_switch(tmp_path):
    loose = tmp_path / "loose"
    loose.mkdir()
    outside = record.outside(loose.resolve())
    outside.mkdir(parents=True)
    for name, value in (
        ("mode", "own\n"),
        ("carry", "message\n"),
        ("project", f"{loose.resolve()}\n"),
        ("frame-size", "3000\n"),
        ("switch", "off\n"),
    ):
        (outside / name).write_text(value, encoding="utf-8")
    assert store.kept(loose) is None and through("switch", "toggle", "--cwd", str(loose))[0] == 1  # it holds files
    assert through("switch", "adopt", "--cwd", str(loose)) == (0, ON)
    assert {p.name: p.read_text(encoding="utf-8") for p in outside.iterdir()} == {
        "archive.lock": "",  # the home's lock, which the switch holds as it turns
        "mode": "own\n",
        "carry": "message\n",
        "project": f"{loose.resolve()}\n",
        "frame-size": "3000\n",
        "switch": "on\n",
    }
    assert store.kept(loose) == outside


def test_a_home_named_outright_is_believed_only_where_the_record_names_it_for_this_project(tmp_path):
    """S3: a project's settings could name another project's home, whose name its path gives away.
    A home named outright is believed as any other: by the line `switch on` writes while the
    setting stands, for this project and this home."""
    named, project, other = tmp_path / "named", tmp_path / "project", tmp_path / "other"  # outside the project
    project.mkdir()
    other.mkdir()
    with set_to(CROSSING_HOME=str(named)):
        assert store.kept(project) is None
        switched_on(project)
        assert store.kept(project) == named
        assert lines(tmp_path) == [{"project": str(project.resolve()), "home": str(named.resolve())}]
        assert store.kept(other) is None  # the same setting in another project opens nothing
        assert through("look", "--cwd", str(other)) == (1, NOT_ON)
    outside = record.outside(project.resolve())  # an existing home of another project, named by its predictable path
    switched_on(project)
    assert store.kept(project) == outside
    with set_to(CROSSING_HOME=str(outside)):
        assert store.kept(other) is None and through("labels", "--cwd", str(other)) == (1, NOT_ON)
        assert store.kept(project) == outside  # its own project's line names it


# --- nothing is written through a link (F2) -----------------------------------------------------------


def linked_home(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A home the person switched on, and a file outside it that a link could lead to."""
    crossings, path = home(tmp_path)
    switched_on(crossings.parent)
    target = tmp_path / "outside.txt"
    target.write_text("not the home's\n", encoding="utf-8")
    return crossings, path, target


def test_a_label_page_that_is_a_link_is_not_written_through(tmp_path):
    crossings, _, target = linked_home(tmp_path)
    project, data = crossings.parent, Path(os.environ["CLAUDE_PLUGIN_DATA"])
    page = crossings.resolve() / "labels" / f"{datetime.date.today().isoformat()}.md"
    page.parent.mkdir(exist_ok=True)
    page.symlink_to(target)
    was = logged(data)
    assert through("mark", "--anchors", D, "A label.", "--cwd", str(project)) == (1, LINKED)
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        assert said("mark", sentence="A label.", anchors=[D]) == (LINKED.strip(), False)
        assert said("look") == (LINKED.strip(), True)  # every handle says it, and reads nothing through it
    assert target.read_text(encoding="utf-8") == "not the home's\n"
    assert logged(data)[len(was) :].count(f"refused: a file of the home is a link: {page}\n") == 3


def test_no_file_of_a_home_is_written_through_a_link(tmp_path):
    crossings, path, target = linked_home(tmp_path)
    project = crossings.parent
    tried = {
        "struck.txt": ["strike", D],
        "reached.jsonl": ["thread", D, "--touch"],
        "models.txt": ["mark", "--anchors", D, "A label.", "--transcript", str(path)],
        "last-cut.json": ["trace", '{"did": "beside"}'],
        "hand-over.md": ["page"],
        "switch": ["switch", "off"],
        "store.db": ["status"],
        "store.db-journal": ["look"],
        "mode": ["words"],
    }
    for name, argv in tried.items():
        (crossings / name).unlink() if (crossings / name).exists() else None
        (crossings / name).symlink_to(target)
        assert through(*argv, "--cwd", str(project)) == (1, LINKED), name
        (crossings / name).unlink()
    (crossings / "frame-size").symlink_to(target)
    assert through("frame", "--cwd", str(project)) == (1, LINKED)
    (crossings / "frame-size").unlink()
    page = sorted((crossings / "said").glob("*.jsonl"))[0]  # the archive a strike rewrites
    page.rename(crossings / "said.was")
    page.symlink_to(target)
    assert through("strike", A, "--cwd", str(project)) == (1, LINKED)
    page.unlink()
    (crossings / "said.was").rename(page)
    (crossings / "said").rename(crossings / "said.was")
    (crossings / "said").symlink_to(tmp_path, target_is_directory=True)  # the archive's own folder, as a link
    assert through("status", "--cwd", str(project), "--transcript", str(path)) == (1, LINKED)
    assert target.read_text(encoding="utf-8") == "not the home's\n" and not (tmp_path / "session-.jsonl").exists()
    (crossings / "said").unlink()
    (crossings / "said.was").rename(crossings / "said")
    assert through("status", "--cwd", str(project))[0] == 0  # and the home, set right, is read again


def test_a_hook_writes_nothing_through_a_link_and_ends_quietly(tmp_path):
    crossings, path, target = linked_home(tmp_path)
    project, data = crossings.parent, tmp_path / "data"
    (crossings / "mode").write_text("beside\n", encoding="utf-8")
    (crossings / "carry").write_text("note\n", encoding="utf-8")
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": "abcdef01-7777"}
    for name, sent, argv in (
        ("last-carry.json", {**event, "hook_event_name": "SessionStart", "source": "compact"}, ["frame"]),
        ("welcomed.txt", {**event, "hook_event_name": "SessionStart", "source": "startup"}, []),
        (
            "abcdef01-cut-1.md",
            {**event, "hook_event_name": "PostCompact", "trigger": "manual", "compact_summary": "A summary."},
            [],
        ),
    ):
        (crossings / name).symlink_to(target)
        done = ran(
            "hook.py",
            *argv,
            stdin=json.dumps(sent),
            CLAUDE_PLUGIN_DATA=str(data),
            CLAUDE_CODE_ENTRYPOINT="cli",
            CROSSING_WAIT="1",
        )
        assert (done.returncode, done.stdout, done.stderr) == (0, "", ""), name
        assert logged(data).endswith(f"refused: a file of the home is a link: {crossings.resolve() / name}\n"), name
        assert target.read_text(encoding="utf-8") == "not the home's\n", name
        (crossings / name).unlink()


def test_the_second_copy_stages_nothing_through_a_link(tmp_path):
    """The stage lies outside the home now (see test_edges): the one file of the home a copy
    keeps of it, the note of where it is, is not read or written through a link."""
    crossings, _, _ = linked_home(tmp_path)
    (tmp_path / "elsewhere.txt").write_text(str(tmp_path) + "\n", encoding="utf-8")
    (crossings / second.STAGED).symlink_to(tmp_path / "elsewhere.txt")
    with set_to(CROSSING_COPY_KEY="a passphrase for this test only"):
        try:
            second.make(crossings, tmp_path / "cloud", "project")
        except record.Linked:
            pass
        else:
            raise AssertionError("the copy was staged through a link")
    assert not (tmp_path / "project" / "said").exists() and not (tmp_path / "cloud").exists()
    assert (tmp_path / "elsewhere.txt").read_text(encoding="utf-8") == str(tmp_path) + "\n"
    (crossings / second.STAGED).unlink()
    (crossings / "copy").symlink_to(tmp_path / "outside.txt")
    try:
        second.destination(crossings)
    except record.Linked:
        pass
    else:
        raise AssertionError("the copy's folder was read through a link")


def test_a_path_that_leads_out_of_a_home_is_refused_and_the_home_itself_may_be_a_link(tmp_path):
    folder = tmp_path / "home"
    folder.mkdir()
    for names in (("..", "outside.txt"), ("said", "..", "..", "x")):
        try:
            record.within(folder, *names)
        except record.Linked as err:
            assert "leads out of the home" in str(err)
        else:
            raise AssertionError(names)
    assert record.within(folder) == folder and record.within(folder, "said", "x.jsonl") == folder / "said" / "x.jsonl"
    (tmp_path / "linked").symlink_to(folder, target_is_directory=True)
    assert record.within(tmp_path / "linked", "switch") == tmp_path / "linked" / "switch"
    before = os.environ["CLAUDE_PLUGIN_DATA"]
    data = tmp_path / "data"
    (data / "errors.log").mkdir(parents=True)  # a log that cannot be written is no reason to stop
    with set_to(CLAUDE_PLUGIN_DATA=str(data)):
        record.refused(record.Linked("a file of the home is a link: somewhere"))
    assert os.environ["CLAUDE_PLUGIN_DATA"] == before


def test_the_module_reads_and_writes_a_home_through_the_door(tmp_path):
    crossings, _, _ = linked_home(tmp_path)
    project = crossings.parent
    (crossings / "mode").write_text("Beside\n", encoding="utf-8")
    assert json.loads(through("words", "--cwd", str(project))[1]) == {"switch": "on", "mode": "beside", "carry": ""}
    assert through("page", "--cwd", str(project))[1].startswith("# a hand-over")
    (crossings / "hand-over.words.md").write_text("- `aaaaaaaa`, the person: the words\n", encoding="utf-8")
    assert through("page", "--cwd", str(project))[1].endswith("|\n\n- `aaaaaaaa`, the person: the words\n")
    (crossings / "hand-over.md").unlink()
    assert through("page", "--cwd", str(project)) == (1, "")
    assert through("trace", '{"did": "beside", "chars": 9}', "--cwd", str(project)) == (0, "")
    assert json.loads((crossings / "last-cut.json").read_text(encoding="utf-8")) == {"did": "beside", "chars": 9}
    for wrong in ("not json", "[1, 2]"):
        assert through("trace", wrong, "--cwd", str(project)) == (2, "trace takes one JSON object.\n")
    through("switch", "off", "--cwd", str(project))
    assert through("trace", '{"did": "own"}', "--cwd", str(project)) == (1, "")  # switched off, nothing is added
    assert json.loads((crossings / "last-cut.json").read_text(encoding="utf-8")) == {"did": "beside", "chars": 9}


# --- two projects, two homes (F3) ------------------------------------------------------------------------


def test_paths_that_read_alike_never_come_to_one_home(tmp_path):
    projects = [tmp_path / name for name in ("a-b", "a_b", "a.b")]
    for project in projects:
        project.mkdir()
    homes = [record.home(project) for project in projects]
    assert len(set(homes)) == 3 and all(found.parent == record.homes() for found in homes)
    for project in projects:
        switched_on(project)
    assert [(found / "project").read_text(encoding="utf-8") for found in homes] == [
        f"{p.resolve()}\n" for p in projects
    ]
    assert [store.kept(project) for project in projects] == homes


def test_a_home_made_before_the_digest_is_used_only_by_the_project_it_names(tmp_path):
    ours_, theirs = tmp_path / "x-y", tmp_path / "x_y"
    ours_.mkdir()
    theirs.mkdir()
    old = record.homes() / record.outside(ours_.resolve()).name[:-9]  # the name a home was given before
    old.mkdir(parents=True)
    (old / "project").write_text(f"{ours_.resolve()}\n", encoding="utf-8")
    (old / "mode").write_text("own\n", encoding="utf-8")
    assert record.home(ours_) == old and record.home(theirs) != old  # the other path is not this home's
    adopted(ours_)  # a home that holds files is taken by the word adopt
    assert store.kept(ours_) == old and (old / "mode").read_text(encoding="utf-8") == "own\n"
    (old / "project").write_text(
        f"{ours_.resolve()}/more\n", encoding="utf-8"
    )  # names another path: not this project's
    assert record.home(ours_) != old and store.kept(ours_) is None
    (old / "project").unlink()
    (old / "project").symlink_to(tmp_path / "x-y-path.txt")  # nor is it where its file is a link
    (tmp_path / "x-y-path.txt").write_text(f"{ours_.resolve()}\n", encoding="utf-8")
    assert record.home(ours_) != old
    assert logged(Path(os.environ["CLAUDE_PLUGIN_DATA"])).endswith(
        f"refused: a file of the home is a link: {old / 'project'}\n"
    )


# --- the search for a home stays inside the project (F4) ----------------------------------------------------


def test_outside_a_repository_only_the_projects_own_folder_is_looked_in(tmp_path):
    house = tmp_path / "house"
    house.mkdir()
    (tmp_path / "crossings").mkdir()  # a folder of that name above a project in no repository is nobody's
    loose = tmp_path / "loose" / "deep"
    loose.mkdir(parents=True)
    (tmp_path / "loose" / "crossings").mkdir()
    with own_folder(house):  # and the person's home is not above it either
        assert record.place(loose) == (record.outside(loose.resolve()), loose.resolve())
        (loose / "crossings").mkdir()
        assert record.place(loose) == (loose.resolve() / "crossings", None)


def test_in_a_repository_the_search_stops_at_its_top(tmp_path):
    (tmp_path / "crossings").mkdir()  # above the repository: not its home
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    deep = repo / "a" / "b"
    deep.mkdir(parents=True)
    assert record.place(deep) == (record.outside(repo.resolve()), repo.resolve())
    (repo / "crossings").mkdir()
    assert record.place(deep) == (repo.resolve() / "crossings", None)
    assert record.located(deep) == (repo.resolve() / "crossings", repo.resolve(), False)


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:
                sweep(folder)
            print("ok", name)
