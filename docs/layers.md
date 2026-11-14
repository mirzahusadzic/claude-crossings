# Layers

What changes when more than one model works in a home. A session can change its model, and a project can be worked by more than one; every line of the session's voice is kept as the line of the model that made it, and what a frame carries and what a stack may stand over then depend on which model is there now. Nothing is moved: the pages stay as they are, and a layer is only a way of reading them.

---

### A layer for each model

| Line | Its layer |
| --- | --- |
| a message of the session's | the model its `model` field names, kept from the transcript's row |
| a label | the model its line in `models.txt` names, by the label's key and its sentence's digest |
| a stack | the model that wrote it, whoever its lines are about |
| a message of the person's, and a plain label whose `whose` is `his` | no layer: there for whichever model faces the person |
| a line with no model named, a label reworded since it was signed, or one a subagent marked | no known layer: read as a line of whichever model faces the person, and stood over by any |

`models.txt` is the one place the plugin keeps who wrote a label. The pages read as they always did, and the frame does not carry a model. Every line a signing through the door or `door.py layer` writes is met by the home (`models-met.txt`); a line a build finds that the home has not met (a pull, a checkout, a hand) is followed all the same, and the person's next `status` names it once, by the label's key and the model it names, as it names a label that came by no mark. A home that is adopted (`/crossings adopt`) has met none of the lines its `models.txt` holds then, whatever a `models-met.txt` that came with it says, so its first build notes every one.

A label marked through the door is signed with the model of the session that marks it. The server is not told which session calls it, so the hook before a call of `mark` hands over the model, and the hook after `mark` or `leave` signs the label where it was not signed as it was written. Only the label of that key and that sentence is signed, and only once. A label a subagent marks is left unsigned: the hook is told the subagent and not its model.

---

### The model that is there

| Event | Crossings |
| --- | --- |
| a session a person sits in starts | keeps the model the harness names in `there.txt`, by the session as the archive names it, with the moment, where it is not the one kept already |
| the harness reports a model switch (`PostModelSwitch`) | brings the archive up to the moment, and keeps the new model the same way |
| a call of `mark` through the door | the hook before it writes the call's digest and the model into `calling.txt`; the server takes the line of the same digest and takes it out |
| the hooks were never told, or a message of the session's own is newer than what they were told | the model is that message's |
| no model can be told | no layering for that call or that frame: everything is read as before |

Two calls the same, from two sessions at the same moment, are the one case `calling.txt` cannot tell apart.

---

### What a frame carries, for whom

For a session whose model is known, the frame carries the person's lines whoever wrote them down, the lines of that model's own layer, and the lines whose writer is not known. It does not carry, as standing, a line of another model's layer. Where such lines are, or where messages of the session's voice were made with another model, one sentence near its opening names the other models and says that the door gives them.

A stack written by another model is not carried, and the lines beneath it cross as themselves. Of the lines left at the door, the frame carries the newest one that is not another model's. A session whose model is not known is given the frame with no layer asked about: every line crosses as of no known layer.

The frame hook takes the model the harness names as the session starts, or failing that the model that is there, as above. The door's `frame` takes the model of the session named with `--session` or `--transcript`.

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

It runs from the person's own terminal; the door's server does not offer it. It signs, as made with that model, every label whose sentence has no line in `models.txt` and every message of the session's voice that has no model, says how many of each it signed, and, where it signed any, makes the index whole. A line that has a model is never changed. A key with a space or a `#` in it, one that begins with `<`, or none, is refused.

---

### What the lists show

Where a home holds lines of more than one known model, `labels`, `look`, `thread` and `find` say which model made each message of the session's voice and each label that is not the person's alone. In a home with one known model, or none, they name no model. `labels <key>` names the model that wrote a label wherever it is known, and `status` counts how many labels and messages of the session's say which model wrote them.

---

### The one who arrives

Where the model a session now runs is not the model of its own newest message in the archive, the session is told once, as context: that it has come into a session another model was holding, that what that one said and marked it holds as read and not as lived, that the person's lines are here for it as they are, and that what it marks from now on is held in a layer of its own.

At a switch inside a session it is told with the `PostModelSwitch` hook's answer, and at a resume on another model with the `SessionStart` hook's. It is told once a change, to a session a person sits in, and never to a subagent. Where `there.txt` cannot be written, nothing is said.
