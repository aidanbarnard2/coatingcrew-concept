#!/bin/bash
cd "$(dirname "$0")"
mkdir -p final
for r in garage sunroom basement; do
  python3 render.py $r A 1320 192 final > final/$r-A.log 2>&1
  B=$(python3 border.py final/${r}_A.exr)
  python3 render.py $r B 1320 192 final border $B > final/$r-B.log 2>&1
  grep RENDERED final/$r-A.log final/$r-B.log
done
echo ALLDONE
