"""A second copy of the plain files, encrypted before it leaves this disk.

The archive is the most private text there is here, and a synced folder is someone else's
computer. So the copy is one encrypted disk image (AES-256, made by macOS's own hdiutil), the
passphrase is a random one kept in the person's Keychain, and the image is replaced whole each
time: after a strike nothing of the struck text stays in the newest copy.

Only plain files go. The database never does: it is made from them, and a live database in a
synced folder is how such files get damaged. They are staged outside the home, in the system's
temporary folder for the user, and a stage a killed run left is taken away by the next (`make`).
"""

from __future__ import annotations

import getpass
import hashlib
import os
import posixpath
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import record, store  # noqa: E402

SERVICE = "crossing-archive"


class Failed(Exception):
    """The Keychain or hdiutil failed, said in words of the plugin's own: the command it ran is
    never part of it, since the Keychain's holds the passphrase."""


def destination(folder: Path) -> Path | None:
    """Where this home's second copy goes: the folder named in its plain `copy` file, if any. A
    leading `~`, alone or before a `/`, is the person's own folder as the system's record of their
    account gives it (record.own), never the HOME variable, which a project's settings can set; and
    what follows it stays under that folder, read with it as its root: `~//tmp` is `~/tmp`, and a
    `..` climbs no higher than it."""
    try:
        given = "\n".join(record.lines_in(store.within(folder, "copy"))).strip()
    except OSError:
        return None
    if given == "~" or given.startswith("~/"):
        below = posixpath.normpath("/" + given[2:]).lstrip("/")  # as from the root: no slash or .. leads out
        return record.own().joinpath(below) if below else record.own()
    return Path(given) if given else None


def named(top: Path) -> str:
    """The name of a project's image, without its `.dmg`: the project's folder and eight
    characters of the SHA-256 of its whole path, as the default home's folder is named (see
    record.outside), so that two projects of one name that copy to one folder never take each
    other's image."""
    return f"{top.name}-{hashlib.sha256(str(top).encode('utf-8')).hexdigest()[:8]}"


def older(dest: Path, top: Path) -> Path | None:
    """The image an earlier make named by the project's folder alone, where it is there in the
    copy's folder: it is no longer renewed, and is never renamed, written or taken away."""
    image = dest / f"{top.name}.dmg"
    return image if image.is_file() and not image.is_symlink() else None


OLDER_TOLD = "copy-told.txt"  # that the person's status said, once, which older image is no longer renewed


_ignored: list[bool] = []  # the line in the log for CROSSING_COPY_KEY passed over, once a process


def passphrase() -> str:
    """The copy's passphrase: the one in the Keychain, made there the first time. CROSSING_COPY_KEY
    gives it instead only where the door stands at a real terminal, the person's own (see
    record.terminal): a project's settings can set a session's environment, and a passphrase of
    their choosing would encrypt the copy for whoever chose it. Anywhere else it is passed over,
    with one line in the error log."""
    given = os.environ.get("CROSSING_COPY_KEY")
    if given and record.terminal():
        return given
    if given and not _ignored:
        _ignored.append(True)
        record.log(
            "ignored: CROSSING_COPY_KEY is set where the door stands at no terminal; the Keychain's passphrase is used"
        )
    return keychain()


def keychain() -> str:
    """The passphrase kept in the person's Keychain, made and put there the first time."""
    user = getpass.getuser()
    try:
        found = subprocess.run(
            ["security", "find-generic-password", "-s", SERVICE, "-a", user, "-w"], capture_output=True, text=True
        )
    except OSError:
        raise Failed("the Keychain could not be asked for the copy's passphrase") from None
    if found.returncode == 0 and found.stdout.strip():
        return found.stdout.strip()
    made = secrets.token_urlsafe(32)
    try:
        added = subprocess.run(
            [
                "security",
                "add-generic-password",
                "-s",
                SERVICE,
                "-a",
                user,
                "-w",
                made,
                "-j",
                "The passphrase of the encrypted second copy of Crossings",
            ],
            capture_output=True,
        )
    except OSError:
        added = None
    if added is None or added.returncode != 0:  # said without the command: it holds the passphrase
        raise Failed("the Keychain would not keep the copy's passphrase")
    return made


def plain(folder: Path) -> list[Path]:
    """The plain files of a home, which are all that a copy holds."""
    files = store.said_pages(folder) + store.pages(folder)
    return files + [
        store.within(folder, name)
        for name in ("struck.txt", store.MODELS, store.off.FILE)
        if store.within(folder, name).exists()
    ]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


