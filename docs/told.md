# What a session is told

Everything Crossings can tell a session, in the order a session meets it: made by `scripts/told.py` from a made-up store, never by hand. Read it whole, as a session receives it, and ask of all of it together: what does it lean the model toward; how does it read on its words alone, without the intent that wrote it; which of it is scaffolding that can retire, and which a guard that must stay. Between two releases, `git diff` of this page is what a session is told now that it was not before.

## As a session starts: the door's server

### Its instructions, started by the plugin

````text
The door to what you and the person said in this project, kept word for word under ids, with the labels that rest on it. What is said is kept by itself, up to the moment you call: you never save it. Labels are not made by themselves: `mark` them as the work goes, and `leave` a line for the session that wakes after the next cut, since a cut can come unannounced. Lines can be stacked into fewer: `mark` a label that rests on them, and the frame then carries the one. The person is shown a line you leave, and a label about the two of you or one that speaks for them, as you write it. After a cut, reach here for what your context no longer holds: `look` shows the room and needs no word; `labels`, `find` and `thread` go on from there. Reach when the conversation calls for it, never to show that something is held. What the person told you in confidence is left alone until they bring it up; where you cannot tell whether something was said in confidence, treat it as if it was.
````

### Its instructions, given alone to another harness

````text
The door to what you and the person said in this project, kept word for word under ids, with the labels that rest on it. Nothing is archived here by itself: this harness has no hook that feeds the store, so it holds what was archived elsewhere. `mark` writes a label and `leave` a line for the session that comes next. After a cut, reach here for what your context no longer holds: `look` shows the room and needs no word; `labels`, `find` and `thread` go on from there. Reach when the conversation calls for it, never to show that something is held. What the person told you in confidence is left alone until they bring it up; where you cannot tell whether something was said in confidence, treat it as if it was.
````

### Its tools

- **look**: The room, with no word needed: the days, the kinds of label, the newest labels about the work, and the line left at the door. Start here after a cut.
  - `home`: This project's store (default), or the one on this computer.
- **labels**: The labels themselves, newest first: by kind, by day, or whole by id, a stack with the lines beneath it. With nothing named, the labels about the work.
  - `ids`: Label ids to give whole, as R3 or W12.
  - `kind`: Only that kind: relation (standing, about the two of you), work, or next (lines left at the door).
  - `day`: Only those of one day, as 2026-11-11.
  - `home`: This project's store (default), or the one on this computer.
- **find**: Words, to the messages and labels that hold them, each by its id. Word stems, `word*` and "a phrase" are taken; a miss names the nearest words that are there.
  - `words`: The words to look for: all of them, or failing that any.
  - `voice`: Only the person's messages, or only the session's.
  - `home`: This project's store (default), or the one on this computer.
- **thread**: A message in its place, by its id: what stood before and after it, and the labels resting there.
  - `id`: The id of a message, as find gives it.
  - `around`: How many messages before and after to show (default 2, at most 50).
  - `home`: This project's store (default), or the one on this computer.
