#!/bin/zsh
ROOT=${0:A:h:h:h}  # repository root
R=$ROOT/results/T00; B=$ROOT/upstream/leanMultisig/target/release/leanvm
n=$1; shift
L=$R/$n.log
{ echo "# cmd: /usr/bin/time -l $B $*"; echo "# date: $(date)"; echo "# swap_before: $(sysctl -n vm.swapusage)"; echo "# power: $(pmset -g batt | tail -1)"; } > $L
/usr/bin/time -l $B "$@" >> $L 2>&1
echo "# swap_after: $(sysctl -n vm.swapusage)" >> $L
