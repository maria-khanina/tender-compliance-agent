# Baseline vs SFT verdict-model comparison

Validation split (`sft/data/verdicts_validation.jsonl`), n=96.

- Baseline: `Qwen/Qwen3-8B-AWQ`
- SFT: `sft-verdict`

## Overall

| Metric | Baseline | SFT | Delta |
|---|---|---|---|
| Verdict accuracy | 0.677 | 0.604 | -0.073 |
| Macro F1 | 0.367 | 0.350 | -0.017 |
| Evidence recall (n=88) | 0.960 | 0.912 | -0.048 |
| Failed to parse (of 96) | 0 | 3 | - |

## Per-class precision / recall / F1

| Class | Support | Base precision | SFT precision | Base recall | SFT recall | Base F1 | SFT F1 |
|---|---|---|---|---|---|---|---|
| compliant | 58 | 0.764 | 0.836 | 0.948 | 0.793 | 0.846 | 0.814 |
| non_compliant | 18 | 1.000 | 1.000 | 0.111 | 0.111 | 0.200 | 0.200 |
| contradictory | 4 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| insufficient_information | 16 | 0.364 | 0.278 | 0.500 | 0.625 | 0.421 | 0.385 |
