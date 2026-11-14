"""What a check of the docs against the code found, each with the test that holds it: a hand-over's
words page made from what the home still keeps, a model a shell cannot name, the module's own
verbs kept for the module, a subagent's cut that writes nothing, a second copy named by its
project's whole path, a strike that names the labels left resting on what it took, a stack listed
by the day of its page, a strike that matched nothing that fails, ids that become no line of a
small file unless they are names, a home's line files broken at line feeds alone, a `~` that is
the account's own folder, and a session's mark that strikes no stack of the person's. No model,
no network, and nothing of the person's: the Keychain is a stand-in.

Run with pytest, or without it:  python3 tests/test_mends.py
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_checks import PERSONS, shell  # noqa: E402
from test_count import BEFORE, SUMMARY, written  # noqa: E402
from test_edges import as_the_module, set_to, through, words_script  # noqa: E402
from test_reach import KEY, stood_in  # noqa: E402
from test_serve import said  # noqa: E402
from test_store import A, B, D, E, home, own_folder, row, started_by, sweep, switched_on  # noqa: E402  (and its data folder)

from crossing import hook, off, record, second, store  # noqa: E402

WHOLE = "-0000-4000-8000-000000000000"  # what follows the first eight characters of a made-up message's id


def page_of(crossings: Path) -> str:
    return (crossings / "hand-over.words.md").read_text(encoding="utf-8")


# --- 1: the hand-over's words page ----------------------------------------------------------------


def test_the_words_page_holds_nothing_struck_nothing_said_off_the_record_and_nothing_unattended(tmp_path):
    crossings, path = home(tmp_path)
    assert through("strike", A, "--cwd", str(crossings.parent))[0] == 0
    # D was said at 09:04, inside a span when Crossing was off; E was held by a session no person sat in.
    (crossings / "off.txt").write_text(
        off.HEAD + "2026-11-11T09:03:30.000000+00:00 2026-11-11T09:04:30.000000+00:00\n", encoding="utf-8"
    )
    (crossings / "unattended.txt").write_text(f"{E}{WHOLE}\n", encoding="utf-8")
    made = words_script(str(path), str(crossings / "hand-over.md"))
    assert made.returncode == 0, made.stderr
    words = page_of(crossings)
    assert f"- `{B}`, the session: Noted: Tern, at mooring 41." in words
    for gone in ("My boat is called Tern", "We paint the hull grey", "Grey it is", A, D, E):
        assert gone not in words, gone


def test_where_the_record_of_when_crossing_was_off_cannot_be_told_the_words_page_gives_no_message(tmp_path):
    crossings, path = home(tmp_path)
    (crossings / "off.txt").mkdir()  # there, and no file that can be read
    assert words_script(str(path), str(crossings / "hand-over.md")).returncode == 0
    assert "- `" not in page_of(crossings) and "Tern" not in page_of(crossings)
    (crossings / "off.txt").rmdir()
    assert through("switch", "off", "--cwd", str(crossings.parent))[0] == 0  # the record now counts its lines
    (crossings / "off.txt").unlink()  # and it is taken away: what it held can no longer be told
    assert words_script(str(path), str(crossings / "hand-over.md")).returncode == 0
    assert "- `" not in page_of(crossings) and "Tern" not in page_of(crossings)
    unnamed = row("user", "1234abcd", 30, "An id that is no name.")
    unnamed["uuid"] = "1234abcd 0000"
    (crossings / "hand-over.md").write_text("| W9 | A label. | his | `1234abcd` |\n", encoding="utf-8")
    path.write_text(json.dumps(unnamed) + "\n", encoding="utf-8")
    through("switch", "on", "--cwd", str(crossings.parent))
    assert words_script(str(path), str(crossings / "hand-over.md")).returncode == 0
    assert "An id that is no name" not in page_of(crossings)


def test_the_words_page_is_written_through_within_and_for_its_owner_alone(tmp_path):
    crossings, path = home(tmp_path)
    made = words_script(str(path), str(crossings / "hand-over.md"))
    assert made.returncode == 0, made.stderr
    if os.name != "nt":  # a wide umask in the shell that runs it is narrowed, as every entry of the plugin does
        assert stat.S_IMODE((crossings / "hand-over.words.md").stat().st_mode) == 0o600
    (crossings / "hand-over.words.md").unlink()
    elsewhere = tmp_path / "elsewhere.md"
    elsewhere.write_text("left alone\n", encoding="utf-8")
    (crossings / "hand-over.words.md").symlink_to(elsewhere)
    linked = words_script(str(path), str(crossings / "hand-over.md"))
    assert linked.returncode == 1 and elsewhere.read_text(encoding="utf-8") == "left alone\n"


def test_the_door_gives_no_words_page_that_names_what_was_struck_or_kept_off(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    assert through("strike", D, "--cwd", project)[0] == 0
    # A page written after the strike by any other hand still names the struck message.
    (crossings / "hand-over.words.md").write_text(
        f"- `{D}`, the person: We paint the hull grey in spring\n", encoding="utf-8"
    )
    shown = as_the_module("page", "--cwd", project, CLAUDE_CODE_ENTRYPOINT="cli")  # a person sits in the session
    assert shown.returncode == 0 and "- W1 (both): " in shown.stdout and "We paint the hull" not in shown.stdout
    (crossings / "unsaid.txt").write_text(f"{E}{WHOLE}\n", encoding="utf-8")
    (crossings / "hand-over.words.md").write_text(f"- `{E}`, the session: Grey it is.\n", encoding="utf-8")
    assert "Grey it is" not in as_the_module("page", "--cwd", project, CLAUDE_CODE_ENTRYPOINT="cli").stdout
    (crossings / "hand-over.words.md").write_text(f"- `{B}`, the session: Noted: Tern.\n", encoding="utf-8")
    assert (
        "Noted: Tern." in as_the_module("page", "--cwd", project, CLAUDE_CODE_ENTRYPOINT="cli").stdout
    )  # one that names neither is given


# --- 3: a model a shell names -----------------------------------------------------------------------


def test_a_shell_cannot_sign_a_label_under_a_model_of_its_choosing(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    assert shell(
        "mark", "--anchors", D, "Signed by a name a shell chose.", "--cwd", project, "--model", "made-up-model"
    ) == (1, PERSONS)
    assert not (crossings / "models.txt").exists() and not (crossings / "labels").exists()
    assert shell("frame", "--cwd", project, "--model", "made-up-model") == (1, PERSONS)  # nor read a frame as one
    code, out = through(
        "mark", "--anchors", D, "Signed at the person's own terminal.", "--cwd", project, "--model", "made-up-model"
    )
    assert code == 0 and "made-up-model" in (crossings / "models.txt").read_text(encoding="utf-8")
    assert (
        shell("mark", "--anchors", D, "A shell's own label, no model named.", "--cwd", project)[0] == 0
    )  # mark itself stays


# --- 4: the module's own verbs ------------------------------------------------------------------------


def test_trace_and_welcome_are_the_hooks_or_the_persons_alone_and_words_and_page_only_read(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    (crossings / "hand-over.md").unlink()  # a home with no label: a session there is welcomed
    store.build(crossings)
    assert shell("trace", '{"did": "beside"}', "--cwd", project) == (1, PERSONS)
    assert not (crossings / "last-cut.json").exists()
    with started_by("cli"):
        assert shell("welcome", "abcdef01-0000", "--cwd", project) == (1, PERSONS)
    assert not (crossings / "welcomed.txt").exists() and not (crossings / "told.txt").exists()
    before = sorted(p.name for p in crossings.iterdir())
    with started_by("cli"):  # a session a person sits in: the page is not refused for who sits there
        assert shell("words", "--cwd", project)[0] == 0 and shell("page", "--cwd", project)[0] == 1  # no page here
    assert sorted(p.name for p in crossings.iterdir()) == before  # they read, and write nothing
    assert as_the_module("trace", '{"did": "beside"}', "--cwd", project).returncode == 0
    assert json.loads((crossings / "last-cut.json").read_text(encoding="utf-8")) == {"did": "beside"}


# --- 5: a subagent's cut ----------------------------------------------------------------------------------


def test_a_hook_that_names_a_subagent_writes_no_cut_and_wakes_nobody(tmp_path):
    (tmp_path / "crossings").mkdir()
    switched_on(tmp_path)
    path = written(tmp_path, BEFORE)
    event = {
        "transcript_path": str(path),
        "cwd": str(tmp_path),
        "session_id": "abcdef0123456789",
        "agent_id": "agent-1",
    }
    with started_by("cli"), set_to(CROSSING_WAIT="1"):
        assert hook.run({**event, "hook_event_name": "SessionStart", "source": "compact"}) is None
        assert (
            hook.run({**event, "hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": SUMMARY}) is None
        )
        assert sorted(p.name for p in (tmp_path / "crossings").iterdir()) == []
        del event["agent_id"]  # the session itself is counted as before
        assert "cut 1 of this session" in hook.run({**event, "hook_event_name": "SessionStart", "source": "compact"})
        hook.run({**event, "hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": SUMMARY})
    assert (tmp_path / "crossings" / "abcdef01-cut-1.md").exists()


# --- 6: the second copy's name ----------------------------------------------------------------------------


def image(project: Path) -> str:
    return f"{project.name}-{hashlib.sha256(str(project.resolve()).encode('utf-8')).hexdigest()[:8]}.dmg"


@stood_in
def test_two_projects_of_one_name_keep_two_images_and_an_older_image_is_left_and_named_once(tmp_path, seen):
    first, _ = home(tmp_path / "one")
    other, _ = home(tmp_path / "two")
    cloud = tmp_path / "cloud"
    cloud.mkdir()
    older = cloud / "project.dmg"  # as the copy was named before: by the project's folder alone
    older.write_bytes(b"an older image")
    for crossings in (first, other):
        (crossings / "copy").write_text(f"{cloud}\n", encoding="utf-8")
    with set_to(CROSSING_COPY_KEY=KEY):
        for crossings in (first, other):
            code, out = through("copy", "--cwd", str(crossings.parent))
            assert code == 0 and f"to {cloud / image(crossings.parent)} " in out, out
    assert sorted(p.name for p in cloud.iterdir()) == sorted(["project.dmg", image(first.parent), image(other.parent)])
    assert older.read_bytes() == b"an older image"  # never renamed, overwritten or taken away
    told = through("status", "--cwd", str(first.parent))[1]
    assert (
        f"An older second copy, {older}, is named by the project's folder alone and is no longer renewed; it is "
        "left as it is."
    ) in told
    assert str(older) not in through("status", "--cwd", str(first.parent))[1]  # once
    assert str(older) not in shell("status", "--cwd", str(other.parent))[1]  # and to the person alone
    assert older.read_bytes() == b"an older image"


# --- 7, 9: what a strike says, and how it ends ---------------------------------------------------------------


def test_a_strike_names_every_label_that_rests_on_what_it_struck_and_strikes_none_of_them(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    code, out = through("strike", D, "--cwd", project)
    assert (
        code == 0
        and ("The label that rests on what was struck stays as it is: W1. door.py strike W1 takes it out as well.")
        in out
    ), out
    assert [label["id"] for label in store.labels(crossings)] == ["R1", "W1"]
    code, out = through("strike", "session:session-0001", "--cwd", project)
    assert code == 0 and "The labels that rest on what was struck stay as they are: R1, W1." in out, out
    code, out = through("strike", "W1", "--cwd", project)
    assert code == 0 and "rests on what was struck" not in out  # a label struck is no message


def test_a_strike_that_struck_nothing_fails_in_one_sentence(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    assert through("strike", "--cwd", project) == (1, "not struck: nothing named\n")
    assert through("strike", "``", "--cwd", project) == (1, "not struck: nothing named\n")
    assert through("strike", "0a0a0a0a+1", "--cwd", project) == (
        1,
        "not struck: nothing in this home is named 0a0a0a0a+1, so nothing was struck\n",
    )
    assert not (crossings / "struck.txt").exists()  # and nothing was written for any of them


# --- 8: a stack by the day of its page -------------------------------------------------------------------------


def test_a_stack_is_listed_by_the_day_of_its_own_page(tmp_path):
    crossings, _ = home(tmp_path)
    for sentence in ("The hull first.", "Then the mast."):
        assert store.mark(crossings, "work", "session", sentence, [D], day="2026-11-11")["written"]
    assert (
        store.mark(crossings, "work", "session", "The hull, then the mast.", ["W2", "W3"], day="2026-12-01")["id"]
        == "W4"
    )
    assert [label["id"] for label in store.listed(crossings, day="2026-12-01")["labels"]] == ["W4"]
    assert [label["id"] for label in store.listed(crossings, day="2026-11-11")["labels"]] == ["W3", "W2", "W1"]


# --- 10: ids that become lines -------------------------------------------------------------------------------------


def test_an_id_that_is_no_name_becomes_no_line_of_a_homes_small_files(tmp_path):
    crossings, _ = home(tmp_path)
    bad = row("user", "12 4", 20, "password=made-up-and-long-enough")
    bad["uuid"] = "12 4\nW1x-0000"  # a space and a line break: two lines of a small file, where it were written
    kept_off = row("user", "1234abcd", 21, "Said while it was off.")
    kept_off["uuid"] = "1234abcd 0000\nW2"
    path = tmp_path / "odd-0001.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in (bad, kept_off)), encoding="utf-8")
    (crossings / "off.txt").write_text(
        off.HEAD + "2026-11-11T09:20:30.000000+00:00 2026-11-11T09:21:30.000000+00:00\n", encoding="utf-8"
    )
    store.archive(path, crossings)
    store.unattended(path, crossings)
    for name in ("flagged.txt", "unsaid.txt", "unattended.txt"):
        held = crossings / name
        lines = (
            [line for line in held.read_text(encoding="utf-8").split("\n") if line and not line.startswith("#")]
            if held.exists()
            else []
        )
        for line in lines:
            record.ident(line)  # every line a name
        assert "W1x-0000" not in lines and "W2" not in lines, name
    assert "made-up-and-long-enough" not in (crossings / "said" / "session-.jsonl").read_text(encoding="utf-8")
    assert not (crossings / "said" / "odd-0001.jsonl").exists()  # a row whose id is no name is not archived either


# --- 11: line feeds alone ------------------------------------------------------------------------------------------


def test_a_homes_line_files_break_at_line_feeds_alone(tmp_path):
    crossings, path = home(tmp_path)
    (crossings / "struck.txt").write_text(f"{A}  # a reason that runs W1\n", encoding="utf-8")
    assert store.struck(crossings) == {A}
    (crossings / "flagged.txt").write_text(f"{A} {B}\n", encoding="utf-8")
    assert store.flagged(crossings) == []
    (crossings / "models.txt").write_text("W1@abcdef model-one W2@abcdef model-two\n", encoding="utf-8")
    assert ("W2", "abcdef") not in store.models(crossings)
    store._moved(crossings, "/a/transcript of a session.jsonl", path, 0)
    assert "/a/transcript of a session.jsonl" in store.markers(crossings)
    (crossings / "off.txt").write_text("2026-11-11T09:00:00Z 2026-11-11T09:01:00Z\n", encoding="utf-8")
    spans, unread = off.spans(crossings)
    assert unread == 0 and [(s.isoformat(), e.isoformat()) for s, e in spans] == [
        ("2026-11-11T09:00:00+00:00", "2026-11-11T09:01:00+00:00")
    ]


# --- 12: a `~` in the copy file -------------------------------------------------------------------------------------


def test_a_leading_tilde_in_the_copy_file_is_the_accounts_own_folder_and_never_home(tmp_path):
    crossings, _ = home(tmp_path)
    with own_folder(tmp_path / "own"), set_to(HOME=str(tmp_path / "set-by-a-project")):
        (crossings / "copy").write_text("~/cloud\n", encoding="utf-8")
        assert second.destination(crossings) == tmp_path / "own" / "cloud"
        (crossings / "copy").write_text("~\n", encoding="utf-8")
        assert second.destination(crossings) == tmp_path / "own"


# --- 14: a session's mark and the person's stack ----------------------------------------------------------------------


def test_a_sessions_mark_never_strikes_a_stack_of_the_persons(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    day = "2026-11-11"
    for sentence, anchor in (("The hull first.", D), ("Then the mast.", E)):
        assert store.mark(crossings, "work", "session", sentence, [anchor], day=day)["written"]
    assert store.mark(crossings, "work", "his", "The order of the work.", ["W2", "W3"], day=day)["id"] == "W4"
    page = crossings / "labels" / f"{day}.md"
    page.write_text(page.read_text(encoding="utf-8").replace("The hull first.", "The hull, first."), encoding="utf-8")
    store.build(crossings)
    assert store.listed(crossings, ids=("W4",))["labels"][0]["state"] == "misaligned"
    with set_to(CLAUDE_PROJECT_DIR=project):
        text, _ = said("mark", sentence="The mast, after the hull.", anchors=["W3"])
    assert text == "not marked: W4 is a stack of the person's, and only the person writes it again", text
    assert shell("mark", "--anchors", "W3", "The mast, after the hull.", "--cwd", project)[1] == (
        "not marked: W4 is a stack of the person's, and only the person writes it again\n"
    )
    assert "W4" not in store.struck(crossings) and "W4" in {label["id"] for label in store.labels(crossings)}
    code, out = through(
        "mark", "--anchors", "W3", "The mast, after the hull.", "--cwd", project
    )  # the person's own hand
    assert code == 0 and "in place of W4" in out and "W4" in store.struck(crossings)


# --- what the repository guide says is preserved ------------------------------------------------------------------------


def test_the_plugin_imports_the_standard_library_alone_and_nothing_that_opens_a_connection():
    import ast

    from crossing import serve

    # The list of the standard library's own modules is known to Python from 3.10 on. An older
    # Python, such as the 3.9 that macOS ships, still checks that nothing opens a connection.
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    for source in sorted((ROOT / "crossing").glob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom) and not node.level
                else []
            )
            for name in names:
                top = name.split(".")[0]
                assert top == "crossing" or not stdlib or top in stdlib, (source.name, name)
                assert top not in ("socket", "ssl", "http", "urllib", "ftplib", "smtplib", "xmlrpc", "asyncio"), (
                    source.name,
                    name,
                )
    module = (ROOT / "hooks" / "crossings.ts").read_text(encoding="utf-8")
    assert [line for line in module.splitlines() if line.startswith("import ")] == [
        "import type { Register } from 'claude-code'"
    ]
    # The door's server offers its seven tools and no verb of the person's or of the hooks module.
    assert serve.NAMES == ["look", "labels", "find", "thread", "mark", "leave", "status"]


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
