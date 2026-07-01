# Exit Rule Comparison

Date: 2026-07-01

## Correction

The selected strategy had two different mechanisms mixed together: non-floor AI positions used trend gates, while NBIS and SMCI conviction floors were allowed to stay as target-weight positions. This report compares that against explicit sell-to-avoid-downturn variants and replaces the defensive bucket with GLD/gold variants.

## Long Framework Window

| strategy                                   | window              |   cagr |   sharpe |   max_drawdown |   worst_12m |   turnover |     end_value |
|:-------------------------------------------|:--------------------|-------:|---------:|---------------:|------------:|-----------:|--------------:|
| current_weekly_rebalance_GLD_defensive     | 2016-07-01_to_today | 0.6261 |   1.7654 |        -0.2970 |     -0.2540 |    10.1085 | 35552174.5502 |
| GLD_all_ai_basket_150dma_exit              | 2016-07-01_to_today | 0.6038 |   1.7283 |        -0.3104 |     -0.2892 |    11.2355 | 30973996.3751 |
| GLD_all_ai_basket_200dma_exit              | 2016-07-01_to_today | 0.6027 |   1.7267 |        -0.3132 |     -0.2854 |    10.4153 | 30762602.9874 |
| GLD_all_ai_20pct_from_21d_high_exit        | 2016-07-01_to_today | 0.5939 |   1.7352 |        -0.3159 |     -0.2503 |    12.0058 | 29113443.6613 |
| GLD_all_ai_25pct_from_21d_high_exit        | 2016-07-01_to_today | 0.5928 |   1.7166 |        -0.3055 |     -0.2552 |    11.1997 | 28910473.5470 |
| GLD_floors_obey_100dma_gate                | 2016-07-01_to_today | 0.5873 |   1.7119 |        -0.2937 |     -0.2729 |    11.5186 | 27931198.1701 |
| GLD_all_ai_25pct_from_63d_high_exit        | 2016-07-01_to_today | 0.5764 |   1.7032 |        -0.3023 |     -0.2531 |    11.7083 | 26077024.6673 |
| GLD_all_ai_20pct_from_63d_high_exit        | 2016-07-01_to_today | 0.5726 |   1.7137 |        -0.3124 |     -0.2402 |    12.5091 | 25456839.8017 |
| GLD_all_ai_basket_100dma_exit              | 2016-07-01_to_today | 0.5725 |   1.6685 |        -0.3458 |     -0.3431 |    13.9545 | 25447213.1216 |
| GLD_all_ai_20pct_from_126d_high_exit       | 2016-07-01_to_today | 0.5674 |   1.7223 |        -0.3215 |     -0.2418 |    12.8978 | 24635599.3036 |
| current_weekly_rebalance_BIL_defensive     | 2016-07-01_to_today | 0.5660 |   1.6644 |        -0.3085 |     -0.2209 |    10.1085 | 24414551.5047 |
| GLD_all_ai_individual_100dma_exit          | 2016-07-01_to_today | 0.5591 |   1.6824 |        -0.2845 |     -0.2589 |    15.5486 | 23364666.3996 |
| GLD_all_ai_25pct_from_126d_high_exit       | 2016-07-01_to_today | 0.5568 |   1.6769 |        -0.3124 |     -0.2570 |    12.2015 | 23016395.8559 |
| GLD_all_ai_individual100_plus_qqq200_exit  | 2016-07-01_to_today | 0.5536 |   1.6787 |        -0.2748 |     -0.2486 |    17.8362 | 22550195.3298 |
| GLD_all_ai_individual_200dma_exit          | 2016-07-01_to_today | 0.5486 |   1.6630 |        -0.3108 |     -0.2822 |    11.0801 | 21836576.9361 |
| GLD_all_ai_individual_150dma_exit          | 2016-07-01_to_today | 0.5430 |   1.6323 |        -0.3162 |     -0.2993 |    12.8668 | 21061645.7394 |
| GLD_all_ai_individual200_or_basket200_exit | 2016-07-01_to_today | 0.5410 |   1.6514 |        -0.3275 |     -0.2889 |    10.9290 | 20799494.9118 |
| BIL_all_ai_basket_200dma_exit              | 2016-07-01_to_today | 0.5392 |   1.6180 |        -0.3130 |     -0.2673 |    10.4153 | 20548940.3723 |
| BIL_all_ai_basket_150dma_exit              | 2016-07-01_to_today | 0.5390 |   1.6183 |        -0.3108 |     -0.2581 |    11.2355 | 20532823.9804 |
| GLD_all_ai_individual150_or_basket150_exit | 2016-07-01_to_today | 0.5376 |   1.6270 |        -0.3305 |     -0.3141 |    13.5126 | 20347932.0774 |
| GLD_all_ai_individual100_plus_qqq100_exit  | 2016-07-01_to_today | 0.5364 |   1.6419 |        -0.2680 |     -0.2387 |    21.0369 | 20181966.2292 |
| GLD_all_ai_individual100_or_basket100_exit | 2016-07-01_to_today | 0.5334 |   1.6338 |        -0.3295 |     -0.3254 |    18.0470 | 19790684.9360 |
| BIL_all_ai_20pct_from_21d_high_exit        | 2016-07-01_to_today | 0.5297 |   1.6229 |        -0.3283 |     -0.2113 |    12.0058 | 19325666.4098 |
| BIL_all_ai_25pct_from_21d_high_exit        | 2016-07-01_to_today | 0.5275 |   1.6015 |        -0.3176 |     -0.2203 |    11.1997 | 19048685.4700 |
| BIL_floors_obey_100dma_gate                | 2016-07-01_to_today | 0.5271 |   1.6085 |        -0.3064 |     -0.2388 |    11.5186 | 19003324.9792 |
| BIL_all_ai_basket_100dma_exit              | 2016-07-01_to_today | 0.5125 |   1.5671 |        -0.3003 |     -0.2936 |    13.9545 | 17267245.5470 |
| GLD_all_ai_individual_75dma_exit           | 2016-07-01_to_today | 0.5101 |   1.5952 |        -0.2917 |     -0.2632 |    19.6884 | 16995823.1078 |
| BIL_all_ai_25pct_from_63d_high_exit        | 2016-07-01_to_today | 0.5095 |   1.5866 |        -0.3144 |     -0.2173 |    11.7083 | 16921259.1192 |
| BIL_all_ai_20pct_from_63d_high_exit        | 2016-07-01_to_today | 0.5029 |   1.5910 |        -0.3220 |     -0.2035 |    12.5091 | 16197507.5749 |
| GLD_all_ai_15pct_from_21d_high_exit        | 2016-07-01_to_today | 0.4981 |   1.5610 |        -0.3079 |     -0.2841 |    17.2004 | 15689334.5117 |
| GLD_all_ai_individual_50dma_exit           | 2016-07-01_to_today | 0.4942 |   1.6040 |        -0.2591 |     -0.2128 |    21.8012 | 15286880.1311 |
| BIL_all_ai_20pct_from_126d_high_exit       | 2016-07-01_to_today | 0.4938 |   1.5921 |        -0.3315 |     -0.2133 |    12.8978 | 15253405.5227 |
| BIL_all_ai_individual_100dma_exit          | 2016-07-01_to_today | 0.4930 |   1.5678 |        -0.2957 |     -0.2253 |    15.5486 | 15167193.9168 |
| GLD_all_ai_15pct_from_63d_high_exit        | 2016-07-01_to_today | 0.4909 |   1.5663 |        -0.3021 |     -0.2825 |    17.3332 | 14954170.2937 |
| BIL_all_ai_25pct_from_126d_high_exit       | 2016-07-01_to_today | 0.4908 |   1.5615 |        -0.3246 |     -0.2213 |    12.2015 | 14950121.8636 |
| GLD_all_ai_basket_50dma_exit               | 2016-07-01_to_today | 0.4895 |   1.5573 |        -0.2808 |     -0.1923 |    24.8667 | 14816622.9897 |
| BIL_all_ai_individual_200dma_exit          | 2016-07-01_to_today | 0.4868 |   1.5540 |        -0.2661 |     -0.2382 |    11.0801 | 14556376.6776 |
| BIL_all_ai_individual_150dma_exit          | 2016-07-01_to_today | 0.4836 |   1.5286 |        -0.2999 |     -0.2646 |    12.8668 | 14239925.1441 |
| BIL_all_ai_individual100_plus_qqq200_exit  | 2016-07-01_to_today | 0.4784 |   1.5554 |        -0.2737 |     -0.1997 |    17.8362 | 13757048.8911 |
| BIL_all_ai_individual200_or_basket200_exit | 2016-07-01_to_today | 0.4761 |   1.5350 |        -0.2737 |     -0.2646 |    10.9290 | 13536230.6459 |
| GLD_all_ai_15pct_from_126d_high_exit       | 2016-07-01_to_today | 0.4754 |   1.5570 |        -0.3175 |     -0.2906 |    17.9534 | 13474627.4852 |
| BIL_all_ai_individual150_or_basket150_exit | 2016-07-01_to_today | 0.4750 |   1.5168 |        -0.2989 |     -0.2839 |    13.5126 | 13442701.4309 |
| BIL_all_ai_individual100_or_basket100_exit | 2016-07-01_to_today | 0.4661 |   1.5154 |        -0.2903 |     -0.2815 |    18.0470 | 12653331.6125 |
| BIL_all_ai_individual100_plus_qqq100_exit  | 2016-07-01_to_today | 0.4593 |   1.5133 |        -0.2656 |     -0.1986 |    21.0369 | 12079645.8017 |
| GLD_all_ai_individual50_or_basket50_exit   | 2016-07-01_to_today | 0.4516 |   1.5398 |        -0.2179 |     -0.1802 |    28.4206 | 11458583.3047 |
| BIL_all_ai_individual_75dma_exit           | 2016-07-01_to_today | 0.4476 |   1.4822 |        -0.3052 |     -0.2261 |    19.6884 | 11146276.4355 |
| BIL_all_ai_15pct_from_21d_high_exit        | 2016-07-01_to_today | 0.4409 |   1.4576 |        -0.2963 |     -0.2413 |    17.2004 | 10645440.5499 |
| BIL_all_ai_basket_50dma_exit               | 2016-07-01_to_today | 0.4300 |   1.4458 |        -0.3144 |     -0.1694 |    24.8667 |  9864684.8985 |
| BIL_all_ai_individual_50dma_exit           | 2016-07-01_to_today | 0.4289 |   1.4789 |        -0.2658 |     -0.1845 |    21.8012 |  9795351.8385 |
| BIL_all_ai_15pct_from_63d_high_exit        | 2016-07-01_to_today | 0.4270 |   1.4509 |        -0.3127 |     -0.2419 |    17.3332 |  9660352.7739 |
| BIL_all_ai_15pct_from_126d_high_exit       | 2016-07-01_to_today | 0.4104 |   1.4371 |        -0.2994 |     -0.2531 |    17.9534 |  8599757.7056 |
| GLD_all_ai_10pct_from_21d_high_exit        | 2016-07-01_to_today | 0.4078 |   1.4226 |        -0.3034 |     -0.2768 |    24.0054 |  8439455.2766 |
| BIL_all_ai_individual50_or_basket50_exit   | 2016-07-01_to_today | 0.3887 |   1.4190 |        -0.2265 |     -0.1578 |    28.4206 |  7364730.1915 |
| GLD_all_ai_10pct_from_63d_high_exit        | 2016-07-01_to_today | 0.3871 |   1.4002 |        -0.2768 |     -0.2589 |    25.2458 |  7281430.2055 |
| GLD_all_ai_10pct_from_126d_high_exit       | 2016-07-01_to_today | 0.3752 |   1.3914 |        -0.2738 |     -0.2250 |    24.4210 |  6684946.2215 |
| BIL_all_ai_10pct_from_21d_high_exit        | 2016-07-01_to_today | 0.3568 |   1.3266 |        -0.2637 |     -0.2378 |    24.0054 |  5843663.0136 |
| BIL_all_ai_10pct_from_63d_high_exit        | 2016-07-01_to_today | 0.3248 |   1.2718 |        -0.2471 |     -0.2273 |    25.2458 |  4606257.1485 |
| BIL_all_ai_10pct_from_126d_high_exit       | 2016-07-01_to_today | 0.3178 |   1.2789 |        -0.2428 |     -0.1754 |    24.4210 |  4368898.9805 |

