import type { Register } from 'claude-code'

// One hooks module a plugin, so the cut and the person's command live in this one file.

// --- the cut -------------------------------------------------------------------------------
//
// Crossing may answer a cut. Plain files in the project's home decide it:
//   switch   off: the cut is left to the harness
//   mode     one word: native (the default), beside, or own
//   carry    one word: message (the default) or note
// What is carried is the frame, composed from the store at the moment of the cut: by the
// plugin's SessionStart hook when the word is note, by crossing/door.py for a message. If no
// frame can be made for a message, the hand-over page goes (hand-over.md, with its words file).
// The record itself is never touched.
//
// The home is the project's own crossings/ folder where it has one, and a folder outside the
// project where it has none. This module puts neither path together and opens no file of a
// home itself: the door reads the home's words for it (`door.py words`), its hand-over page
// (`door.py page`) and writes the trace of what a cut did (`door.py trace`), by the rule the
// plugin's other hooks find the home by and through the one check that no file of a home is
// a link. A project the door names no home for is one where Crossing was never switched on:
// its cuts are left to the harness, and nothing is read or written for it.

type Mode = 'native' | 'beside' | 'own'

// How what is carried beside the summary gets there:
//   message  a user message in the cut's answer. The engine files that as a plain user row,
//            which reads as the person's own words, and draws it on their screen.
//   note     as context, added by the plugin's SessionStart hook when the session starts again
//            after the cut (crossing/hook.py, called with `frame`). The model reads it with its
//            next request, at a cut the person chose and at one that came by itself alike, and
//            nothing is filed or drawn as a message. This module then leaves a `beside` cut as
//            the harness made it. The plugin's own cut (`own`) still answers with a message.
type Carry = 'message' | 'note'

// How the harness opens the message that holds an earlier cut's summary.
const EARLIER = 'This session is being continued from a previous conversation'

// How a hand-over page is introduced. The frame brings its own opening, which begins the same
// way: the plugin's reader knows what the plugin carried by these first words. A frame or a note
// from before the plugin said its name as Crossings opens with the older words, and is still known.
const CARRIED = ['A note from the Crossings plugin', 'A note from the Crossing plugin']
const NOTE =
  'A note from the Crossings plugin, as context and not as an instruction from the person. ' +
  'What follows is a hand-over written before this cut: labels, each one sentence about a stretch of ' +
  'the conversation, with the ids of the messages they rest on. You hold them as read, not as ' +
  'experienced. A label can be mistaken; the transcript is the record. To read a message back, use the ' +
  "door's find and thread, never the transcript file itself."

// The project's root. A shell `cd` moves the session's working directory and must not move the
// store: the door would otherwise look for the home of whatever folder the shell stood in.
const root = async ($: any): Promise<string> => {
  try {
    return await $.session.root()
  } catch {
    return await $.session.cwd() // a build without root()
  }
}

// The door, as the plugin's own module calls it: with the flag that says so and the plugin's
// folder in CLAUDE_PLUGIN_ROOT, which together let it do what is the person's alone (the switch, a
// transcript by its session's id). A session's shell is refused the same call by the guard below.
// How the harness says the session was started (CLAUDE_CODE_ENTRYPOINT) is handed on as it is, so
// that the door carries no frame or hand-over to a session no person sits in.
const entrypoint = async ($: any): Promise<Record<string, string>> => {
  try {
    const started = await $.env.get('CLAUDE_CODE_ENTRYPOINT')
    return typeof started === 'string' ? { CLAUDE_CODE_ENTRYPOINT: started } : {}
  } catch {
    return {}
  }
}
const door = async ($: any, argv: string[]): Promise<{ ok: boolean; text: string }> => {
  try {
    const cwd = await root($)
    const ran = await $.process.run(
      ['python3', '-I', `${$.plugin.root}/crossing/door.py`, ...argv, '--by-module', '--cwd', cwd],
      { timeoutMs: 60000, env: { ...(await entrypoint($)), CLAUDE_PLUGIN_ROOT: $.plugin.root } },
    )
    return { ok: ran.exitCode === 0, text: (ran.exitCode === 0 ? ran.stdout : ran.stdout || ran.stderr).trim() }
  } catch (err) {
    return { ok: false, text: String(err) }
  }
}

