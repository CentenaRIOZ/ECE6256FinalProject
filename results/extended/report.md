# Extended experiments (PACE-ICE, hard cap)

## Fresh timelines: accuracy

| data   | model                 | condition        |   n |   accuracy |   lo |   hi |   execute |   execute_lo |   execute_hi |   memory_tokens |   max_tokens |
|:-------|:----------------------|:-----------------|----:|-----------:|-----:|-----:|----------:|-------------:|-------------:|----------------:|-------------:|
| fresh  | Llama-3.1-8B-Instruct | abl_noguard      | 912 |       81.1 | 78   | 84.2 |      90   |         87.9 |         92   |             295 |          384 |
| fresh  | Llama-3.1-8B-Instruct | abl_noreceipt    | 912 |       75.3 | 71.9 | 78.8 |      87.1 |         84.9 |         89.2 |             293 |          384 |
| fresh  | Llama-3.1-8B-Instruct | chrono           | 912 |       78.4 | 75   | 81.7 |      87.8 |         85.4 |         90.1 |             318 |          384 |
| fresh  | Llama-3.1-8B-Instruct | full             | 912 |       83.4 | 80.3 | 86.4 |      88.8 |         86.3 |         91.2 |               0 |            0 |
| fresh  | Llama-3.1-8B-Instruct | lifecycle        | 912 |       77.4 | 73.8 | 81.1 |      89.7 |         87.4 |         91.9 |             293 |          384 |
| fresh  | Llama-3.1-8B-Instruct | lifecycle_gold   | 912 |       83.8 | 81   | 86.6 |      92.5 |         90.7 |         94.3 |             295 |          384 |
| fresh  | Llama-3.1-8B-Instruct | lifecycle_nohint | 912 |       79.2 | 76   | 82.2 |      90.1 |         87.8 |         92.4 |             276 |          384 |
| fresh  | Llama-3.1-8B-Instruct | lifecycle_strict | 912 |       80.7 | 77.7 | 83.8 |      90.1 |         87.9 |         92.3 |             295 |          384 |
| fresh  | Llama-3.1-8B-Instruct | pinning          | 912 |       71.6 | 69.2 | 73.9 |      83.6 |         81.6 |         85.4 |             326 |          384 |
| fresh  | Llama-3.1-8B-Instruct | summary          | 912 |       73.2 | 70   | 76.3 |      87.8 |         85.5 |         90.1 |             186 |          384 |
| fresh  | Llama-3.1-8B-Instruct | typed_llm        | 912 |       76.2 | 73.1 | 79.3 |      88.4 |         86.4 |         90.3 |             292 |          384 |
| fresh  | Qwen2.5-7B-Instruct   | abl_noguard      | 912 |       77   | 73.7 | 80   |      88.2 |         85.8 |         90.5 |             251 |          384 |
| fresh  | Qwen2.5-7B-Instruct   | abl_noreceipt    | 912 |       74.5 | 70.4 | 77.9 |      86   |         83.3 |         88.6 |             246 |          384 |
| fresh  | Qwen2.5-7B-Instruct   | chrono           | 912 |       70.6 | 67.3 | 73.8 |      86.8 |         84.4 |         89.2 |             279 |          384 |
| fresh  | Qwen2.5-7B-Instruct   | full             | 912 |       57.2 | 53.2 | 61.1 |      82.9 |         80.4 |         85.2 |               0 |            0 |
| fresh  | Qwen2.5-7B-Instruct   | lifecycle        | 912 |       78.1 | 74.9 | 81   |      89.4 |         87.5 |         91.3 |             252 |          384 |
| fresh  | Qwen2.5-7B-Instruct   | lifecycle_gold   | 912 |       83.8 | 81.4 | 86   |      93   |         91   |         94.8 |             258 |          384 |
| fresh  | Qwen2.5-7B-Instruct   | lifecycle_nohint | 912 |       69.5 | 66.1 | 72.7 |      85   |         82.2 |         87.5 |             233 |          384 |
| fresh  | Qwen2.5-7B-Instruct   | lifecycle_strict | 912 |       78.5 | 75.4 | 81.4 |      89.1 |         86.9 |         91.3 |             251 |          384 |
| fresh  | Qwen2.5-7B-Instruct   | pinning          | 912 |       62.4 | 59.2 | 65.5 |      78.7 |         76.4 |         81.1 |             183 |          384 |
| fresh  | Qwen2.5-7B-Instruct   | summary          | 912 |       58.3 | 54.6 | 61.8 |      79.3 |         76.4 |         82.3 |             124 |          384 |
| fresh  | Qwen2.5-7B-Instruct   | typed_llm        | 912 |       71.4 | 67.7 | 74.9 |      83.2 |         80.7 |         85.7 |             244 |          384 |

## Fresh timelines: confirmation tests

