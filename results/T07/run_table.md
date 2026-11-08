| variant | n | pass | cycles | TOTAL_COMMITTED | node mu (trace / TC rule) | proof KiB | prove s (3 repeats) | median s | leanVM peak GiB | OS footprint GiB | swap at start MiB | swap Δ MiB | verify | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline (df7d122, sound) | 2 | 1 | 392,988 | 2^23.842 | 24 / 24 | 232.6 | 0.552 0.557 0.545 | 0.552 | 1.39 | 1.427 | 2711 | +192 | ok (13.614 ms) | AC; swap at start 2711 MiB |
| V5 UNSOUND (B'-L1 emulation) | 2 | 1 | 362,925 | 2^23.745 | 24 / 24 | 229.1 | 0.533 0.534 0.528 | 0.533 | 1.285 | 1.319 | 2895 | +99 | ok (13.754 ms) | AC; swap at start 2895 MiB |
| baseline (df7d122, sound) | 4 | 1 | 766,603 | 2^24.791 | 25 / 25 | 239.9 | 1.312 1.386 1.383 | 1.383 | 2.301 | 2.456 | 2994 | +86 | ok (15.272 ms) | AC; swap at start 2994 MiB |
| V5 UNSOUND (B'-L1 emulation) | 4 | 1 | 676,205 | 2^24.464 | 25 / 25 | 228.3 | 1.029 0.954 0.9 | 0.954 | 1.954 | 2.037 | 3080 | +0 | ok (13.902 ms) | AC; swap at start 3080 MiB |
| baseline (df7d122, sound) | 6 | 1 | 1,140,247 | 2^25.036 | 26 / 26 | 227.4 | 1.971 2.309 2.122 | 2.122 | 2.97 | 3.097 | 3080 | +852 | ok (17.58 ms) | AC; memory-pressured; swap at start 3080 MiB |
| V5 UNSOUND (B'-L1 emulation) | 6 | 1 | 989,529 | 2^24.997 | 25 / 25 | 246.3 | 1.26 1.106 1.136 | 1.136 | 2.609 | 2.639 | 3924 | -8 | ok (13.958 ms) | AC; swap at start 3924 MiB |
| baseline (df7d122, sound) | 2 | 2 | 392,988 | 2^23.842 | 24 / 24 | 232.6 | 0.541 0.553 0.544 | 0.544 | 1.386 | 1.427 | 3908 | +0 | ok (13.529 ms) | AC; swap at start 3908 MiB |
| V5 UNSOUND (B'-L1 emulation) | 2 | 2 | 362,925 | 2^23.745 | 24 / 24 | 229.1 | 0.518 0.526 0.53 | 0.526 | 1.277 | 1.321 | 3740 | +0 | ok (13.666 ms) | AC; swap at start 3740 MiB |
| baseline (df7d122, sound) | 4 | 2 | 766,603 | 2^24.791 | 25 / 25 | 239.9 | 1.307 1.125 1.302 | 1.302 | 2.333 | 2.4 | 3732 | +0 | ok (13.629 ms) | AC; swap at start 3732 MiB |
| V5 UNSOUND (B'-L1 emulation) | 4 | 2 | 676,205 | 2^24.464 | 25 / 25 | 228.3 | 0.899 0.894 0.891 | 0.894 | 1.999 | 2.035 | 3724 | -8 | ok (13.8 ms) | AC; swap at start 3724 MiB |
| baseline (df7d122, sound) | 6 | 2 | 1,140,247 | 2^25.036 | 26 / 26 | 227.4 | 1.976 2.145 2.106 | 2.106 | 3.029 | 3.097 | 3716 | +302 | ok (14.727 ms) | AC; memory-pressured; swap at start 3716 MiB |
| V5 UNSOUND (B'-L1 emulation) | 6 | 2 | 989,529 | 2^24.997 | 25 / 25 | 246.3 | 1.166 1.24 1.258 | 1.24 | 2.614 | 2.643 | 3906 | -120 | ok (14.008 ms) | AC; swap at start 3906 MiB |

n = 8, `--repeat 1` (prove time is paging-bound here; not used):

| variant | n | cycles | TOTAL_COMMITTED | node mu (trace / TC rule) | proof KiB | prove s (paging-bound) | OS footprint GiB | swap at start MiB | swap Δ MiB | verify |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline (df7d122, sound) | 8 | 1,514,224 | 2^25.778 | 26 / 26 | 248.3 |  (paging-bound) | 4.304 | 3778 | +991 | ok (54.915 ms) |
| V5 UNSOUND (B'-L1 emulation) | 8 | 1,303,164 | 2^25.447 | 26 / 26 | 237.4 |  (paging-bound) | 3.55 | 4569 | -72 | ok (20.261 ms) |

Per-opcode lines (`details`):

- base n=2 pass 1: `MUL 2^17.132 (36.5%)  XOR 2^16.681 (26.7%)  DEREF 2^16.105 (17.9%)  SET 2^15.213 (9.7%)  JUMP 2^14.637 (6.5%)  KECCAK 2^13.347 (2.7%)  MEMORY 2^19.379  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842`
- v5 n=2 pass 1: `MUL 2^17.017 (36.5%)  XOR 2^16.563 (26.7%)  DEREF 2^15.989 (17.9%)  SET 2^15.133 (9.9%)  JUMP 2^14.506 (6.4%)  KECCAK 2^13.177 (2.6%)  MEMORY 2^19.32  BYTECODE 2^18.922  TOTAL_COMMITTED 2^23.745`
- base n=4 pass 1: `MUL 2^18.129 (37.4%)  XOR 2^17.678 (27.3%)  DEREF 2^17.093 (18.2%)  SET 2^15.845 (7.7%)  JUMP 2^15.634 (6.6%)  KECCAK 2^14.344 (2.7%)  MEMORY 2^20.357  BYTECODE 2^18.899  TOTAL_COMMITTED 2^24.791`
- v5 n=4 pass 1: `MUL 2^17.953 (37.5%)  XOR 2^17.496 (27.3%)  DEREF 2^16.914 (18.3%)  SET 2^15.683 (7.8%)  JUMP 2^15.428 (6.5%)  KECCAK 2^14.084 (2.6%)  MEMORY 2^20.239  BYTECODE 2^18.922  TOTAL_COMMITTED 2^24.464`
- base n=6 pass 1: `MUL 2^18.713 (37.7%)  XOR 2^18.262 (27.6%)  DEREF 2^17.674 (18.3%)  SET 2^16.282 (7.0%)  JUMP 2^16.218 (6.7%)  KECCAK 2^14.928 (2.7%)  MEMORY 2^20.935  BYTECODE 2^18.899  TOTAL_COMMITTED 2^25.036`
- v5 n=6 pass 1: `MUL 2^18.516 (37.9%)  XOR 2^18.058 (27.6%)  DEREF 2^17.473 (18.4%)  SET 2^16.08 (7.0%)  JUMP 2^15.986 (6.6%)  KECCAK 2^14.637 (2.6%)  MEMORY 2^20.796  BYTECODE 2^18.922  TOTAL_COMMITTED 2^24.997`
- base n=2 pass 2: `MUL 2^17.132 (36.5%)  XOR 2^16.681 (26.7%)  DEREF 2^16.105 (17.9%)  SET 2^15.213 (9.7%)  JUMP 2^14.637 (6.5%)  KECCAK 2^13.347 (2.7%)  MEMORY 2^19.379  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842`
- v5 n=2 pass 2: `MUL 2^17.017 (36.5%)  XOR 2^16.563 (26.7%)  DEREF 2^15.989 (17.9%)  SET 2^15.133 (9.9%)  JUMP 2^14.506 (6.4%)  KECCAK 2^13.177 (2.6%)  MEMORY 2^19.32  BYTECODE 2^18.922  TOTAL_COMMITTED 2^23.745`
- base n=4 pass 2: `MUL 2^18.129 (37.4%)  XOR 2^17.678 (27.3%)  DEREF 2^17.093 (18.2%)  SET 2^15.845 (7.7%)  JUMP 2^15.634 (6.6%)  KECCAK 2^14.344 (2.7%)  MEMORY 2^20.357  BYTECODE 2^18.899  TOTAL_COMMITTED 2^24.791`
- v5 n=4 pass 2: `MUL 2^17.953 (37.5%)  XOR 2^17.496 (27.3%)  DEREF 2^16.914 (18.3%)  SET 2^15.683 (7.8%)  JUMP 2^15.428 (6.5%)  KECCAK 2^14.084 (2.6%)  MEMORY 2^20.239  BYTECODE 2^18.922  TOTAL_COMMITTED 2^24.464`
- base n=6 pass 2: `MUL 2^18.713 (37.7%)  XOR 2^18.262 (27.6%)  DEREF 2^17.674 (18.3%)  SET 2^16.282 (7.0%)  JUMP 2^16.218 (6.7%)  KECCAK 2^14.928 (2.7%)  MEMORY 2^20.935  BYTECODE 2^18.899  TOTAL_COMMITTED 2^25.036`
- v5 n=6 pass 2: `MUL 2^18.516 (37.9%)  XOR 2^18.058 (27.6%)  DEREF 2^17.473 (18.4%)  SET 2^16.08 (7.0%)  JUMP 2^15.986 (6.6%)  KECCAK 2^14.637 (2.6%)  MEMORY 2^20.796  BYTECODE 2^18.922  TOTAL_COMMITTED 2^24.997`
- base n=8 pass n8: `MUL 2^19.128 (37.8%)  XOR 2^18.676 (27.7%)  DEREF 2^18.088 (18.4%)  JUMP 2^16.632 (6.7%)  SET 2^16.618 (6.6%)  KECCAK 2^15.342 (2.7%)  MEMORY 2^21.346  BYTECODE 2^18.899  TOTAL_COMMITTED 2^25.778`
- v5 n=8 pass n8: `MUL 2^18.921 (38.1%)  XOR 2^18.462 (27.7%)  DEREF 2^17.876 (18.5%)  SET 2^16.392 (6.6%)  JUMP 2^16.387 (6.6%)  KECCAK 2^15.036 (2.6%)  MEMORY 2^21.197  BYTECODE 2^18.922  TOTAL_COMMITTED 2^25.447`