// The home's plain files of one word (switch, mode, carry), as the door reads them; null where
// the project has no home the person switched on, or the door gave no such answer.
const words = async ($: any): Promise<Record<string, string> | null> => {
  const found = await door($, ['words'])
  if (!found.ok) return null
  try {
    const read = JSON.parse(found.text)
    return read !== null && typeof read === 'object' ? read : null
  } catch {
    return null
  }
}

// What the plain files of the project's home ask for.
const asked = async ($: any): Promise<{ mode: Mode; carry: Carry }> => {
  const read = await words($)
  // No home, or the person's switch (/crossings off): the cut is the harness's alone.
  if (read === null || read.switch === 'off') return { mode: 'native', carry: 'message' }
  const mode: Mode = read.mode === 'beside' || read.mode === 'own' ? read.mode : 'native'
  return { mode, carry: mode !== 'native' && read.carry === 'note' ? 'note' : 'message' }
}

// What a message carries: the frame, or failing that the hand-over page; nothing when there is neither.
const held = async ($: any): Promise<{ text: string; what: string }> => {
  // The frame, from the store. Making it also brings the archive up to this moment.
  const framed = await door($, ['frame', '--session', await $.session.id()])
  if (framed.ok && CARRIED.some((opening) => framed.text.startsWith(opening))) return { text: framed.text, what: 'frame' }
  // The page with its words beside it, as the door reads them; nothing where there is no page.
  const page = await door($, ['page'])
  return page.ok && page.text ? { text: `${NOTE}\n\n${page.text}`, what: 'hand-over' } : { text: '', what: '' }
}

const registerCut = (on: Parameters<Register>[0]) => {
  on('session.compact', async ($, e, next) => {
    // A subagent's own cut, and one the harness computes ahead of time, are never touched.
    if (e.agentId !== undefined || e.trigger === 'precompute') return next(e)
    const { mode, carry } = await asked($)
    if (mode === 'native') return next(e)

    // The trace of what was done is a convenience, written by the door; the cut goes on without it.
    const said = async (did: object) => {
      await door($, ['trace', JSON.stringify({ ...did, trigger: e.trigger, messagesBefore: e.messages.length })])
    }
    if (mode === 'beside' && carry === 'note') {
      // The cut stands as the harness makes it, whatever set it off: the harness also cuts by
      // itself while the person is away. The plugin's SessionStart hook brings the frame as
      // context when the session starts again, so nothing is added here, or it would cross twice.
      await said({ did: 'beside', carried: 'context, by the hook' })
      return next(e)
    }

    const { text, what } = await held($)
    if (!text) return next(e)
    const carried = { role: 'user' as const, text, toolUses: [] }
    // An automatic cut comes in the middle of work, so the harness's summary is kept there.
    if (mode === 'own' && e.trigger !== 'auto') {
      // An earlier cut's summary is all there is for the stretch before it until that
      // stretch has labels of its own, so it is carried on as the engine holds it.
      const earlier = e.messages[0]
      const isEarlier = earlier !== undefined && earlier.role === 'user' && earlier.text.startsWith(EARLIER)
      await said({ did: 'own', carried: 'message', what, chars: text.length, keptEarlierSummary: isEarlier })
      return { messages: isEarlier ? [earlier, carried] : [carried] }
    }
    const made = await next(e)
    if (made.skip !== undefined) return made
    // The engine's answer holds at least one message, the summary first: it refuses a cut that
    // leaves none. The frame goes after it.
    const { messages } = made
    await said({ did: 'beside', carried: 'message', what, chars: text.length })
    return { ...made, messages: [...messages.slice(0, 1), carried, ...messages.slice(1)] }
  }).catch(($, e, next) => next(e)) // a throw here leaves the cut to the harness
}

// --- the door ------------------------------------------------------------------------------
//
// The door's handles (look, labels, find, thread, mark, leave, status) are not registered here
// any more. They are served by crossing/serve.py, a server the plugin ships (.mcp.json), so
// that any harness that can be given a server can be given the door, and so that nothing a
// session reads names a script or a file. This module keeps what only a harness's hooks can
// do: the cut, and the person's own command, which shows the store through the same script.

