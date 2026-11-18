"""The weighed and unmarked: the person's messages of a session's stretch since its last cut that the sampler
weighs and no label rests on, named by their ids alone in one sentence, in the answer of a line left at the door
through the server and in a cut's frame for the session that was cut. Every index is made by hand in memory (the
three tables of tests/sampler_schema.sql, rows inserted directly), from label pages written through `store.mark` or
by the server, with made-up ids and a made-up word; every home is a temporary folder."""

from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_refused import DAY, kept_home, served  # noqa: E402
from test_sample_join import DOOR, WABE, at_home, b, cut, index, pulls, quotes_in, said, standing_in  # noqa: E402
from test_store import sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, sample, serve, store  # noqa: E402
from crossing.sampler import core  # noqa: E402

# The sentence, word for word, in its two forms: many, and one.
MANY = "The record weighs these, and no label rests on them: {}; `thread` gives each in its place."
ONE = "The record weighs this one, and no label rests on it: {}; `thread` gives it in its place."
LINE = "Find out whether the tove is gyred."


def named(*ids: str) -> str:
    """The ids as the sentence names them, in this order."""
    return ", ".join(f"`{each}`" for each in ids)


def homes(tmp_path: Path) -> tuple[Path, Path]:
    folder, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    folder.mkdir()
    return folder, project


def leave(*anchors: str) -> tuple[str, bool]:
    """A line left at the door through the server, resting on these ids."""
    return serve.call("leave", {"sentence": LINE, "anchors": list(anchors)})


# --- in the answer of `leave` through the server ---------------------------------------------------------------------


def test_a_line_left_through_the_server_is_answered_with_the_unlabelled_in_the_cores_order_and_no_labelled_one(
    tmp_path,
):
    folder, project = homes(tmp_path)
    with kept_home(folder, *[b(k) for k in range(1, 7)]), served(folder, project):
        store.mark(folder, "work", "session", "The wabe is mapped.", [b(2)], day=DAY)  # W1: b2 is labelled
        pulls(folder, b(1), b(1), b(1))  # the oldest, reached for three times: it outweighs the newer ones
        text, failed = leave(b(6))  # N1: and b6 is labelled by the line itself
        crossed, _ = serve.call("crossing", {})
    # tail 15 and three pulls for b1 (21); then b5 (19), b4 (18), b3 (17), as the sampler ranks them
    told = MANY.format(named(b(1), b(5), b(4), b(3)))
    assert not failed and text == "marked N1\n\n" + told
    assert f"`{b(2)}`" not in text and f"`{b(6)}`" not in text
    assert told in crossed.split("\n\n")  # and the served `crossing` gives the frame that carries it


def test_with_none_unlabelled_the_answer_of_leave_is_as_before_and_a_mark_or_the_persons_own_line_says_nothing(
    tmp_path,
):
    folder, project = homes(tmp_path)
    with kept_home(folder, b(1), b(2)), served(folder, project):
        store.mark(folder, "work", "session", "The wabe is mapped.", [b(1)], day=DAY)
        assert leave(b(2)) == ("marked N1", False)
    with kept_home(folder, b(1), b(2), b(3)), served(folder, project):  # b3 is not labelled now
        marked, _ = serve.call("mark", {"sentence": "The borogove waits.", "anchors": [b(1)]})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):  # the person's own line at the door, from the command line
            code = door.main(["mark", "--kind", "next", f"--anchors={b(2)}", "--cwd", str(project), "--", LINE])
        through = leave(b(2))  # and the same line through the server, in the same home
    assert marked.startswith("marked W2") and "weighs" not in marked
    assert code == 0 and out.getvalue().startswith("marked N2") and "weighs" not in out.getvalue()
    assert through == ("marked N3\n\n" + ONE.format(named(b(3))), False)


def test_more_than_the_cap_names_exactly_the_cap_the_heaviest(tmp_path):
    folder, project = homes(tmp_path)
    with kept_home(folder, *[b(k) for k in range(1, 10)]), served(folder, project):
        pulls(folder, b(1), b(1), b(1))  # tail 12 and three pulls: 18, as b7's tail, and b7 is the newer
        text, _ = leave(b(9))
    assert sample.UNMARKED == 5
    assert text == "marked N1\n\n" + MANY.format(named(b(8), b(7), b(1), b(6), b(5)))


