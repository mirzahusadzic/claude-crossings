#!/bin/sh
# Branch coverage of crossing/ under both suites, the hooks' own processes included, and the
# floor in .coveragerc. Coverage lives in a venv of its own under tests/.work, with a startup
# hook that only that venv's Python loads: the plugin itself needs nothing. The hooks module
# is not counted here: `claude plugin test .` runs its tests and gives no measure.
set -e
root=$(cd "$(dirname "$0")/.." && pwd)
venv="$root/tests/.work/coverage-venv"
[ -x "$venv/bin/python" ] || uv venv -q --python 3.13 "$venv"
python="$venv/bin/python"
uv pip install -q --python "$python" "coverage==7.17.2"
site=$("$python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
echo "import coverage; coverage.process_startup()" > "$site/crossing_coverage.pth"
mkdir -p "$root/tests/.work/coverage"
cd "$root"
export COVERAGE_ROOT="$root" COVERAGE_PROCESS_START="$root/.coveragerc"
export PATH="$venv/bin:$PATH" # hooks/run.sh starts `python3`: this venv's, so its lines are counted too
"$python" -m coverage erase
for suite in tests/test_*.py; do
  "$python" -m coverage run "$suite" | grep -v '^ok ' || true
done
"$python" -m coverage combine -q
"$python" -m coverage report
