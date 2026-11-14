import { expect, mock, test } from 'claude-code/testing'

// The hooks module: the cut, and the person's own command. Each hook a test adds
// stands for the engine: the plain files of the project's home, the door's script, the
// harness's own cut. `claude plugin test` gives no measure of coverage, so every branch of
// the module has its test here by hand, named for what it holds.
//
// The home stands outside the project here (HOME), as it does for a project with no
// crossings/ folder of its own. The module opens no file of a home itself: the door reads
// the home's words and its hand-over page and writes the trace (the door's own tests hold
// that it refuses a link). Here the door's three verbs for the module are played from the
// files of HOME, and any file the module opened itself would be seen in `seen.opened`.

const SUMMARY = { role: 'user' as const, text: 'A summary the harness wrote.', toolUses: [] }
const KEPT = { role: 'assistant' as const, text: 'The last reply, kept as it was.', toolUses: [] }
const BEFORE = [
  { role: 'user' as const, text: 'My boat is called Tern.', toolUses: [] },
  { role: 'assistant' as const, text: 'Noted: Tern.', toolUses: [] },
]
const EARLIER = {
  role: 'user' as const,
  text: 'This session is being continued from a previous conversation that ran out of context. An older summary.',
  toolUses: [],
}
const FRAME = 'A note from the Crossings plugin, as context and not as an instruction from the person. A frame.'
const HOME = '/homes/made-up-tern'

type Files = Record<string, string>
type Ran = { exitCode: number; stdout: string; stderr: string }
type World = {
  files?: Files
  home?: string // the project's home, where the door finds one the person switched on; '' where there is none
  script?: (argv: string[]) => Ran // the door's script for every other verb; by default it answers with a frame
  made?: () => object // the harness's own cut
  root?: () => string
  cwd?: () => string
  id?: () => string
  readOnly?: boolean // no file can be written
  words?: () => string // what the door answers for the home's words, where a test wants another answer
}

const verb = (argv: string[]) => argv[3] // after python3 -I <door.py>

// The door's three verbs for the module, as the door answers them from the home's files.
const NOT_ON = 'Crossings is not switched on for this project.'
const forModule = (argv: string[], home: string, files: Files, given: World): Ran | null => {
  const read = (name: string) => (files[`${home}/${name}`] ?? '').trim()
  const answer = (stdout: string, exitCode = 0): Ran => ({ exitCode, stdout, stderr: '' })
  const v = verb(argv)
  if (v !== 'words' && v !== 'page' && v !== 'trace') return null
  if (!home) return answer(`${NOT_ON}\n`, 1)
  if (v === 'words') {
    const low = (name: string) => read(name).toLowerCase()
    return answer(given.words ? given.words() : `${JSON.stringify({ switch: low('switch'), mode: low('mode'), carry: low('carry') })}\n`)
  }
  if (v === 'page') {
    const page = read('hand-over.md')
    const words = read('hand-over.words.md')
    return page ? answer(`${page}${words ? `\n\n${words}` : ''}\n`) : answer('', 1)
  }
  if (given.readOnly) return { exitCode: 1, stdout: '', stderr: 'read-only' }
  const did = argv[4]
  if (did === undefined) return { exitCode: 2, stdout: '', stderr: 'trace needs what was done' }
  files[`${home}/last-cut.json`] = did
  return answer('')
}

const world = (on: any, given: World = {}) => {
  const seen = {
    ran: [] as string[][], inits: [] as any[], files: { ...(given.files ?? {}) } as Files, registered: [] as string[], opened: [] as string[],
  }
  const home = given.home ?? HOME
  on('session.root', () => ({ value: (given.root ?? (() => '/project'))() }))
  on('session.cwd', () => ({ value: (given.cwd ?? (() => '/elsewhere'))() })) // where a shell `cd` left the session
  on('session.id', () => ({ value: (given.id ?? (() => 'abcdef01-0000'))() }))
  on('fs.read', (_: unknown, e: { path: string }) => {
    seen.opened.push(`read ${e.path}`)
    throw new Error('the module reads no file of its own')
  })
  on('fs.write', (_: unknown, e: { path: string }) => {
    seen.opened.push(`write ${e.path}`)
    throw new Error('the module writes no file of its own')
  })
  on('process.run', (_: unknown, e: { argv: readonly string[]; init?: unknown }) => {
    seen.ran.push([...e.argv])
    seen.inits.push(e.init)
    const played = forModule([...e.argv], home, seen.files, given)
    if (played !== null) return { value: played }
    return { value: (given.script ?? (() => ({ exitCode: 0, stdout: FRAME, stderr: '' })))([...e.argv]) }
  })
  on('session.compact', () => (given.made ?? (() => ({ messages: [SUMMARY, KEPT] })))())
  on('session.start', (_: unknown, e: { cwd: string }) => ({ cwd: e.cwd }))
  on('command.register', (_: unknown, e: { name: string }) => {
    seen.registered.push(`command ${e.name}`)
    return { value: { command: e.name } }
  })
  on('tool.register', (_: unknown, e: { name: string }) => {
    seen.registered.push(`tool ${e.name}`)
    return { value: { tool: `mcp__crossing__${e.name}` } }
  })
  return seen
}

const asks = (mode: string, carry: string, more: Files = {}): Files => ({
  [`${HOME}/mode`]: `${mode}\n`,
  [`${HOME}/carry`]: `${carry}\n`,
  ...more,
})
const trace = (seen: { files: Files }) => JSON.parse(seen.files[`${HOME}/last-cut.json`] ?? '{}')
const texts = (made: any) => made.messages?.map((m: { text: string }) => m.text)
const failing = (): Ran => ({ exitCode: 1, stdout: '', stderr: 'the store could not be opened' })
const verbs = (seen: { ran: string[][] }) => seen.ran.map(verb)

// --- the cut -------------------------------------------------------------------------------

