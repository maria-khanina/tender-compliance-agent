# Baseline vs SFT vs DPO verdict-model comparison

Validation split (`sft/data/verdicts_validation.jsonl`), n=96.

## Overall

| Metric | baseline | sft | dpo |
|---|---|---|---|
| Verdict accuracy | 0.531 | 0.573 | 0.583 |
| Macro F1 | 0.254 | 0.292 | 0.436 |
| Evidence recall | 0.922 | 0.947 | 0.931 |
| Failed to parse (of 96) | 13 | 3 | 1 |

## Per-class F1

| Class | Support | baseline | sft | dpo |
|---|---|---|---|---|
| compliant | 58 | 0.733 | 0.807 | 0.796 |
| non_compliant | 18 | 0.083 | 0.095 | 0.091 |
| insufficient_information | 16 | 0.200 | 0.267 | 0.311 |
| contradictory | 4 | 0.000 | 0.000 | 0.545 |