## Common Window Including Current Target Names

Common start: 2025-02-13. This is the clean comparison for static no-rebalance because NBIS/SNDK proxy do not have full 10-year histories.

| strategy                                   | window              |   cagr |   sharpe |   max_drawdown |   worst_12m |   turnover |    end_value |
|:-------------------------------------------|:--------------------|-------:|---------:|---------------:|------------:|-----------:|-------------:|
| static_buy_once_no_rebalance               | 2025-02-13_to_today | 3.7736 |   2.7958 |        -0.3730 |      2.1267 |     0.0000 | 2383652.2484 |
| GLD_all_ai_individual50_or_basket50_exit   | 2025-02-13_to_today | 1.6622 |   2.7877 |        -0.1389 |      1.1287 |    28.4206 | 1069132.5219 |
| current_weekly_rebalance_GLD_defensive     | 2025-02-13_to_today | 1.6612 |   2.4617 |        -0.2397 |      1.0936 |    10.1085 | 1068624.1836 |
| GLD_all_ai_basket_50dma_exit               | 2025-02-13_to_today | 1.5942 |   2.5242 |        -0.1857 |      0.9271 |    24.8667 | 1031810.9701 |
| GLD_all_ai_basket_200dma_exit              | 2025-02-13_to_today | 1.5886 |   2.4026 |        -0.2448 |      1.0156 |    10.4153 | 1028798.8017 |
| GLD_all_ai_basket_100dma_exit              | 2025-02-13_to_today | 1.5852 |   2.4130 |        -0.1944 |      1.0119 |    13.9545 | 1026905.3116 |
| GLD_all_ai_basket_150dma_exit              | 2025-02-13_to_today | 1.5605 |   2.3765 |        -0.2420 |      0.9856 |    11.2355 | 1013492.2628 |
| current_weekly_rebalance_BIL_defensive     | 2025-02-13_to_today | 1.5155 |   2.3539 |        -0.2510 |      0.9187 |    10.1085 |  989104.8018 |
| GLD_all_ai_individual_50dma_exit           | 2025-02-13_to_today | 1.5056 |   2.5819 |        -0.1866 |      1.1155 |    21.8012 |  983785.7694 |
| BIL_all_ai_basket_200dma_exit              | 2025-02-13_to_today | 1.4522 |   2.3016 |        -0.2559 |      0.8528 |    10.4153 |  955113.1530 |
| BIL_all_ai_basket_100dma_exit              | 2025-02-13_to_today | 1.4503 |   2.3243 |        -0.2018 |      0.8508 |    13.9545 |  954082.4904 |
| GLD_all_ai_20pct_from_21d_high_exit        | 2025-02-13_to_today | 1.4337 |   2.3962 |        -0.2308 |      0.9013 |    12.0058 |  945218.5817 |
| BIL_all_ai_basket_150dma_exit              | 2025-02-13_to_today | 1.4110 |   2.2659 |        -0.2535 |      0.8101 |    11.2355 |  933124.3849 |
| GLD_all_ai_25pct_from_21d_high_exit        | 2025-02-13_to_today | 1.4004 |   2.2969 |        -0.2420 |      0.9102 |    11.1997 |  927524.8160 |
| GLD_all_ai_individual_75dma_exit           | 2025-02-13_to_today | 1.3180 |   2.3437 |        -0.2275 |      0.8916 |    19.6884 |  884089.4890 |
| GLD_all_ai_individual100_or_basket100_exit | 2025-02-13_to_today | 1.3119 |   2.3156 |        -0.1967 |      0.9042 |    18.0470 |  880880.4897 |
| GLD_floors_obey_100dma_gate                | 2025-02-13_to_today | 1.2873 |   2.1980 |        -0.2350 |      0.8614 |    11.5186 |  868053.8129 |
| BIL_all_ai_individual50_or_basket50_exit   | 2025-02-13_to_today | 1.2627 |   2.4396 |        -0.1446 |      0.7616 |    28.4206 |  855224.3783 |
| BIL_all_ai_basket_50dma_exit               | 2025-02-13_to_today | 1.2562 |   2.2169 |        -0.2057 |      0.6759 |    24.8667 |  851850.8052 |
| GLD_all_ai_20pct_from_63d_high_exit        | 2025-02-13_to_today | 1.2460 |   2.2828 |        -0.2240 |      0.7804 |    12.5091 |  846584.2541 |
| BIL_all_ai_20pct_from_21d_high_exit        | 2025-02-13_to_today | 1.2380 |   2.2257 |        -0.2381 |      0.7291 |    12.0058 |  842419.2247 |
| GLD_all_ai_individual100_plus_qqq200_exit  | 2025-02-13_to_today | 1.2347 |   2.2119 |        -0.2132 |      0.8560 |    17.8362 |  840749.7798 |
| BIL_all_ai_individual_50dma_exit           | 2025-02-13_to_today | 1.2276 |   2.3503 |        -0.1819 |      0.8138 |    21.8012 |  837065.7077 |
| GLD_all_ai_25pct_from_63d_high_exit        | 2025-02-13_to_today | 1.2261 |   2.1954 |        -0.2408 |      0.7240 |    11.7083 |  836321.9891 |
| GLD_all_ai_individual100_plus_qqq100_exit  | 2025-02-13_to_today | 1.2235 |   2.1956 |        -0.2058 |      0.8681 |    21.0369 |  834952.7425 |
| GLD_all_ai_individual_100dma_exit          | 2025-02-13_to_today | 1.2229 |   2.2080 |        -0.2237 |      0.8454 |    15.5486 |  834668.8471 |
| GLD_all_ai_20pct_from_126d_high_exit       | 2025-02-13_to_today | 1.2059 |   2.2916 |        -0.2240 |      0.7234 |    12.8978 |  825893.1670 |
| BIL_all_ai_25pct_from_21d_high_exit        | 2025-02-13_to_today | 1.2032 |   2.1220 |        -0.2529 |      0.7258 |    11.1997 |  824487.9990 |
| BIL_floors_obey_100dma_gate                | 2025-02-13_to_today | 1.1623 |   2.0942 |        -0.2468 |      0.7041 |    11.5186 |  803545.4023 |
| GLD_all_ai_individual_200dma_exit          | 2025-02-13_to_today | 1.1421 |   2.0918 |        -0.1883 |      0.5735 |    11.0801 |  793273.9457 |
| GLD_all_ai_individual200_or_basket200_exit | 2025-02-13_to_today | 1.1421 |   2.0918 |        -0.1883 |      0.5735 |    10.9290 |  793273.9457 |
| GLD_all_ai_15pct_from_21d_high_exit        | 2025-02-13_to_today | 1.1300 |   2.1793 |        -0.1791 |      0.9086 |    17.2004 |  787139.6556 |
| BIL_all_ai_individual100_or_basket100_exit | 2025-02-13_to_today | 1.0995 |   2.1445 |        -0.1934 |      0.7342 |    18.0470 |  771688.4566 |
| GLD_all_ai_individual150_or_basket150_exit | 2025-02-13_to_today | 1.0945 |   1.9959 |        -0.2177 |      0.6539 |    13.5126 |  769184.8926 |
| GLD_all_ai_individual_150dma_exit          | 2025-02-13_to_today | 1.0902 |   1.9908 |        -0.2193 |      0.6492 |    12.8668 |  766996.9323 |
| GLD_all_ai_25pct_from_126d_high_exit       | 2025-02-13_to_today | 1.0760 |   2.0765 |        -0.2436 |      0.6710 |    12.2015 |  759862.4295 |
| BIL_all_ai_individual_75dma_exit           | 2025-02-13_to_today | 1.0745 |   2.1325 |        -0.2323 |      0.6367 |    19.6884 |  759122.9670 |
| GLD_all_ai_15pct_from_63d_high_exit        | 2025-02-13_to_today | 1.0669 |   2.1579 |        -0.1938 |      0.8817 |    17.3332 |  755283.5783 |
| BIL_all_ai_individual_100dma_exit          | 2025-02-13_to_today | 1.0285 |   2.0444 |        -0.2277 |      0.6542 |    15.5486 |  736091.5607 |
| BIL_all_ai_25pct_from_63d_high_exit        | 2025-02-13_to_today | 1.0265 |   2.0159 |        -0.2512 |      0.5399 |    11.7083 |  735095.8547 |
| BIL_all_ai_20pct_from_63d_high_exit        | 2025-02-13_to_today | 1.0073 |   2.0592 |        -0.2276 |      0.5614 |    12.5091 |  725549.9706 |
| BIL_all_ai_individual100_plus_qqq100_exit  | 2025-02-13_to_today | 1.0054 |   2.0419 |        -0.1946 |      0.6335 |    21.0369 |  724617.8411 |
| BIL_all_ai_individual100_plus_qqq200_exit  | 2025-02-13_to_today | 0.9869 |   2.0077 |        -0.2035 |      0.6246 |    17.8362 |  715468.6016 |
| BIL_all_ai_individual_200dma_exit          | 2025-02-13_to_today | 0.9823 |   1.9404 |        -0.1850 |      0.3968 |    11.0801 |  713161.9789 |
| BIL_all_ai_individual200_or_basket200_exit | 2025-02-13_to_today | 0.9823 |   1.9404 |        -0.1850 |      0.3968 |    10.9290 |  713161.9789 |
| BIL_all_ai_individual150_or_basket150_exit | 2025-02-13_to_today | 0.9727 |   1.8927 |        -0.2285 |      0.5092 |    13.5126 |  708438.6191 |
| BIL_all_ai_individual_150dma_exit          | 2025-02-13_to_today | 0.9691 |   1.8880 |        -0.2295 |      0.5054 |    12.8668 |  706661.3777 |
| GLD_all_ai_15pct_from_126d_high_exit       | 2025-02-13_to_today | 0.9570 |   2.0984 |        -0.1729 |      0.7928 |    17.9534 |  700715.7217 |
| BIL_all_ai_20pct_from_126d_high_exit       | 2025-02-13_to_today | 0.9381 |   2.0313 |        -0.2276 |      0.5029 |    12.8978 |  691450.8153 |
| BIL_all_ai_15pct_from_21d_high_exit        | 2025-02-13_to_today | 0.9200 |   1.9693 |        -0.1815 |      0.6830 |    17.2004 |  682605.8935 |
| BIL_all_ai_25pct_from_126d_high_exit       | 2025-02-13_to_today | 0.8868 |   1.8946 |        -0.2540 |      0.4926 |    12.2015 |  666406.1921 |
| GLD_all_ai_10pct_from_21d_high_exit        | 2025-02-13_to_today | 0.8300 |   1.9886 |        -0.1836 |      0.7220 |    24.0054 |  639044.4309 |
| BIL_all_ai_15pct_from_63d_high_exit        | 2025-02-13_to_today | 0.8156 |   1.9047 |        -0.1966 |      0.5980 |    17.3332 |  632150.6834 |
| GLD_all_ai_10pct_from_63d_high_exit        | 2025-02-13_to_today | 0.8083 |   2.0185 |        -0.1875 |      0.7041 |    25.2458 |  628676.4614 |
| BIL_all_ai_15pct_from_126d_high_exit       | 2025-02-13_to_today | 0.7130 |   1.8308 |        -0.1737 |      0.5315 |    17.9534 |  583621.4922 |
| GLD_all_ai_10pct_from_126d_high_exit       | 2025-02-13_to_today | 0.7010 |   1.8836 |        -0.1875 |      0.5716 |    24.4210 |  578028.0180 |
| BIL_all_ai_10pct_from_21d_high_exit        | 2025-02-13_to_today | 0.6672 |   1.8184 |        -0.1622 |      0.5816 |    24.0054 |  562296.7373 |
| BIL_all_ai_10pct_from_63d_high_exit        | 2025-02-13_to_today | 0.5835 |   1.7567 |        -0.1617 |      0.4512 |    25.2458 |  523923.3285 |
| BIL_all_ai_10pct_from_126d_high_exit       | 2025-02-13_to_today | 0.5154 |   1.6849 |        -0.1617 |      0.3741 |    24.4210 |  493232.3585 |

## Interpretation

- Daily close-to-close is the return measurement, not necessarily the rebalance rule.
- The prior chosen strategy was not a pure downturn-avoidance strategy for NBIS/SMCI. It was trend-gated for non-floor AI names and target-weight rebalanced for NBIS/SMCI floors.
- GLD variants replace the BIL/cash defensive sleeve and route exit proceeds into gold.
- In this dataset, the weekly current strategy still beat the 100-day hard-exit variants on CAGR in the long framework window.
- Hard 100-day exits reduced some risk in some windows but also created more whipsaw and did not clearly dominate.
- Static buy-once/no-rebalance is only testable on the shorter common window and should not be treated as a 10-year proof.

Chart: `exit_rule_comparison_chart.png`