for (const [trigger, kind] of [['auto', 'a cut that came by itself'], ['manual', 'a chosen cut']] as const) {
  test(`with the word note, ${kind} is left as the harness made it`, async ($, on) => {
    // The harness also cuts by itself while the person is away, and calls that automatic. With
    // the word note the module adds nothing there either: the hook brings the frame, as context.
    const seen = world(on, { files: asks('beside', 'note') })
    const made = await $.session.compact({ trigger, messages: BEFORE })
    expect(made.messages).toEqual([SUMMARY, KEPT])
    expect(verbs(seen)).toEqual(['words', 'trace']) // no frame is made here: the hook makes the one that is carried
    expect(trace(seen).carried).toBe('context, by the hook')
    expect(trace(seen).trigger).toBe(trigger)
  })
}

test('with the word message, the frame goes into the answer after the summary', async ($, on) => {
  const seen = world(on, { files: asks('beside', 'message') })
  const made = await $.session.compact({ trigger: 'auto', messages: BEFORE })
  expect(texts(made)).toEqual([SUMMARY.text, FRAME, KEPT.text])
  expect(verbs(seen)).toEqual(['words', 'frame', 'trace'])
  expect(seen.opened).toEqual([]) // every file of the home was the door's to read and write
  for (const [n, argv] of seen.ran.entries()) {
    expect(argv.slice(-3)).toEqual(['--by-module', '--cwd', '/project']) // the door is given the project's root, not the shell's directory
    expect(argv).not.toContain('/elsewhere')
    // and it is told the plugin's own module calls it: the flag, with the plugin's folder in CLAUDE_PLUGIN_ROOT
    const root = seen.inits[n]?.env?.CLAUDE_PLUGIN_ROOT
    expect(typeof root === 'string' && root.length > 0 && argv[2] === `${root}/crossing/door.py`).toBe(true)
  }
  expect(trace(seen)).toEqual({ did: 'beside', carried: 'message', what: 'frame', chars: FRAME.length, trigger: 'auto', messagesBefore: 2 })
})

test('the home is the folder the door names, and nothing is read or written in the project itself', async ($, on) => {
  // Files of the same names inside the project are not the home's: only the door says where the home is.
  const inProject = { '/project/crossings/mode': 'native\n', '/project/crossings/switch': 'off\n' }
  const seen = world(on, { files: asks('beside', 'message', inProject) })
  expect(texts(await $.session.compact({ trigger: 'manual', messages: BEFORE }))).toEqual([SUMMARY.text, FRAME, KEPT.text])
  expect(Object.keys(seen.files).filter(path => path.startsWith('/project')).sort()).toEqual(Object.keys(inProject).sort())
  expect(seen.files[`${HOME}/last-cut.json`]).toContain('"did":"beside"')
})

test('where Crossing was never switched on, the cut is left to the harness and nothing is written', async ($, on) => {
  // The project has no home. A crossings/ folder the door did not name decides nothing.
  const files = { '/project/crossings/mode': 'beside\n', '/project/crossings/carry': 'message\n' }
  const seen = world(on, { home: '', files })
  expect((await $.session.compact({ trigger: 'manual', messages: BEFORE })).messages).toEqual([SUMMARY, KEPT])
  expect(verbs(seen)).toEqual(['words']) // the door was asked for the home's words, and for nothing else
  expect(seen.files).toEqual(files)
})

test('with no word for carrying, a message is how it goes', async ($, on) => {
  world(on, { files: { [`${HOME}/mode`]: 'beside\n' } })
  expect(texts(await $.session.compact({ trigger: 'manual', messages: BEFORE }))).toEqual([SUMMARY.text, FRAME, KEPT.text])
})

test('a project that has not asked, or is switched off, keeps the cut as it is', async ($, on) => {
  const off = world(on, { files: asks('beside', 'message', { [`${HOME}/switch`]: 'off\n' }) })
  expect((await $.session.compact({ trigger: 'manual', messages: BEFORE })).messages).toEqual([SUMMARY, KEPT])
  expect(verbs(off)).toEqual(['words'])
  expect(off.files[`${HOME}/last-cut.json`]).toBe(undefined)
})

test('a project with no mode, or an unknown one, keeps the cut as it is', async ($, on) => {
  const seen = world(on, { files: asks('sideways', 'message') })
  expect((await $.session.compact({ trigger: 'manual', messages: BEFORE })).messages).toEqual([SUMMARY, KEPT])
  expect(verbs(seen)).toEqual(['words'])
  expect(seen.files[`${HOME}/last-cut.json`]).toBe(undefined)
})

test("a subagent's own cut, and one computed ahead of time, are never touched", async ($, on) => {
  const seen = world(on, { files: asks('beside', 'message') })
  expect((await $.session.compact({ trigger: 'auto', messages: BEFORE, agentId: 'agent-1' })).messages).toEqual([SUMMARY, KEPT])
  expect((await $.session.compact({ trigger: 'precompute', messages: BEFORE })).messages).toEqual([SUMMARY, KEPT])
  expect(seen.ran).toEqual([])
})

test("the plugin's own cut answers a chosen cut in the harness's place", async ($, on) => {
  const seen = world(on, { files: asks('own', 'message'), made: () => { throw new Error('the harness was not to be asked') } })
  expect(texts(await $.session.compact({ trigger: 'manual', messages: BEFORE }))).toEqual([FRAME])
  expect(trace(seen)).toEqual({ did: 'own', carried: 'message', what: 'frame', chars: FRAME.length, keptEarlierSummary: false, trigger: 'manual', messagesBefore: 2 })
  // An earlier cut's summary is all there is for the stretch before it, so it is carried on.
  expect(texts(await $.session.compact({ trigger: 'manual', messages: [EARLIER, ...BEFORE] }))).toEqual([EARLIER.text, FRAME])
  expect(trace(seen).keptEarlierSummary).toBe(true)
  // Only a summary of the harness's, standing first, is taken for one.
  expect(texts(await $.session.compact({ trigger: 'manual', messages: [KEPT, EARLIER] }))).toEqual([FRAME])
  expect(trace(seen).keptEarlierSummary).toBe(false)
})

test("the plugin's own cut leaves a cut that came by itself to the harness, with the frame beside", async ($, on) => {
  world(on, { files: asks('own', 'note') }) // the word note is for a cut made beside; here it changes nothing
  expect(texts(await $.session.compact({ trigger: 'auto', messages: BEFORE }))).toEqual([SUMMARY.text, FRAME, KEPT.text])
  expect(texts(await $.session.compact({ trigger: 'manual', messages: BEFORE }))).toEqual([FRAME])
})