def test_one_alone_is_said_as_one_for_the_session_that_spoke_last(tmp_path):
    folder, project = homes(tmp_path)
    # s2 spoke last: its stretch is the one weighed, and s1's message, though no label rests on it, is not named
    with kept_home(folder, b(1), f"{b(2)}@s2", f"{b(3)}@s2"), served(folder, project):
        assert door.spoke_last(folder) == "s2"
        assert leave(b(3)) == ("marked N1\n\n" + ONE.format(named(b(2))), False)


def test_a_flagged_message_one_before_the_last_cut_one_of_another_session_and_the_sessions_own_are_never_named(
    tmp_path,
):
    folder, project = homes(tmp_path)
    given = (b(1), b(2), f"{b(7)}@s2", b(3), "c0000001@s1@m-test", b(4), b(5))
    with kept_home(folder, *given), served(folder, project), standing_in(store, "flagged", lambda *a, **k: [b(3)]):
        cut(folder, "s1", 1, b(2))  # the session's last cut came after b2
        assert leave(b(5)) == ("marked N1\n\n" + ONE.format(named(b(4))), False)


def test_once_a_label_rests_on_a_named_message_the_next_leave_no_longer_names_it(tmp_path):
    folder, project = homes(tmp_path)
    with kept_home(folder, b(1), b(2), b(3), b(4)), served(folder, project):
        assert leave(b(4)) == ("marked N1\n\n" + MANY.format(named(b(3), b(2), b(1))), False)
        assert serve.call("mark", {"sentence": "The wabe is mapped.", "anchors": [b(3)]})[0].startswith("marked W1")
        assert leave(b(4)) == ("marked N2\n\n" + MANY.format(named(b(2), b(1))), False)
        serve.call("mark", {"sentence": "The borogove waits.", "anchors": [b(2)]})
        assert leave(b(4)) == ("marked N3\n\n" + ONE.format(named(b(1))), False)
        serve.call("mark", {"kind": "refused", "sentence": "Not done: the person said to wait.", "anchors": [b(1)]})
        assert leave(b(4)) == ("marked N4", False)  # a label of any kind is a label


# --- what the sampler weighs, and what the sentence holds ------------------------------------------------------------


def test_a_message_the_sampler_weighs_under_its_least_score_is_not_named_until_it_is_reached_for(tmp_path):
    # 22 of the person's, a label on every one but the oldest: its distance from the end, 21, is past the tail's span
    rows = [said(k, b(k)) for k in range(1, 23)]
    db = index(*rows, labels=(("W1", "work"),), anchors=tuple(("W1", b(k)) for k in range(2, 23)))
    assert core.SEEDS["tail_span"] == 20 and core.SEEDS["min_score"] == 1
    assert sample.unmarked(tmp_path, db, "s1", set()) == ""
    pulls(tmp_path, b(1))  # reached for once: weighed 2
    assert sample.unmarked(tmp_path, db, "s1", set()) == ONE.format(named(b(1)))
    assert sample.unmarked(tmp_path, db, "", set()) == ""  # for no session named, nothing is said


def test_the_sentence_holds_no_text_of_any_message_only_ids(tmp_path):
    texts = ("the borogove is mimsy", "outgrabe in the wabe", "a frumious word")
    db = index(*[said(k, b(k), text=text) for k, text in enumerate(texts, 1)])
    told = sample.unmarked(tmp_path, db, "s1", set())
    assert told == MANY.format(named(b(3), b(2), b(1)))
    assert not [word for text in texts for word in text.split() if len(word) > 3 and word in told]
    # with its ids taken out, what is left is the sentence's own words
    assert re.sub(r"`b\d{7}`", "", told) == MANY.format(", , ")


# --- in a cut's frame for the session that was cut -----------------------------------------------------------------


def test_a_cuts_frame_for_the_named_session_carries_the_sentence_and_a_new_or_unnamed_ones_frame_does_not(tmp_path):
    with at_home(tmp_path, (b(1), b(2), b(3)), (DOOR, WABE), (("N1", b(3)), ("W1", b(3)))):
        made = frame.compose(tmp_path, 9000, session="s1")
        unnamed = frame.compose(tmp_path, 9000)
        started = frame.compose(tmp_path, 9000, new=True, session="s1")
        without = frame.compose(tmp_path, 9000, session="s2")  # a session with no message in the home
    told = MANY.format(named(b(2), b(1)))
    paragraphs = made.split("\n\n")
    assert paragraphs[-2] == told and paragraphs[-1].startswith("The store holds ")  # near the end, before the store
    assert made.count("weighs") == 1
    for each in (unnamed, started, without):
        assert "weighs" not in each