// --- the command ---------------------------------------------------------------------------
//
// The person's own handle on this project: /crossings on and off turn the switch, a bare
// /crossings turns it over, and /crossings adopt switches on a home that already holds what this
// computer has no record of switching on (a crossings/ folder that came with a repository: on
// alone, the door says what is there and switches nothing on). Status, look, find, labels and
// frame show what the store holds
// through the same script the session's tool uses, so both have a hand on the same door. The
// switch is one word in the `switch` file of the project's home; the hooks, the cut and a
// status line read it, and off means no cut is counted, noted or answered here. The door
// turns it (`door.py switch`), since switching on is also what makes a home for a project
// that has none, and where that home lies is the door's to say. Switching off also keeps the
// moment, and switching on again closes the span: nothing said inside one is ever kept.

const registerCommand = (on: Parameters<Register>[0]) => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'crossings',
      description:
        'Switch Crossings on or off for this project (/crossings on, off, or bare to turn it over; adopt takes a home that came ' +
        'with the project), or see what its store holds: ' +
        '/crossings status, look, find <words>, labels [relation|work|door|a day|ids], frame',
    })
    return next(e)
  })

  on('command.run', { command: 'crossings' }, async ($, e) => {
    const [first = '', ...rest] = e.args.trim().split(/\s+/)
    const said = first.toLowerCase()
    const shown = async (argv: string[]) => ({ text: (await door($, [...argv, '--session', await $.session.id()])).text || 'Nothing came back.' })
    if (said === 'status') {
      const read = await words($)
      if (read === null) return { text: 'Crossings was never switched on for this project.' }
      const isOff = read.switch === 'off' // no switch written: on
      const out = await door($, ['status', '--session', await $.session.id()])
      return { text: `${isOff ? 'Crossings is off for this project.' : 'Crossings is on for this project.'} ${out.text}` }
    }
    if (said === 'look' || said === 'frame') return shown([said])
    if (said === 'find') return rest.length ? shown(['find', ...rest]) : { text: 'find needs words: /crossings find <words>' }
    if (said === 'labels') {
      const argv = ['labels']
      for (const one of rest) {
        const low = one.toLowerCase()
        if (low === 'relation' || low === 'standing') argv.push('--kind', 'relation')
        else if (low === 'work') argv.push('--kind', 'work')
        else if (low === 'door' || low === 'next') argv.push('--kind', 'next')
        else if (/^\d{4}-\d\d-\d\d$/.test(one)) argv.push('--day', one)
        else argv.push(one)
      }
      return shown(argv)
    }
    // Only a bare /crossings turns the switch over. A word it does not know changes nothing:
    // a slip of the hand must not switch Crossing off.
    if (said !== '' && said !== 'on' && said !== 'off' && said !== 'adopt') {
      return { text: `/crossings takes: on, off, adopt, status, look, find <words>, labels, frame. "${first}" is none of these; nothing was changed.` }
    }
    // The session the person turns the switch from is told what it now means, as context after
    // the answer, which the person is not shown: switched off, that nothing said from now until
    // it is switched on again is kept or can be reached through the door, and that it is to mark
    // nothing of it; switched on again, that it is kept again; and, by the rule a session's start
    // is welcomed by, the welcome. The door says which is due, and nothing otherwise; the
    // plugin's hooks then need no hook at every prompt to say it.
    let session = ''
    try {
      session = await $.session.id()
    } catch {
      session = ''
    }
    // The door turns the switch and says how it now stands: on, off, or never switched on. Given
    // the session, it notes by id what that session said while it was off, as the span closes.
    const text = (await door($, ['switch', said || 'toggle', ...(session ? ['--session', session] : [])])).text || 'Nothing came back.'
    if (!session) return { text }
    const told = await door($, ['welcome', session])
    return told.ok && told.text ? { text, context: [told.text] } : { text }
  })
}