| metric   | model                 | a                | b                |   original_diff |   diff |   lo |   hi |     p |   p_holm | confirmed   |
|:---------|:----------------------|:-----------------|:-----------------|----------------:|-------:|-----:|-----:|------:|---------:|:------------|
| four_way | Qwen2.5-7B-Instruct   | lifecycle        | summary          |            18.1 |   19.7 | 15.2 | 24.2 | 0.001 |    0.012 | True        |
| four_way | Qwen2.5-7B-Instruct   | lifecycle        | pinning          |            11.7 |   15.7 | 11.8 | 19.7 | 0.001 |    0.012 | True        |
| four_way | Qwen2.5-7B-Instruct   | lifecycle        | chrono           |             7.2 |    7.5 |  4.1 | 10.7 | 0.001 |    0.012 | True        |
| four_way | Qwen2.5-7B-Instruct   | lifecycle        | typed_llm        |             4.4 |    6.7 |  3.1 | 10.5 | 0.001 |    0.012 | True        |
| four_way | Qwen2.5-7B-Instruct   | lifecycle        | lifecycle_nohint |             6.6 |    8.6 |  5.6 | 11.5 | 0.001 |    0.012 | True        |
| four_way | Qwen2.5-7B-Instruct   | lifecycle_strict | lifecycle        |            -0.2 |    0.4 | -1.4 |  2.2 | 0.663 |    1     | False       |
| four_way | Llama-3.1-8B-Instruct | lifecycle        | summary          |            -2   |    4.2 |  0.5 |  7.7 | 0.029 |    0.145 | False       |
| four_way | Llama-3.1-8B-Instruct | lifecycle        | pinning          |             2.4 |    5.8 |  2.3 |  9.2 | 0.002 |    0.014 | True        |
| four_way | Llama-3.1-8B-Instruct | lifecycle        | chrono           |            -7.5 |   -1   | -4.6 |  2.5 | 0.582 |    1     | False       |
| four_way | Llama-3.1-8B-Instruct | lifecycle        | typed_llm        |             1.8 |    1.2 | -1.8 |  4   | 0.436 |    1     | False       |
| four_way | Llama-3.1-8B-Instruct | lifecycle        | lifecycle_nohint |            -4.1 |   -1.8 | -5.1 |  1.5 | 0.337 |    1     | False       |
| four_way | Llama-3.1-8B-Instruct | lifecycle_strict | lifecycle        |             6.6 |    3.3 |  0.7 |  6.1 | 0.011 |    0.066 | False       |
| execute  | Qwen2.5-7B-Instruct   | lifecycle        | summary          |             8.3 |   10.1 |  6.9 | 13.3 | 0.001 |    0.012 | True        |
| execute  | Qwen2.5-7B-Instruct   | lifecycle        | pinning          |             6.5 |   10.6 |  8   | 13.4 | 0.001 |    0.012 | True        |
| execute  | Qwen2.5-7B-Instruct   | lifecycle        | chrono           |             3.6 |    2.5 |  0.1 |  5.2 | 0.05  |    0.35  | False       |
| execute  | Qwen2.5-7B-Instruct   | lifecycle        | typed_llm        |             4.8 |    6.1 |  3.6 |  8.7 | 0.001 |    0.012 | True        |
| execute  | Qwen2.5-7B-Instruct   | lifecycle        | lifecycle_nohint |             2.7 |    4.4 |  1.9 |  6.9 | 0.002 |    0.016 | True        |
| execute  | Qwen2.5-7B-Instruct   | lifecycle_strict | lifecycle        |            -0.2 |   -0.2 | -1.5 |  1.1 | 0.853 |    1     | False       |
| execute  | Llama-3.1-8B-Instruct | lifecycle        | summary          |             0.5 |    1.9 | -0.7 |  4.6 | 0.181 |    1     | False       |
| execute  | Llama-3.1-8B-Instruct | lifecycle        | pinning          |             5.4 |    6.1 |  3.2 |  9.2 | 0.001 |    0.012 | True        |
| execute  | Llama-3.1-8B-Instruct | lifecycle        | chrono           |             3   |    1.9 | -1   |  5   | 0.251 |    1     | False       |
| execute  | Llama-3.1-8B-Instruct | lifecycle        | typed_llm        |             3   |    1.3 | -1.1 |  3.8 | 0.298 |    1     | False       |
| execute  | Llama-3.1-8B-Instruct | lifecycle        | lifecycle_nohint |             1.7 |   -0.4 | -2.7 |  1.7 | 0.758 |    1     | False       |
| execute  | Llama-3.1-8B-Instruct | lifecycle_strict | lifecycle        |             0.5 |    0.4 | -1.2 |  2.1 | 0.598 |    1     | False       |

## Fresh timelines: accuracy by category

| model                 | condition        |   completion |   conditional |   revocation |   static |
|:----------------------|:-----------------|-------------:|--------------:|-------------:|---------:|
| Llama-3.1-8B-Instruct | chrono           |         78.3 |          61.8 |         85.6 |     84.6 |
| Llama-3.1-8B-Instruct | full             |         76.1 |          74.1 |         87.5 |     93.3 |
| Llama-3.1-8B-Instruct | lifecycle        |         82.2 |          50.9 |         87.5 |     85.1 |
| Llama-3.1-8B-Instruct | lifecycle_gold   |         83.3 |          72.6 |         89.1 |     87.5 |
| Llama-3.1-8B-Instruct | lifecycle_nohint |         75.6 |          63.7 |         87.5 |     85.6 |
| Llama-3.1-8B-Instruct | lifecycle_strict |         80.6 |          64.6 |         89.4 |     84.1 |
| Llama-3.1-8B-Instruct | pinning          |         63.3 |          57.5 |         80.8 |     79.3 |
| Llama-3.1-8B-Instruct | summary          |         77.8 |          60.4 |         82.1 |     69.2 |
| Llama-3.1-8B-Instruct | typed_llm        |         78.9 |          57.1 |         84.3 |     81.2 |
| Qwen2.5-7B-Instruct   | chrono           |         63.3 |          68.4 |         75.6 |     71.6 |
| Qwen2.5-7B-Instruct   | full             |         55   |          65.6 |         63.8 |     40.9 |
| Qwen2.5-7B-Instruct   | lifecycle        |         71.1 |          76.4 |         79.5 |     83.7 |
| Qwen2.5-7B-Instruct   | lifecycle_gold   |         78.9 |          84.4 |         85.6 |     84.6 |
| Qwen2.5-7B-Instruct   | lifecycle_nohint |         62.2 |          70.8 |         71.2 |     72.1 |
| Qwen2.5-7B-Instruct   | lifecycle_strict |         73.9 |          76.9 |         79.2 |     83.2 |
| Qwen2.5-7B-Instruct   | pinning          |         47.8 |          63.7 |         66.7 |     67.3 |
| Qwen2.5-7B-Instruct   | summary          |         56.7 |          61.8 |         67.6 |     42.3 |
| Qwen2.5-7B-Instruct   | typed_llm        |         56.1 |          62.7 |         79.8 |     80.8 |