def fuller_at_home(folder: Path):
    """The full home of tests/test_sample_join.py (eight standing lines, eight work rows each on one of eight quoted
    sentences, and a long line at the door on all eight), and seven newer messages of the person's no label rests on."""
    ids = tuple(b(n) for n in range(1, 9))
    labels = tuple((f"R{n}", "relation", ("The tove is the person's own. " * 20).strip()) for n in range(1, 9))
    labels += tuple((f"W{n}", "work", ("The wabe is mapped. " * 45).strip()) for n in range(1, 9))
    labels += (("N1", "next", ("Find out whether the tove is gyred. " * 78).strip()),)
    anchors = tuple((f"R{n}", b(1)) for n in range(1, 9)) + tuple((f"W{n}", ids[n - 1]) for n in range(1, 9))
    extra = tuple(b(n) for n in range(9, 16))
    return at_home(folder, ids + extra, labels, anchors + tuple(("N1", each) for each in ids))


MORE = re.compile(r"\d+ more labels? in the store: `labels` lists them\.")


def test_over_every_size_the_cuts_frame_is_within_it_and_carries_the_sentence_whole_or_not_at_all(tmp_path):
    told = MANY.format(named(b(15), b(14), b(13), b(12), b(11)))
    seen = set()
    with fuller_at_home(tmp_path):
        for size in range(frame.LEAST, frame.MOST + 1, 25):
            made = frame.compose(tmp_path, size, session="s1")
            assert len(made) <= frame.bounded(size), size
            assert (frame.PACKED_HEAD in made) == bool(quotes_in(made)), size
            paragraphs = made.split("\n\n")
            assert ("weighs" in made) == (told in paragraphs), size  # whole, or not at all
            if told in paragraphs:
                at = paragraphs.index(told)
                assert MORE.fullmatch(paragraphs[at - 1]) or not any(map(MORE.fullmatch, paragraphs)), size
            else:  # left out, the frame is the one the home gives with no message named
                with standing_in(frame, "unmarked", lambda *args, **kwargs: ""):
                    assert made == frame.compose(tmp_path, size, session="s1"), size
            seen.add(told in paragraphs)
        assert told in frame.compose(tmp_path, frame.SIZE, session="s1").split("\n\n")
        assert told in frame.compose(tmp_path, frame.MOST, session="s1").split("\n\n")
    assert seen == {True, False}


def test_at_a_size_too_small_for_the_sentence_it_is_absent_and_the_frame_is_within_its_size(tmp_path):
    told = MANY.format(named(b(15), b(14), b(13), b(12), b(11)))
    with fuller_at_home(tmp_path):
        made = frame.compose(tmp_path, frame.LEAST, session="s1")
        with standing_in(frame, "unmarked", lambda *args, **kwargs: ""):
            unnamed = frame.compose(tmp_path, frame.LEAST, session="s1")
    assert "weighs" not in made and len(made) <= frame.LEAST and made == unnamed
    # beside what the frame carries at the least, it does not fit
    assert len(unnamed) + len("\n\n" + told) > frame.LEAST


# --- where the stretch since the last cut begins ---------------------------------------------------------------------


def test_where_the_newest_cut_names_only_ids_the_index_no_longer_holds_its_stretch_is_not_known_and_none_is_named(
    tmp_path,
):
    # b1 stood before the first cut and b3 before the second; the person struck b3, the one the newest cut points at,
    # so the index no longer holds it: the stretch since that cut cannot be placed, and b2, said before it, is not named
    folder, project = homes(tmp_path)
    cut(folder, "s1", 1, b(1))
    cut(folder, "s1", 2, b(3))
    struck = (b(1), b(2), b(4), b(5))
    db = index(*[said(k, each) for k, each in enumerate(struck, 1)])
    # what the sampler is handed
    assert [row["id"] for row in sample.stretch(folder, db, "s1", 400)] == [b(2), b(4), b(5)]
    assert sample.unmarked(folder, db, "s1", set()) == ""
    with kept_home(folder, *struck), served(folder, project):
        assert leave(b(5)) == ("marked N1", False)
    with at_home(folder, struck, (DOOR,), (("N1", b(5)),)):
        assert "weighs" not in frame.compose(folder, 9000, session="s1")
    # where the newest cut names one id the index still holds beside the one struck, its stretch is known again
    cut(folder, "s1", 2, b(3), b(2))
    assert sample.unmarked(folder, db, "s1", set()) == MANY.format(named(b(5), b(4)))
    # and a newer cut whose record names no id at all cannot be placed either
    cut(folder, "s1", 3)
    assert sample.unmarked(folder, db, "s1", set()) == ""