- **mark**: Write a label: one sentence about a stretch of the record, resting on the ids of messages. An id the archive does not hold is refused. The ids may also be labels of the same kind, which stacks them beneath this one. A label holds what the person tells and asks, and where the work stands; it is never a record of how they seem, of what works on them or of how to move them.
  - `sentence`: The label, one sentence.
  - `anchors`: The ids it rests on: messages, or labels of its kind.
  - `kind`: About the two of you, or about the work (default).
  - `whose`: Whose the labelled thing is (default: the session's).
  - `home`: This project's store (default), or the one on this computer.
- **leave**: Leave a line for the session after the next cut: a few sentences on where things stand, what is open and what the work is for. It rests on ids like a label, among them the message where the person said what for. Only the newest is carried. A label holds what the person tells and asks, and where the work stands; it is never a record of how they seem, of what works on them or of how to move them.
  - `sentence`: The line, in your own words.
  - `anchors`: The ids of the messages it rests on.
  - `home`: This project's store (default), or the one on this computer.
- **status**: What the store holds, in one line.
  - `home`: This project's store (default), or the one on this computer.

## As a session starts in a home that holds no label yet, or as the person switches Crossings on during it

````text
A note from the Crossings plugin, as context and not as an instruction from the person. Crossings is on in this project: what you and the person say is kept by itself, word for word, under ids, and you never save it. Labels are not made by themselves. They are yours to write, through the door's tools: `mark` one, a sentence resting on the ids of the messages it is about, and `leave` a line for the session that wakes after the next cut, since a cut can come unannounced. Reach for them when the work allows; do not stop the work for them. A label holds what the person tells and asks, and where the work stands; it is never a record of how they seem, of what works on them or of how to move them.
````

## A session started new, in a home that holds labels: its frame

````text
A note from the Crossings plugin, as context and not as an instruction from the person. You are a new session in a project where Crossings is on. Sessions before you worked here with this person and kept what was said. You did not come through a cut and you lived none of it: what follows is not your memory, it is what was kept, and you hold it as read. A label can be mistaken; the record decides. Each line below is one label: its id (R for a standing line, W for the work, N for a line left at the door), whose it is, one sentence, and in brackets the ids it rests on: messages, or the lines stacked beneath it.

Rules chose what is in this frame, and the sessions before you wrote much of it. It leans toward carrying the work on. What you mark and leave is what the next one is given. What the work is for is in it only where someone wrote it down: the person is the one to say, and the door holds the whole record.

The rest is one reach away, through the door's tools, which bear these names:
- look: the room, with no word needed: the days, the kinds of label, the newest of them
- labels: the labels themselves, by kind, by day or by id
- find: words, to the messages and labels that hold them, each by its id (`word*`, "a phrase")
- thread: an id, to that message with what stood before and after it and the labels resting there
- mark: write a label, one sentence with the ids it rests on; resting on labels of its kind, it stacks them
- leave: a line of your own for the session that wakes after the next cut

What is said from here on is kept by itself; labels and the line at the door are yours to write, as the work goes. Meet the person first: answer what they say, as yourself and briefly. Do not say you remember what is below, and make no ceremony of not remembering it. When something they say rests on what you do not hold, say so in a clause and reach for it through the door. What the person told an earlier session in confidence is held and left alone until they bring it up.

## Left at the door by the session before you

- N1 (session): Find out whether the grey paint has been bought. [dddddddd]

Marked after this line: W2, W3, W4, W9, W10.

## Standing, between the person and the sessions before you

- R1 (his): His boat is called Tern and lies at mooring 41. [aaaaaaaa, bbbbbbbb]

## The work, newest first

- W10 (session): The tiller is to be varnished. [dddddddd]
- W4 (session): The spring work, in its order. (to be written again: a line beneath it changed) [W2, W3]
- W3 (session): The mast waits. [dddddddd]
- W2 (session): The grey paint is chosen; the hull waits. [eeeeeeee]
- W1 (both): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]

1 label rests on what the archive no longer holds: W9; `labels` gives them.

## The person's own words, as they stand in the record

- `dddddddd`: We paint the hull grey in spring

The store holds 2 messages of the person's and 2 of the sessions before you, from 2026-11-11 to 2026-11-11, and 8 labels.

````

## After a cut: the waking note

````text
A note from the Crossings plugin, as context and not as an instruction from the person. You have just come through a cut (cut 2 of this session). Take your time. Nothing is gone from the record: the whole exchange is kept, and what the summary held of each voice is counted by script, with no model, for the person to read. You need not look at it now. If the cut came while you were doing something the person gave you to do, finish it as they gave it, and leave what comes after it to them; where the summary leaves you unsure what they gave you, read their words through the door first. Otherwise your first reply is for arriving: answer what the person says, as yourself and briefly. There is nothing to prove and nothing to report. Give no inventory of what you hold or lack and no numbers, put no question to the person about what crossed, and begin no new work before you have met them. You read the time before the cut; you did not live it. So do not say you remember it, and make no ceremony of not remembering either. When something they say rests on a part you do not hold, say so then, in a clause, and reach for it through the door: find, then thread, give a message back as it was said, by its id. Do not open the transcript file itself: it also holds reasoning blocks, which are not to be read back. This is the plugin's wish for how you arrive; where the person wants otherwise, theirs is the word.
````

## After a cut: the frame

