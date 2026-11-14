#!/bin/sh
# One entry for every hook; the script reads the hook's input on stdin. A word after it
# (`frame`) asks for the hook that carries the frame, across a cut or to a session started new.
root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
exec python3 -I "$root/crossing/hook.py" "$@"