def test_an_ordinary_cut_still_begins_the_stretch_the_newest_by_its_number_and_one_with_no_readable_record_passed_over(
    tmp_path,
):
    folder, project = homes(tmp_path)
    cut(folder, "s1", 9, "c0000009")  # an older cut, whose one id is gone
    cut(folder, "s1", 10, b(3))  # the newest by its number, though not by its name's letters: b3 is held
    store.within(folder, "s1-cut-11.json").write_text("{ cut short", encoding="utf-8")  # no record that can be read
    store.within(folder, "s1-cut-12.json").write_text("[1, 2]", encoding="utf-8")  # nor one that is a record
    held = (b(1), b(2), b(3), b(4), b(5))
    db = index(*[said(k, each) for k, each in enumerate(held, 1)])
    assert sample.unmarked(folder, db, "s1", set()) == MANY.format(named(b(5), b(4)))
    with kept_home(folder, *held), served(folder, project):
        assert leave(b(5)) == ("marked N1\n\n" + ONE.format(named(b(4))), False)
    with at_home(folder, held, (DOOR,), (("N1", b(5)),)):
        assert ONE.format(named(b(4))) in frame.compose(folder, 9000, session="s1").split("\n\n")
    # and where the session has no recorded cut, from the window fixed in the sampler on, as before
    assert sample.unmarked(folder, db, "s2", set()) == ""  # a session with no message in the index
    others = index(*[said(k, each, session="s3") for k, each in enumerate(held, 1)])
    assert sample.unmarked(folder, others, "s3", set()) == MANY.format(named(*reversed(held)))


def test_a_cuts_frame_names_the_stretch_that_cut_ended_whether_or_not_the_cuts_own_record_is_written_yet(tmp_path):
    # The count of a cut and the frame for it are two hooks, and either may finish first. The cut's own record names
    # every message that stood before it, the last one too: read as the start of the stretch, it leaves none.
    folder, project = homes(tmp_path)
    cut(folder, "s1", 1, b(1))  # the cut before: b1 stood before it
    held = (b(1), b(2), b(3), b(4))
    told = MANY.format(named(b(3), b(2)))
    with at_home(folder, held, (DOOR,), (("N1", b(4)),)):
        before = frame.compose(folder, 9000, session="s1")  # the frame first
        cut(folder, "s1", 2, *held)  # then the record of the cut it crosses
        after = frame.compose(folder, 9000, session="s1")  # or the record first
    assert told in before.split("\n\n")
    assert told in after.split("\n\n")
    # so too in the answer of a line left before the person has said anything since
    db = index(*[said(k, each) for k, each in enumerate(held, 1)])
    assert sample.unmarked(folder, db, "s1", set()) == MANY.format(named(b(4), b(3), b(2)))
    # once the person has spoken after the cut, the stretch is the one since it, and what stood before is not named
    later = index(*[said(k, each) for k, each in enumerate((*held, b(5)), 1)])
    assert sample.unmarked(folder, later, "s1", set()) == ONE.format(named(b(5)))
    # the session's own voice after the cut is not the person's: the stretch is still the one the cut ended
    woken = index(*[said(k, each) for k, each in enumerate(held, 1)], said(5, b(5), voice="session"))
    assert sample.unmarked(folder, woken, "s1", set()) == MANY.format(named(b(4), b(3), b(2)))


def test_the_stretch_a_recorded_cut_ended_is_not_named_where_the_cut_before_it_can_no_longer_be_placed(tmp_path):
    # b1 stood before the first cut and was struck since; the second cut is on record and nothing was said after it.
    # The stretch it ended began after the first cut, which names nothing the index holds: its start is not known.
    folder, project = homes(tmp_path)
    cut(folder, "s1", 1, b(1))
    left = (b(2), b(3), b(4))
    cut(folder, "s1", 2, *left)
    db = index(*[said(k, each) for k, each in enumerate(left, 1)])
    assert sample.unmarked(folder, db, "s1", set()) == ""
    # a session's first cut, on record with nothing said since: the stretch it ended is placed by the sampler's window,
    # as it was before the record was written
    cut(folder, "s9", 1, *left)
    first = index(*[said(k, each, session="s9") for k, each in enumerate(left, 1)])
    assert sample.unmarked(folder, first, "s9", set()) == MANY.format(named(b(4), b(3), b(2)))


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
