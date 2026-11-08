#!/bin/zsh
# usage: run.sh <results_dir> <leanvm_binary> <log_name> <leanvm args...>
# Runs the binary under /usr/bin/time -l with DBG_TABLES=1, logging swap before/after and all output.
R=$1; B=$2; n=$3; shift 3
L=$R/$n.log
{ echo "# cmd: DBG_TABLES=1 /usr/bin/time -l $B $*"; echo "# date: $(date)"; echo "# swap_before: $(sysctl -n vm.swapusage)"; echo "# power: $(pmset -g batt | tail -1)"; } > $L
DBG_TABLES=1 /usr/bin/time -l $B "$@" >> $L 2>&1
echo "# swap_after: $(sysctl -n vm.swapusage)" >> $L
