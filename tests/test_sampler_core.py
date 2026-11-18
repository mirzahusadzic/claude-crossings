"""The core's arithmetic, over event dicts alone: made-up ids and whole numbers. Runs with or without pytest."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing.sampler import core

SEEDS = core.SEEDS
# Scores by anchored and pulled alone, so that ranks and ties can be laid out by hand.
BARE = {**SEEDS, "w_tail": 0}
GONE = ("w_pause", "w_short", "pause_seconds", "short_chars")  # the settings of the two features taken out


def event(name: str, **given) -> dict:
    """An event at the end of the stretch with nothing on it: unanchored, unpulled, unguarded."""
    made = {"id": name, "in_stretch": True, "distance": 0, "anchored": 0, "pulled": 0, "guard": "", "length": 10}
    made.update(given)
    return made


def features(settings: dict | None = None, **given) -> dict:
    return core.shape(event("e1", **given), settings or SEEDS)


def ranks(picked: dict) -> list:
    return [(each["id"], each["score"], each["carried"]) for each in picked["ranked"]]


def places(picked: dict) -> list:
    """Each ranked event's id, rank and score: what `first` never changes."""
    return [(each["id"], each["rank"], each["score"]) for each in picked["ranked"]]


def ruled(picked: dict) -> list:
    """The ids carried by rule, in the order of their rank."""
    return [each["id"] for each in picked["ranked"] if each["by_rule"]]


def by_hand() -> list[dict]:
    """A stretch of five, its ranks laid out by hand under the seeds."""
    return [
        event("m1", distance=4),  # tail 16: 16
        event("m2", distance=3, anchored=1),  # anchored 3, tail 17: 20
        event("m3", distance=2, pulled=2),  # pulled 4, tail 18: 22
        event("m4", distance=1),  # tail 19: 19
        event("m5", distance=0),  # tail 20: 20
    ]


# --- the tables -------------------------------------------------------------------------------------------


def test_the_tables():
    assert core.FEATURES == ("anchored", "pulled", "tail")
    assert core.SEEDS == {name: seed for name, (seed, _) in core.SETTINGS.items()}
    for name, (seed, what) in core.SETTINGS.items():
        assert type(seed) is int and seed >= 0, name
        assert what and "\n" not in what, name
    assert {name for name in core.SETTINGS if name.startswith("w_")} == {f"w_{name}" for name in core.FEATURES}
    assert not set(GONE) & set(core.SETTINGS)


# --- each feature at its cap and its edges ----------------------------------------------------------------


def test_the_shape_is_three_features_and_reads_nothing_of_how_a_message_is_written():
    assert list(features()) == list(core.FEATURES)
    # an event that still holds the measures of the two features taken out is shaped as one that does not
    plain = event("w1", distance=3, anchored=1, pulled=1)
    old = {**plain, "seconds": 86400, "opens": True, "chars": 0}
    assert core.shape(old, SEEDS) == core.shape(plain, SEEDS) == {"anchored": 1, "pulled": 1, "tail": 17}


def test_anchored_counts_to_its_cap():
    for raw, want in ((0, 0), (1, 1), (3, 3), (4, 3), (9, 3)):
        assert features(anchored=raw)["anchored"] == want, raw
    assert features({**SEEDS, "anchored_cap": 1}, anchored=2)["anchored"] == 1
    assert features({**SEEDS, "anchored_cap": 0}, anchored=2)["anchored"] == 0


def test_pulled_counts_to_its_cap():
    for raw, want in ((0, 0), (1, 1), (3, 3), (4, 3), (9, 3)):
        assert features(pulled=raw)["pulled"] == want, raw
    assert features({**SEEDS, "pulled_cap": 5}, pulled=9)["pulled"] == 5
    assert features({**SEEDS, "pulled_cap": 0}, pulled=2)["pulled"] == 0


def test_tail_counts_down_from_the_end():
    for distance, want in ((0, 20), (1, 19), (19, 1), (20, 0), (21, 0), (400, 0)):
        assert features(distance=distance)["tail"] == want, distance
    assert features({**SEEDS, "tail_span": 5}, distance=2)["tail"] == 3
    assert features({**SEEDS, "tail_span": 0}, distance=0)["tail"] == 0


def test_the_score_is_the_weights_times_the_features():
    shaped = {"anchored": 2, "pulled": 1, "tail": 5}
    assert core.score(shaped, SEEDS) == 13  # 3*2 + 2*1 + 1*5
    weights = {**SEEDS, "w_anchored": 0, "w_pulled": 10, "w_tail": 7}
    assert core.score(shaped, weights) == 45
    assert core.score(dict.fromkeys(core.FEATURES, 0), SEEDS) == 0
    assert type(core.score(shaped, SEEDS)) is int


