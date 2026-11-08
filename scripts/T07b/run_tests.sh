#!/bin/zsh
# Existing tests of touched crates (rec_aggregation guest; leanvm_core DBG print) on baseline and B0U.
R=${0:A:h:h:h}/results/T07b
for v in base b0u; do
  cd $R/wt-$v
  { echo "# tests start $v $(date)"; /usr/bin/time -l cargo +1.99.0 test --release -p rec_aggregation -p leanvm_core 2>&1; echo "# tests end $v $(date) exit=$?"; } > $R/tests_$v.log 2>&1
done