## Hard-cap budget sweep: accuracy

|   budget | model                 | condition        |   n |   accuracy |   lo |   hi |   execute |   execute_lo |   execute_hi |   memory_tokens |   max_tokens |
|---------:|:----------------------|:-----------------|----:|-----------:|-----:|-----:|----------:|-------------:|-------------:|----------------:|-------------:|
|      256 | Llama-3.1-8B-Instruct | abl_noguard      | 664 |       73.3 | 69.7 | 76.9 |      85.8 |         82.7 |         88.7 |             234 |          256 |
|      256 | Llama-3.1-8B-Instruct | abl_noreceipt    | 664 |       65.7 | 60.7 | 70.5 |      83.3 |         80   |         86.2 |             233 |          256 |
|      256 | Llama-3.1-8B-Instruct | chrono           | 664 |       75.3 | 71.5 | 78.7 |      83.1 |         80   |         85.9 |             238 |          256 |
|      256 | Llama-3.1-8B-Instruct | full             | 664 |       81.3 | 77.6 | 84.5 |      87   |         84.3 |         89.6 |               0 |            0 |
|      256 | Llama-3.1-8B-Instruct | lifecycle        | 664 |       67.2 | 62.3 | 72.2 |      85.7 |         82.2 |         88.8 |             234 |          256 |
|      256 | Llama-3.1-8B-Instruct | lifecycle_gold   | 664 |       78.8 | 75.6 | 81.8 |      89.6 |         87   |         92.1 |             239 |          256 |
|      256 | Llama-3.1-8B-Instruct | lifecycle_nohint | 664 |       76.2 | 72.6 | 79.9 |      87.2 |         84.3 |         90   |             228 |          256 |
|      256 | Llama-3.1-8B-Instruct | lifecycle_strict | 664 |       72.9 | 68.6 | 76.9 |      84.8 |         81.1 |         88.2 |             235 |          256 |
|      256 | Llama-3.1-8B-Instruct | pinning          | 664 |       68.4 | 64.8 | 71.9 |      83.4 |         80.6 |         86.1 |             239 |          256 |
|      256 | Llama-3.1-8B-Instruct | summary          | 664 |       70.6 | 66.8 | 74.4 |      86.3 |         83.2 |         89.5 |             146 |          256 |
|      256 | Llama-3.1-8B-Instruct | typed_llm        | 664 |       68.5 | 64.1 | 73   |      86.3 |         83.4 |         89   |             233 |          256 |
|      256 | Qwen2.5-7B-Instruct   | abl_noguard      | 664 |       73.8 | 70.4 | 77.2 |      85.1 |         82.3 |         87.7 |             215 |          256 |
|      256 | Qwen2.5-7B-Instruct   | abl_noreceipt    | 664 |       74.1 | 70.6 | 77.5 |      85.2 |         82.6 |         88.1 |             215 |          256 |
|      256 | Qwen2.5-7B-Instruct   | chrono           | 664 |       66.3 | 62.1 | 70.4 |      81.8 |         78.6 |         85   |             221 |          256 |
|      256 | Qwen2.5-7B-Instruct   | full             | 664 |       60.8 | 56   | 65.2 |      84.3 |         81   |         87.6 |               0 |            0 |
|      256 | Qwen2.5-7B-Instruct   | lifecycle        | 664 |       77.1 | 73.9 | 80.1 |      88.1 |         86   |         90.3 |             215 |          256 |
|      256 | Qwen2.5-7B-Instruct   | lifecycle_gold   | 664 |       78   | 74   | 82.1 |      89.5 |         87   |         91.9 |             221 |          256 |
|      256 | Qwen2.5-7B-Instruct   | lifecycle_nohint | 664 |       69.4 | 66.4 | 72.5 |      85.7 |         83.3 |         88.1 |             208 |          256 |
|      256 | Qwen2.5-7B-Instruct   | lifecycle_strict | 664 |       76.2 | 73   | 79.3 |      87.2 |         85   |         89.4 |             213 |          256 |
|      256 | Qwen2.5-7B-Instruct   | pinning          | 664 |       62.8 | 58.2 | 67.1 |      80   |         76.5 |         83.3 |             170 |          256 |
|      256 | Qwen2.5-7B-Instruct   | summary          | 664 |       58.1 | 53.7 | 62.4 |      78.9 |         75.7 |         82   |             120 |          256 |
|      256 | Qwen2.5-7B-Instruct   | typed_llm        | 664 |       67.6 | 63.3 | 71.8 |      81   |         77.1 |         84.7 |             212 |          256 |
|      384 | Llama-3.1-8B-Instruct | abl_noguard      | 664 |       77.4 | 73.2 | 81.4 |      88.7 |         85.7 |         91.6 |             291 |          384 |
|      384 | Llama-3.1-8B-Instruct | abl_noreceipt    | 664 |       69.4 | 64.3 | 74.6 |      86.6 |         83.4 |         89.8 |             289 |          384 |
|      384 | Llama-3.1-8B-Instruct | chrono           | 664 |       78.3 | 74.1 | 82.2 |      85.4 |         81.6 |         88.8 |             317 |          384 |
|      384 | Llama-3.1-8B-Instruct | full             | 664 |       81.3 | 77.6 | 84.5 |      87   |         84.3 |         89.6 |               0 |            0 |
|      384 | Llama-3.1-8B-Instruct | lifecycle        | 664 |       70.8 | 65.3 | 76.1 |      88.4 |         85.2 |         91.5 |             291 |          384 |
|      384 | Llama-3.1-8B-Instruct | lifecycle_gold   | 664 |       83.3 | 79.8 | 86.5 |      92.5 |         90   |         94.7 |             296 |          384 |
|      384 | Llama-3.1-8B-Instruct | lifecycle_nohint | 664 |       74.8 | 70.9 | 78.7 |      86.7 |         83.1 |         90.2 |             273 |          384 |
|      384 | Llama-3.1-8B-Instruct | lifecycle_strict | 664 |       77.4 | 73.1 | 81.4 |      88.9 |         85.8 |         91.9 |             290 |          384 |
|      384 | Llama-3.1-8B-Instruct | pinning          | 664 |       68.4 | 65.8 | 70.9 |      83   |         80.1 |         85.7 |             327 |          384 |
|      384 | Llama-3.1-8B-Instruct | summary          | 664 |       72.7 | 69.4 | 76   |      88   |         85.1 |         90.8 |             183 |          384 |
|      384 | Llama-3.1-8B-Instruct | typed_llm        | 664 |       69   | 64.3 | 73.7 |      85.4 |         82.4 |         88.3 |             289 |          384 |
|      384 | Qwen2.5-7B-Instruct   | abl_noguard      | 664 |       73.9 | 69.9 | 77.7 |      86.4 |         83.8 |         89.1 |             255 |          384 |
|      384 | Qwen2.5-7B-Instruct   | abl_noreceipt    | 664 |       74.1 | 69.7 | 78.2 |      86.6 |         83.7 |         89.4 |             252 |          384 |
|      384 | Qwen2.5-7B-Instruct   | chrono           | 664 |       68.2 | 64.2 | 71.9 |      84.5 |         81.1 |         87.5 |             283 |          384 |
|      384 | Qwen2.5-7B-Instruct   | full             | 664 |       60.8 | 56   | 65.2 |      84.3 |         81   |         87.6 |               0 |            0 |
|      384 | Qwen2.5-7B-Instruct   | lifecycle        | 664 |       75.5 | 71.4 | 79.1 |      88.1 |         85.6 |         90.7 |             254 |          384 |
|      384 | Qwen2.5-7B-Instruct   | lifecycle_gold   | 664 |       82.8 | 79.8 | 85.7 |      91.7 |         89.4 |         93.8 |             263 |          384 |
|      384 | Qwen2.5-7B-Instruct   | lifecycle_nohint | 664 |       68.8 | 65.3 | 72.2 |      85.4 |         83.3 |         87.7 |             238 |          384 |
|      384 | Qwen2.5-7B-Instruct   | lifecycle_strict | 664 |       75.3 | 71.2 | 79   |      88   |         85.4 |         90.5 |             253 |          384 |
|      384 | Qwen2.5-7B-Instruct   | pinning          | 664 |       63.7 | 59.5 | 67.8 |      81.6 |         78.9 |         84.3 |             194 |          384 |
|      384 | Qwen2.5-7B-Instruct   | summary          | 664 |       57.4 | 53.5 | 61.1 |      79.8 |         77   |         82.8 |             131 |          376 |
|      384 | Qwen2.5-7B-Instruct   | typed_llm        | 664 |       71.1 | 66.7 | 75.4 |      83.3 |         79.9 |         86.7 |             250 |          384 |
|      768 | Llama-3.1-8B-Instruct | abl_noguard      | 664 |       77.6 | 72.4 | 82.6 |      88.3 |         85.3 |         91   |             357 |          768 |
|      768 | Llama-3.1-8B-Instruct | abl_noreceipt    | 664 |       71.1 | 65.6 | 76.8 |      88.3 |         85.6 |         90.6 |             355 |          711 |
|      768 | Llama-3.1-8B-Instruct | chrono           | 664 |       75.9 | 71.6 | 79.5 |      85.1 |         81.8 |         88.1 |             400 |          768 |
|      768 | Llama-3.1-8B-Instruct | full             | 664 |       81.3 | 77.6 | 84.5 |      87   |         84.3 |         89.6 |               0 |            0 |
|      768 | Llama-3.1-8B-Instruct | lifecycle        | 664 |       73.3 | 67.8 | 78.9 |      90.2 |         87.4 |         92.9 |             360 |          768 |
|      768 | Llama-3.1-8B-Instruct | lifecycle_gold   | 664 |       83   | 79.5 | 86.3 |      92.2 |         90.1 |         94.2 |             360 |          737 |
|      768 | Llama-3.1-8B-Instruct | lifecycle_nohint | 664 |       75.3 | 71.6 | 79.1 |      88.6 |         86.2 |         90.9 |             339 |          750 |
|      768 | Llama-3.1-8B-Instruct | lifecycle_strict | 664 |       76.8 | 71.7 | 81.8 |      88.6 |         85.6 |         91.4 |             359 |          703 |
|      768 | Llama-3.1-8B-Instruct | pinning          | 664 |       70.5 | 66.7 | 74.1 |      84.5 |         81.8 |         87.2 |             483 |          768 |
|      768 | Llama-3.1-8B-Instruct | summary          | 664 |       70.3 | 66.6 | 74   |      87.5 |         84.8 |         90.1 |             221 |          515 |
|      768 | Llama-3.1-8B-Instruct | typed_llm        | 664 |       69.7 | 64.3 | 74.7 |      86.4 |         83.5 |         89.2 |             357 |          650 |
|      768 | Qwen2.5-7B-Instruct   | abl_noguard      | 664 |       76.8 | 72.8 | 80.6 |      88.1 |         85.9 |         90.3 |             275 |          491 |
|      768 | Qwen2.5-7B-Instruct   | abl_noreceipt    | 664 |       73.9 | 70.1 | 77.5 |      86   |         83.3 |         88.8 |             271 |          464 |
|      768 | Qwen2.5-7B-Instruct   | chrono           | 664 |       69.3 | 65.8 | 72.6 |      84.2 |         80.9 |         87.1 |             311 |          577 |
|      768 | Qwen2.5-7B-Instruct   | full             | 664 |       60.8 | 56   | 65.2 |      84.3 |         81   |         87.6 |               0 |            0 |
|      768 | Qwen2.5-7B-Instruct   | lifecycle        | 664 |       77.3 | 73.5 | 80.8 |      88.3 |         85.9 |         90.4 |             271 |          464 |
|      768 | Qwen2.5-7B-Instruct   | lifecycle_gold   | 664 |       81.6 | 79   | 84.2 |      90.7 |         88.5 |         92.9 |             279 |          474 |
|      768 | Qwen2.5-7B-Instruct   | lifecycle_nohint | 664 |       69.7 | 65   | 74.2 |      85.5 |         83.1 |         88.1 |             250 |          463 |
|      768 | Qwen2.5-7B-Instruct   | lifecycle_strict | 664 |       76.4 | 72.3 | 80.4 |      88.4 |         85.7 |         91.1 |             277 |          478 |
|      768 | Qwen2.5-7B-Instruct   | pinning          | 664 |       63.9 | 59.8 | 67.9 |      82.2 |         79.1 |         85.1 |             205 |          484 |
|      768 | Qwen2.5-7B-Instruct   | summary          | 664 |       56.8 | 52.7 | 60.6 |      80.3 |         77   |         83.6 |             138 |          401 |
|      768 | Qwen2.5-7B-Instruct   | typed_llm        | 664 |       70.3 | 66.7 | 73.7 |      82.2 |         79.3 |         85   |             266 |          505 |