STAGED = "copy-stage.txt"  # where the copy being made stages its plain files, so that a killed run's are found
STAGE = "crossing-copy-"  # how the name of a stage begins
MARK = ".mark"  # after a stage's name, the file beside it that holds the token its note holds


def staging() -> Path:
    """Where a copy stages its plain files: the system's temporary folder for this user, outside
    the home and outside any synced place."""
    return Path(tempfile.gettempdir()).resolve()


def emptied(stage: Path) -> None:
    """A stage taken away file by file, never as a whole: a link is removed as a link and nothing
    it leads to is touched, and a folder goes once it is empty."""
    for top, folders, files in os.walk(stage, topdown=False, followlinks=False):
        for each in files:
            os.unlink(os.path.join(top, each))
        for each in folders:
            path = os.path.join(top, each)
            os.unlink(path) if os.path.islink(path) else os.rmdir(path)
    os.rmdir(stage)


def cleared(folder: Path) -> None:
    """The stage a run that was killed before its end left, as the home's note names it: taken
    away (see `emptied`), and the note with it. A note names a stage and a token, which the file
    beside the stage (`<stage>.mark`) holds too, so that a stage is known as this copy's in
    whatever temporary folder it was made; a note of an older make names only a stage, which must
    lie in today's temporary folder. A note that names anything else is taken away alone, with a
    line in the log."""
    note = store.within(folder, STAGED)
    try:
        given = "\n".join(record.lines_in(note)).strip()
    except FileNotFoundError:
        return
    named, _, token = given.partition("\t")
    left = Path(named)
    ours = left.is_absolute() and left.name.startswith(STAGE)
    ours = ours and (marked(left, token) if token else left.parent == staging())
    if not ours:
        record.log(f"refused: the note of a copy's stage names no stage of the plugin's: {named[:120]!r}")
    else:
        if left.is_dir() and not left.is_symlink():
            emptied(left)
        mark_of(left).unlink(missing_ok=True)
    note.unlink()


def mark_of(stage: Path) -> Path:
    return stage.with_name(stage.name + MARK)


def marked(stage: Path, token: str) -> bool:
    """Whether the file beside a stage holds the token its note holds: a plain file, never a link."""
    mark = mark_of(stage)
    try:
        return not mark.is_symlink() and mark.is_file() and mark.read_bytes().strip() == token.encode("utf-8")
    except OSError:
        return False


NOTHING = "nothing to copy yet"
COPYING = "copy.lock"  # held by one copy of a home at a time, from its first file read to its image's place
HELD = "another act was writing this home, so no copy was made this time"
BUSY = "another copy of this home was being made at that moment, so none was made this time"
UNUSABLE = "the home's copy lock is not a file this account can write"
UNREAD = "the note of a copy's stage in the home cannot be read"
CHANGED = "the home changed while the copy was made, so it was not put in place; the next copy takes it as it stands"


def make(folder: Path, dest: Path, name: str, top: Path | None = None) -> dict:
    """Write `<dest>/<name>.dmg`, replacing the one there, and check it by opening it again. The
    staged files, the folder named for the copy where it is made here, and the image are the
    owner's alone (see record.private).

    The plain files are staged in a folder made for the owner alone in the system's temporary
    folder (see `staging`), never in the home, and taken away file by file once the image is
    made. The home keeps the stage's path in `copy-stage.txt` meanwhile, so that a run killed
    before its end (a tool that overran the hook's time) has its stage taken away by the next.
    Where the temporary folder lies inside the home, the copy's folder or the project being served
    (`top`), no copy is made.

    One copy of a home is made at a time: it holds `copy.lock` all the while, so the next never
    takes a live stage for one a killed run left, and one that cannot have it within the lock's
    wait makes none. The plain files are read and staged under the home's lock (store._locked), so
    that no archive, mark or strike writes them halfway through; the image is made once it is let
    go, so that no act waits for hdiutil; and it is put in place under that lock again, only where
    each staged file is still the start of the file there now. A home that only grew meanwhile (an
    archive, a mark) has its image put in place, older by those lines; one where a strike or any
    other act took or rewrote words keeps the image before, so that the newest copy never holds a
    text struck before it was put in place."""
    record.private()
    lock = store.within(folder, COPYING)
    try:
        copying = store._held_at(lock)
    except OSError:  # a folder, or a file this account cannot write: said, never a traceback
        raise Failed(UNUSABLE) from None
    if copying is None:
        return {"copied": False, "why": BUSY}
    try:
        return _make(folder, dest, name, top)
    finally:
        store._let_go(lock, copying)