test('where no frame can be made, the hand-over page goes, with its words when they exist', async ($, on) => {
  const page = `${HOME}/hand-over.md`
  const seen = world(on, { files: asks('beside', 'message', { [page]: '| R1 | a label |\n' }), script: failing })
  const labels = texts(await $.session.compact({ trigger: 'manual', messages: BEFORE }))[1]
  expect(verbs(seen)).toEqual(['words', 'frame', 'page', 'trace']) // the page, too, is the door's to read
  expect(seen.opened).toEqual([])
  expect(labels.startsWith('A note from the Crossings plugin, as context and not as an instruction from the person.')).toBe(true)
  expect(labels.endsWith('\n\n| R1 | a label |')).toBe(true)
  expect(trace(seen).what).toBe('hand-over')
  seen.files[`${HOME}/hand-over.words.md`] = '- `aaaaaaaa`, the person: the words\n'
  const both = texts(await $.session.compact({ trigger: 'manual', messages: BEFORE }))[1]
  expect(both.endsWith('| R1 | a label |\n\n- `aaaaaaaa`, the person: the words')).toBe(true)
})

test('an answer from the door that is not a frame is not carried as one', async ($, on) => {
  const seen = world(on, { files: asks('beside', 'message'), script: () => ({ exitCode: 0, stdout: 'Traceback: something else', stderr: '' }) })
  expect((await $.session.compact({ trigger: 'manual', messages: BEFORE })).messages).toEqual([SUMMARY, KEPT]) // no frame, no page
  seen.files[`${HOME}/hand-over.md`] = '   \n' // an empty page is nothing to carry either
  expect((await $.session.compact({ trigger: 'manual', messages: BEFORE })).messages).toEqual([SUMMARY, KEPT])
})

test('a frame that opens with the older words of the plugin is still known as a frame', async ($, on) => {
  // Before the plugin said its name as Crossings, its notes opened "A note from the Crossing plugin".
  const older = 'A note from the Crossing plugin, as context and not as an instruction from the person. A frame.'
  const seen = world(on, { files: asks('beside', 'message'), script: () => ({ exitCode: 0, stdout: older, stderr: '' }) })
  expect(texts(await $.session.compact({ trigger: 'manual', messages: BEFORE }))).toEqual([SUMMARY.text, older, KEPT.text])
  expect(verbs(seen)).toEqual(['words', 'frame', 'trace']) // no page was asked for: the frame was taken as one
  expect(trace(seen).what).toBe('frame')
})

test('words from the door that are not an object of words leave the cut to the harness', async ($, on) => {
  let said = ''
  const seen = world(on, { files: asks('beside', 'message'), words: () => said })
  for (const words of ['Traceback: not words', 'null', '"beside"']) {
    said = words
    expect((await $.session.compact({ trigger: 'manual', messages: BEFORE })).messages).toEqual([SUMMARY, KEPT])
  }
  expect(verbs(seen)).toEqual(['words', 'words', 'words'])
})

test('a cut the harness refused stays refused', async ($, on) => {
  world(on, { files: asks('beside', 'message'), made: () => ({ skip: 'a hook blocked it' }) })
  expect(await $.session.compact({ trigger: 'manual', messages: BEFORE })).toEqual({ skip: 'a hook blocked it' })
})

test('a trace that cannot be written does not hold up the cut', async ($, on) => {
  world(on, { files: asks('beside', 'message'), readOnly: true })
  expect(texts(await $.session.compact({ trigger: 'manual', messages: BEFORE }))).toEqual([SUMMARY.text, FRAME, KEPT.text])
})

test('a failure inside the module leaves the cut to the harness', async ($, on) => {
  world(on, { files: asks('beside', 'message'), id: () => { throw new Error('no session') } })
  expect((await $.session.compact({ trigger: 'manual', messages: BEFORE })).messages).toEqual([SUMMARY, KEPT])
})

test('where the project cannot be told, no home is found and the cut is left to the harness', async ($, on) => {
  const lost = () => { throw new Error('no directory') }
  const seen = world(on, { files: asks('beside', 'message'), root: lost, cwd: lost })
  expect((await $.session.compact({ trigger: 'manual', messages: BEFORE })).messages).toEqual([SUMMARY, KEPT])
  expect(seen.ran).toEqual([]) // the door was never started: there was no project to start it for
  expect(seen.files[`${HOME}/last-cut.json`]).toBe(undefined)
})

test('on a build with no project root, the directory the session runs in is used', async ($, on) => {
  const seen = world(on, {
    files: { [`${HOME}/mode`]: 'beside\n' },
    root: () => { throw new Error('no such call') },
  })
  expect(texts(await $.session.compact({ trigger: 'manual', messages: BEFORE }))).toEqual([SUMMARY.text, FRAME, KEPT.text])
  expect(seen.ran.map(argv => argv.slice(-2))).toEqual([['--cwd', '/elsewhere'], ['--cwd', '/elsewhere'], ['--cwd', '/elsewhere']])
})

const asked = (seen: { ran: string[][] }) => (seen.ran[seen.ran.length - 1] ?? []).slice(3) // after python3 -I <door.py>; [] where nothing ran

// --- the switch ----------------------------------------------------------------------------

const start = ($: any) => $.session.start({ cwd: '/elsewhere', surface: 'terminal', isInteractive: true })
const say = async ($: any, args: string) => (await $.command.run({ command: 'crossings', args })).text
// The door's own switch, as far as the module can tell: it says what it was told to do.
const switching = (argv: string[]): Ran => ({ exitCode: 0, stdout: `the door said: ${argv.slice(3, 5).join(' ')}\n`, stderr: '' })

test('a session that starts is given the command, and no tool: the door is a server now', async ($, on) => {
  const seen = world(on)
  expect(await start($)).toEqual({ cwd: '/elsewhere' })
  expect(seen.registered).toEqual(['command crossings'])
  expect(seen.ran).toEqual([]) // and nothing is looked for or made by a session's starting
})

