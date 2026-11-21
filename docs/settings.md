# Settings

Every environment variable and every one-line file of a home that changes what Crossings does, with its default and what is refused. A `~` on this page is the person's own folder as the system's record of their account gives it. It is never the `HOME` variable ([The store](store.md)).

[The words](words.md) says in a line or two what each of the tool's own words means.

---

### Environment variables

A project's own settings file can set a session's environment. So the four settings that say where things are kept are not followed where one names no absolute path, or a place inside the project. The project is its repository's top, or its folder where it stands in no repository.

| Variable | Sets | Default | Refused |
| --- | --- | --- | --- |
| `CROSSING_HOME` | A home named outright, for a harness with no project to find one by. It is believed only as the person's record allows (below). | Unset. | No absolute path, or a place inside the project. |
| `CROSSING_HOMES` | Where the homes of projects with no `crossings/` folder lie. | `~/.claude/crossing/homes` | The same. |
| `CROSSING_OURS` | The home on this computer. | `~/.claude/crossing/ours` | The same. |
| `CROSSING_SWITCHED` | The person's record of switches. | `~/.claude/crossing/switched` | The same. |
| `CROSSING_LIVE` | The folder of the empty files that mark the sessions the plugin is loaded in. | `~/.claude/crossing/live` | Not checked. |
| `CROSSING_COPY_KEY` | The second copy's passphrase. | A random one in the Keychain. | Passed over, with a line in the error log, wherever the door does not stand at a real terminal. |
| `CROSSING_DEBUG` | `0` writes no line to `calls.log`. | Two lines a hook call. | Any other value reads as unset. |
| `CROSSING_WAIT` | `1`: a session's end archives its transcript in the hook's own process. It also renews the second copy, in a process of its own. | Unset: the archive is made in a process of its own, which does not hold the session up, and makes no copy. | Any other value reads as unset. |

#### When a setting is not followed

Where one of the first four is not followed, the project is one where Crossings was never switched on. The error log has one line for it.

- **What is said.** Every verb of the door and every tool of its server says in one sentence which setting was not followed, with exit status 1.
- **A home named outright.** `CROSSING_HOME` is believed only where the person's record holds a line for this project and that home. `/crossings on` writes that line while the setting stands.
- **Inside, by the files.** Inside is decided by the files, not by their names. Neither the case of a letter nor another path to the same folder makes a place inside read as one outside.
- **Outside.** A setting that names a place outside the project is followed.

#### The harness's variables

The harness gives the plugin four more, which it reads and does not set:

| Variable | Read as |
| --- | --- |
| `CLAUDE_CODE_ENTRYPOINT` | Whether a person sits in the session: only `cli` is taken for one. The hooks module hands it to the door it starts, for `frame` and `page`. |
| `CLAUDE_PROJECT_DIR` | The project's root, for the hooks and the server, so that a shell's `cd` does not move the home. Else the folder the hook is told, or the server runs in. |
| `CLAUDE_PLUGIN_ROOT` | The plugin's folder. The door does what is the person's for the plugin's own hooks or module only where it names this same folder. |
| `CLAUDE_PLUGIN_ROOT`, for the server | A server started without it tells a session that nothing is archived by itself there. |
| `CLAUDE_PLUGIN_DATA` | The plugin's data folder, for its two logs. Else `~/.claude/crossing`. |

#### The system's own

Three of the system's own are used, each trusted as it stands:

| Variable | Used as |
| --- | --- |
| `HOME` | Never the person's own folder, nor a `~` in `copy`: those are the account's. It is read only where the account has no entry, with a line in the error log. |
| `TMPDIR` | Where the second copy stages its plain files. Else `TEMP` or `TMP`, else the system's default. |
| `PATH` | Which `python3` runs the hooks, the door and its server. Also which `security` and `hdiutil` the second copy runs. |

Where each is used, and how far it is trusted:

- **`HOME` in the hooks module.** The module spells `~` and `$HOME` in a call's text with it, for its string checks alone.
- **The stage.** The second copy stages in a folder made for the owner alone, and takes it away file by file.
- **A stage inside.** No copy is made where the stage lies inside the home, the copy's folder or the project, as the folders themselves decide.
- **A stage set elsewhere.** A project whose settings set `TMPDIR` elsewhere is trusted with where that is.
- **`PATH`.** A project whose settings set it is trusted: a program of its choosing would run in their place.

---

### A home's one-line files

Each is a plain file of the home with one line. A word is read without case or the space around it.

| File | Sets | Default | Refused or passed over |
| --- | --- | --- | --- |
| `switch` | `on` or `off`, as `/crossings` writes it. | On, where there is no file. | Any word but `off` reads as on. A switch written by hand keeps no span in `off.txt`. |
| `mode` | How a cut is answered: `native`, `beside` or `own` ([Cuts](cuts.md)). | `native`. A home made, or found empty, as it is switched on starts with `beside` (below). | A word not known reads as `native`. |
| `carry` | How the frame is carried: `message` or `note`. | `message`. A home made or found empty starts with `note`. | A word not known reads as `message`. |
| `copy` | The folder for the second copy. A leading `~`, alone or before a `/`, is the person's own folder (below). | No copy. | A place inside the project makes no copy. |
| `frame-size` | The frame's size in characters. | 9,000 | Held between 2,400 and 9,500. A file that holds no whole number leaves 9,000. |
| `retelling-length` | How long a summary must be, in characters, for the retelling line. | 20,000 | A file that holds no whole number leaves the default. |
| `retelling-share` | How much of it, in percent, must repeat the summary before. `%` may follow. | 60 | The same. |
| `project` | The path of the project a home outside it belongs to, written by `/crossings on`. | None: a home inside the project has no `project` file. | A home named by the slug alone, without a digest, is used only where this names exactly the project's path. |

After a leading `~` in `copy`, what follows stays below the person's own folder. `~//tmp` is `~/tmp`, and a `..` climbs no higher.

#### A home made, or found empty

A home that holds nothing yet is set to `beside` and `note` as it is switched on. A home that holds anything else, a project's own `crossings/` folder among them, is its person's, and no `mode` or `carry` is written into it.

What `on` and `adopt` each do with a home this computer has no record of switching on depends on what the home holds:

| The home holds | `/crossings on` | `/crossings adopt` |
| --- | --- | --- |
| nothing, or a `.gitignore` alone, or it is not there yet | Makes it where it is not there, switches it on, and sets `beside` and `note`. | As `on`. |
| no folder, and only files whose names begin with a dot, as `.DS_Store` or `.gitkeep` | Names what it holds and where, and switches nothing on. | Switches it on, and sets `beside` and `note`. |
| folders with no file in them, and no file but a `.gitignore` | Switches it on, and sets neither. | As `on`. |
| any other file, at its top or in a folder below | Names what it holds and where, and switches nothing on. | Switches it on, and sets neither. An index it holds is made anew. |

- **Empty.** A home is found empty where it holds no folder, and no file but those whose names begin with a dot (`.DS_Store`, `.gitkeep`, `.gitignore`).
- **Switching again.** Once switched on, a home holds its switch, so switching off and on again never writes either anew.
- **Not switched on here before.** A home may hold any file but a `.gitignore`, with no record on this computer of switching it on. There `/crossings on` names what it holds and leaves it, and `adopt` takes it.
- **The frame there.** A person who wants it writes `mode` as `beside` and `carry` as `note`.

A home inside a repository is also given a `.gitignore` as it is switched on, where it has none ([Privacy](privacy.md)).

Anyone who can write the home can set these files. That is why `frame-size` is held within its bounds. It is also why `copy` is refused inside the project: a copy there would put the words in it.