# --- a message outside the stretch -------------------------------------------------------------------------


def test_a_message_outside_the_stretch_has_no_tail():
    outside = event("o1", in_stretch=False, anchored=2, pulled=1)
    assert core.shape(outside, SEEDS) == {"anchored": 2, "pulled": 1, "tail": 0}
    inside = {**outside, "in_stretch": True}
    assert core.shape(inside, SEEDS) == {"anchored": 2, "pulled": 1, "tail": 20}


def test_a_message_outside_the_stretch_with_a_label_is_ranked_by_the_rest():
    events = [
        event("s1", distance=6),  # tail 14
        event("s2", distance=3),  # tail 17
        # anchored and pulled alone: 3*3 + 2*3 = 15, where its distance would have given 20 more
        event("o1", in_stretch=False, anchored=3, pulled=3),
        event("s3", distance=0),  # tail 20
    ]
    picked = core.pick(events, SEEDS, 1000)
    assert ranks(picked) == [("s3", 20, True), ("s2", 17, True), ("o1", 15, True), ("s1", 14, True)]
    assert picked["carried"] == ["s3", "s2", "s1", "o1"]


def test_a_message_outside_the_stretch_with_no_label_is_never_taken_by_rank():
    events = [
        event("o1", in_stretch=False, pulled=3, length=500),  # 2*3 = 6
        event("o2", in_stretch=False, pulled=3, anchored=1),  # 3 + 2*3 = 9
        event("s1", distance=19),  # tail 1
    ]
    picked = core.pick(events, SEEDS, 100)
    assert ranks(picked) == [("o2", 9, True), ("o1", 6, False), ("s1", 1, True)]
    assert picked["ended"] is None  # passed over, as a guard is, its length ends nothing
    assert picked["carried"] == ["s1", "o2"]


# --- the rank, the ties and the room ------------------------------------------------------------------------


def test_a_stretch_ranked_by_hand():
    events = by_hand()
    picked = core.pick(events, SEEDS, 1000)
    # m5 and m2 tie at 20, and the newer goes first
    assert places(picked) == [("m3", 1, 22), ("m5", 2, 20), ("m2", 3, 20), ("m4", 4, 19), ("m1", 5, 16)]
    assert picked["ranked"][0]["features"] == {"anchored": 0, "pulled": 2, "tail": 18}
    assert picked["carried"] == ["m5", "m4", "m3", "m2", "m1"]
    assert picked["ended"] is None and picked["room"] == 1000
    above = core.pick(events, {**SEEDS, "min_score": 20}, 1000)
    assert [each["carried"] for each in above["ranked"]] == [True, True, True, False, False]
    assert above["carried"] == ["m5", "m3", "m2"]
    assert core.pick(events, {**SEEDS, "min_score": 22}, 1000)["carried"] == ["m3"]
    assert core.pick(events, {**SEEDS, "min_score": 23}, 1000)["carried"] == []


def test_ties_go_to_the_newer_then_to_the_id():
    events = [  # every one scores 3, laid out in no order the rank keeps
        event("a2", in_stretch=False, anchored=1),
        event("y2", distance=2, anchored=1),
        event("x9", distance=7, anchored=1),
        event("a1", in_stretch=False, anchored=1),
        event("y1", distance=2, anchored=1),
    ]
    picked = core.pick(events, BARE, 1000)
    # the nearer the end first, every message of the stretch before any outside it, and then by id
    assert [each["id"] for each in picked["ranked"]] == ["y1", "y2", "x9", "a1", "a2"]
    assert {each["score"] for each in picked["ranked"]} == {3}
    assert picked["carried"] == ["y1", "y2", "x9", "a1", "a2"]


def test_the_room_ends_at_the_first_that_does_not_fit():
    events = [
        event("e1", distance=3, anchored=3, length=10),  # 9
        event("e2", distance=1, anchored=2, length=10),  # 6
        event("e3", distance=2, anchored=1, length=30),  # 3
        event("e4", distance=0, pulled=1, length=1),  # 2
    ]
    # each takes its length and one more: 11, then 22; 22 + 30 is past 50, and e4 is not taken though it fits
    short = core.pick(events, BARE, 50)
    assert [each["carried"] for each in short["ranked"]] == [True, True, False, False]
    assert short["ended"] == 3 and short["carried"] == ["e2", "e1"]
    exact = core.pick(events, BARE, 52)  # e3 fits to the character; then 53 + 1 is past 52
    assert exact["ended"] == 4 and exact["carried"] == ["e2", "e3", "e1"]
    whole = core.pick(events, BARE, 54)
    assert whole["ended"] is None and whole["carried"] == ["e4", "e2", "e3", "e1"]
    none = core.pick(events, BARE, 9)
    assert none["ended"] == 1 and none["carried"] == []


