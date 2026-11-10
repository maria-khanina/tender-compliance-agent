# Training memory and step time

| Configuration | Checkpointing | Tokens per micro-batch | Micro-batches per step | Static GiB | Peak allocated GiB | Peak reserved GiB | Seconds per step | Tokens per second |
|---|---|---|---|---|---|---|---|---|
| checkpointing_on_len1024_batch1 | on | 1024 | 1 | 2.62 | 4.81 | 5.48 | 1.74 | 589.68 |
| checkpointing_off_len1024_batch1 | off | 1024 | 1 | 2.62 | 11.67 | 12.27 | 19.91 | 51.44 |
| checkpointing_on_len2048_batch1 | on | 2048 | 1 | 2.62 | 6.73 | 7.87 | 3.84 | 533.85 |
| checkpointing_off_len2048_batch1 | off | 2048 | 1 | 2.62 | 14.42 | 14.55 | out of memory | out of memory |
| checkpointing_on_len2048_batch4 | on | 8192 | 1 | 2.62 | 11.17 | 12.33 | out of memory | out of memory |
| checkpointing_on_len1024_batch8 | on | 8192 | 1 | 2.62 | 11.17 | 12.33 | out of memory | out of memory |
| checkpointing_on_len1024_batch1_accumulation8 | on | 1024 | 8 | 2.62 | 4.93 | 5.48 | 13.97 | 586.29 |

## Memory budget

- Parameters: 4,055,498,240 in total, 33,030,144 trainable (LoRA).
- Full fine-tuning with Adam in mixed precision needs about 16 bytes per parameter (bf16 weights and gradients, fp32 master weights, two fp32 Adam moments): 60.4 GiB before activations.
- LoRA weights, gradients and Adam moments take 0.49 GiB; the frozen 4-bit base and the adapter together measured 2.62 GiB before the first step.
