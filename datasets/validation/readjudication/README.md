# Re-adjudication Queue

`v1.1-s4-scope.json` freezes the cases that must be reviewed again after the
S4 reset-scope clarification in Annotation Guide v1.1. Re-adjudication uses the
existing candidate, blind review packet, and trusted task assets. It must not
regenerate the model answer or consult evaluator predictions.

For each case, replace the old human annotation only after completing a fresh
blind review. Set `guideline_version` to `1.1`, reconsider every later process
item after withdrawing an invalid old root, and promote only after the new
annotation passes `rtlreason promote-case` validation.