def test_a_guard_or_a_low_score_is_passed_over_and_ends_nothing():
    events = [
        event("g1", guard="twin", anchored=3, length=999),
        event("g2", guard="flagged", anchored=3, length=999),
        event("g3", guard="standing", anchored=3, length=999),
        event("k1", anchored=1),
        event("l1", length=999),
    ]
    picked = core.pick(events, BARE, 20)
    assert ranks(picked) == [("g1", 9, False), ("g2", 9, False), ("g3", 9, False), ("k1", 3, True), ("l1", 0, False)]
    assert picked["ended"] is None and picked["carried"] == ["k1"]
    nought = core.pick(events, {**BARE, "min_score": 0}, 20)  # l1 is taken up now, and does not fit
    assert nought["ended"] == 5 and nought["carried"] == ["k1"]


def test_the_pick_leaves_the_events_as_they_were():
    events = [event("p1", anchored=1, n=7), event("p2")]
    kept = copy.deepcopy(events)
    first = ["p2"]
    picked = core.pick(events, SEEDS, 5, first)
    assert events == kept and first == ["p2"]
    assert picked["ranked"][0]["n"] == 7  # what else an event holds goes through to its rank


# --- the carry by rule ----------------------------------------------------------------------------------------


def test_first_empty_gives_the_pick_as_it_was():
    events = by_hand()
    for room in (1000, 25, 9):
        bare = core.pick(events, SEEDS, room)
        assert core.pick(events, SEEDS, room, ()) == core.pick(events, SEEDS, room, []) == bare
        assert [each["by_rule"] for each in bare["ranked"]] == [False] * 5
    tight = core.pick(events, SEEDS, 25)  # room for two
    assert tight["carried"] == ["m5", "m3"] and tight["ended"] == 3
    # with `first` the ranks stand as they were, and the room goes to the two by rule
    door = core.pick(events, SEEDS, 25, ["m1", "m4"])
    assert places(door) == places(tight)
    assert ruled(door) == ["m4", "m1"] and door["carried"] == ["m4", "m1"] and door["ended"] == 1


def test_an_id_by_rule_is_carried_though_its_score_is_under_min_score():
    events = [event("a1", distance=30), event("a2", distance=0), event("o1", in_stretch=False)]  # 0, 20, 0
    bare = core.pick(events, SEEDS, 1000)
    assert ranks(bare) == [("a2", 20, True), ("a1", 0, False), ("o1", 0, False)] and bare["carried"] == ["a2"]
    door = core.pick(events, SEEDS, 1000, ["a1"])
    assert places(door) == places(bare)
    assert ranks(door) == [("a2", 20, True), ("a1", 0, True), ("o1", 0, False)]
    assert [(each["id"], each["by_rule"]) for each in door["ranked"]] == [("a2", False), ("a1", True), ("o1", False)]
    assert door["carried"] == ["a2", "a1"]  # the newer first, both kinds together
    high = core.pick(events, {**SEEDS, "min_score": 50}, 1000, ["a1", "o1"])
    # whatever its score: and the rule asks no more than the id, the guard and the room, so o1, outside the
    # stretch with no label on it, is carried by rule too
    assert high["carried"] == ["a1", "o1"] and ruled(high) == ["a1", "o1"]


def test_an_id_by_rule_is_carried_though_it_ranks_last_in_a_room_for_one():
    events = [
        event("b1", distance=0),  # 20
        event("b2", distance=1),  # 19
        event("b3", distance=2, anchored=1),  # 21
        event("b9", distance=10),  # 10
    ]
    bare = core.pick(events, SEEDS, 10)
    assert bare["carried"] == ["b3"] and bare["ended"] == 2
    door = core.pick(events, SEEDS, 10, ["b9"])
    assert places(door) == places(bare) and door["ranked"][-1]["id"] == "b9"
    assert door["carried"] == ["b9"] and ruled(door) == ["b9"]
    assert door["ended"] == 1  # by rank the first ends it: the room is gone


def test_a_guarded_id_is_not_carried_and_counts_for_nothing():
    events = [
        event("g1", guard="twin", distance=0),
        event("g2", guard="flagged", distance=1),
        event("g3", guard="standing", distance=2),
        event("k1", distance=30),  # 0
        event("k2", distance=31),  # 0
    ]
    door = core.pick(events, {**SEEDS, "door_most": 1}, 1000, ["g1", "g2", "g3", "k1", "k2"])
    assert ruled(door) == ["k1"] and door["carried"] == ["k1"]
    assert all(not each["carried"] for each in door["ranked"] if each["guard"])