## Hard-cap budget sweep: LADL minus baseline

|   budget | model                 | baseline         |   diff |    lo |   hi |     p |
|---------:|:----------------------|:-----------------|-------:|------:|-----:|------:|
|      256 | Llama-3.1-8B-Instruct | summary          |   -3.5 |  -8.5 |  1.4 | 0.16  |
|      256 | Llama-3.1-8B-Instruct | pinning          |   -1.2 |  -7   |  4.4 | 0.722 |
|      256 | Llama-3.1-8B-Instruct | chrono           |   -8.1 | -13.2 | -2.8 | 0.002 |
|      256 | Llama-3.1-8B-Instruct | typed_llm        |   -1.4 |  -4.9 |  2.3 | 0.489 |
|      256 | Llama-3.1-8B-Instruct | lifecycle_nohint |   -9   | -13.7 | -4.6 | 0.001 |
|      256 | Qwen2.5-7B-Instruct   | summary          |   19   |  14.7 | 23   | 0.001 |
|      256 | Qwen2.5-7B-Instruct   | pinning          |   14.3 |   9.8 | 18.9 | 0.001 |
|      256 | Qwen2.5-7B-Instruct   | chrono           |   10.8 |   6.4 | 15.4 | 0.001 |
|      256 | Qwen2.5-7B-Instruct   | typed_llm        |    9.5 |   5.4 | 13.9 | 0.001 |
|      256 | Qwen2.5-7B-Instruct   | lifecycle_nohint |    7.7 |   4.8 | 10.5 | 0.001 |
|      384 | Llama-3.1-8B-Instruct | summary          |   -2   |  -7.8 |  3.6 | 0.49  |
|      384 | Llama-3.1-8B-Instruct | pinning          |    2.4 |  -3.8 |  8.6 | 0.48  |
|      384 | Llama-3.1-8B-Instruct | chrono           |   -7.5 | -13   | -2.2 | 0.006 |
|      384 | Llama-3.1-8B-Instruct | typed_llm        |    1.8 |  -2   |  5.7 | 0.358 |
|      384 | Llama-3.1-8B-Instruct | lifecycle_nohint |   -4.1 |  -8.2 |  0   | 0.052 |
|      384 | Qwen2.5-7B-Instruct   | summary          |   18.1 |  13.6 | 22.4 | 0.001 |
|      384 | Qwen2.5-7B-Instruct   | pinning          |   11.7 |   7.9 | 15.8 | 0.001 |
|      384 | Qwen2.5-7B-Instruct   | chrono           |    7.2 |   3.4 | 11.3 | 0.001 |
|      384 | Qwen2.5-7B-Instruct   | typed_llm        |    4.4 |   0.9 |  7.9 | 0.016 |
|      384 | Qwen2.5-7B-Instruct   | lifecycle_nohint |    6.6 |   3.4 |  9.8 | 0.001 |
|      768 | Llama-3.1-8B-Instruct | summary          |    3   |  -2.2 |  8.2 | 0.281 |
|      768 | Llama-3.1-8B-Instruct | pinning          |    2.9 |  -1.9 |  8   | 0.296 |
|      768 | Llama-3.1-8B-Instruct | chrono           |   -2.6 |  -7.4 |  2.6 | 0.335 |
|      768 | Llama-3.1-8B-Instruct | typed_llm        |    3.6 |   0.1 |  7.5 | 0.048 |
|      768 | Llama-3.1-8B-Instruct | lifecycle_nohint |   -2   |  -6.5 |  2.4 | 0.384 |
|      768 | Qwen2.5-7B-Instruct   | summary          |   20.5 |  16.2 | 25.2 | 0.001 |
|      768 | Qwen2.5-7B-Instruct   | pinning          |   13.4 |   8.8 | 18.3 | 0.001 |
|      768 | Qwen2.5-7B-Instruct   | chrono           |    8   |   3.9 | 11.9 | 0.001 |
|      768 | Qwen2.5-7B-Instruct   | typed_llm        |    6.9 |   3.6 | 10.4 | 0.001 |
|      768 | Qwen2.5-7B-Instruct   | lifecycle_nohint |    7.5 |   4   | 11   | 0.001 |