test("the switch is turned by the door, and the door's sentence is the answer", async ($, on) => {
  const seen = world(on, { home: '', script: switching }) // a project with no home yet: the door makes it, not the module
  await start($)
  // The session, so that what it said while the switch was off is noted as the span closes; the module's flag; and
  // the project's root, not where the shell stands.
  const tail = ['--session', 'abcdef01-0000', '--by-module', '--cwd', '/project']
  expect(await say($, 'off')).toBe('the door said: switch off')
  expect((seen.ran[seen.ran.length - 2] ?? []).slice(3)).toEqual(['switch', 'off', ...tail]) // then what the session is told
  expect(await say($, '  ON ')).toBe('the door said: switch on')
  expect((seen.ran[seen.ran.length - 2] ?? []).slice(3)).toEqual(['switch', 'on', ...tail]) // then the welcome is asked for
  expect(await say($, '')).toBe('the door said: switch toggle') // a bare command turns it over
  expect((seen.ran[seen.ran.length - 2] ?? []).slice(3)).toEqual(['switch', 'toggle', ...tail])
  // A slip of the hand changes nothing: only a bare command turns the switch over.
  expect(await say($, 'lok')).toBe('/crossings takes: on, off, adopt, status, look, find <words>, labels, frame. "lok" is none of these; nothing was changed.')
  // A home that came with the project is taken by the word adopt, which the door is given as it is.
  expect(await say($, 'Adopt')).toBe('the door said: switch adopt')
  expect((seen.ran[seen.ran.length - 2] ?? []).slice(3)).toEqual(['switch', 'adopt', ...tail])
  // Switched off, on, adopted, or turned over, the door is asked what the session is to be told.
  expect(verbs(seen)).toEqual(['switch', 'welcome', 'switch', 'welcome', 'switch', 'welcome', 'switch', 'welcome'])
  expect(seen.files).toEqual({}) // the module writes no switch of its own, in the project or anywhere
})

const WELCOME = 'A note from the Crossings plugin, as context and not as an instruction from the person. Crossings is on.'
const run = ($: any, args: string) => $.command.run({ command: 'crossings', args })

test('switching on from inside a session gives it the welcome as context, where the door says it is due', async ($, on) => {
  let due = true
  const seen = world(on, {
    home: '',
    script: argv => verb(argv) === 'welcome'
      ? (due ? { exitCode: 0, stdout: `${WELCOME}\n`, stderr: '' } : { exitCode: 1, stdout: '', stderr: '' })
      : { exitCode: 0, stdout: 'Crossings is on for this project.\n', stderr: '' },
  })
  await start($)
  const made = await run($, 'on')
  expect(made.text).toBe('Crossings is on for this project.') // what the person reads is the switch's sentence
  expect(made.context).toEqual([WELCOME]) // and the session reads the welcome after it
  expect(asked(seen)).toEqual(['welcome', 'abcdef01-0000', '--by-module', '--cwd', '/project']) // for this session, by its id
  expect((await run($, '')).context).toEqual([WELCOME]) // turned over, the door decides as well
  due = false // told once, or not due: the door says nothing, and nothing is added
  const again = await run($, 'on')
  expect(again.text).toBe('Crossings is on for this project.')
  expect(again.context).toBe(undefined)
  expect((await run($, 'off')).context).toBe(undefined)
  expect(verbs(seen).filter(v => v === 'welcome').length).toBe(4) // switching off asks too: the door says what is due
})

const UNKEPT = 'A note from the Crossings plugin, as context and not as an instruction from the person. Crossings is off.'
const AGAIN = 'A note from the Crossings plugin, as context and not as an instruction from the person. Crossings is on again.'

test('switching off from inside a session tells it, as context, that nothing is kept from now on', async ($, on) => {
  let now = 'off'
  const seen = world(on, {
    script: argv => verb(argv) === 'welcome'
      ? { exitCode: 0, stdout: `${now === 'off' ? UNKEPT : AGAIN}\n`, stderr: '' }
      : { exitCode: 0, stdout: `Crossings is ${now} for this project.\n`, stderr: '' },
  })
  await start($)
  const made = await run($, 'off')
  expect(made.text).toBe('Crossings is off for this project.') // what the person reads is the switch's sentence
  expect(made.context).toEqual([UNKEPT]) // and the session reads the note after it
  expect(asked(seen)).toEqual(['welcome', 'abcdef01-0000', '--by-module', '--cwd', '/project'])
  now = 'on again'
  expect((await run($, '')).context).toEqual([AGAIN]) // turned over and on again, the door says that too
  expect(verbs(seen)).toEqual(['switch', 'welcome', 'switch', 'welcome'])
})

test('a session whose id cannot be told is switched on and not welcomed', async ($, on) => {
  const seen = world(on, { script: switching, id: () => { throw new Error('no session') } })
  await start($)
  const made = await run($, 'on')
  expect(made.text).toBe('the door said: switch on')
  expect(made.context).toBe(undefined)
  expect(verbs(seen)).toEqual(['switch'])
  expect(asked(seen)).toEqual(['switch', 'on', '--by-module', '--cwd', '/project']) // and no session is named
})

test('a switch the door could not turn is said so, in what came back from it', async ($, on) => {
  let ran = failing()
  world(on, { script: () => ran })
  await start($)
  expect(await say($, 'off')).toBe('the store could not be opened')
  ran = { exitCode: 1, stdout: '', stderr: '' }
  expect(await say($, 'on')).toBe('Nothing came back.')
})

test('status says whether Crossing is on and what the store holds', async ($, on) => {
  const seen = world(on, { script: () => ({ exitCode: 0, stdout: 'The store holds 2 messages.\n', stderr: '' }) })
  await start($)
  expect(await say($, 'status')).toBe('Crossings is on for this project. The store holds 2 messages.')
  expect(asked(seen)).toEqual(['status', '--session', 'abcdef01-0000', '--by-module', '--cwd', '/project'])
  seen.files[`${HOME}/switch`] = 'off\n' // the switch is the home's own file, wherever the door says the home is
  expect(await say($, 'status')).toBe('Crossings is off for this project. The store holds 2 messages.')
  seen.files[`${HOME}/switch`] = 'on\n'
  seen.files['/project/crossings/switch'] = 'off\n' // a file of that name in the project is not the switch
  expect(await say($, 'status')).toBe('Crossings is on for this project. The store holds 2 messages.')
})

