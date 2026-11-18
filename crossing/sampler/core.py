"""The sampler's arithmetic: events in, a ranked pick out.

One event is one message of the person's that a frame might carry: a plain dict of its id, the guard that
leaves it out where one does, whether it lies in the stretch (`in_stretch`), and whole numbers (`distance`,
`anchored`, `pulled`, and `length`, the room its entry takes in a frame, as the caller gives it). The core
reads no file, no store and no clock, quotes no word and calls no model, and nothing of how a person writes
(the time of a message, the length of its words) is read here: the score reads a session's own acts (its
labels, its reaches) and a position (the nearness to the cut). It gives back ids and whole numbers, and the
plugin says the rest.

  shape       for each event, three whole numbers (FEATURES), each from its measures and the settings
  score       the weights times the features, summed
  pick        ranked by score, then the newer first, then by id; the messages the line at the door rests on
              (`first`) are taken by rule first, up to `door_most` of them and whatever their score, then
              the rest by rank; an event a guard leaves out is never taken, and by rank neither is one under
              `min_score` or one outside the stretch that no carried label rests on; each is taken while the
              room lasts, as the frame's own rule takes them

Every value that decides is a setting (SETTINGS), every score is a whole number, and nothing here holds a
floating point: the same events and the same settings give the same pick on every machine.
"""

from __future__ import annotations

FEATURES = ("anchored", "pulled", "tail")  # in the order `shape` gives them
# Every value that decides how the sampler weighs the person's messages and which it takes: its seed, and what
# it does. The values are fixed here: a home holds no file of settings, and the person has no command for them.
# They are heuristics: chosen by hand from one home's use, and tried and changed outside this repository before
# they are fixed here. None is derived, and no measurement of them is reported.
SETTINGS = {
    "w_anchored": (3, "the weight of anchored: how many carried work labels and door lines rest on the message"),
    "w_pulled": (2, "the weight of pulled: how often the log of pulls names the message"),
    "w_tail": (1, "the weight of tail: how near the message stands to the end of the person's messages"),
    "anchored_cap": (3, "the most anchored counts"),
    "pulled_cap": (3, "the most pulled counts"),
    "tail_span": (20, "how far back tail reaches: the newest message counts this much, and each before it one less"),
    "min_score": (1, "the least score a message is carried with by rank"),
    "door_most": (6, "how many of the messages the line at the door rests on may cross by rule"),
    "window": (400, "the person's newest messages scored where no cut of the session is recorded"),
}
SEEDS = {name: seed for name, (seed, _) in SETTINGS.items()}


# --- the shape of each message, its score, and the pick ---------------------------------------------------


def shape(event: dict, settings: dict[str, int]) -> dict[str, int]:
    """An event's features, from its measures and the settings: each a whole number.

    anchored  how many carried work labels and door lines rest on it, to `anchored_cap`
    pulled    how often the log of pulls names it, to `pulled_cap`
    tail      `tail_span` less its distance from the end in the person's messages, not below nought

    A message outside the stretch has no place in it: its tail is nought, and its anchored and pulled are as
    for any other."""
    return {
        "anchored": min(event["anchored"], settings["anchored_cap"]),
        "pulled": min(event["pulled"], settings["pulled_cap"]),
        "tail": max(0, settings["tail_span"] - event["distance"]) if event["in_stretch"] else 0,
    }


def score(features: dict[str, int], settings: dict[str, int]) -> int:
    """The weights times the features, summed."""
    return sum(settings[f"w_{name}"] * features[name] for name in FEATURES)


def _age(each: dict) -> tuple[int, int]:
    """Where an event stands from the end, the newer first: in the stretch by its distance; outside it, after
    every message of the stretch, since no distance of it is counted."""
    return (0, each["distance"]) if each["in_stretch"] else (1, 0)


def _takes(each: dict, settings: dict[str, int]) -> bool:
    """Whether the pick may take a ranked event by rank: no guard leaves it out, its score is `min_score` or
    more, and it lies in the stretch or a carried label rests on it."""
    return not each["guard"] and each["score"] >= settings["min_score"] and (each["in_stretch"] or each["anchored"] > 0)


def _by_rule(ranked: list[dict], first: list[str] | tuple[str, ...], settings: dict[str, int], room: int) -> int:
    """The taking by rule, before any score is asked: each id of `first`, in its order and once, up to
    `door_most` of them, is carried where an event bears it (the first in rank of those that do), no guard is
    on that event and it fits the room, whatever its score. An id no event bears, or a guarded one, is passed
    over and counts for nothing toward `door_most`; the first that does not fit ends the taking. Marks those
    taken in `ranked` and gives the room they took."""
    bearing: dict[str, dict] = {}
    for each in ranked:
        bearing.setdefault(each["id"], each)
    taken, ruled = 0, 0
    for said in dict.fromkeys(first):
        if ruled >= settings["door_most"]:
            break
        each = bearing.get(said)
        if each is None or each["guard"]:
            continue
        if taken + each["length"] > room:
            break
        each["carried"] = each["by_rule"] = True
        taken += each["length"] + 1
        ruled += 1
    return taken


def pick(events: list[dict], settings: dict[str, int], room: int, first: list[str] | tuple[str, ...] = ()) -> dict:
    """The events shaped and scored, then ranked by score, the higher first, then the newer (the nearer the
    end, every message of the stretch before any outside it), then by id. Then taken while the room lasts,
    each taking its `length` and one character more, in two turns. By rule first: the ids of `first`, the
    messages the line at the door rests on, as `_by_rule` takes them. Then by rank, in the room left and over
    what is not yet carried: an event a guard leaves out, one whose score is under `min_score`, or one outside
    the stretch that no carried label rests on, is not taken; the rest are taken in the order of their rank,
    and the first that does not fit ends it, as the frame's own rule ends. The ranks are the same whatever
    `first` holds. Gives every event with its features, its score, its rank, whether it is carried and whether
    by rule (`ranked`), the ids of those carried, the newest first, both kinds together (`carried`), the rank
    the taking by rank ended at (`ended`, nothing where it did not end) and the room."""
    weighed = []
    for event in events:
        features = shape(event, settings)
        weighed.append({**event, "features": features, "score": score(features, settings)})
    order = sorted(weighed, key=lambda each: (-each["score"], _age(each), each["id"]))
    ranked = [{**each, "rank": n, "carried": False, "by_rule": False} for n, each in enumerate(order, 1)]
    taken, ended = _by_rule(ranked, first, settings, room), None
    for each in ranked:
        if each["carried"] or not _takes(each, settings):
            continue
        if taken + each["length"] > room:
            ended = each["rank"]
            break
        each["carried"] = True
        taken += each["length"] + 1
    carried = [each["id"] for each in sorted((each for each in ranked if each["carried"]), key=_age)]
    return {"ranked": ranked, "carried": carried, "ended": ended, "room": room}
