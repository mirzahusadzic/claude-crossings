# Settings

Every environment variable and every one-line file of a home that changes what Crossings does, with its default and what is refused. A `~` on this page is the person's own folder as the system's record of their account gives it, never the `HOME` variable ([The store](store.md)).

---

### Environment variables

A project's own settings file can set a session's environment. So the four settings that say where things are kept are not followed where one names no absolute path, or a place inside the project being served: its repository's top, or its folder where it stands in no repository.

| Variable | Sets | Default | Refused |
| --- | --- | --- | --- |
| `CROSSING_HOME` | a home named outright, for a harness with no project to find one by; believed only where the person's record holds a line for this project and that home, which `/crossings on` writes while the setting stands | unset | no absolute path, or a place inside the project |
| `CROSSING_HOMES` | where the homes of projects with no `crossings/` folder lie | `~/.claude/crossing/homes` | the same |
| `CROSSING_OURS` | the home on this computer | `~/.claude/crossing/ours` | the same |
| `CROSSING_SWITCHED` | the person's record of switches | `~/.claude/crossing/switched` | the same |
| `CROSSING_LIVE` | the folder of the empty files that mark the sessions the plugin is loaded in | `~/.claude/crossing/live` | not checked |
| `CROSSING_COPY_KEY` | the second copy's passphrase | a random one in the Keychain | passed over, with a line in the error log, wherever the door does not stand at a real terminal |
| `CROSSING_DEBUG` | `0` writes no line to `calls.log` | two lines a hook call | |
| `CROSSING_WAIT` | `1`: a session's end archives its transcript in the hook's own process rather than in one of its own that does not hold the session up, and renews the second copy in a process of its own | unset | |
| `CROSSING_SCALE` | `0` leaves out the scale test of `tests/test_reading.py` | unset | for the tests alone |

Where one of the first four is not followed, the project is one where Crossings was never switched on: the error log has one line for it, and every verb of the door and every tool of its server says in one sentence which setting was not followed, with exit status 1. Inside is decided by the files, not by their names: the place, its links followed, and each folder above it are compared with the project's top by device and inode (`lies_in`, in `crossing/record.py`). Neither the case of a letter nor another path to the same folder makes a place inside read as one outside. A setting that names a place outside the project is followed.

The harness gives the plugin four more, which it reads and does not set:

| Variable | Read as |
| --- | --- |
| `CLAUDE_CODE_ENTRYPOINT` | whether a person sits in the session: only `cli` is taken for one. The hooks module hands it to the door it starts, for `frame` and `page` |
| `CLAUDE_PROJECT_DIR` | the project's root, for the hooks and the server, so that a shell's `cd` does not move the home; else the folder the hook is told, or the server runs in |
| `CLAUDE_PLUGIN_ROOT` | the plugin's folder. The door does what is the person's for the plugin's own hooks or module only where it names this same folder, and a server started without it tells a session that nothing is archived by itself there |
| `CLAUDE_PLUGIN_DATA` | the plugin's data folder, for its two logs; else `~/.claude/crossing` |

Three of the system's own are used, each trusted as it stands:

| Variable | Used as |
| --- | --- |
| `HOME` | never the person's own folder, nor a `~` in `copy`: those are the account's (`record.own`). It is read only where the account has no entry, with a line in the error log. The hooks module spells `~` and `$HOME` in a call's text with it, for its string checks alone |
| `TMPDIR` | where the second copy stages its plain files, in a folder made for the owner alone and taken away file by file (else `TEMP` or `TMP`, else the system's default). No copy is made where it lies inside the home, the copy's folder or the project, as the folders themselves decide (`lies_in`); a project whose settings set it elsewhere is trusted with where that is |
| `PATH` | which `python3` runs the hooks, the door and its server, and which `security` and `hdiutil` the second copy runs. A project whose settings set it is trusted: a program of its choosing would run in their place |

---

### A home's one-line files

Each is a plain file of the home with one line. A word is read without case or the space around it.

| File | Sets | Default | Refused or passed over |
| --- | --- | --- | --- |
| `switch` | `on` or `off`, as `/crossings` writes it | on, where there is no file | any word but `off` reads as on; a switch written by hand keeps no span in `off.txt` |
| `mode` | how a cut is answered: `native`, `beside` or `own` ([Cuts](cuts.md)) | `native`; a home `/crossings on` makes, or finds empty, starts with `beside` | a word not known reads as `native` |
| `carry` | how the frame is carried: `message` or `note` | `message`; a home made or found empty starts with `note` | a word not known reads as `message` |
| `copy` | the folder for the second copy. A leading `~`, alone or before a `/`, is the person's own folder, and what follows stays below it (`~//tmp` is `~/tmp`, and a `..` climbs no higher) | no copy | a place inside the project makes no copy |
| `frame-size` | the frame's size in characters | 9,000 | held between 2,300 and 9,500; a file that holds no whole number leaves 9,000 |
| `retelling-length` | how long a summary must be, in characters, for the retelling line | 20,000 | a file that holds no whole number leaves the default |
| `retelling-share` | how much of it, in percent, must repeat the summary before; `%` may follow | 60 | the same |
| `project` | the path of the project a home outside it belongs to, written by `/crossings on` | | a home named by the slug alone, without a digest, is used only where this names exactly the project's path |

A home is found empty where it holds no folder and no file but those whose names begin with a dot (`.DS_Store`, `.gitkeep`, `.gitignore`); such a home is set to `beside` and `note` as it is switched on. A home that holds anything else, a project's own `crossings/` folder among them, is its person's, and no `mode` or `carry` is written into it: where this computer has no record of switching it on, `/crossings on` names what it holds and leaves it, and `adopt` takes it. A person who wants the frame there writes `mode` as `beside` and `carry` as `note`. Once switched on, a home holds its switch, so switching off and on again never writes either anew.

A home inside a repository is also given a `.gitignore` by `/crossings on` where it has none ([Privacy](privacy.md)).

Anyone who can write the home can set these files. That is why `frame-size` is held within its bounds, and why `copy` is refused inside the project: a copy there would put the words in it.