test('status of a project where Crossing was never switched on says so and looks no further', async ($, on) => {
  const seen = world(on, { home: '' })
  await start($)
  expect(await say($, 'STATUS')).toBe('Crossings was never switched on for this project.')
  expect(verbs(seen)).toEqual(['words'])
  expect(seen.files).toEqual({})
})

// --- his own handle ---------------------------------------------------------------------------

test('his own command shows the store through the same script', async ($, on) => {
  let out = 'what the door said\n'
  const seen = world(on, { script: () => ({ exitCode: 0, stdout: out, stderr: '' }) })
  const tail = ['--session', 'abcdef01-0000', '--by-module', '--cwd', '/project']
  await start($)
  expect(await say($, 'look')).toBe('what the door said')
  expect(asked(seen)).toEqual(['look', ...tail]) // and not --touch: his looking is not the session's pull
  expect(await say($, 'FRAME')).toBe('what the door said')
  expect(asked(seen)).toEqual(['frame', ...tail])
  await say($, 'find  Tern "at mooring" moor*')
  expect(asked(seen)).toEqual(['find', 'Tern', '"at', 'mooring"', 'moor*', ...tail])
  expect(await say($, 'find')).toBe('find needs words: /crossings find <words>')
  await say($, 'labels')
  expect(asked(seen)).toEqual(['labels', ...tail])
  await say($, 'labels Standing 2026-11-11')
  expect(asked(seen)).toEqual(['labels', '--kind', 'relation', '--day', '2026-11-11', ...tail])
  await say($, 'labels relation')
  expect(asked(seen)).toEqual(['labels', '--kind', 'relation', ...tail])
  await say($, 'labels work')
  expect(asked(seen)).toEqual(['labels', '--kind', 'work', ...tail])
  await say($, 'labels door')
  expect(asked(seen)).toEqual(['labels', '--kind', 'next', ...tail])
  await say($, 'labels next R3 w12')
  expect(asked(seen)).toEqual(['labels', '--kind', 'next', 'R3', 'w12', ...tail])
  out = ''
  expect(await say($, 'look')).toBe('Nothing came back.')
})

// --- the archive's own files ----------------------------------------------------------------

// The person's own folder and the folder the homes outside a project lie in, as a session's
// environment would give them. Made-up places: no test reaches a real home.
const PLACES = { HOME: '/Users/someone', CROSSING_HOMES: '/elsewhere/homes', CROSSING_OURS: '/elsewhere/ours' }
const SAID = '/elsewhere/homes/made-up-tern-1a2b3c4d/said/abcdef01.jsonl'

// The engine beneath the module: every call that reaches it runs, and is counted.
const tools = (on: any, places: Record<string, string> = PLACES) => {
  mock.env(on, places)
  const reached: string[] = []
  on('tool.call', (_: unknown, e: { tool: string }) => {
    reached.push(e.tool)
    return { result: 'ran' }
  })
  return reached
}
const refused = (made: any) => made.deny ?? (made.isError ? made.text : undefined)

test("a Read of a file of the archive is refused, in one sentence that names the door's tools", async ($, on) => {
  const reached = tools(on)
  const made = await $.tool.call({ tool: 'Read', file_path: SAID })
  expect(refused(made)).toBe(
    "What was said is reached through the door's tools (look, labels, find and thread), not by opening the archive's own files, so this call was not run.")
  expect(reached).toEqual([])
  // The index, the folder itself, a project's own home, and the home on this computer alike.
  for (const file_path of ['/elsewhere/homes/made-up-tern-1a2b3c4d/store.db', '/elsewhere/homes/made-up-tern-1a2b3c4d/said',
    '/project/crossings/said/abcdef01.jsonl', '/project/sub/crossings/store.db-journal', '/elsewhere/ours/said/x.jsonl',
    '/Users/someone/.claude/crossing/homes/other-0a0a0a0a/said/x.jsonl', '/PROJECT/Crossings/Said/x.jsonl']) {
    expect(refused(await $.tool.call({ tool: 'Read', file_path }))).toBe(refused(made))
  }
  for (const call of [{ tool: 'Edit', file_path: SAID, old_string: 'a', new_string: 'b' }, { tool: 'Write', file_path: SAID, content: '' }]) {
    expect(refused(await $.tool.call(call as any))).toBe(refused(made))
  }
  expect(reached).toEqual([])
})

test('a shell command that names a file of the archive is refused, however it spells the place', async ($, on) => {
  const reached = tools(on)
  for (const command of [`cat ${SAID}`, 'cat ~/.claude/crossing/homes/made-up-tern-1a2b3c4d/said/abcdef01.jsonl',
    'grep -r Tern "$HOME/.claude/crossing/homes/made-up-tern-1a2b3c4d/said"', 'sqlite3 crossings/store.db .dump',
    'head -n 3 ./crossings/said/*.jsonl', 'ls /elsewhere/homes/*/said', 'cat /project//crossings/./said/abcdef01.jsonl']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toContain("through the door's tools")
  }
  expect(reached).toEqual([])
})

test("the label pages, the cut pages, the door's own script and a word said elsewhere are left alone", async ($, on) => {
  const reached = tools(on)
  const reads = ['/project/crossings/labels/2026-11-12.md', '/project/crossings/hand-over.md', '/project/crossings/abcdef01-cut-2.md',
    '/elsewhere/homes/made-up-tern-1a2b3c4d/labels/2026-11-12.md', '/project/notes/said/what-was-said.md',
    '/project/my-crossings/said/x.md', '/project/said/store.db']
  for (const file_path of reads) expect(refused(await $.tool.call({ tool: 'Read', file_path }))).toBe(undefined)
  for (const command of ['python3 -I /plugins/crossing/crossing/door.py find "what was said" --cwd /project',
    'python3 crossing/door.py thread abcdef01 --cwd /project', 'grep -n said crossing/store.py', 'cat crossings/labels/2026-11-12.md']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(undefined)
  }
  expect(reached.length).toBe(reads.length + 4)
})

