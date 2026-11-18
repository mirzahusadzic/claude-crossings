"""The sampler's rules, held over made-up events drawn by a fixed seed. The tests beside this one lay each case
out by hand, and so check what was thought of. Here the events are drawn, and what is checked is what a pick may
never do, whatever they are; the rules are written out again below, apart from the code, and the two are held to
each other. The seed is fixed, so every run draws the same events. An event is ids and whole numbers alone, and a
made-up stretch holds one made-up word. Runs with or without pytest."""

from __future__ import annotations

import copy
import random
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_sample_join import cut, index, pulls, said  # noqa: E402
from test_store import sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import sample  # noqa: E402
from crossing.sampler import core  # noqa: E402

SEED = 4711
PICKS = 6000  # picks drawn, each over its own events, settings, room and ids to take by rule
STRETCHES = 300  # made-up stretches weighed through the plugin's own path
GUARDS = ("", "", "", "", "twin", "flagged", "standing")  # most messages have no guard on them
NAMED = 5  # the most the sentence names, written here apart from the code


def drawn(rng: random.Random, most: int = 40) -> list[dict]:
    """Up to `most` events, the oldest first: most of them in the stretch, each at its distance from the end
    there, with counts and a guard drawn."""
    inside = [rng.random() < 0.8 for _ in range(rng.randrange(most + 1))]
    events, met = [], 0
    for at, within in enumerate(inside):
        events.append(
            {
                "id": f"e{at:04d}",
                "in_stretch": within,
                "distance": sum(inside) - 1 - met if within else 0,
                "anchored": rng.randrange(6),
                "pulled": rng.randrange(7),
                "guard": rng.choice(GUARDS),
                "length": rng.randrange(301),
            }
        )
        met += within
    return events


def settings_drawn(rng: random.Random) -> dict[str, int]:
    """The seeds as they stand, half the time; else every value that decides drawn anew."""
    if rng.random() < 0.5:
        return dict(core.SEEDS)
    return {
        **core.SEEDS,
        "w_anchored": rng.randrange(5),
        "w_pulled": rng.randrange(5),
        "w_tail": rng.randrange(5),
        "anchored_cap": rng.randrange(5),
        "pulled_cap": rng.randrange(5),
        "tail_span": rng.randrange(31),
        "min_score": rng.randrange(6),
        "door_most": rng.randrange(9),
    }


def scored(each: dict, settings: dict[str, int]) -> int:
    """An event's score, written out apart from the code: the weights times what is counted, each count to its
    cap, and the nearness to the end for a message of the stretch alone."""
    tail = max(0, settings["tail_span"] - each["distance"]) if each["in_stretch"] else 0
    return (
        settings["w_anchored"] * min(each["anchored"], settings["anchored_cap"])
        + settings["w_pulled"] * min(each["pulled"], settings["pulled_cap"])
        + settings["w_tail"] * tail
    )


def place(each: dict, settings: dict[str, int]) -> tuple:
    """Where an event ranks: the heavier first, then the newer (a message of the stretch before any outside it),
    then by id."""
    return (-scored(each, settings), (0, each["distance"]) if each["in_stretch"] else (1, 0), each["id"])


def told_of(picked: dict) -> list[tuple]:
    return [(each["id"], each["rank"], each["score"], each["carried"], each["by_rule"]) for each in picked["ranked"]]