## Compaction placement: accuracy

| placement   | model                 | condition        |   n |   accuracy |   lo |   hi |   execute |   execute_lo |   execute_hi |   memory_tokens |   max_tokens |
|:------------|:----------------------|:-----------------|----:|-----------:|-----:|-----:|----------:|-------------:|-------------:|----------------:|-------------:|
| spread      | Llama-3.1-8B-Instruct | abl_noguard      | 912 |       81.1 | 78   | 84.2 |      90   |         87.9 |         92   |             295 |          384 |
| spread      | Llama-3.1-8B-Instruct | abl_noreceipt    | 912 |       75.3 | 71.9 | 78.8 |      87.1 |         84.9 |         89.2 |             293 |          384 |
| spread      | Llama-3.1-8B-Instruct | chrono           | 912 |       78.4 | 75   | 81.7 |      87.8 |         85.4 |         90.1 |             318 |          384 |
| spread      | Llama-3.1-8B-Instruct | full             | 912 |       83.4 | 80.3 | 86.4 |      88.8 |         86.3 |         91.2 |               0 |            0 |
| spread      | Llama-3.1-8B-Instruct | lifecycle        | 912 |       77.4 | 73.8 | 81.1 |      89.7 |         87.4 |         91.9 |             293 |          384 |
| spread      | Llama-3.1-8B-Instruct | lifecycle_gold   | 912 |       83.8 | 81   | 86.6 |      92.5 |         90.7 |         94.3 |             295 |          384 |
| spread      | Llama-3.1-8B-Instruct | lifecycle_nohint | 912 |       79.2 | 76   | 82.2 |      90.1 |         87.8 |         92.4 |             276 |          384 |
| spread      | Llama-3.1-8B-Instruct | lifecycle_strict | 912 |       80.7 | 77.7 | 83.8 |      90.1 |         87.9 |         92.3 |             295 |          384 |
| spread      | Llama-3.1-8B-Instruct | pinning          | 912 |       71.6 | 69.2 | 73.9 |      83.6 |         81.6 |         85.4 |             326 |          384 |
| spread      | Llama-3.1-8B-Instruct | summary          | 912 |       73.2 | 70   | 76.3 |      87.8 |         85.5 |         90.1 |             186 |          384 |
| spread      | Llama-3.1-8B-Instruct | typed_llm        | 912 |       76.2 | 73.1 | 79.3 |      88.4 |         86.4 |         90.3 |             292 |          384 |
| spread      | Qwen2.5-7B-Instruct   | abl_noguard      | 912 |       77   | 73.7 | 80   |      88.2 |         85.8 |         90.5 |             251 |          384 |
| spread      | Qwen2.5-7B-Instruct   | abl_noreceipt    | 912 |       74.5 | 70.4 | 77.9 |      86   |         83.3 |         88.6 |             246 |          384 |
| spread      | Qwen2.5-7B-Instruct   | chrono           | 912 |       70.6 | 67.3 | 73.8 |      86.8 |         84.4 |         89.2 |             279 |          384 |
| spread      | Qwen2.5-7B-Instruct   | full             | 912 |       57.2 | 53.2 | 61.1 |      82.9 |         80.4 |         85.2 |               0 |            0 |
| spread      | Qwen2.5-7B-Instruct   | lifecycle        | 912 |       78.1 | 74.9 | 81   |      89.4 |         87.5 |         91.3 |             252 |          384 |
| spread      | Qwen2.5-7B-Instruct   | lifecycle_gold   | 912 |       83.8 | 81.4 | 86   |      93   |         91   |         94.8 |             258 |          384 |
| spread      | Qwen2.5-7B-Instruct   | lifecycle_nohint | 912 |       69.5 | 66.1 | 72.7 |      85   |         82.2 |         87.5 |             233 |          384 |
| spread      | Qwen2.5-7B-Instruct   | lifecycle_strict | 912 |       78.5 | 75.4 | 81.4 |      89.1 |         86.9 |         91.3 |             251 |          384 |
| spread      | Qwen2.5-7B-Instruct   | pinning          | 912 |       62.4 | 59.2 | 65.5 |      78.7 |         76.4 |         81.1 |             183 |          384 |
| spread      | Qwen2.5-7B-Instruct   | summary          | 912 |       58.3 | 54.6 | 61.8 |      79.3 |         76.4 |         82.3 |             124 |          384 |
| spread      | Qwen2.5-7B-Instruct   | typed_llm        | 912 |       71.4 | 67.7 | 74.9 |      83.2 |         80.7 |         85.7 |             244 |          384 |
| early       | Llama-3.1-8B-Instruct | abl_noguard      | 912 |       82.3 | 79.5 | 85.1 |      91.6 |         89.8 |         93.4 |             290 |          384 |
| early       | Llama-3.1-8B-Instruct | abl_noreceipt    | 912 |       79.1 | 76   | 82.2 |      90.6 |         88.5 |         92.7 |             287 |          384 |
| early       | Llama-3.1-8B-Instruct | chrono           | 912 |       80.5 | 77.7 | 83.2 |      87.8 |         85.4 |         90.1 |             318 |          384 |
| early       | Llama-3.1-8B-Instruct | full             | 912 |       83.4 | 80.3 | 86.4 |      88.8 |         86.3 |         91.2 |               0 |            0 |
| early       | Llama-3.1-8B-Instruct | lifecycle        | 912 |       79.1 | 75.7 | 82.4 |      91   |         89.2 |         92.8 |             291 |          384 |
| early       | Llama-3.1-8B-Instruct | lifecycle_gold   | 912 |       85.1 | 82   | 88   |      92.5 |         90.8 |         94.2 |             292 |          384 |
| early       | Llama-3.1-8B-Instruct | lifecycle_nohint | 912 |       81.7 | 78.8 | 84.6 |      90.9 |         88.9 |         92.8 |             275 |          384 |
| early       | Llama-3.1-8B-Instruct | lifecycle_strict | 912 |       83.6 | 80.9 | 86.4 |      91.6 |         89.9 |         93.3 |             290 |          384 |
| early       | Llama-3.1-8B-Instruct | pinning          | 912 |       79.4 | 76.8 | 81.9 |      88.9 |         86.9 |         91   |             325 |          384 |
| early       | Llama-3.1-8B-Instruct | summary          | 912 |       76.8 | 73.8 | 79.5 |      89.3 |         86.9 |         91.4 |             178 |          374 |
| early       | Llama-3.1-8B-Instruct | typed_llm        | 912 |       77.4 | 74.2 | 80.6 |      89.7 |         87.7 |         91.8 |             288 |          384 |
| early       | Qwen2.5-7B-Instruct   | abl_noguard      | 912 |       76.4 | 73.5 | 79.3 |      88.7 |         86.3 |         91.1 |             230 |          383 |
| early       | Qwen2.5-7B-Instruct   | abl_noreceipt    | 912 |       74.2 | 70.7 | 77.4 |      86.7 |         84   |         89.4 |             227 |          383 |
| early       | Qwen2.5-7B-Instruct   | chrono           | 912 |       70.8 | 66.4 | 75.1 |      86.1 |         83.6 |         88.3 |             264 |          384 |
| early       | Qwen2.5-7B-Instruct   | full             | 912 |       57.3 | 53.3 | 61.2 |      82.9 |         80.4 |         85.2 |               0 |            0 |
| early       | Qwen2.5-7B-Instruct   | lifecycle        | 912 |       76.8 | 73.8 | 79.5 |      90   |         88   |         92.1 |             230 |          377 |
| early       | Qwen2.5-7B-Instruct   | lifecycle_gold   | 912 |       82.5 | 80.1 | 85   |      92.4 |         90.5 |         94.3 |             242 |          384 |
| early       | Qwen2.5-7B-Instruct   | lifecycle_nohint | 912 |       71.2 | 67.6 | 74.9 |      88.8 |         86   |         91.5 |             211 |          377 |
| early       | Qwen2.5-7B-Instruct   | lifecycle_strict | 912 |       77.3 | 74   | 80.3 |      89.8 |         87.6 |         92   |             231 |          383 |
| early       | Qwen2.5-7B-Instruct   | pinning          | 912 |       65.1 | 61.2 | 68.8 |      84   |         81.2 |         86.5 |             162 |          336 |
| early       | Qwen2.5-7B-Instruct   | summary          | 912 |       59.9 | 56.4 | 63.4 |      81.8 |         79   |         84.5 |             107 |          227 |
| early       | Qwen2.5-7B-Instruct   | typed_llm        | 912 |       73.9 | 71   | 76.8 |      85.4 |         83.1 |         87.7 |             223 |          384 |
| late        | Llama-3.1-8B-Instruct | abl_noguard      | 912 |       80.7 | 77.1 | 84.1 |      90.8 |         88.6 |         92.6 |             309 |          384 |
| late        | Llama-3.1-8B-Instruct | abl_noreceipt    | 912 |       77.1 | 72.9 | 81   |      89.7 |         87.4 |         91.8 |             307 |          384 |
| late        | Llama-3.1-8B-Instruct | chrono           | 912 |       77.1 | 74   | 80.2 |      84.5 |         82   |         87   |             338 |          384 |
| late        | Llama-3.1-8B-Instruct | full             | 912 |       83.4 | 80.3 | 86.4 |      88.8 |         86.3 |         91.2 |               0 |            0 |
| late        | Llama-3.1-8B-Instruct | lifecycle        | 912 |       78   | 74.3 | 81.7 |      90.9 |         88.7 |         92.9 |             309 |          384 |
| late        | Llama-3.1-8B-Instruct | lifecycle_gold   | 912 |       83.9 | 80.9 | 86.9 |      91.9 |         90.3 |         93.5 |             308 |          384 |
| late        | Llama-3.1-8B-Instruct | lifecycle_nohint | 912 |       80.8 | 77.7 | 83.8 |      91.2 |         89.6 |         92.8 |             295 |          384 |
| late        | Llama-3.1-8B-Instruct | lifecycle_strict | 912 |       81.5 | 78.4 | 84.4 |      91   |         89   |         92.8 |             308 |          384 |
| late        | Llama-3.1-8B-Instruct | pinning          | 912 |       71.4 | 68.3 | 74.5 |      82.9 |         80.6 |         85.1 |             347 |          384 |
| late        | Llama-3.1-8B-Instruct | summary          | 912 |       74   | 70.5 | 77.3 |      87   |         84.6 |         89.1 |             198 |          384 |
| late        | Llama-3.1-8B-Instruct | typed_llm        | 912 |       77.3 | 73.8 | 80.7 |      89   |         86.6 |         91.4 |             306 |          384 |
| late        | Qwen2.5-7B-Instruct   | abl_noguard      | 912 |       77.9 | 74.9 | 80.9 |      87.6 |         85.3 |         89.9 |             276 |          384 |
| late        | Qwen2.5-7B-Instruct   | abl_noreceipt    | 912 |       75   | 71.6 | 78.3 |      86.1 |         83.1 |         88.9 |             271 |          384 |
| late        | Qwen2.5-7B-Instruct   | chrono           | 912 |       72.1 | 68.8 | 75.4 |      86.1 |         83.5 |         88.5 |             307 |          384 |
| late        | Qwen2.5-7B-Instruct   | full             | 912 |       57.3 | 53.3 | 61.2 |      82.9 |         80.4 |         85.2 |               0 |            0 |
| late        | Qwen2.5-7B-Instruct   | lifecycle        | 912 |       79.4 | 76.3 | 82.6 |      89.7 |         87.4 |         91.9 |             275 |          384 |
| late        | Qwen2.5-7B-Instruct   | lifecycle_gold   | 912 |       82.2 | 79.9 | 84.6 |      91.4 |         89.7 |         93.2 |             279 |          384 |
| late        | Qwen2.5-7B-Instruct   | lifecycle_nohint | 912 |       71.9 | 69   | 74.9 |      86   |         83.7 |         88.2 |             258 |          384 |
| late        | Qwen2.5-7B-Instruct   | lifecycle_strict | 912 |       80.3 | 77.4 | 83.3 |      90.7 |         88.3 |         92.9 |             274 |          384 |
| late        | Qwen2.5-7B-Instruct   | pinning          | 912 |       61.7 | 58.7 | 64.7 |      79.7 |         77.6 |         81.8 |             207 |          384 |
| late        | Qwen2.5-7B-Instruct   | summary          | 912 |       57.2 | 53.3 | 61.3 |      78.6 |         75.3 |         81.7 |             150 |          384 |
| late        | Qwen2.5-7B-Instruct   | typed_llm        | 912 |       72   | 69.3 | 74.8 |      84.3 |         82.1 |         86.6 |             266 |          384 |