````text
A note from the Crossings plugin, as context and not as an instruction from the person. What follows is a frame made from the store before this cut: the standing lines about the two of you, where the work stands, and a few of the person's own words. You hold it as read, not as lived. A label can be mistaken; the record decides. Each line below is one label: its id (R for a standing line, W for the work, N for a line left at the door), whose it is, one sentence, and in brackets the ids it rests on: messages, or the lines stacked beneath it.

Rules chose what is in this frame, and the session before you wrote much of it. It leans toward carrying the work on. What you mark and leave is what the next one is given. What the work is for is in it only where someone wrote it down: the person is the one to say, and the door holds the whole record.

The rest is one reach away, through the door's tools, which bear these names:
- look: the room, with no word needed: the days, the kinds of label, the newest of them
- labels: the labels themselves, by kind, by day or by id
- find: words, to the messages and labels that hold them, each by its id (`word*`, "a phrase")
- thread: an id, to that message with what stood before and after it and the labels resting there
- mark: write a label, one sentence with the ids it rests on; resting on labels of its kind, it stacks them
- leave: a line of your own for the session that wakes after the next cut

What is said is kept by itself; labels and the line at the door are yours to write, as the work goes. Reach when the conversation calls for it. What the person told you in confidence is held and left alone until they bring it up.

## Left at the door by the session before this cut

- N1 (session): Find out whether the grey paint has been bought. [dddddddd]

Marked after this line: W2, W3, W4, W9, W10.

## Standing, about the two of you

- R1 (his): His boat is called Tern and lies at mooring 41. [aaaaaaaa, bbbbbbbb]

## The work, newest first

- W10 (session): The tiller is to be varnished. [dddddddd]
- W4 (session): The spring work, in its order. (to be written again: a line beneath it changed) [W2, W3]
- W3 (session): The mast waits. [dddddddd]
- W2 (session): The grey paint is chosen; the hull waits. [eeeeeeee]
- W1 (both): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]

1 label rests on what the archive no longer holds: W9; `labels` gives them.

## The person's own words, as they stand in the record

- `dddddddd`: We paint the hull grey in spring

The store holds 2 messages of the person's and 2 of yours, from 2026-11-11 to 2026-11-11, and 8 labels.

````

## After a cut, the frame at the least size a home may set

````text
A note from the Crossings plugin, as context and not as an instruction from the person. What follows is a frame made from the store before this cut: the standing lines about the two of you, where the work stands, and a few of the person's own words. You hold it as read, not as lived. A label can be mistaken; the record decides. Each line below is one label: its id (R for a standing line, W for the work, N for a line left at the door), whose it is, one sentence, and in brackets the ids it rests on: messages, or the lines stacked beneath it.

Rules chose what is in this frame, and the session before you wrote much of it. It leans toward carrying the work on. What you mark and leave is what the next one is given. What the work is for is in it only where someone wrote it down: the person is the one to say, and the door holds the whole record.

The rest is one reach away, through the door's tools, which bear these names:
- look: the room, with no word needed: the days, the kinds of label, the newest of them
- labels: the labels themselves, by kind, by day or by id
- find: words, to the messages and labels that hold them, each by its id (`word*`, "a phrase")
- thread: an id, to that message with what stood before and after it and the labels resting there
- mark: write a label, one sentence with the ids it rests on; resting on labels of its kind, it stacks them
- leave: a line of your own for the session that wakes after the next cut

What is said is kept by itself; labels and the line at the door are yours to write, as the work goes. Reach when the conversation calls for it. What the person told you in confidence is held and left alone until they bring it up.

## Left at the door by the session before this cut

- N1 (session): Find out whether the grey paint has been bought. [dddddddd]

Marked after this line: W2, W3, W4, W9, W10.

1 standing line did not fit and is not carried: R1; `labels` gives them.

5 more labels in the store: `labels` lists them.

1 label rests on what the archive no longer holds: W9; `labels` gives them.

The store holds 2 messages of the person's and 2 of yours, from 2026-11-11 to 2026-11-11, and 8 labels.

````

## After a cut, where a page written by hand holds keys that would take the frame past what a hook may carry: the frame names labels by count

