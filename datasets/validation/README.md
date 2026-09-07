# Gold validation data

Validation records may embed genuine Hy3 outputs, including failures.  Their
trusted task assets, human error labels, and gold causal annotations must be
created independently of the Hy3 instance under evaluation.

Each held-out record should minimally contain:

- `gold_rtl_correct` and `gold_process_correct`;
- `gold_first_error_stage` and `gold_root_error` for an erroneous process;
- `gold_error_type_l1` (and optionally L2);
- `gold_parent_dependency` for the critical causal edge;
- `gold_affected_obligation` for the observed behavioral consequence;
- annotator identity/version and adjudication state.

The evaluator's ordinary `Evaluator-Inferred Dependency` is a prediction.  It
must be compared with the critical `Gold Causal Dependency` annotations here;
it is never relabeled as gold merely because its name contains "inferred" or
"verified".

Development and held-out test partitions must be stored separately.  Do not
tune prompts or thresholds against the held-out partition.

## Pending adjudication

Runs selected for review must first be exported with `rtlreason queue-case`.
These candidate records contain evaluator predictions but deliberately contain
no `gold_*` fields and use `adjudication.status = pending_human`.  A prediction,
including a plausible same-family Hy3 Judge explanation, must never be promoted
to Gold merely by copying or renaming it.  An independent reviewer applies the
guideline, records identity/version, and only then creates a development record
conforming to `gold_validation.schema.json`.

Before labeling, create a blinded reviewer packet so the evaluator prediction
cannot anchor the reviewer:

```text
rtlreason blind-case --candidate <pending.json> --output <review.json>
```

The reviewer follows `ANNOTATION_GUIDE_CN.md`, opens the blinded packet and the
trusted task assets, and does not open the original pending candidate until the
labels have been locked.

Copy `templates/human_annotation.template.json`, replace every placeholder,
and have the independent reviewer enter explicit labels.  The template's null
booleans are intentionally invalid until reviewed.  Promote a completed label
file with:

```text
rtlreason promote-case --candidate <pending.json> --annotation <human.json> \
  --split development --output <gold.json>
```

The command never derives Gold fields from `evaluator_prediction`.  It rejects
non-independent labels, incomplete error localization, error labels attached to
a Gold-correct process, and singly annotated records targeting `held_out`.

The frozen development/held-out, task-layer, baseline, and reporting rules are
defined in `EXPERIMENT_PROTOCOL_CN.md`.

## Current pool

As of 2026-09-03, the blinded review pool contains 44 complete real model runs
and three controlled cases. Provenance identifies 40 Hy3 outputs and four
`deepseek-v4-flash` outputs; these model families must not be pooled when
reporting Hy3 accuracy. Every trusted task has at least two complete model
answers, while FIFO, ready/valid FIFO, round-robin arbiter, and APB each have
three. The interrupt
task has one Hy3 and one DeepSeek answer; stream-width has two DeepSeek answers,
and all three APB answers are independent Hy3 outputs. Replaced APB runs and
their superseded review records remain recoverable under
`archive/provenance-replaced-20260903-apb/` and are excluded from the active
pool. `interrupt-001` retains its original Hy3 generation metadata and was
completed with a DeepSeek Judge. `fifo2-003`, `arbiter-003`, and all three
current APB outputs were collected with schema and trusted EDA only, without a
Semantic Judge pass.
Controlled-mutation intent remains internal provenance
and is removed from reviewer packets. No record is Gold until an independent
human annotation is completed and promoted through the command above.

Annotation Guide v1.1 and Semantic Judge Prompt v1.4 freeze ordinary S4
operational properties as implicitly reset-disabled. Fifteen v1.0 S4-error
annotations are listed in `readjudication/v1.1-s4-scope.json`; they cannot be
used as active Gold until a fresh blind v1.1 adjudication is completed. The
superseded `rising-edge-001` Development record remains recoverable under
`archive/readjudication-v1.1/`.