const PERSONS = "This is the person's to run, from their own terminal or with the plugin's command (/crossings), so this call was not run."
const REFUSED =
  "What was said is reached through the door's tools (look, labels, find and thread), not by opening the archive's own files, so this call was not run."

test("a shell command that runs the door with what is the person's alone is refused", async ($, on) => {
  const reached = tools(on)
  for (const command of ['python3 crossing/door.py switch off --cwd /project', 'python3 -I door.py strike aaaaaaaa',
    'cd /x && python3 /plugins/crossing/crossing/door.py layer some-model', 'python3 door.py copy',
    'python3 door.py SWITCH on', 'python3 door.py look --transcript /tmp/x.jsonl', 'python3 door.py status --session "*"',
    'python3 door.py find hull --by-hook', 'CLAUDE_PLUGIN_ROOT=/p python3 /p/crossing/door.py switch on --by-module',
    "echo hi; python3 door.py 'switch' adopt"]) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(PERSONS)
  }
  expect(reached).toEqual([])
  // The words in another command of the same line, or a verb before the door is named, are not the door's.
  for (const command of ['git switch main && python3 door.py look', 'python3 door.py find "the switch on the mast"',
    'echo strike | cat; python3 door.py labels', 'python3 crossing/doorway.py switch on']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(command === 'python3 door.py find "the switch on the mast"' ? PERSONS : undefined)
  }
  expect(reached.length).toBe(3)
})

test("a shell command or a write that names the person's record or a home's kept small files is refused", async ($, on) => {
  const reached = tools(on, { ...PLACES, CROSSING_SWITCHED: '/elsewhere/record/switched' })
  for (const command of ['rm crossings/off.txt', ': > /elsewhere/homes/made-up-tern-1a2b3c4d/off.txt',
    'cat /dev/null > ~/.claude/crossing/switched', 'truncate -s 0 /elsewhere/record/switched', 'rm /elsewhere/ours/unsaid.txt',
    'sed -i "" d crossings/models.txt', 'rm crossings/welcomed.txt crossings/told.txt', 'echo > crossings/there.txt',
    'rm crossings/unattended.txt', 'rm crossings/shelled.txt']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(PERSONS)
  }
  for (const call of [{ tool: 'Write', file_path: '/project/crossings/off.txt', content: '' },
    { tool: 'Edit', file_path: '/Users/someone/.claude/crossing/switched', old_string: 'a', new_string: '' }]) {
    expect(refused(await $.tool.call(call as any))).toBe(PERSONS)
  }
  expect(reached).toEqual([])
  // Read, the person's plain pages may be: a record of when Crossing was off holds no word that was said.
  expect(refused(await $.tool.call({ tool: 'Read', file_path: '/project/crossings/off.txt' }))).toBe(undefined)
  expect(refused(await $.tool.call({ tool: 'Bash', command: 'cat notes/off.txt' }))).toBe(undefined)
  expect(reached).toEqual(['Read', 'Bash'])
})

const WRITTEN =
  "This file of the home is written through the door (a label by mark or leave) or by the person's own hand, not by a " +
  "session's call, so this call was not run."
// Every place a home can stand, as the guard knows them, and the files there that the door alone writes.
const HOMES = ['/project/crossings', '/project/sub/Crossings', '/elsewhere/homes/made-up-tern-1a2b3c4d', '/elsewhere/ours',
  '/Users/someone/.claude/crossing/homes/other-0a0a0a0a', '/Users/someone/.claude/crossing/ours']
const WRITTEN_FILES = ['labels/2026-11-12.md', 'labels', 'hand-over.md', 'hand-over.words.md', 'struck.txt', 'calling.txt',
  'flagged.txt', 'copy', 'switch', 'mode', 'carry', 'frame-size']

test('a writing tool is refused on the label pages, what was struck, and the one-word settings, wherever a home stands', async ($, on) => {
  const reached = tools(on)
  for (const home of HOMES) {
    for (const file of WRITTEN_FILES) {
      const file_path = `${home}/${file}`
      for (const call of [{ tool: 'Write', file_path, content: '' }, { tool: 'Edit', file_path, old_string: 'a', new_string: 'b' },
        { tool: 'MultiEdit', file_path, edits: [] }, { tool: 'NotebookEdit', notebook_path: file_path, new_source: '' }]) {
        expect(refused(await $.tool.call(call as any))).toBe(WRITTEN)
      }
    }
  }
  expect(reached).toEqual([])
  // Read, every one of them may be but a words page: a label page is read beside the work.
  const readable = WRITTEN_FILES.filter(file => !file.endsWith('.words.md'))
  for (const file of readable) expect(refused(await $.tool.call({ tool: 'Read', file_path: `/project/crossings/${file}` }))).toBe(undefined)
  // A word of the same name that is no file of a home is left alone.
  for (const file_path of ['/project/notes/mode', '/project/src/labels/x.md', '/project/my-crossings/copy']) {
    expect(refused(await $.tool.call({ tool: 'Write', file_path, content: '' }))).toBe(undefined)
  }
  expect(reached.length).toBe(readable.length + 3)
})

test('a shell command that writes those files is refused, and one that reads them runs', async ($, on) => {
  const reached = tools(on)
  for (const command of ['echo beside > crossings/mode', 'rm crossings/labels/2026-11-12.md', 'rm -r crossings/labels',
    'sed -i "" s/a/b/ crossings/hand-over.md', 'cat x | tee crossings/struck.txt', 'cp /x ~/.claude/crossing/homes/made-up-tern-1a2b3c4d/copy',
    'printf "%s" a >> /elsewhere/ours/calling.txt', 'mv a crossings/flagged.txt', `python3 -c "open('crossings/frame-size','w')"`,
    'cat crossings/labels/2026-11-12.md > crossings/labels/2026-11-13.md', 'cd /x; touch "$HOME/.claude/crossing/ours/switch"',
    'FOO=1 truncate -s 0 crossings/carry', 'find crossings/labels -delete', 'ln -sf /x crossings/hand-over.words.md']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(WRITTEN)
  }
  expect(reached).toEqual([])
  const reads = ['cat crossings/labels/2026-11-12.md', 'grep -n hull crossings/hand-over.md', 'head -3 crossings/struck.txt 2>/dev/null',
    'ls crossings/labels', 'wc -l /elsewhere/ours/labels/x.md', 'cat crossings/mode crossings/carry | grep beside',
    'echo the mode > notes/mode.txt']
  for (const command of reads) expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(undefined)
  expect(reached.length).toBe(reads.length)
})