## Compaction placement: LADL minus baseline

| placement   | model                 | baseline         |   diff |   lo |   hi |     p |
|:------------|:----------------------|:-----------------|-------:|-----:|-----:|------:|
| spread      | Llama-3.1-8B-Instruct | summary          |    4.2 |  0.5 |  7.7 | 0.029 |
| spread      | Llama-3.1-8B-Instruct | pinning          |    5.8 |  2.3 |  9.2 | 0.002 |
| spread      | Llama-3.1-8B-Instruct | chrono           |   -1   | -4.6 |  2.5 | 0.582 |
| spread      | Llama-3.1-8B-Instruct | typed_llm        |    1.2 | -1.8 |  4   | 0.436 |
| spread      | Llama-3.1-8B-Instruct | lifecycle_nohint |   -1.8 | -5.1 |  1.5 | 0.337 |
| spread      | Qwen2.5-7B-Instruct   | summary          |   19.7 | 15.2 | 24.2 | 0.001 |
| spread      | Qwen2.5-7B-Instruct   | pinning          |   15.7 | 11.8 | 19.7 | 0.001 |
| spread      | Qwen2.5-7B-Instruct   | chrono           |    7.5 |  4.1 | 10.7 | 0.001 |
| spread      | Qwen2.5-7B-Instruct   | typed_llm        |    6.7 |  3.1 | 10.5 | 0.001 |
| spread      | Qwen2.5-7B-Instruct   | lifecycle_nohint |    8.6 |  5.6 | 11.5 | 0.001 |
| early       | Llama-3.1-8B-Instruct | summary          |    2.3 | -1.6 |  6.2 | 0.238 |
| early       | Llama-3.1-8B-Instruct | pinning          |   -0.3 | -3.6 |  3   | 0.922 |
| early       | Llama-3.1-8B-Instruct | chrono           |   -1.4 | -5.3 |  2.2 | 0.499 |
| early       | Llama-3.1-8B-Instruct | typed_llm        |    1.6 | -0.6 |  4   | 0.165 |
| early       | Llama-3.1-8B-Instruct | lifecycle_nohint |   -2.6 | -5.3 |  0   | 0.056 |
| early       | Qwen2.5-7B-Instruct   | summary          |   16.9 | 13.9 | 19.9 | 0.001 |
| early       | Qwen2.5-7B-Instruct   | pinning          |   11.6 |  7.7 | 15.4 | 0.001 |
| early       | Qwen2.5-7B-Instruct   | chrono           |    5.9 |  2.6 |  9.8 | 0.001 |
| early       | Qwen2.5-7B-Instruct   | typed_llm        |    2.9 |  0.4 |  5.4 | 0.021 |
| early       | Qwen2.5-7B-Instruct   | lifecycle_nohint |    5.6 |  2.6 |  8.5 | 0.001 |
| late        | Llama-3.1-8B-Instruct | summary          |    3.9 | -0.4 |  8.1 | 0.076 |
| late        | Llama-3.1-8B-Instruct | pinning          |    6.6 |  2.4 | 10.6 | 0.002 |
| late        | Llama-3.1-8B-Instruct | chrono           |    0.9 | -3.3 |  4.8 | 0.697 |
| late        | Llama-3.1-8B-Instruct | typed_llm        |    0.7 | -1.9 |  3.3 | 0.665 |
| late        | Llama-3.1-8B-Instruct | lifecycle_nohint |   -2.9 | -6   |  0.2 | 0.071 |
| late        | Qwen2.5-7B-Instruct   | summary          |   22.1 | 18.1 | 26.3 | 0.001 |
| late        | Qwen2.5-7B-Instruct   | pinning          |   17.7 | 13.5 | 21.9 | 0.001 |
| late        | Qwen2.5-7B-Instruct   | chrono           |    7.2 |  3.5 | 11.1 | 0.001 |
| late        | Qwen2.5-7B-Instruct   | typed_llm        |    7.3 |  4.5 | 10.2 | 0.001 |
| late        | Qwen2.5-7B-Instruct   | lifecycle_nohint |    7.5 |  4.6 | 10.4 | 0.001 |
