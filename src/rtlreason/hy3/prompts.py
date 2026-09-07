from __future__ import annotations

import json

from rtlreason.models import ItemAssessment, ProcessArtifact, TaskAssets


SOLVER_SYSTEM_PROMPT = """You are the RTLReason Hy3 solver. Produce explicit, user-visible
hardware design artifacts, not hidden chain-of-thought. Return exactly one JSON object and no
Markdown fences. You may choose any architecture that satisfies the frozen interface semantics.
Do not assume that the reference implementation architecture is required.
"""


def build_solver_messages(task: TaskAssets) -> list[dict[str, str]]:
    schema = {
        "task_id": task.task_id,
        "architecture_summary": "short description",
        "stages": [
            {
                "id": "S1",
                "title": "Specification Understanding",
                "items": [
                    {
                        "id": "S1.1",
                        "claim": "verifiable claim",
                        "maps_to": ["REQ_ID"],
                        "claimed_dependencies": [],
                        "reads": [],
                        "writes": [],
                        "rtl_blocks": [],
                    }
                ],
            },
            {"id": "S2", "title": "Architecture / State Modeling", "items": []},
            {"id": "S3", "title": "Transition & Temporal Rules", "items": []},
            {"id": "S4", "title": "Candidate Properties", "items": []},
            {"id": "S5", "title": "RTL Implementation", "items": []},
        ],
        "rtl": {
            "language": "systemverilog",
            "module_name": "required module name",
            "code": "complete synthesizable RTL",
        },
        "metadata": {"notes": []},
    }
    content = (
        "Solve the task using the five fixed semantic stages. All item IDs must be unique. "
        "S2 must declare your chosen architecture rather than imitate a reference. S4 contains "
        "candidate properties and is not the trusted formal oracle. Claimed dependencies are "
        "your traceability claims and may point only to earlier items in total process order, "
        "including an earlier item in the same stage. Populate reads, writes, and rtl_blocks "
        "whenever a claim defines, consumes, or implements named state or logic. Use 2--5 concise items "
        "per stage. Put the complete RTL only in rtl.code. Do not repeat the task or schema and "
        "reserve enough output budget to close the final JSON object.\n\n"
        f"TASK:\n{task.problem}\n\n"
        "FROZEN INTERFACE SEMANTICS:\n"
        f"{json.dumps(task.interface_semantics, ensure_ascii=False, indent=2)}\n\n"
        "BEHAVIORAL OBLIGATIONS:\n"
        f"{json.dumps([o.__dict__ for o in task.obligations], ensure_ascii=False, indent=2)}\n\n"
        "OUTPUT SHAPE:\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}"
    )
    return [
        {"role": "system", "content": SOLVER_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


JUDGE_PROMPT_VERSION = "1.5"


JUDGE_SYSTEM_PROMPT = """You are the RTLReason semantic evaluator. Judge explicit design
artifacts against trusted behavioral obligations and frozen interface semantics. Do not require
the candidate to use any particular internal architecture. Assess every explicit process item
even when the final RTL is correct, while using its stated dependencies and surrounding stage
context to resolve terminology. An S1--S3 architecture or transition item may inherit an explicitly
stated reset priority from its stage context or earlier process context; do not require every local
rule to repeat the reset guard. This exception supplies only reset priority, not enable, load,
valid/ready, address, direction, or simultaneous-operation guards. Outside this reset-only exception,
dependencies may not add a missing antecedent condition or strengthen a claim's temporal quantification. Treat an ordinary operational S4 property as
implicitly disabled while reset is asserted unless the property explicitly describes reset or
claims including-reset/all-cycle behavior. Do not mark a property incorrect solely because it
omits an explicit reset guard. This implicit scope does not supply enable, valid/ready, priority,
or simultaneous-operation conditions. For history properties, verify that past state belongs to
the current reset epoch; disabling the current reset cycle does not repair invalid history.
Words such as always, never, and every cycle explicitly claim all-cycle behavior. Phrases such as
only if, changes only if, and the only cause assert a necessary or exclusive causal condition and
must be checked for other legal causes, including reset unless the claim explicitly narrows scope. Distinguish
pre-edge values from post-edge values. A maps_to entry is a many-to-many traceability association,
not a claim that the item covers every case of that obligation; do not reject a valid subcase merely
because the obligation is broader. Treat behaviorally equivalent combinational RTL forms, such as
continuous assignment and always_comb, as equivalent unless the exact construct changes behavior.
Descriptive words such as allows, enables, or can express capability and do not assert that an
otherwise absent request is active. Multi-cycle delay and propagation claims must preserve their
required enable/valid guards across every relevant cycle. A transition rule gated by enable on
each individual edge does not imply that enable remains asserted across a downstream property's
whole delay interval. Saying that an input is ignored or has no effect is a causal statement about
that input; it does not freeze unrelated default state evolution or a concurrent independently
accepted operation. Conversely, an explicit statement that all registers or all state remain
unchanged must be checked literally. Treat a countdown description by its observable acceptance,
terminal, and pulse timing; do not reject it solely because an irrelevant internal counter is not
written on the terminal edge. Use unknown only when the claim remains
underdetermined after considering its dependencies and context; if a legal concrete counterexample
exists, mark it incorrect. Check S5 implementation claims against the actual RTL, including syntax
and elaboration validity. In particular, verify procedural/block-label syntax rather than assuming
that intent makes malformed RTL compilable. A correct RTL does not repair an incorrect process claim. Return one JSON
object only.
"""


def build_judge_messages(
    task: TaskAssets, process: ProcessArtifact
) -> list[dict[str, str]]:
    content = {
        "evaluation_protocol": {
            "version": JUDGE_PROMPT_VERSION,
            "rules": [
                "Assess every S1-S5 item; do not infer process correctness from RTL correctness.",
                "For ordinary operational S4 properties, assume reset-disabled scope; do not require a repeated !rst guard.",
                "For reset-specific, explicitly all-cycle, and history properties, check reset and reset-epoch semantics explicitly.",
                "Treat always, never, and every cycle as explicit all-cycle quantifiers rather than ordinary reset-disabled shorthand.",
                "Treat only-if, changes-only-if, and only-cause wording as necessary or exclusive causal claims; check reset and every other legal cause unless scope is explicitly narrowed.",
                "Allow S1-S3 local architecture/transition items to inherit an explicitly established reset priority, but no other missing operational guard.",
                "Check whether temporal claims refer to pre-edge, post-edge, current-state, or next-state values.",
                "Do not infer enable, load, valid/ready, priority, or simultaneous-operation guards from the reset default.",
                "For a multi-cycle delay or propagation claim, require its enable/valid conditions over the complete interval; dependencies cannot add an unstated continuous guard.",
                "Ignored/no-effect input wording is causal and does not freeze unrelated default updates or concurrent accepted operations; explicit all-state-unchanged wording is literal.",
                "Judge countdown summaries by observable acceptance and terminal timing, not by an irrelevant terminal-edge write to an internal counter.",
                "Interpret maps_to as a many-to-many traceability association; a correct subcase may map to a broader obligation.",
                "Accept behaviorally equivalent RTL constructs and do not confuse allows/enables capability language with an unconditional request.",
                "Use dependencies and stage context to resolve terminology, but never to add a missing antecedent or strengthen temporal quantification; use unknown only when the claim remains underdetermined, and use incorrect when a legal counterexample exists.",
                "Inspect the actual RTL when judging S5 syntax, elaboration, implementation claims, and procedural/block-label placement.",
            ],
        },
        "task": task.problem,
        "interface_semantics": task.interface_semantics,
        "behavioral_obligations": [o.__dict__ for o in task.obligations],
        "error_taxonomy": task.error_taxonomy,
        "candidate_process": process.to_dict(),
        "required_output": {
            "assessments": [
                {
                    "item_id": "S3.1",
                    "status": "correct|incorrect|unknown",
                    "error_type_l1": "one error_taxonomy key or null",
                    "error_type_l2": "one subtype under error_type_l1 or null",
                    "explanation": "concise evidence-based explanation",
                    "confidence": 0.0,
                }
            ]
        },
    }
    return [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(content, ensure_ascii=False)},
    ]


def parse_assessments(data: dict) -> list[ItemAssessment]:
    results: list[ItemAssessment] = []
    for item in data.get("assessments", []):
        try:
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        results.append(
            ItemAssessment(
                item_id=str(item["item_id"]),
                status=str(item.get("status", "unknown")),
                error_type_l1=item.get("error_type_l1"),
                error_type_l2=item.get("error_type_l2"),
                explanation=str(item.get("explanation", "")),
                confidence=confidence,
            )
        )
    return results
