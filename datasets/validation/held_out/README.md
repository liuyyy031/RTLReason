# Held-Out Gold Test Set

This directory is reserved for adjudicated records produced by
`rtlreason promote-case --split held_out`.  Do not inspect this split while
tuning prompts, dependency rules, thresholds, or trusted task assets.  A record
with only `single_annotated` status cannot enter this directory.

Current adjudicated held-out Gold records: **20**.

Held-out Batch 001 contains **20** independently reviewed real-Hy3 candidates
across all 20 trusted tasks.  All records reached `adjudicated` status before
the frozen v1.5 evaluator was run.  The batch has 14 process-correct and 6
process-incorrect cases; 19 RTL-correct and 1 RTL-incorrect case.  See
`datasets/validation/HELD_OUT_BATCH_001_REVIEW_CN.md` and
`datasets/validation/EVALUATOR_V1_5_FREEZE.json` for the collection boundary
and evaluator hashes.

The one-shot frozen v1.5 evaluation is complete.  Full RTLReason achieved
0.7500 process accuracy, 0.7151 process macro-F1, 0.5000 root accuracy, and
0.2500 critical-dependency micro-F1.  These results must not be used to tune
v1.5 and then re-report this batch as held-out.  See
`runs/metrics/evaluator-v1.5-held-out-batch-001/HELD_OUT_RESULTS_CN.md`.