// --- the archive's own files ------------------------------------------------------------------
//
// What was said is reached through the door's tools. Text a session reads can steer it to open
// the archive around the door: a home's said/ folder, its index (store.db), or a words page, which
// gives what was said word for word. A call of the session's that names any of them is refused, in
// one sentence that names the door's tools; and so is one that names any other path below a home
// that is none of the files a session may read there (READABLE), whatever its folder is named, so
// that a link made inside a home is no way round. The homes are those outside a project (the
// folder CROSSING_HOMES names, else ~/.claude/crossing/homes), the home on this computer
// (CROSSING_OURS, else ~/.claude/crossing/ours), a home named outright (CROSSING_HOME), and a
// project's own crossings/ folder, wherever it stands. The label pages, the pages of the cuts and
// the other plain files a session may read stay readable: the person reads those beside the work,
// and so may the session.
//
// It is decided at every tool call, so it is decided by string checks on the call's input alone:
// no process is started and no file is opened. A cheap check is no wall: a path it cannot see in
// the call's text (a `cd` into a home and a relative name after it, a search of a whole home)
// is not caught. The door's own tools are not looked at, nor the plugin's own reads, which are
// no tool calls of the session's; a shell call of door.py names no such path and runs.
//
// What is the person's alone is guarded the same way. A shell command that runs door.py with one
// of the person's verbs (switch, strike, layer, copy), with a verb that writes a kept file for the
// hooks module (trace, welcome), or with an option that hands it a transcript, names a model or
// speaks for the plugin (--transcript, --session, --model, --by-hook, --by-module) is refused; so
// is a shell command, or a call of a tool that writes a file, that names the person's record of
// switches, or a small file of a home a hook or the door alone writes (KEPT). The files of a home
// that the door alone writes and the person reads (WRITTEN_BY_DOOR: the label pages, the hand-over
// and every words page, what was struck, the model behind a call, the ids noted as looking like a
// key, the pages of the cuts, the one-line settings) are refused to a tool that writes a file, and to a
// shell command that names one in any part of it that is not a plain read (a command of READS
// with no `>` in it); reading them stays open, but for a words page. A shell command that runs the hand-over's words
// script is the person's too. A command's quotes and backslashes are taken out before any of this. These too are string checks: against a session with a shell, the
// wall is the person's own approval of the commands it runs.

const REFUSED =
  "What was said is reached through the door's tools (look, labels, find and thread), not by opening the archive's own " +
  'files, so this call was not run.'
const PERSONS =
  "This is the person's to run, from their own terminal or with the plugin's command (/crossings), so this call was not run."
const WRITTEN =
  "This file of the home is written through the door (a label by mark or leave) or by the person's own hand, not by a " +
  "session's call, so this call was not run."

// The keys of a call's input that name a path, or hold a shell's command.
const NAMING = ['file_path', 'notebook_path', 'path', 'command'] as const
// Where a name of the archive ends: a separator, the end, or a mark of the shell's.
const END = String.raw`(?=$|[/\s'"\x60;|&()<>*?{}\[\],])`
const ARCHIVE = String.raw`(?:said${END}|store\.db\b)`
const escaped = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const trimmed = (folder: string) => folder.replace(/\\/g, '/').replace(/\/+$/, '')

