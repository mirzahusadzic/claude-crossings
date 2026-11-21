# Layers

What changes when more than one model works in a home. A session can change its model, and a project can be worked by more than one. Every line of the session's voice is kept as the line of the model that made it.

[The words](words.md) says in a line or two what each of the tool's own words means.

---

### A layer for each model

What a frame carries, and what a stack may stand over, depend on which model is there now. Nothing is moved: the pages stay as they are, and a layer is only a way of reading them.

| Line | Its layer |
| --- | --- |
| a message of the session's | The model its `model` field names, kept from the transcript's row. |
| a label | The model its line in `models.txt` names, by the label's key and its sentence's digest. |
| a stack | The model that wrote it, whoever its lines are about. |
| a message of the person's | No layer: there for whichever model faces the person. |
| a plain label of the person's (its `whose` cell `his`, printed `theirs`) | No layer, the same way. |
| a silencing that is the person's, alone or with the session (`whose` `his` or `both`, as offered `their` or `both`) | No layer: it puts the refusal it rests on to rest for every model, whichever model's session wrote it down. |
| a line with no model named | No known layer: read as a line of whichever model faces the person, and stood over by any. |
| a label reworded since it was signed | No known layer, the same way. |
| a label a subagent marked | No known layer, the same way. |

`models.txt` is the one place the plugin keeps who wrote a label. The pages read as they always did, and the frame does not carry a model.

#### How a label is signed

A label marked through the door is signed with the model of the session that marks it. The server is not told which session calls it, so the hooks around the call do the signing.