def test_over_drawn_events_a_pick_keeps_every_rule_of_its_own():
    rng = random.Random(SEED)
    for _ in range(PICKS):
        events, settings, room = drawn(rng), settings_drawn(rng), rng.randrange(2001)
        ids = [each["id"] for each in events]
        first = [rng.choice([*ids, "nobody"]) for _ in range(rng.randrange(10))]
        before = copy.deepcopy(events)
        picked = core.pick(events, settings, room, first)
        assert events == before  # the events handed over are left as they were
        ranked = picked["ranked"]
        # every event once, ranked from one on, in the order the rules give and by the score they give
        assert [each["id"] for each in ranked] == [
            each["id"] for each in sorted(events, key=lambda e: place(e, settings))
        ]
        assert [each["rank"] for each in ranked] == list(range(1, len(events) + 1))
        assert all(type(each["score"]) is int and each["score"] == scored(each, settings) for each in ranked)
        carried = [each for each in ranked if each["carried"]]
        assert not any(each["guard"] for each in carried)  # a guard leaves a message out, however heavy it is
        ruled = [each for each in ranked if each["by_rule"]]
        assert all(each["carried"] and each["id"] in first for each in ruled) and len(ruled) <= settings["door_most"]
        for each in carried:  # by rank, only what weighs enough and lies in the stretch or under a carried label
            if not each["by_rule"]:
                assert each["score"] >= settings["min_score"] and (each["in_stretch"] or each["anchored"] > 0)
        assert sum(each["length"] + 1 for each in carried) <= room + 1  # each fitted the room as it was taken
        assert sorted(picked["carried"]) == sorted(each["id"] for each in carried)
        # the order the events are handed in decides nothing
        mixed = events[:]
        rng.shuffle(mixed)
        assert told_of(core.pick(mixed, settings, room, first)) == told_of(picked)
        # and what is taken by rule first changes no rank and no score
        plain = core.pick(events, settings, room)
        assert [each[:3] for each in told_of(plain)] == [each[:3] for each in told_of(picked)]


def weighed(name: str, stretch: list[str], reached: list[str]) -> int:
    """What an unlabelled message of a stretch weighs, written out apart from the code: its reaches through the
    door, to their cap, and its nearness to the end of the stretch."""
    seeds = core.SEEDS
    distance = len(stretch) - 1 - stretch.index(name)
    return seeds["w_pulled"] * min(reached.count(name), seeds["pulled_cap"]) + seeds["w_tail"] * max(
        0, seeds["tail_span"] - distance
    )


def test_over_drawn_stretches_the_sentence_names_the_five_the_rules_give_and_never_what_it_must_not(tmp_path):
    rng = random.Random(SEED + 1)
    for round_ in range(STRETCHES):
        folder = tmp_path / f"home-{round_}"
        folder.mkdir()
        rows = [
            said(seq, f"{'b' if voice == 'his' else 'c'}{seq:07d}", voice=voice)
            for seq in range(1, rng.randrange(1, 60) + 1)
            for voice in [rng.choice(("his", "his", "his", "session", "session"))]
        ]
        his = [name for _, name, voice, _, _ in rows if voice == "his"]
        stretch = his
        if rng.random() < 0.7:  # a cut on record, which names every message up to somewhere in the session
            at = rng.randrange(len(rows))
            cut(folder, "s1", 1, *[name for _, name, _, _, _ in rows[: at + 1]])
            since = [name for _, name, voice, _, _ in rows[at + 1 :] if voice == "his"]
            stretch = since or his  # nothing of the person's since: the stretch is the one that cut ended
        labelled = set(rng.sample(his, rng.randrange(len(his) + 1)))
        flagged = set(rng.sample(his, rng.randrange(min(3, len(his)) + 1)))
        reached = [rng.choice(his) for _ in range(rng.randrange(8))] if his else []
        pulls(folder, *reached)
        keys = {name: f"W{k}" for k, name in enumerate(sorted(labelled), 1)}
        db = index(
            *rows,
            labels=tuple((key, "work") for key in keys.values()),
            anchors=tuple((key, name) for name, key in keys.items()),
        )
        told = sample.unmarked(folder, db, "s1", flagged)
        named = re.findall(r"`([bc]\d{7})`", told)

        free = [name for name in stretch if name not in labelled and name not in flagged]
        weights = {name: weighed(name, stretch, reached) for name in free}
        heavy = sorted(
            (name for name in free if weights[name] >= core.SEEDS["min_score"]),
            key=lambda name: (-weights[name], len(stretch) - stretch.index(name), name),
        )
        assert named == heavy[:NAMED], (round_, named, heavy)
        assert bool(told) == bool(heavy)  # said only where there is one to name
        assert not set(named) & (labelled | flagged) and set(named) <= set(stretch)  # and never what it must not


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
