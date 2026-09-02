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


JUDGE_PROMPT_VERSION = "1.1"


JUDGE_SYSTEM_PROMPT = """You are the RTLReason semantic evaluator. Judge explicit design
artifacts against trusted behavioral obligations and frozen interface semantics. Do not require
the candidate to use any particular internal architecture. Assess every explicit process item
independently even when the final RTL is correct. Treat an unqualified candidate property as
applying to every reachable cycle: check reset, enable, valid/ready, priority, and simultaneous
operation branches, and distinguish pre-edge values from post-edge values. A correct RTL does
not repair an incorrect process claim. Return one JSON object only.
"""


def build_judge_messages(
    task: TaskAssets, process: ProcessArtifact
) -> list[dict[str, str]]:
    content = {
        "evaluation_protocol": {
            "version": JUDGE_PROMPT_VERSION,
            "rules": [
                "Assess every S1-S5 item; do not infer process correctness from RTL correctness.",
                "For every S4 property, test its antecedent and consequent against reset and all higher-priority branches.",
                "Check whether temporal claims refer to pre-edge, post-edge, current-state, or next-state values.",
                "Check enable/valid/ready gating and simultaneous boundary operations when relevant.",
                "Use unknown rather than correct when the claim lacks enough semantics to prove.",
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
