#!/bin/zsh
# usage: run.sh <results_dir> <leanvm_binary> <log_name> <leanvm args...>
# Runs the binary under /usr/bin/time -l, logging command, date, power, swap before/after, all output.
R=$1; B=$2; n=$3; shift 3
L=$R/$n.log
{ echo "# cmd: /usr/bin/time -l $B $*"; echo "# date: $(date)"; echo "# swap_before: $(sysctl -n vm.swapusage)"; echo "# power: $(pmset -g batt | tail -1)"; } > $L
/usr/bin/time -l $B "$@" >> $L 2>&1
echo "# swap_after: $(sysctl -n vm.swapusage)" >> $L
