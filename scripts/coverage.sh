#!/bin/sh
# Branch coverage of crossing/ under both suites, the hooks' own processes included, and the
# floor in .coveragerc. Coverage lives in a venv of its own under tests/.work, with a startup
# hook that only that venv's Python loads: the plugin itself needs nothing. The hooks module
# is not counted here: `claude plugin test .` runs its tests and gives no measure. The venv's
# Python is the one uv is set to (`UV_PYTHON`, as the pipeline sets it for each of its cells),
# else 3.13, and the venv is named by it, so that a run on one Python never reuses another's.
# The tool is pinned for each: coverage 7.17.2 needs 3.11 or later, and 7.10.7 is the last that
# runs on 3.9, the python3 macOS ships.
set -e
root=$(cd "$(dirname "$0")/.." && pwd)
asked="${UV_PYTHON:-3.13}"
venv="$root/tests/.work/coverage-venv-$(printf '%s' "$asked" | tr -c 'A-Za-z0-9.' '_')"
[ -x "$venv/bin/python" ] || uv venv -q --python "$asked" "$venv"
python="$venv/bin/python"
if "$python" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
  tool="coverage==7.17.2"
else
  tool="coverage==7.10.7"
fi
uv pip install -q --python "$python" "$tool"
site=$("$python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
echo "import coverage; coverage.process_startup()" > "$site/crossing_coverage.pth"
mkdir -p "$root/tests/.work/coverage"
cd "$root"
export COVERAGE_ROOT="$root" COVERAGE_PROCESS_START="$root/.coveragerc"
export PATH="$venv/bin:$PATH" # hooks/run.sh starts `python3`: this venv's, so its lines are counted too
"$python" -m coverage erase
# Each suite's lines but its `ok` ones. A suite that fails is named after the report, and the measure
# fails with it: a suite cut short walks less, and the floor alone would not always say so.
failed=""
said="$root/tests/.work/coverage/suite.out"
for suite in tests/test_*.py; do
  "$python" -m coverage run "$suite" > "$said" 2>&1 || failed="$failed $suite"
  grep -v '^ok ' "$said" || true
done
"$python" -m coverage combine -q
status=0
"$python" -m coverage report || status=$?
if [ -n "$failed" ]; then
  echo "These suites failed:$failed" >&2
  status=1
fi
exit $status