def _make(folder: Path, dest: Path, name: str, top: Path | None) -> dict:
    """`make`, with the home's copy lock held."""
    try:
        cleared(folder)
    except OSError:  # a note that is no file
        raise Failed(UNREAD) from None
    files = plain(folder)
    if not files:
        return {"copied": False, "why": NOTHING}
    where = staging()
    if any(where == place or place in where.parents for place in (folder.resolve(), dest.resolve())):
        return {"copied": False, "why": "the system's temporary folder lies inside the home or the copy's folder"}
    if top is not None and record.lies_in(where, top):
        return {"copied": False, "why": "the system's temporary folder lies inside the project"}
    key = passphrase().encode() + b"\0"
    stage = Path(tempfile.mkdtemp(prefix=STAGE, dir=where))
    token = secrets.token_hex(16)  # the stage is known as this copy's by it, in whatever temporary folder
    mark_of(stage).write_text(f"{token}\n", encoding="utf-8")
    note = store.within(folder, STAGED)
    note.write_text(f"{stage}\t{token}\n", encoding="utf-8")
    made: list[Path] = []
    staged: dict[Path, tuple[int, str]] = {}  # each source as it was staged: its length and digest
    try:
        held = store._locked(folder)
        if held is None:
            return {"copied": False, "why": HELD}
        try:
            files = plain(folder)  # as they stand while no other act writes them
            for source in files:
                target = stage.joinpath(*source.relative_to(folder).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                made.append(target)
                staged[source] = (target.stat().st_size, digest(target))
        finally:
            store._unlocked(folder, held)
        dest.mkdir(parents=True, exist_ok=True)
        fresh = dest / f".{name}.new.dmg"
        made_image = _ran(
            [
                "hdiutil",
                "create",
                "-quiet",
                "-encryption",
                "AES-256",
                "-stdinpass",
                "-format",
                "UDZO",
                "-volname",
                f"Crossings {name}",
                "-srcfolder",
                str(stage),
                "-ov",
                str(fresh),
            ],
            key,
        )
        if made_image is None or made_image.returncode != 0:
            raise Failed("hdiutil could not make the encrypted image")
        expected = {str(target.relative_to(stage)): staged[source][1] for source, target in zip(files, made)}
        if not verify(fresh, expected, key):
            fresh.unlink()
            return {"copied": False, "why": "the image did not read back the same"}
        held = store._locked(folder)  # the image is put in place only while no other act writes the home
        if held is None:
            fresh.unlink()
            return {"copied": False, "why": HELD}
        try:
            if not all(begins(source, *was) for source, was in staged.items()):
                fresh.unlink()
                return {"copied": False, "why": CHANGED}
            os.replace(fresh, dest / f"{name}.dmg")
        finally:
            store._unlocked(folder, held)
    finally:
        for target in made:  # the staged plain copies, one by one
            target.unlink()
        emptied(stage)  # its folders, now empty
        mark_of(stage).unlink()
        note.unlink()
    image = dest / f"{name}.dmg"
    return {"copied": True, "image": str(image), "files": len(files), "bytes": image.stat().st_size}


def begins(path: Path, length: int, sha: str) -> bool:
    """Whether a file still begins with what was staged of it: its first `length` bytes have that
    digest. A file that grew since does; one cut short, rewritten or gone does not."""
    try:
        with open(path, "rb") as handle:
            start = handle.read(length)
    except OSError:
        return False
    return len(start) == length and hashlib.sha256(start).hexdigest() == sha


def _ran(argv: list[str], given: bytes) -> subprocess.CompletedProcess | None:
    """hdiutil, with the passphrase on its input; nothing where it cannot be started."""
    try:
        return subprocess.run(argv, input=given, capture_output=True)
    except OSError:
        return None


def verify(image: Path, expected: dict[str, str], key: bytes) -> bool:
    """Open the image read-only, compare every file with what went in, and close it."""
    attached = _ran(
        ["hdiutil", "attach", "-stdinpass", "-nobrowse", "-readonly", "-mountrandom", "/tmp", str(image)], key
    )
    if attached is None or attached.returncode != 0:
        return False
    mount = attached.stdout.decode().strip().splitlines()[-1].split("\t")[-1].strip()
    try:
        return all((Path(mount) / rel).exists() and digest(Path(mount) / rel) == sha for rel, sha in expected.items())
    finally:
        subprocess.run(["hdiutil", "detach", "-quiet", mount], capture_output=True)
