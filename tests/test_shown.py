"""The hook after a call of the door's `mark` or `leave`, for every kind of label: the line the person is shown under
the turn, and the model it signs a label with where the server wrote it with none handed over. Each label is written
by the server and the hook is handed the call as the harness hands it, with the door's answer; the transcript's path
it is handed names no file. Every index is made by hand in memory (see tests/test_refused.py), from label pages the
server writes, with made-up ids and a made-up word; every home is a temporary folder."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to  # noqa: E402
from test_refused import BRANCH, DROPPED, kept_home, served  # noqa: E402
from test_sample_join import b  # noqa: E402
from test_since import of  # noqa: E402
from test_store import at_terminal, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, hook, serve, store  # noqa: E402

MODEL = "m-test"  # the model of the session's own newest message, as the hand-made index holds it
SAID = (b(1), b(2), b(3), f"c0000004@s1@{MODEL}")  # three of the person's, and one of the session's, in session s1


def homes(tmp_path: Path) -> tuple[Path, Path]:
    folder, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    folder.mkdir()
    return folder, project


def after(project: Path, tool: str, given: dict, answer: str) -> str | None:
    """The hook after a call of the door's tool that the server answered, as the harness calls it for session s1:
    what it gives, None or its JSON."""
    event = {
        "hook_event_name": "PostToolUse",
        "tool_name": f"mcp__plugin_crossings_door__{tool}",
        "transcript_path": str(project.parent / "s1.jsonl"),  # names no file
        "cwd": str(project),
        "session_id": "s1",
        "tool_input": given,
        "tool_response": [{"type": "text", "text": answer}],
    }
    return hook.run(event)


def through(project: Path, tool: str, given: dict) -> tuple[str, str | None]:
    """A call of the door's tool through the server, and then the hook after it: the door's answer, and what the hook
    gives."""
    answer, failed = serve.call(tool, given)
    assert not failed and answer.startswith("marked "), answer
    return answer, after(project, tool, given, answer)


def signed_by(folder: Path, key: str) -> str:
    """The model `models.txt` names for a label, by its key alone; '' where it names none."""
    return next((model for (each, _), model in store.models(folder).items() if each == key), "")


def shows(key: str, whose: str, sentence: str) -> str:
    return json.dumps({"systemMessage": f"Crossings · marked {key} ({whose}): {sentence}"}, ensure_ascii=False)


def test_a_silencing_that_speaks_for_the_person_is_shown_as_a_work_label_that_does_and_the_sessions_own_is_not(
    tmp_path,
):
    folder, project = homes(tmp_path)
    put = "Put to rest by both: the tag is pushed by hand."
    with kept_home(folder, *SAID), served(folder, project):
        work = through(project, "mark", {"whose": "his", "sentence": "The wabe is the person's.", "anchors": [b(1)]})
        refused = through(project, "mark", {"kind": "refused", "sentence": BRANCH, "anchors": [b(1)]})
        # a refusal sent as the person's is written as the session's own, and so is never shown as theirs
        theirs = through(
            project, "mark", {"kind": "refused", "whose": "his", "sentence": "Not now.", "anchors": [b(2)]}
        )
        his = through(
            project, "mark", {"kind": "silenced", "whose": "his", "sentence": DROPPED, "anchors": ["X1", b(3)]}
        )
        both = through(project, "mark", {"kind": "silenced", "whose": "both", "sentence": put, "anchors": ["X2", b(3)]})
        through(project, "mark", {"kind": "refused", "sentence": "Nor that.", "anchors": [b(1)]})  # X3
        own = through(project, "mark", {"kind": "silenced", "sentence": "Pushed by hand.", "anchors": ["X3", b(3)]})
    assert work == ("marked W1", shows("W1", "theirs", "The wabe is the person's."))  # as a work label that does is
    assert his == ("marked S1", shows("S1", "theirs", DROPPED))
    assert both == ("marked S2", shows("S2", "both", put))
    assert refused == ("marked X1", None) and theirs == ("marked X2", None) and own == ("marked S3", None)


def test_the_hook_after_a_call_signs_a_label_of_every_kind_the_server_wrote_with_no_model_handed_over(tmp_path):
    folder, project = homes(tmp_path)
    calls = (
        ("mark", {"kind": "relation", "sentence": "The tove is the person's own.", "anchors": [b(1)]}),
        ("mark", {"sentence": "The wabe is mapped.", "anchors": [b(1)]}),
        ("leave", {"sentence": "Find out whether the tove is gyred.", "anchors": [b(1)]}),
        ("mark", {"kind": "refused", "sentence": BRANCH, "anchors": [b(2)]}),
        ("mark", {"kind": "silenced", "sentence": DROPPED, "anchors": ["X1", b(3)]}),
    )
    keys, before = [], {}
    with kept_home(folder, *SAID), served(folder, project):
        for tool, given in calls:
            answer, failed = serve.call(tool, given)
            assert not failed, answer
            key = answer.split()[1]
            before[key] = signed_by(folder, key)  # the server was handed no model: it signed nothing
            after(project, tool, given, answer)
            keys.append(key)
    assert keys == ["R1", "W1", "N1", "X1", "S1"] and {key[0] for key in keys} == set(store.KINDS)
    assert before == dict.fromkeys(keys, "")
    assert {key: signed_by(folder, key) for key in keys} == dict.fromkeys(keys, MODEL)


def test_a_line_the_person_is_shown_cut_at_160_ends_with_its_whole_length_and_one_not_cut_is_as_before(tmp_path):
    """Guard: the line the person is shown under the turn stopped at 160 characters with " […]" alone, so a label of
    2,140 characters looked to them like one of 200. Cut, it now ends with the whole length of the text as it is shown,
    after the mark of the cut, with a thousands comma; at 160 it is shown as before, byte for byte. So for every line
    the hook shows: a standing line, a label of the person's or of both, a silencing that speaks for the person, and a
    line left at the door."""
    folder, project = homes(tmp_path)

    def line(key: str, whose: str, text: str) -> str:  # as the hook writes it, for the person
        if key[0] == "N":
            return f"Crossings · left at the door: {text}"
        return f"Crossings · marked {key} ({whose}): {text}"

    with kept_home(folder, *SAID), served(folder, project):
        for n, length in enumerate((160, 2140), 1):
            refused = {"kind": "refused", "sentence": f"Not that, {n}.", "anchors": [b(1)]}
            refusal = through(project, "mark", refused)[0].split()[1]
            for tool, more, whose in (
                ("mark", {"kind": "relation"}, "session"),
                ("mark", {"whose": "his"}, "theirs"),
                ("mark", {"whose": "both"}, "both"),
                ("mark", {"kind": "silenced", "whose": "his", "anchors": [refusal, b(3)]}, "theirs"),
                ("leave", {}, ""),
            ):
                sentence = of(length)
                answer, out = through(project, tool, {"sentence": sentence, "anchors": [b(1)], **more})
                key = answer.split()[1].rstrip(".")
                text = sentence if length == 160 else f"{sentence[:160].rstrip()} […] (2,140 characters)"
                assert json.loads(out)["systemMessage"] == line(key, whose, text), (key, length)


def test_a_label_the_person_is_shown_is_said_long_from_160_as_the_person_sees_it_cut(tmp_path):
    """Guard: the person is shown a standing line and a label that speaks for them cut at 160 characters, and the
    session was told nothing below 240. Through the server the plugin started, whose hook after the call shows the
    line, such a label longer than 160 is answered with its length and that the person is shown 160 of one, and past
    240 also what a list shows and that a frame may have no room for it, as the person sees it cut. A work label of
    the session's own is answered from 240, as before; a refusal and a silencing with nothing; a line at the door from
    900. Where no hook shows the line (a server given alone to a harness without the plugin's hooks, a session's
    shell), the answer says nothing of what the person is shown."""
    folder, project = homes(tmp_path)
    shown = "This label is {} characters long: the person is shown 160 of one."
    listed = (
        "This label is {} characters long: the person is shown 160 of one, a list shows 240, and a frame may have no "
        "room for it."
    )
    own = "This label is {} characters long: a list shows 240 of one, and a frame may have no room for it."

    def mark(**given) -> tuple[str, str | None]:
        return through(project, "mark", {"anchors": [b(1)], **given})

    with kept_home(folder, *SAID), served(folder, project), set_to(CLAUDE_PLUGIN_ROOT=str(ROOT)):
        assert mark(kind="relation", sentence=of(160)) == ("marked R1", shows("R1", "session", of(160)))
        answer, out = mark(kind="relation", sentence=of(161))
        assert answer == "marked R2. " + shown.format("161")
        assert json.loads(out)["systemMessage"].endswith(" […] (161 characters)")  # the same moment, the same length
        assert mark(kind="relation", sentence=of(240))[0] == "marked R3. " + shown.format("240")
        assert mark(kind="relation", sentence=of(241))[0] == "marked R4. " + listed.format("241")
        assert mark(whose="his", sentence=of(212))[0] == "marked W1. " + shown.format("212")
        assert mark(whose="both", sentence=of(2500))[0] == "marked W2. " + listed.format("2,500")
        assert mark(sentence=of(241))[0] == "marked W3. " + own.format("241")  # the session's own: not shown
        assert mark(sentence=of(240)) == ("marked W4", None)
        assert mark(kind="refused", sentence=of(612)) == ("marked X1", None)
        answer, out = mark(kind="silenced", whose="his", sentence=of(612), anchors=["X1", b(3)])
        assert answer == "marked S1" and json.loads(out)["systemMessage"].endswith(" […] (612 characters)")
        assert through(project, "leave", {"sentence": of(612), "anchors": [b(1)]})[0].split("\n\n")[0] == "marked N1"
    with kept_home(folder, *SAID), served(folder, project):  # a server given alone to a harness: no hook shows it
        alone, _ = serve.call("mark", {"kind": "relation", "sentence": of(612), "anchors": [b(1)]})
        out = io.StringIO()
        with set_to(CLAUDE_PLUGIN_ROOT=str(ROOT)), at_terminal(False), contextlib.redirect_stdout(out):
            # a session's shell, as the plugin's own session would run it: no hook after it shows the person anything
            words = of(612).split()
            code = door.main(["mark", "--kind", "relation", "--anchors", b(1), "--bare", "--cwd", str(project), *words])
    assert alone == "marked R5. " + own.format("612")
    assert code == 0 and out.getvalue() == "marked R6. " + own.format("612") + "\n"
    assert store.SHOWN == 160 and not hasattr(hook, "SHOWN")  # one number, one home, read by the hook and the door


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