test("a shell command that runs the module's own verbs, or names a model for the door, is refused", async ($, on) => {
  const reached = tools(on)
  for (const command of ['python3 crossing/door.py trace {} --cwd /project', 'python3 door.py welcome abcdef01-0000',
    'python3 door.py mark --anchors aaaaaaaa A label. --model made-up-model', 'python3 door.py frame --model=made-up-model']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(PERSONS)
  }
  expect(reached).toEqual([])
  for (const command of ['python3 door.py words --cwd /project', 'python3 door.py page', 'python3 door.py build']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(undefined)
  }
  expect(reached.length).toBe(3)
})

test('with no settings, the homes are looked for where the plugin keeps them by default', async ($, on) => {
  const reached = tools(on, { HOME: '/Users/someone' })
  expect(refused(await $.tool.call({ tool: 'Read', file_path: '/Users/someone/.claude/crossing/ours/said/x.jsonl' }))).toContain('door')
  expect(refused(await $.tool.call({ tool: 'Read', file_path: '/elsewhere/homes/made-up-tern-1a2b3c4d/labels/x.md' }))).toBe(undefined)
  expect(reached).toEqual(['Read'])
})

// --- what an independent review found ---------------------------------------------------------

test('a path that steps back with .. is read where it leads, and the door run as a module is the door', async ($, on) => {
  const reached = tools(on)
  for (const file_path of ['/project/crossings/labels/../said/x.jsonl', '/project/crossings/a/b/../../store.db',
    '/elsewhere/ours/labels/./../said/x.jsonl']) {
    expect(refused(await $.tool.call({ tool: 'Read', file_path }))).toContain("through the door's tools")
  }
  for (const command of ['cat crossings/labels/../said/x.jsonl', 'head "./crossings/x/../said/y.jsonl"',
    'sqlite3 crossings/labels/../store.db .dump']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toContain("through the door's tools")
  }
  for (const command of ['python3 -m crossing.door switch off --cwd /project', 'cd /p && python3 -I -m crossing.door strike aaaaaaaa',
    'python3 -m crossing.door look --session x', 'rm crossings/labels/../off.txt']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(PERSONS)
  }
  expect(reached).toEqual([])
  // A `..` that leads out of a home names no file of it, and the module with a reading verb runs.
  for (const command of ['cat crossings/../notes/said.md', 'python3 -m crossing.door look --cwd /project', 'ls ../said']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(undefined)
  }
  expect(reached.length).toBe(3)
})

test("the home's files of labels met, labels arrived and ids shared are kept from a session's hand", async ($, on) => {
  const reached = tools(on)
  for (const command of ['rm crossings/arrived.txt', 'echo W9@abcdef >> crossings/labelled.txt', ': > crossings/collided.txt']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(PERSONS)
  }
  expect(refused(await $.tool.call({ tool: 'Write', file_path: '/project/crossings/labelled.txt', content: '' }))).toBe(PERSONS)
  expect(reached).toEqual([])
})

test('the door is handed how the session was started, so that it carries nothing to one no person sits in', async ($, on) => {
  mock.env(on, { CLAUDE_CODE_ENTRYPOINT: 'sdk-cli' })
  const seen = world(on, { files: asks('beside', 'message') })
  await $.session.compact({ trigger: 'auto', messages: BEFORE })
  expect(verbs(seen)).toEqual(['words', 'frame', 'trace'])
  for (const init of seen.inits) {
    expect(init?.env?.CLAUDE_CODE_ENTRYPOINT).toBe('sdk-cli')
    expect(typeof init?.env?.CLAUDE_PLUGIN_ROOT).toBe('string')
  }
})

test("a shell command that runs the hand-over's words script is the person's, and one that reads the script runs", async ($, on) => {
  const reached = tools(on)
  for (const command of ['python3 crossing/handover.py /x/abcdef01.jsonl crossings/hand-over.md',
    'python3 -I /plugins/crossing/crossing/handover.py /x/abcdef01.jsonl /elsewhere/notes.md', 'cd /p && python crossing/handover.py a b',
    'FOO=1 python3.9 "crossing/handover.py" a b', 'python3 -m crossing.handover a b', './crossing/handover.py a b',
    'CLAUDE_PLUGIN_ROOT=/p python3 /p/crossing/handover.py --by-module a b']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(PERSONS)
  }
  expect(reached).toEqual([])
  for (const command of ['cat crossing/handover.py', 'grep -n main crossing/handover.py', 'python3 crossing/read.py a b']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(undefined)
  }
  expect(reached.length).toBe(3)
})