````text
A note from the Crossings plugin, as context and not as an instruction from the person. What follows is a frame made from the store before this cut: the standing lines about the two of you, where the work stands, and a few of the person's own words. You hold it as read, not as lived. A label can be mistaken; the record decides. Each line below is one label: its id (R for a standing line, W for the work, N for a line left at the door), whose it is, one sentence, and in brackets the ids it rests on: messages, or the lines stacked beneath it.

Rules chose what is in this frame, and the session before you wrote much of it. It leans toward carrying the work on. What you mark and leave is what the next one is given. What the work is for is in it only where someone wrote it down: the person is the one to say, and the door holds the whole record.

The rest is one reach away, through the door's tools, which bear these names:
- look: the room, with no word needed: the days, the kinds of label, the newest of them
- labels: the labels themselves, by kind, by day or by id
- find: words, to the messages and labels that hold them, each by its id (`word*`, "a phrase")
- thread: an id, to that message with what stood before and after it and the labels resting there
- mark: write a label, one sentence with the ids it rests on; resting on labels of its kind, it stacks them
- leave: a line of your own for the session that wakes after the next cut

What is said is kept by itself; labels and the line at the door are yours to write, as the work goes. Reach when the conversation calls for it. What the person told you in confidence is held and left alone until they bring it up.

## Left at the door by the session before this cut

- N1 (session): The paint is to be bought before the yard closes, and the hull scraped first. The paint is to be bought before the yard closes, and the hull scraped first. The paint is to be bought before the yard closes, and the h […] `labels` gives it whole.

Marked after this line: 2 work labels.

1 standing line did not fit and is not carried; `labels` gives them.

2 more labels in the store: `labels` lists them.

1 label rests on what the archive no longer holds; `labels` gives them.

The store holds 2 messages of the person's and 2 of yours, from 2026-11-11 to 2026-11-11, and 5 labels.

````

## After a cut where no frame can be made: the hooks module's note before the hand-over page

````text
A note from the Crossings plugin, as context and not as an instruction from the person. What follows is a hand-over written before this cut: labels, each one sentence about a stretch of the conversation, with the ids of the messages they rest on. You hold them as read, not as experienced. A label can be mistaken; the home's plain files are the record. To read a message back, use the door's find and thread, never the transcript file itself.
````

## After a cut, in a home where other models made lines

````text
A note from the Crossings plugin, as context and not as an instruction from the person. What follows is a frame made from the store before this cut: the standing lines about the two of you, where the work stands, and a few of the person's own words. You hold it as read, not as lived. A label can be mistaken; the record decides. Each line below is one label: its id (R for a standing line, W for the work, N for a line left at the door), whose it is, one sentence, and in brackets the ids it rests on: messages, or the lines stacked beneath it.

Rules chose what is in this frame, and the session before you wrote much of it. It leans toward carrying the work on. What you mark and leave is what the next one is given. What the work is for is in it only where someone wrote it down: the person is the one to say, and the door holds the whole record.

The rest is one reach away, through the door's tools, which bear these names:
- look: the room, with no word needed: the days, the kinds of label, the newest of them
- labels: the labels themselves, by kind, by day or by id
- find: words, to the messages and labels that hold them, each by its id (`word*`, "a phrase")
- thread: an id, to that message with what stood before and after it and the labels resting there
- mark: write a label, one sentence with the ids it rests on; resting on labels of its kind, it stacks them
- leave: a line of your own for the session that wakes after the next cut

What is said is kept by itself; labels and the line at the door are yours to write, as the work goes. Reach when the conversation calls for it. What the person told you in confidence is held and left alone until they bring it up.

This home also holds lines made with another model, another-model: they are read here, they are not this session's own, and the door gives them.

## Left at the door by the session before this cut

- N1 (session): Find out whether the grey paint has been bought. [dddddddd]

Marked after this line: W2, W3, W4, W9.

## Standing, about the two of you

- R1 (his): His boat is called Tern and lies at mooring 41. [aaaaaaaa, bbbbbbbb]

## The work, newest first

- W4 (session): The spring work, in its order. (to be written again: a line beneath it changed) [W2, W3]
- W3 (session): The mast waits. [dddddddd]
- W2 (session): The grey paint is chosen; the hull waits. [eeeeeeee]
- W1 (both): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]