def test_an_id_no_event_bears_is_passed_over_and_counts_for_nothing():
    events = [event("k1", distance=30), event("k2", distance=31)]  # 0 and 0
    door = core.pick(events, {**SEEDS, "door_most": 1}, 1000, ["zz", "k1", "k2"])
    assert ruled(door) == ["k1"] and door["carried"] == ["k1"]
    assert core.pick(events, SEEDS, 1000, ["zz"]) == core.pick(events, SEEDS, 1000)


def test_a_repeated_id_is_counted_once():
    events = [event("r1", distance=30), event("r2", distance=31)]  # 0 and 0, each 10 long
    # r1 takes 11 once; r2 fits to the character, and is the second of two
    door = core.pick(events, {**SEEDS, "door_most": 2}, 21, ["r1", "r1", "r2", "r1"])
    assert ruled(door) == ["r1", "r2"] and door["carried"] == ["r1", "r2"]


def test_door_most_holds_back_the_one_past_it():
    events = [
        event("d1", distance=30),  # 0
        event("d2", distance=31),  # 0
        event("d3", distance=0),  # 20
        event("d4", distance=32),  # 0
    ]
    two = {**SEEDS, "door_most": 2}
    # d3, held back, stands in the ranking like any other: its score carries it
    door = core.pick(events, two, 1000, ["d1", "d2", "d3"])
    assert ruled(door) == ["d1", "d2"]
    top = door["ranked"][0]
    assert (top["id"], top["carried"], top["by_rule"]) == ("d3", True, False)
    assert door["carried"] == ["d3", "d1", "d2"]  # the newer first, both kinds together
    # d4, held back, has a score under `min_score`, and is not carried
    held = core.pick(events, two, 1000, ["d1", "d2", "d4"])
    assert ruled(held) == ["d1", "d2"] and held["carried"] == ["d3", "d1", "d2"]
    # under the seeds six cross by rule, in the order `first` names them, and the seventh is held back
    seven = [event(f"s{n}", distance=30 + n) for n in range(1, 8)]  # each 0
    seeded = core.pick(seven, SEEDS, 1000, [f"s{n}" for n in range(7, 0, -1)])
    assert sorted(ruled(seeded)) == ["s2", "s3", "s4", "s5", "s6", "s7"] and seeded["carried"] == ruled(seeded)


def test_the_first_that_does_not_fit_ends_the_taking_by_rule():
    events = [
        event("s2", distance=0, length=5),  # 20
        event("big", distance=1, length=100),  # 19
        event("s1", distance=30, length=5),  # 0
    ]
    # big does not fit, and s1 after it is not taken by rule though it would fit; by rank s2, shorter, still is
    door = core.pick(events, SEEDS, 20, ["big", "s1"])
    assert ruled(door) == [] and door["carried"] == ["s2"] and door["ended"] == 2
    # s1 first is taken, then big ends the rule's taking, and by rank s2 is taken in the room left
    other = core.pick(events, SEEDS, 20, ["s1", "big"])
    assert ruled(other) == ["s1"] and other["carried"] == ["s2", "s1"] and other["ended"] == 2


def test_one_carried_by_rule_is_not_taken_again_by_rank():
    events = [event("x1", distance=0), event("y1", distance=1)]  # 20 and 19, each 10 long
    # x1 takes 11 by rule; by rank it is passed over, and y1 fits to the character in the room left
    door = core.pick(events, SEEDS, 21, ["x1"])
    assert ruled(door) == ["x1"] and door["carried"] == ["x1", "y1"] and door["ended"] is None


def test_where_two_events_bear_an_id_the_first_in_rank_is_taken_by_rule():
    events = [event("t1", distance=31), event("t1", distance=30)]  # each 0: the nearer the end ranks first
    door = core.pick(events, SEEDS, 1000, ["t1"])
    assert [(each["distance"], each["carried"], each["by_rule"]) for each in door["ranked"]] == [
        (30, True, True),
        (31, False, False),
    ]


# --- the settings -------------------------------------------------------------------------------------------


def test_door_most_in_the_seeds_and_a_value_over_it():
    assert SEEDS["door_most"] == 6
    events = [event("n1", distance=30), event("n2", distance=31)]  # 0 and 0
    assert ruled(core.pick(events, SEEDS, 1000, ["n2", "n1"])) == ["n1", "n2"]
    assert ruled(core.pick(events, {**SEEDS, "door_most": 1}, 1000, ["n2", "n1"])) == ["n2"]
    nought = {**SEEDS, "door_most": 0}
    none = core.pick(events, nought, 1000, ["n2", "n1"])
    assert ruled(none) == [] and none == core.pick(events, nought, 1000)


def _run() -> None:
    tests = [test for name, test in list(globals().items()) if name.startswith("test_") and callable(test)]
    for test in tests:
        test()
    print(f"{Path(__file__).name}: {len(tests)} tests passed")


if __name__ == "__main__":
    _run()