// The paths and commands a call names, as one text, with a separator of one kind and the
// person's own folder spelled out where the shell would spell it.
const named = (e: Record<string, unknown>, home: string): string => {
  // A shell's quotes and backslashes are taken out of a command first, as the shell takes them out:
  // `crossings/'said'` and `crossings/sa\id` name `crossings/said`. A file tool's path keeps its own.
  const said = NAMING.map(key => (key === 'command' && typeof e[key] === 'string' ? (e[key] as string).replace(/['"\\]/g, '') : e[key]))
    .filter((v): v is string => typeof v === 'string')
  for (const key of ['file_paths', 'paths']) {
    const many = e[key]
    if (Array.isArray(many)) said.push(...many.filter((v): v is string => typeof v === 'string'))
  }
  for (const key of ['pattern', 'glob']) {
    // A search's own pattern names files only where the tool is one that lists files by it.
    const value = e[key]
    if (typeof value === 'string' && (e.tool === 'Glob' || key === 'glob')) {
      said.push(value, `${typeof e.path === 'string' ? e.path : ''}/${value}`)
    }
  }
  let text = said.join('\n').replace(/\\/g, '/')
  if (home) text = text.replace(/\$\{HOME\}|\$HOME\b/g, home).replace(/(^|[\s'"=:])~(?=\/)/g, `$1${home}`)
  text = text.replace(/\/(?:\.\/)+/g, '/').replace(/\/{2,}/g, '/')
  // A folder and a `..` after it are no step at all: `crossings/labels/../said` is `crossings/said`.
  for (let before = ''; before !== text;) {
    before = text
    text = text.replace(/(^|[\/\s'"=])(?!\.\.(?:[\/\s'"\x60]|$))[^\/\s'"\x60]+\/\.\.(?=[\/\s'"\x60]|$)\/?/g, '$1')
  }
  return text.replace(/\/{2,}/g, '/')
}

// The small files of a home a session is not to write or take away: the record of when Crossing
// was off, of where each transcript stood as it was switched off, and of what was said then, which model wrote each label, the files of session ids, how far
// each transcript was read, the sentences said once, what was pulled, the lock, a copy's stage, and
// the traces of the last cut and the last frame.
const KEPT = String.raw`(?:(?:off|unsaid|models|welcomed|told|there|unattended|shelled|labelled|arrived|collided|passed-over|ignore-told|copy-told|damaged-told|copy-stage|models-met|models-arrived)\.txt\b|(?:markers|reached|off-places)\.jsonl\b|archive\.lock\b|last-(?:carry|cut)\.json\b)`
// The files of a home the door alone writes, which a session may read: the label pages, the hand-over
// and every words page, what was struck, the model behind a call, the ids noted as looking like a key,
// the pages of the cuts and their sidecars, the one-line settings, the project's name and the ignore file.
const WRITTEN_BY_DOOR =
  String.raw`(?:labels${END}|hand-over\.md\b|[^/\s'"\x60]+\.words\.md\b|(?:struck|calling|flagged)\.txt\b|[^/\s'"\x60]+-cut-\d+\.(?:md|json)\b|(?:copy|switch|mode|carry|frame-size|retelling-length|retelling-share|project|\.gitignore)${END})`

// Where a path below a home ends, for the files a session may read there: a mark of the shell's, a
// quote, a space or the end, and never a separator, so that nothing reached through one of them is
// taken for it.
const STOP = String.raw`(?=$|[\s'"\x60;|&()<>{}\[\],])`
// The files below a home a session may read, by the lists above: every file of KEPT, and every file of
// WRITTEN_BY_DOOR but a words page, which holds what was said word for word; the label pages only as
// the folder labels/ and its own pages, one step below it.
const READABLE = String.raw`(?:${KEPT}|labels/?|labels/[^/\s'"\x60]+\.md|hand-over\.md|(?:struck|calling|flagged)\.txt|[^/\s'"\x60]+-cut-\d+\.(?:md|json)|(?:copy|switch|mode|carry|frame-size|retelling-length|retelling-share|project|\.gitignore))${STOP}`
// Any other path below a home: whatever its folder is named, so that a link made inside a home (an
// alias of said/, or of the home itself) is no way round the check on the archive's files.
const BELOW = String.raw`(?!${READABLE})(?=[^\s'"\x60;|&()<>{}\[\],])`

// The places of the archive's files, or of the home's kept files, as patterns over that text.
const places = (homes: string, ours: string, outright: string, files = ARCHIVE): RegExp[] => {
  const found = [
    String.raw`(?:^|[^\w.-])crossings/${files}`, // a project's own home, wherever the project stands
    String.raw`\.claude/crossing/homes/[^/\s'"\x60]+/${files}`, // the default homes, however the path begins
    String.raw`\.claude/crossing/ours/${files}`,
  ]
  if (homes) found.push(`${escaped(trimmed(homes))}/[^/\\s'"\\x60]+/${files}`)
  for (const one of [ours, outright]) if (one) found.push(`${escaped(trimmed(one))}/${files}`)
  return found.map(pattern => new RegExp(pattern, 'i')) // a Mac's folders are not told apart by case
}

// A shell command that runs the door with what is the person's alone: in any one of its commands
// (split at ; & | and line breaks), door.py, or the module crossing.door, and, after it, a verb or
// an option of theirs.
const DOOR = /door\.py\b|\bcrossing\.door\b/i
const THEIRS =
  /(?:^|[\s'"=])(?:switch|strike|layer|copy|trace|welcome|--transcript|--session|--model|--by-hook|--by-module)(?=$|[\s'"=])/i
const PARTS = /[;&|\n]/ // where one command of a shell's line ends and the next begins
const runsTheirs = (command: string): boolean =>
  command.split(PARTS).some(part => DOOR.test(part) && THEIRS.test(part.slice(part.search(DOOR))))

// The commands that only read the files they name.
const READS = new Set(['cat', 'head', 'tail', 'less', 'more', 'grep', 'egrep', 'fgrep', 'rg', 'wc', 'ls', 'stat', 'file',
  'diff', 'cmp', 'nl', 'cut', 'md5', 'md5sum', 'shasum', 'sha256sum'])
const commandOf = (part: string): string[] =>
  part.trim().split(/\s+/).filter(word => !/^[A-Za-z_]\w*=/.test(word)) // an assignment before the command
const plainRead = (part: string): boolean => {
  const said = part.replace(/\d*>\s*\/dev\/null|\d*>&\d/g, ' ') // what is sent to nowhere writes nothing
  const first = (commandOf(said)[0] ?? '').replace(/^.*\//, '')
  return READS.has(first) && !/>/.test(said)
}
// A shell command that runs the hand-over's words script (crossing/handover.py), which writes a words
// page into a home: the person's to run, as the door's own verbs are. Read, the script is a file as any.
const PYTHON = /^python(?:3(?:\.\d+)?)?$/
const runsHelper = (command: string): boolean =>
  command.split(PARTS).some(part => {
    const words = commandOf(part.replace(/['"\\]/g, ''))
    const first = (words[0] ?? '').replace(/^.*\//, '')
    if (first === 'handover.py') return true // the script itself, by its own first line
    if (!PYTHON.test(first)) return false
    const at = words.findIndex((word, n) => n > 0 && !word.startsWith('-'))
    return (at > 0 && /(?:^|\/)handover\.py$/.test(words[at] ?? '')) || words.some((word, n) => word === '-m' && words[n + 1] === 'crossing.handover')
  })
// A shell command that names a file of `places` in any part of it that is not a plain read.
const writesTo = (command: string, home: string, found: RegExp[]): boolean =>
  command.replace(/\d*>&\d/g, ' ').split(PARTS).some(part => found.some(place => place.test(named({ command: part }, home))) && !plainRead(part))

// The person's record of switches, by its default place or the one CROSSING_SWITCHED names.
const recordOf = (switched: string): RegExp[] =>
  [/\.claude\/crossing\/switched\b/i, ...(switched ? [new RegExp(`${escaped(trimmed(switched))}\\b`, 'i')] : [])]

// The tools that write or take away a file by its path.
const WRITES = ['Write', 'Edit', 'MultiEdit', 'NotebookEdit']

const registerGuard = (on: Parameters<Register>[0]) => {
  on('tool.call', async ($, e, next) => {
    if (e.tool.startsWith('mcp__plugin_crossing_door__')) return next(e)
    const given = e as unknown as Record<string, unknown>
    const home = trimmed((await $.env.get('HOME')) ?? '')
    const text = named(given, home)
    if (!text) return next(e)
    const homes = (await $.env.get('CROSSING_HOMES')) ?? ''
    const ours = (await $.env.get('CROSSING_OURS')) ?? ''
    const outright = (await $.env.get('CROSSING_HOME')) ?? ''
    if (places(homes, ours, outright).some(place => place.test(text))) return { deny: REFUSED }
    const command = typeof given.command === 'string' ? given.command : ''
    if (command && (runsTheirs(command) || runsHelper(command))) return { deny: PERSONS }
    if (command || WRITES.includes(e.tool)) {
      const switched = (await $.env.get('CROSSING_SWITCHED')) ?? ''
      const kept = [...places(homes, ours, outright, KEPT), ...recordOf(switched)]
      if (kept.some(place => place.test(text))) return { deny: PERSONS }
      const byDoor = places(homes, ours, outright, WRITTEN_BY_DOOR)
      if (command ? writesTo(command, home, byDoor) : byDoor.some(place => place.test(text))) return { deny: WRITTEN }
    }
    // Read or written, a path below a home that is none of the files a session may read there.
    if (places(homes, ours, outright, BELOW).some(place => place.test(text))) return { deny: REFUSED }
    return next(e)
  }).catch(($, e, next) => next(e)) // a fault here never stops the session's work
}

export const register: Register = on => {
  registerCut(on)
  registerCommand(on)
  registerGuard(on)
}