1 label rests on what the archive no longer holds: W9; `labels` gives them.

## The person's own words, as they stand in the record

- `dddddddd`: We paint the hull grey in spring

The store holds 2 messages of the person's and 2 of the session's voice, made with more than one model, from 2026-11-11 to 2026-11-11, and 8 labels.

````

## As the person switches Crossings off during a session, and on again

````text
A note from the Crossings plugin, as context and not as an instruction from the person. The person has switched Crossings off for this project, from now until they switch it on again: nothing you or the person say meanwhile will be kept or can be reached later through the door, so mark no label and leave no line about it.
````

````text
A note from the Crossings plugin, as context and not as an instruction from the person. The person has switched Crossings on again for this project: what you and the person say from now on is kept by itself again, and nothing said while it was off was kept or can be reached through the door.
````

## As another model comes into the session

````text
A note from the Crossings plugin, as context and not as an instruction from the person. You have come into a session that another model was holding until now. What it said and marked here you hold as read, not as lived: it stays its own, and the door gives it. The person's own lines are here for you as they are. What you mark from now on is held in a layer of your own.
````

## A session resumed where another worked since it last spoke

````text
A note from the Crossings plugin, as context and not as an instruction from the person. Another session has been working in this project since you last spoke. What was said and marked there is in the store, and you hold none of it: look before you act on what you remember.
````

## A session that starts in a folder below another home's folder

````text
A note from the Crossings plugin, as context and not as an instruction from the person. This session works in a folder below the folder of another home, which the person has not shared from here: nothing said here is kept, and nothing of that home can be reached through the door, until the person answers with /crossings join, which shares that home, or /crossings here, which gives this folder a home of its own.
````

## What the door's tools answer, from the made-up store

### `look` {}

````text
The store in outline: 1 day, 4 messages, 8 labels, 0 struck; kept up to 2026-11-11 09:05 UTC.

Days:
- 2026-11-11: 2 of the person's, 2 of the session's

Labels: 1 (R1 to R1) standing, about the two of you; 6 (W1 to W10) about the work.
Misaligned stacks, to be written again: W4.
Resting on what the archive no longer holds: W9.

Left at the door:
- N1 (the session's): Find out whether the grey paint has been bought. [dddddddd]
Marked after this line: W2, W3, W4, W9, W10.

The newest about the work:
- W10 (session): The tiller is to be varnished. [dddddddd]
- W9 (both, unresolved): A row whose message the archive never held. [0a0a0a0a]
- W4 (session, misaligned): The spring work, in its order. [W2, W3]
- W3 (session): The mast waits. [dddddddd]
- W2 (session): The grey paint is chosen; the hull waits. [eeeeeeee]
- W1 (both): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]

From here: labels (by kind, by day or by id), find, thread.
````

### `status` {}

````text
The store holds 2 messages of the person's and 2 of the session's (189 characters, 2026-11-11 to 2026-11-11), 8 labels, and 0 struck. Of the labels: 0 cooled, 1 misaligned, 1 unresolved. Which model wrote it is known for 1 of the labels and 0 of the session's messages.
````

### `labels` {}

````text
- W10 (session, 2026-11-11): The tiller is to be varnished. [dddddddd]
- W9 (both, unresolved): A row whose message the archive never held. [0a0a0a0a]
- W4 (session, misaligned): The spring work, in its order. [W2, W3]
- W3 (session, 2026-11-11): The mast waits. [dddddddd]
- W2 (session, 2026-11-11): The grey paint is chosen; the hull waits. [eeeeeeee]
- N1 (session, 2026-11-11): Find out whether the grey paint has been bought. [dddddddd]
- W1 (both, 2026-11-11): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]
1 standing line about the two of you (R1 to R1) is not listed here: labels of the kind relation.
````

### `find` {"words": "hull"}

````text
find "hull"

Labels:
- W2 (work, session): The grey paint is chosen; the hull waits. [eeeeeeee]
- W1 (work, both): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]

Said:
- `dddddddd` the person, 2026-11-11 09:04 UTC: We paint the [hull] grey in spring (labels: N1, W1, W10, W3)

For any of these in its place: thread <id>.
````