- **Before `mark`.** The hook before a call of `mark` hands over the model ([below](#the-model-that-is-there)).
- **After `mark` or `leave`.** The hook after the call signs the label where it was not signed as it was written. It signs only the label of that key and that sentence, and only once.
- **A subagent's label.** A label a subagent marks is left unsigned, since the hook is told the subagent and not its model.

#### Lines that came another way

Every line a signing through the door or `layer` writes is kept in the receipts beside the person's record ([The store](store.md)). A line a build finds that those receipts do not know is followed all the same.

- **Where it came from.** A pull, a checkout, or a hand.
- **What the person is told.** Their next `status` names it once, by the label's key and the model it names.
- **An adopted home.** It has met none of the lines its `models.txt` holds, so its first build notes every one.

---

### The model that is there

The hooks keep which model each session runs, as the harness tells them. Where they were never told, the session's own messages say it.

| Event | Crossings |
| --- | --- |
| a session a person sits in starts | Keeps the model the harness names in `there.txt`, by the session, with the moment, where it is not the one kept already. |
| the harness reports a model switch (`PostModelSwitch`) | Brings the archive up to the moment, and keeps the new model the same way. |
| a call of `mark` through the door | The hook before it hands the model to the server through `calling.txt`. |
| the hooks were never told | The model is that of the session's own newest message. |
| a message of the session's own is newer than what the hooks were told | The model is that message's. |
| no model can be told | No layering for that call or that frame: everything is read as before. |

Two calls the same, from two sessions at the same moment, are the one case `calling.txt` cannot tell apart.

---

### What a frame carries, for whom

For a session whose model is known, the frame is made for that model. A session whose model is not known is given the frame with no layer asked about.

- **What it carries.** The person's lines whoever wrote them down, the lines of that model's own layer, and the lines whose writer is not known.
- **What it does not.** No standing line or work label of another model's layer.
- **The line at the door.** Of the lines left at the door, the frame carries the newest one that is not another model's.
- **Another model's stack.** A stack written by another model is not carried, and the lines beneath it cross as themselves.
- **A session's own silencing, under another model.** It puts the refusal it rests on to rest for that model alone. In this model's frame the refusal stands, whole, as its family's line.
- **The person's silencing.** It puts the refusal to rest for every model.
- **The other models, named.** Where another model's lines are, or messages of the session's voice were made with another model, one sentence near the opening names the other models. It names eight at most, and fewer, or only how many they are, where the frame has no room for so many. It says that the door gives them.

#### Which model the frame is for

The frame is made for the model that is there, and each way of asking for one finds it its own way.

- **The frame hook.** The model the harness names as the session starts, or failing that the model that is there, as above.
- **The door's `frame`.** The model `--model` names, else the model of the session named with `--session` or `--transcript`.

#### Refusals, for the model that asks

`look`, `labels` and `status` say a family of refusals stands or is silenced as the frame for the model that asks takes it. Where it stands otherwise for another model, one clause says so.

- **Through the server.** The model that asks is that of the session that spoke last, as `crossing` takes it.
- **From a terminal.** It is the one `--model` names, or the model of the session a `--transcript` names, as `frame` takes it.
- **Else.** None, and then as before layers.

A family whose every sound label (one neither misaligned nor unresolved) is of another model's layer is another model's alone. The frame for the model that asks carries nothing of it, and it is counted neither standing nor silenced there. The clauses read:

| The family | In `look` and `status` | In its row of `labels` |
| --- | --- | --- |
| stands here, and is at rest for another model alone | `X1 is at rest for another model alone, not for this one` | `standing here: S1 puts it to rest for another model alone` |
| is at rest here, and stands for another model alone | `X2 stands for another model alone, not for this one` | `at rest here: X2 stands for another model alone` |
| is another model's alone, and stands there | `X1 stands for another model alone, not for this one` | `another model's alone, standing there` |
| is another model's alone, and is at rest there | `S1 is another model's alone, at rest there` | `another model's alone, at rest there` |

A family that is another model's alone is named by the key that stands in it for that model. That label's row of `labels` carries the clause.

---

### Resting on, and restacking

A label resting on another model's messages is resting, not reframing, and is marked. `leave` is the same for every model. Reframing is a model's own to do:

| Event | The door |
| --- | --- |
| a stack would stand over a line, at any depth, written by a known model other than the one that marks, and not the person's | Refuses it, naming the line and its model. |
| a stack would take the place of another model's misaligned stack | Refuses it: that stack is written again by its own model. |
| a stack stands over the person's lines, its own model's, or lines of no known model | Marks it. |
| the model that marks is not known | Asks none of this. |

Striking stays the person's, whatever layer a line is in.

---

### Signing old lines

A label or a message with no model named is read as of no known layer until the person says whose it was. They sign such lines from their own terminal:

```sh
python3 crossing/door.py layer <model-key>
```

- **Who runs it.** It runs from the person's own terminal. The door's server does not offer it.
- **Switched off.** While the project is switched off it signs nothing, and says so in one sentence, with exit status 1.
- **What it signs.** Switched on, it signs, as made with that model, every label whose sentence has no line in `models.txt`. So too every message of the session's voice that has no model.
- **What it says.** How many of each it signed.
- **The index.** Where it signed any, it makes the index whole.
- **A line that has a model.** It is never changed.
- **A key refused.** A key with a space or a `#` in it, one that begins with `<`, or none.

---

### What the lists show

`labels`, `look`, `thread` and `find` name a model only where a home holds lines of more than one known model. Then they say which model made each message of the session's voice, and each label that is not the person's alone. In a home with one known model, or none, they name no model.

`labels <key>` names the model that wrote a label wherever it is known. `status` counts how many labels and messages of the session's say which model wrote them.

---

### The one who arrives

Where the model a session now runs is not the model of its own newest message in the archive, the session is told once, as context:

- that it has come into a session another model was holding.
- that what that one said and marked it holds as read, and not as lived.
- that the person's lines are here for it as they are.
- that what it marks from now on is held in a layer of its own.

It is told once a change, to a session a person sits in, and never to a subagent. Where `there.txt` cannot be written, nothing is said.

- **At a switch inside a session.** It is told with the `PostModelSwitch` hook's answer.
- **At a resume on another model.** It is told with the `SessionStart` hook's.
