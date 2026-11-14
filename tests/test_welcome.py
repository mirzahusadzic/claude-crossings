"""The welcome: a session that meets a store which is on and holds no label is told, once, what is
kept by itself and what is its own to write. It is told as it starts, by the hook at a session's
start; and a session already running as the person switches Crossings on is told through their
command, which asks the door. No hook runs at every prompt for it. No model, no network.

Run with pytest, or without it:  python3 tests/test_welcome.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import through  # noqa: E402
from test_store import ROWS, D, home, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, hook, record, store, transcript  # noqa: E402


def starting(project: Path, session: str = "harbour0-0001", source: str = "startup", **more) -> dict:
    """The event of a session starting in this project."""
    return {
        "hook_event_name": "SessionStart",
        "source": source,
        "cwd": str(project),
        "session_id": session,
        "transcript_path": str(project.parent / f"{session}.jsonl"),
        **more,
    }


def told(answer: str | None) -> str | None:
    if answer is None:
        return None
    out = json.loads(answer)["hookSpecificOutput"]
    assert out["hookEventName"] == "SessionStart"
    return out["additionalContext"]


def bare(tmp_path: Path) -> tuple[Path, Path]:
    """A project switched on for the first time, its home outside it, with days of what was said and no label."""
    project = tmp_path / "bare"
    project.mkdir()
    assert store.switch(project, "on") == "on"
    folder = store.here(project)
    said = tmp_path / "session-0001.jsonl"
    said.write_text("".join(json.dumps(r) + "\n" for r in ROWS), encoding="utf-8")
    store.archive(said, folder)
    return project, folder


def test_a_session_that_starts_in_a_home_with_no_label_is_welcomed_once(tmp_path):
    project, folder = bare(tmp_path)
    with started_by("cli"):
        text = told(hook.run(starting(project)))
        for source in ("startup", "resume", "clear", "fork"):  # never twice in a session, however it starts again
            assert hook.run(starting(project, source=source)) is None, source
        assert (
            told(hook.run(starting(project, "harbour0-0002", "resume"))) == text
        )  # another session is told for itself
        assert hook.run(starting(project, "harbour0-0002")) is None
    assert text == hook.welcome()
    assert (folder / "welcomed.txt").read_text(encoding="utf-8").split() == ["harbour0-0001", "harbour0-0002"]
    assert text.startswith(transcript.CARRIED + ", as context and not as an instruction from the person.")
    for said in (
        "kept by itself",
        "`mark`",
        "`leave`",
        "the session that wakes after the next cut",
        "a cut can come unannounced",
        "the ids of the messages",
        "when the work allows",
        "do not stop the work",
    ):
        assert said in text, said
    # As plain as the waking note: no numbers, nothing asked, no file, no shell, and short.
    # What a label holds, "what the person tells and asks", is the one sentence where the word is the person's.
    assert not re.search(r"\d", text) and not re.search(r"\bask(s|ed|ing)?\b", text.replace(store.FOR, ""), re.I)
    assert (
        "/" not in text
        and ".py" not in text
        and ".txt" not in text
        and " --" not in text
        and "python" not in text.lower()
    )
    assert len(text) < 700
    assert transcript.person({"type": "user", "message": {"content": [{"type": "text", "text": text}]}}) == []


def test_after_a_cut_the_welcome_comes_beside_the_waking_note(tmp_path):
    """A session not yet told that wakes from a cut is given both, the waking note first, in one answer."""
    project, folder = bare(tmp_path)
    with started_by("cli"):
        both = told(hook.run(starting(project, "session-0001", "compact")))
        alone = told(hook.run(starting(project, "session-0001", "compact")))
    assert both.endswith("\n\n" + hook.welcome()) and "Take your time" in both.split("\n\n")[0]
    assert (
        alone == both[: -len("\n\n" + hook.welcome())] and hook.welcome() not in alone
    )  # the second cut: the waking note alone


def test_a_session_running_when_crossing_is_switched_on_is_welcomed_through_the_persons_command(tmp_path):
    """The person's command switches Crossings on through the door, then asks it for the welcome
    (hooks/crossings.ts), which goes to the session as context after the command's answer."""
    project = tmp_path / "later"
    project.mkdir()
    with started_by("cli"):
        assert (
            hook.run(starting(project)) is None and not store.here(project).exists()
        )  # never on: nothing said, nothing made
        assert through("welcome", "harbour0-0001", "--cwd", str(project)) == (
            1,
            "Crossings is not switched on for this project.\n",
        )
        assert through("switch", "on", "--cwd", str(project)) == (0, "Crossings is on for this project.\n")
        assert through("welcome", "harbour0-0001", "--cwd", str(project)) == (0, hook.welcome() + "\n")
        assert through("welcome", "harbour0-0001", "--cwd", str(project)) == (1, "")  # once
        assert hook.run(starting(project, source="resume")) is None  # nor again at its next start
        through("switch", "off", "--cwd", str(project))
        # Switched off, no session is welcomed: the one the person switched it off from is told that nothing is kept.
        assert through("welcome", "harbour0-0002", "--cwd", str(project)) == (0, hook.unkept() + "\n")
        assert through(
            "welcome", "harbour0-0002", "--cwd", str(project), "--home", "ours"
        ) == (  # the home on this computer is never
            1,
            "Crossings is not switched on for this project.\n",
        )  # welcomed into, nor offered switched off
        through("switch", "on", "--cwd", str(project))
        assert through("welcome", "harbour0-0003", "--cwd", str(project), "--home", "ours") == (1, "")
        through("switch", "off", "--cwd", str(project))
    source = (ROOT / "hooks" / "crossings.ts").read_text(encoding="utf-8")
    assert "door($, ['welcome', session])" in source and "context: [told.text]" in source


