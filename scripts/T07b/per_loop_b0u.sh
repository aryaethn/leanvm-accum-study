#!/bin/zsh
# Per-loop accounting for B0U: applies one edit at a time on the dbg-tables guest, builds, runs n=2.
# Restores the worktree afterwards (checks the guest out of research/dbg-tables).
ROOT=${0:A:h:h:h}  # repository root
RES=$ROOT/results/T07b/prof/per_loop
mkdir -p $RES
cd $ROOT/upstream/leanMultisig
GUEST=crates/rec_aggregation/guests/lean_ethereum.py
for only in sq q1 q2 q3 q4; do
  git checkout -q research/dbg-tables -- $GUEST
  B0U_ONLY=$only python3 $ROOT/scripts/T07b/make_b0u.py $GUEST > /dev/null
  CARGO_TARGET_DIR=target-b0u cargo +1.99.0 build --release -p leanvm-cli > $RES/build_$only.log 2>&1
  DBG_TABLES=1 target-b0u/release/leanvm recursion --n 2 --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 1 > $RES/$only.log 2>&1
  echo "$only: $(grep -E 'kind=node table=JUMP' $RES/$only.log | tail -1) code_len=$(grep -E 'kind=node cycles' $RES/$only.log | tail -1 | sed -E 's/.*code_len=([0-9]+).*/\1/') cycles=$(grep -E 'cycles \(VM' $RES/$only.log | sed -E 's/.*: ([0-9,]+).*/\1/') verify=$(grep -c 'verifying ' $RES/$only.log)"
done
git checkout -q research/b0u -- $GUEST
