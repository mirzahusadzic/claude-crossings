# Layers

What changes when more than one model works in a home. A session can change its model, and a project can be worked by more than one. Every line of the session's voice is kept as the line of the model that made it, and what a frame carries, and what a stack may stand over, then depend on which model is there now. Nothing is moved: the pages stay as they are, and a layer is only a way of reading them.

---

### A layer for each model

| Line | Its layer |
| --- | --- |
| a message of the session's | the model its `model` field names, kept from the transcript's row |
| a label | the model its line in `models.txt` names, by the label's key and its sentence's digest |
| a stack | the model that wrote it, whoever its lines are about |
| a message of the person's, and a plain label of the person's (its `whose` cell `his`, printed `theirs`) | no layer: there for whichever model faces the person |
| a silencing that is the person's, alone or with the session (`whose` `his` or `both`, as offered `their` or `both`) | no layer: it puts the refusal it rests on to rest for every model, whichever model's session wrote it down |
| a line with no model named, a label reworded since it was signed, or one a subagent marked | no known layer: read as a line of whichever model faces the person, and stood over by any |

`models.txt` is the one place the plugin keeps who wrote a label. The pages read as they always did, and the frame does not carry a model.

A label marked through the door is signed with the model of the session that marks it. The server is not told which session calls it, so the hook before a call of `mark` hands over the model, and the hook after `mark` or `leave` signs the label where it was not signed as it was written: only the label of that key and that sentence, and only once. A label a subagent marks is left unsigned, since the hook is told the subagent and not its model.

Every line a signing through the door or `layer` writes is kept in the receipts beside the person's record ([The store](store.md)). A line a build finds that those receipts do not know (a pull, a checkout, a hand) is followed all the same, and the person's next `status` names it once, by the label's key and the model it names. An adopted home has met none of the lines its `models.txt` holds, so its first build notes every one.

---

### The model that is there

| Event | Crossings |
| --- | --- |
| a session a person sits in starts | keeps the model the harness names in `there.txt`, by the session, with the moment, where it is not the one kept already |
| the harness reports a model switch (`PostModelSwitch`) | brings the archive up to the moment, and keeps the new model the same way |
| a call of `mark` through the door | the hook before it writes the call's digest and the model into `calling.txt`; the server takes the line of the same digest out |
| the hooks were never told, or a message of the session's own is newer than what they were told | the model is that message's |
| no model can be told | no layering for that call or that frame: everything is read as before |

Two calls the same, from two sessions at the same moment, are the one case `calling.txt` cannot tell apart.

---

### What a frame carries, for whom

For a session whose model is known, the frame carries the person's lines whoever wrote them down, the lines of that model's own layer, and the lines whose writer is not known. It does not carry, as standing, a line of another model's layer. Where such lines are, or where messages of the session's voice were made with another model, one sentence near its opening names the other models, eight at most and fewer, or only how many they are, where the frame has no room for so many, and says that the door gives them.

A stack written by another model is not carried, and the lines beneath it cross as themselves. So too a session's own silencing written under another model: it puts the refusal it rests on to rest for that model alone, and in this model's frame the refusal stands, whole, as its family's line; the person's silencing puts it to rest for every model. Of the lines left at the door, the frame carries the newest one that is not another model's. A session whose model is not known is given the frame with no layer asked about.

The frame hook takes the model the harness names as the session starts, or failing that the model that is there, as above. The door's `frame` takes the model of the session named with `--session` or `--transcript`.

`look`, `labels` and `status` say a family of refusals stands or is silenced as the frame for the model that asks takes it: through the server, the model of the session that spoke last, as `crossing` takes it; from a terminal, the one `--model` names, or the model of the session a `--transcript` names, as `frame` takes it; else none, and then as before layers. Where a family stands here and is at rest for another model alone, or the other way about, one clause says so: `X1 is at rest for another model alone, not for this one` and `X2 stands for another model alone, not for this one` in `look` and `status`, and in a row of `labels` `standing here: S1 puts it to rest for another model alone` or `at rest here: X2 stands for another model alone`. A family whose every sound label is of another model's layer is another model's alone: the frame for the model that asks carries nothing of it, and it is counted neither standing nor silenced there. One clause names it by the key that stands in it for that model, in `look` and in `status`: `X1 stands for another model alone, not for this one` where it stands there, and `S1 is another model's alone, at rest there` where it is at rest there. That label's row of `labels` says `another model's alone, standing there` or `another model's alone, at rest there`.

---

### Resting on, and restacking

A label resting on another model's messages is resting, not reframing, and is marked. `leave` is the same for every model. Reframing is a model's own to do:

| Event | The door |
| --- | --- |
| a stack would stand over a line, at any depth, that a known model other than the one that marks wrote, and that is not the person's | refuses it, naming the line and its model |
| a stack would take the place of another model's misaligned stack | refuses it: that stack is written again by its own model |
| a stack stands over the person's lines, its own model's, or lines of no known model | marks it |
| the model that marks is not known | asks none of this |

Striking stays the person's, whatever layer a line is in.

---

### Signing old lines

A label or a message with no model named is read as of no known layer until the person says whose it was:

```sh
python3 crossing/door.py layer <model-key>
```

It runs from the person's own terminal; the door's server does not offer it. While the project is switched off it signs nothing, and says so in one sentence, with exit status 1.

Switched on, it signs, as made with that model, every label whose sentence has no line in `models.txt` and every message of the session's voice that has no model, and says how many of each it signed; where it signed any, it makes the index whole. A line that has a model is never changed. A key with a space or a `#` in it, one that begins with `<`, or none, is refused.

---

### What the lists show

Where a home holds lines of more than one known model, `labels`, `look`, `thread` and `find` say which model made each message of the session's voice and each label that is not the person's alone. In a home with one known model, or none, they name no model. `labels <key>` names the model that wrote a label wherever it is known, and `status` counts how many labels and messages of the session's say which model wrote them.

---

### The one who arrives

Where the model a session now runs is not the model of its own newest message in the archive, the session is told once, as context: that it has come into a session another model was holding, that what that one said and marked it holds as read and not as lived, that the person's lines are here for it as they are, and that what it marks from now on is held in a layer of its own.

At a switch inside a session it is told with the `PostModelSwitch` hook's answer, and at a resume on another model with the `SessionStart` hook's. It is told once a change, to a session a person sits in, and never to a subagent. Where `there.txt` cannot be written, nothing is said.