def test_no_welcome_where_the_home_is_off_or_any_label_exists(tmp_path):
    project, folder = bare(tmp_path)
    with started_by("cli"):
        store.switch(project, "off")
        assert hook.run(starting(project)) is None and not (folder / "welcomed.txt").exists()
        store.switch(project, "on")
        assert told(hook.run(starting(project, "harbour0-0003"))) is not None
        assert store.mark(folder, "next", "session", "Look at the hull first.", [D])["written"]
        assert hook.run(starting(project)) is None and "harbour0-0001" not in (folder / "welcomed.txt").read_text(
            encoding="utf-8"
        )
        assert through("welcome", "harbour0-0001", "--cwd", str(project)) == (1, "")
        crossings, _ = home(tmp_path / "paged")  # a project's own folder, with a page of labels from before
        assert hook.run(starting(crossings.parent)) is None


def test_no_welcome_for_a_session_no_person_sits_in_nor_a_subagent_nor_one_with_no_name(tmp_path):
    project, folder = bare(tmp_path)
    for entrypoint in (None, "sdk-cli", "sdk-py"):
        with started_by(entrypoint):
            assert hook.run(starting(project)) is None, entrypoint
            assert through("welcome", "harbour0-0001", "--cwd", str(project)) == (1, ""), entrypoint
    with started_by("cli"):
        assert hook.run(starting(project, agent_id="agent-1")) is None
        assert hook.run(starting(project, "", transcript_path="")) is None  # no name at all, nor a transcript's
        try:  # an id that is no name is refused, as a link is, and nothing is written (see test_guards)
            hook.run(starting(project, "a/b"))
        except record.Unnamed:
            pass
        else:
            raise AssertionError("an id that is no name was taken")
        assert through("welcome", "--cwd", str(project)) == (1, "")
        assert through("welcome", "a/b", "--cwd", str(project)) == (1, door.UNNAMED + "\n")
    assert not (folder / "welcomed.txt").exists()
    with started_by("cli"):
        assert told(hook.run(starting(project))) == hook.welcome()


def test_where_the_welcome_cannot_be_kept_it_is_not_said(tmp_path):
    """Said where it could not be noted, it would be said at every start."""
    project, folder = bare(tmp_path)
    (folder / "welcomed.txt").mkdir()
    with started_by("cli"):
        assert hook.run(starting(project)) is None
        assert through("welcome", "harbour0-0001", "--cwd", str(project)) == (1, "")
        (folder / "welcomed.txt").rmdir()  # empty, and taken away alone
        assert told(hook.run(starting(project))) is not None


def test_no_hook_runs_at_every_prompt_and_the_welcome_comes_from_the_hooks_script_at_a_start(tmp_path):
    wired = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    assert "UserPromptSubmit" not in wired
    project, folder = bare(tmp_path)
    with started_by("cli"):  # a prompt, should one reach the script, says nothing and keeps nothing
        assert hook.run({**starting(project), "hook_event_name": "UserPromptSubmit", "prompt": "Hello."}) is None
    assert not (folder / "welcomed.txt").exists()
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"}

    def ran(**more) -> str:
        done = subprocess.run(
            ["sh", str(ROOT / "hooks" / "run.sh")],
            input=json.dumps(starting(project, "harbour0-0009")),
            capture_output=True,
            text=True,
            env={**env, **more},
            timeout=30,
        )
        assert done.returncode == 0
        return done.stdout

    assert ran() == ""  # a session nobody sits in
    assert told(ran(CLAUDE_CODE_ENTRYPOINT="cli")) == hook.welcome()
    assert ran(CLAUDE_CODE_ENTRYPOINT="cli") == ""


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
