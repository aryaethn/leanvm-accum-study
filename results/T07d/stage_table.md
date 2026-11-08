| stage | n5_300 ms | n6 ms | diff ms | ratio n6/n5 | v6_n6 ms |
| execute | 41.1 | 130.9 | +89.8 | 3.18 | 48.5 |
| witness build | 16.9 | 24.8 | +7.8 | 1.46 | 15.1 |
| commit (encode+Merkle) | 365.5 | 625.5 | +260.0 | 1.71 | 413.5 |
| bus GKR | 94.8 | 132.5 | +37.7 | 1.40 | 95.0 |
| bus other (leaves+decompose+tables+untraced) | 63.2 | 203.5 | +140.3 | 3.22 | 69.0 |
| table sumcheck (Prove constraints) | 36.9 | 39.2 | +2.4 | 1.07 | 37.0 |
| Keccak reduction | 168.5 | 192.5 | +24.0 | 1.14 | 173.0 |
| ring switch + claim batching | 84.8 | 82.9 | -1.9 | 0.98 | 79.4 |
| WHIR L0 | 141.2 | 297.0 | +155.8 | 2.10 | 140.1 |
| WHIR L1 | 58.1 | 146.0 | +87.8 | 2.51 | 64.8 |
| WHIR L2 | 28.1 | 61.0 | +32.8 | 2.17 | 28.0 |
| WHIR L3 | 12.7 | 25.7 | +13.1 | 2.03 | 12.6 |
| final/tail | 0.2 | 0.2 | -0.1 | 0.73 | 0.1 |
| untraced (Prove total - top-level children) | 0.6 | 0.1 | -0.5 | 0.17 | -0.6 |
| TOTAL (Prove span) | 1130.0 | 1975.0 | +845.0 | 1.75 | 1185.0 |
sum of diffs excl TOTAL 849.07081
base_n5_300 {'base_n5_300_p1.log': (40.0, 366.0, 1090.0), 'base_n5_300_p2.log': (42.0, 365.0, 1170.0)}
base_n6 {'base_n6_p1.log': (169.0, 616.0, 1960.0), 'base_n6_p2.log': (93.0, 635.0, 1990.0)}
v6_n6 {'v6_n6_p1.log': (42.0, 352.0, 1080.0), 'v6_n6_p2.log': (56.0, 475.0, 1290.0)}