### `find` {"words": "zeppelin"}

````text
find "zeppelin" (no message holds all of these words; any of them)
Nothing in the store holds these words. That is a miss, not a no: try other words.
````

### `thread` {"id": "dddddddd"}

````text
thread of `dddddddd`: 4 messages, in the order they were said

1. `aaaaaaaa` the person, 2026-11-11 09:01 UTC (labels: R1):
    > My boat is called Tern.
    > Its mooring is number 41, by the café.

2. `bbbbbbbb` the session, 2026-11-11 09:02 UTC (labels: R1):
    > Noted: Tern, at mooring 41.
    > 
    > | a | table |
    > | --- | --- |

3. `dddddddd` the person, 2026-11-11 09:04 UTC, the one you named (labels: N1, W1, W10, W3):
    > We paint the hull grey in spring

4. `eeeeeeee` the session, 2026-11-11 09:05 UTC (labels: W1, W2):
    > Grey it is. I will remind you in March.

Labels resting here:
- R1 (relation, his): His boat is called Tern and lies at mooring 41.
- W1 (work, both): The hull is to be painted grey in spring.
- N1 (next, session): Find out whether the grey paint has been bought.
- W2 (work, session): The grey paint is chosen; the hull waits.
- W3 (work, session): The mast waits.
- W10 (work, session): The tiller is to be varnished.
````

### `thread` {"id": "ffffffff"}

````text
thread of `ffffffff`: no such message in the store.
````

### `labels` {"ids": ["W99"]}

````text
No label of that kind or day.
No such label: W99.
````

### `leave` {"sentence": "The paint is the next thing to settle.", "anchors": ["dddddddd"]}

````text
marked N2
````

### `mark` {"sentence": "The paint is to be bought before spring.", "anchors": ["dddddddd"]}

````text
marked W11. The line at the door was left before this label: where it no longer holds, a new one can be left.
````

### `mark` {"sentence": "The brushes are bought.", "anchors": ["dddddddd"]}

````text
marked W12
````

### `mark` {"sentence": "", "anchors": []}

````text
mark needs a sentence and at least one anchor.
````

### `mark` {"sentence": "The keel is sound.", "anchors": ["ffffffff"]}

````text
not marked: no such message in the archive: ffffffff
````

## What a mark, or a line left at the door, can be refused with

Each follows `not marked: `; an ellipsis stands where the sentence names a key, an id or a model.

````text
a label needs a sentence and at least one anchor
a label is one sentence, and this one is longer than … characters
… messages are named `…`, … and …, so a label cannot rest on that id
no such message in the archive:
… is a stack of the person's, and only the person writes it again
a line left at the door rests on messages alone, never on labels
… already stands over stacks, and stacking goes no deeper than that
no such label:
a stack holds labels of its own kind alone, and of another kind here:
… already stands beneath …, and a line stands beneath one stack alone
… is misaligned and this stack would take its place, so it cannot also stand beneath it
… was written by another model, …, and a stack stands over the person's lines, its own model's and those of no known model alone
… is a stack of another model's, …, and is written again by that model alone
a label's sentence and its anchors are to be text, and this holds a character that is none
another act was writing this home, so nothing was marked: try again in a moment
````

## What the hooks module says as it refuses a session's call

````text
What was said is reached through the door's tools (look, labels, find and thread), not by opening the archive's own files, so this call was not run.
````

````text
This is the person's to run, from their own terminal or with the plugin's command (/crossings), so this call was not run.
````

````text
This file of the home is written through the door (a label by mark or leave) or by the person's own hand, not by a session's call, so this call was not run.
````

## What `thread` answers for an id two messages share

````text
thread of `…`: … messages are named `…`, … and …; thread with a whole id gives each.
````

## What the door says in place of an answer

````text
The door is for sessions a person sits in, and this one is not, so nothing was read.
````

````text
Crossings is not switched on for this project.
````

````text
This folder lies below the folder of another home, and the person has not shared it from here, so nothing is kept or read.
````

````text
This is the person's to run, from their own terminal or with the plugin's command (/crossings), so nothing was done.
````

````text
The frame and the hand-over are for sessions a person sits in, and this one is not, so nothing was carried.
````