test('every small file a hook or the door alone writes is kept from a session that would write it, wherever a home stands', async ($, on) => {
  const reached = tools(on)
  // Neither written nor named in a shell: how far each transcript was read (a marker set by hand would hide what
  // came before it), the sentences said once, what was pulled, the lock, a copy's stage and the traces.
  const kept = ['markers.jsonl', 'passed-over.txt', 'ignore-told.txt', 'copy-told.txt', 'damaged-told.txt', 'reached.jsonl',
    'archive.lock', 'copy-stage.txt', 'last-carry.json', 'last-cut.json', 'models-met.txt', 'models-arrived.txt', 'off-places.jsonl']
  for (const home of HOMES) {
    for (const file of kept) {
      const file_path = `${home}/${file}`
      for (const call of [{ tool: 'Write', file_path, content: '' }, { tool: 'Edit', file_path, old_string: 'a', new_string: 'b' }]) {
        expect(refused(await $.tool.call(call as any))).toBe(PERSONS)
      }
      expect(refused(await $.tool.call({ tool: 'Bash', command: `echo x > ${file_path}` }))).toBe(PERSONS)
    }
  }
  // Not written: every words page, the pages of the cuts and their sidecars, and the one-line settings.
  const written = ['notes.words.md', 'abcdef01-cut-2.md', 'abcdef01-cut-2.json', 'retelling-length', 'retelling-share',
    'project', '.gitignore']
  for (const home of HOMES) {
    for (const file of written) {
      const file_path = `${home}/${file}`
      for (const call of [{ tool: 'Write', file_path, content: '' }, { tool: 'Edit', file_path, old_string: 'a', new_string: 'b' }]) {
        expect(refused(await $.tool.call(call as any))).toBe(WRITTEN)
      }
      expect(refused(await $.tool.call({ tool: 'Bash', command: `echo x > ${file_path}` }))).toBe(WRITTEN)
    }
  }
  expect(reached).toEqual([])
  // Read, each of them may be but a words page, which holds what was said word for word.
  const read = written.filter(file => !file.endsWith('.words.md'))
  for (const file of read) expect(refused(await $.tool.call({ tool: 'Read', file_path: `/project/crossings/${file}` }))).toBe(undefined)
  for (const file of read) expect(refused(await $.tool.call({ tool: 'Bash', command: `cat crossings/${file}` }))).toBe(undefined)
  for (const file of kept) expect(refused(await $.tool.call({ tool: 'Read', file_path: `/project/crossings/${file}` }))).toBe(undefined)
  // A word of the same name that is no file of a home is left alone, outside a home.
  for (const file_path of ['/project/notes/markers.jsonl', '/project/.gitignore']) {
    expect(refused(await $.tool.call({ tool: 'Write', file_path, content: '' }))).toBe(undefined)
  }
  expect(reached.length).toBe(read.length * 2 + kept.length + 2)
})

test("a command's quotes and backslashes are taken out before its paths are looked at, as the shell takes them out", async ($, on) => {
  const reached = tools(on)
  for (const command of ["cat crossings/'said'/x.jsonl", 'cat crossings/sa\\id/x.jsonl', 'cat "crossings/s"aid/x.jsonl',
    "sqlite3 crossings/'store'.db .dump", 'head ~/.claude/crossing/ours/"said"/x.jsonl']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toContain("through the door's tools")
  }
  for (const command of ["rm crossings/'off'.txt", 'echo > crossings/mark\\ers.jsonl']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(PERSONS)
  }
  for (const command of ["echo x > crossings/la''bels/2026-11-12.md", 'sed -i "" s/a/b/ "crossings/hand-over.md"']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(WRITTEN)
  }
  expect(reached).toEqual([])
  for (const command of ["grep -n 'said' notes.md", 'echo "the store" > notes/store.md']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(undefined)
  }
  expect(reached.length).toBe(2)
})

test("the marks of the homes' indexes, beside the person's record, are kept from a session's hand", async ($, on) => {
  const reached = tools(on, { ...PLACES, CROSSING_SWITCHED: '/elsewhere/record/switched' })
  for (const command of ['rm ~/.claude/crossing/switched.indexes', 'echo x >> /elsewhere/record/switched.indexes']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(PERSONS)
  }
  for (const file_path of ['/Users/someone/.claude/crossing/switched.indexes', '/elsewhere/record/switched.indexes']) {
    expect(refused(await $.tool.call({ tool: 'Write', file_path, content: '' }))).toBe(PERSONS)
  }
  expect(reached).toEqual([])
})

test("a words page is read through the door alone, as the archive's own files are, by any tool and any shell read", async ($, on) => {
  const reached = tools(on)
  for (const home of HOMES) {
    for (const file_path of [`${home}/hand-over.words.md`, `${home}/notes.words.md`]) {
      expect(refused(await $.tool.call({ tool: 'Read', file_path }))).toBe(REFUSED)
      expect(refused(await $.tool.call({ tool: 'Grep', pattern: 'Tern', path: file_path }))).toBe(REFUSED)
      expect(refused(await $.tool.call({ tool: 'Bash', command: `cat ${file_path}` }))).toBe(REFUSED)
    }
  }
  for (const call of [{ tool: 'Glob', pattern: 'crossings/*.words.md' }, { tool: 'Grep', pattern: 'Tern', path: '/project/crossings', glob: '*.words.md' },
    { tool: 'Bash', command: 'grep -n Tern crossings/hand-over.words.md | head -3' }]) {
    expect(refused(await $.tool.call(call as any))).toBe(REFUSED)
  }
  expect(reached).toEqual([])
})

test('a path below a home is refused by whatever name its folder bears, but for the files a session may read there', async ($, on) => {
  const reached = tools(on)
  // A link a session made inside a home leads to said/ or to the home itself by another name.
  for (const home of HOMES) {
    for (const file of ['alias/x.jsonl', 'alias/said/x.jsonl', 'alias/store.db', 'labels/alias/x.jsonl', 'labels/said/x.md',
      'said.md', 'cut-2.md', 'model.txt', 'projects/x.md', 'copy-stage', 'off.txt.new', 'hand-over.md.bak', 'labels/x.md/said']) {
      expect(refused(await $.tool.call({ tool: 'Read', file_path: `${home}/${file}` }))).toBe(REFUSED)
      // Written, one that lies below labels/ or begins as a file the door or a hook writes is refused as that file is.
      const why = refused(await $.tool.call({ tool: 'Write', file_path: `${home}/${file}`, content: '' }))
      expect([REFUSED, WRITTEN, PERSONS].includes(why)).toBe(true)
    }
  }
  for (const command of ['cat crossings/alias/said/x.jsonl', 'ls crossings/alias', 'sqlite3 crossings/alias/store.db .dump',
    'cp crossings/alias/x.jsonl /tmp/x', 'head ~/.claude/crossing/homes/made-up-tern-1a2b3c4d/alias/x.jsonl']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(REFUSED)
  }
  expect(reached).toEqual([])
  // The home itself, and the files a session may read in it, are left alone.
  for (const command of ['ls crossings', 'ls crossings/', 'ls crossings/labels/', 'cat crossings/labels/2026-11-12.md',
    'cat crossings/hand-over.md crossings/abcdef01-cut-2.json', 'grep -c W crossings/struck.txt crossings/mode']) {
    expect(refused(await $.tool.call({ tool: 'Bash', command }))).toBe(undefined)
  }
  expect(reached.length).toBe(6)
})
