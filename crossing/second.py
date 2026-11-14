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
    account gives it (record.own), never the HOME variable, which a project's settings can set."""
    try:
        given = "\n".join(record.lines_in(store.within(folder, "copy"))).strip()
    except OSError:
        return None
    if given == "~" or given.startswith("~/"):
        return record.own().joinpath(given[2:]) if given != "~" else record.own()
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
                "The passphrase of Crossing's encrypted second copy",
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
    away (see `emptied`), and the note with it. A note that names anything but a stage of this
    plugin's in the temporary folder is taken away alone, with a line in the log."""
    note = store.within(folder, STAGED)
    try:
        left = Path("\n".join(record.lines_in(note)).strip())
    except FileNotFoundError:
        return
    ours = left.is_absolute() and left.name.startswith(STAGE) and left.parent == staging()
    if not ours:
        record.log(f"refused: the note of a copy's stage names no stage of the plugin's: {str(left)[:120]!r}")
    elif left.is_dir() and not left.is_symlink():
        emptied(left)
    note.unlink()


def make(folder: Path, dest: Path, name: str, top: Path | None = None) -> dict:
    """Write `<dest>/<name>.dmg`, replacing the one there, and check it by opening it again. The
    staged files, the folder named for the copy where it is made here, and the image are the
    owner's alone (see record.private).

    The plain files are staged in a folder made for the owner alone in the system's temporary
    folder (see `staging`), never in the home, and taken away file by file once the image is
    made. The home keeps the stage's path in `copy-stage.txt` meanwhile, so that a run killed
    before its end (a tool that overran the hook's time) has its stage taken away by the next.
    Two copies of one home made at the same moment are not kept apart. Where the temporary folder
    lies inside the home, the copy's folder or the project being served (`top`), no copy is made."""
    record.private()
    cleared(folder)
    files = plain(folder)
    if not files:
        return {"copied": False, "why": "nothing to copy yet"}
    where = staging()
    if any(where == place or place in where.parents for place in (folder.resolve(), dest.resolve())):
        return {"copied": False, "why": "the system's temporary folder lies inside the home or the copy's folder"}
    if top is not None and record.lies_in(where, top):
        return {"copied": False, "why": "the system's temporary folder lies inside the project"}
    key = passphrase().encode() + b"\0"
    stage = Path(tempfile.mkdtemp(prefix=STAGE, dir=where))
    note = store.within(folder, STAGED)
    note.write_text(f"{stage}\n", encoding="utf-8")
    made: list[Path] = []
    try:
        for source in files:
            target = stage.joinpath(*source.relative_to(folder).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            made.append(target)
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
                f"Crossing {name}",
                "-srcfolder",
                str(stage),
                "-ov",
                str(fresh),
            ],
            key,
        )
        if made_image is None or made_image.returncode != 0:
            raise Failed("hdiutil could not make the encrypted image")
        checked = verify(fresh, {str(p.relative_to(stage)): digest(p) for p in made}, key)
        if not checked:
            fresh.unlink()
            return {"copied": False, "why": "the image did not read back the same"}
        os.replace(fresh, dest / f"{name}.dmg")
    finally:
        for target in made:  # the staged plain copies, one by one
            target.unlink()
        emptied(stage)  # its folders, now empty
        note.unlink()
    image = dest / f"{name}.dmg"
    return {"copied": True, "image": str(image), "files": len(files), "bytes": image.stat().st_size}


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
