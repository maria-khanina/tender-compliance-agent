"""Requirement recall and precision report sections."""
from evaluation.matching import MatchGroup
from evaluation.orchestrator import EvaluationReport
from evaluation.rendering._common import (
    percent,
    predicted_line,
    predicted_text_line,
    true_line,
)


def groups_by_shape(groups: list[MatchGroup]) -> dict[str, list[MatchGroup]]:
    grouped: dict[str, list[MatchGroup]] = {}
    for group in groups:
        grouped.setdefault(group.shape, []).append(group)
    return grouped


def render_missed(
    groups: list[MatchGroup],
    report: EvaluationReport,
    missed_chunk_diagnostics: dict[str, str] | None = None,
) -> list[str]:
    if not groups:
        return ["- none"]
    diagnostics = missed_chunk_diagnostics or {}
    lines = []
    for group in groups:
        for topic_id in group.true_topic_ids:
            lines.append(f"- {true_line(topic_id, report)}")
            diagnostic = diagnostics.get(topic_id)
            if diagnostic:
                lines.append(f"    - **chunk check:** {diagnostic}")
    return lines


def render_over_split(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        topic_id = group.true_topic_ids[0]
        lines.append(
            f"- {true_line(topic_id, report)} split into "
            f"{len(group.predicted_node_ids)} predicted requirements:"
        )
        for requirement_id in group.predicted_node_ids:
            lines.append(f"  - {predicted_line(requirement_id, report)}")
    return lines


def render_over_merge(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        requirement_id = group.predicted_node_ids[0]
        lines.append(
            f"- {predicted_line(requirement_id, report)} lumps together "
            f"{len(group.true_topic_ids)} true requirements:"
        )
        for topic_id in group.true_topic_ids:
            lines.append(f"  - {true_line(topic_id, report)}")
    return lines


def render_tangled(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        lines.append(
            f"- tangle of {len(group.true_topic_ids)} true and "
            f"{len(group.predicted_node_ids)} predicted requirements, all "
            "overlapping — needs manual untangling:"
        )
        for topic_id in group.true_topic_ids:
            lines.append(f"  - {true_line(topic_id, report)}")
        for requirement_id in group.predicted_node_ids:
            lines.append(f"  - {predicted_line(requirement_id, report)}")
    return lines


def render_recall_section(
    report: EvaluationReport,
    missed_chunk_diagnostics: dict[str, str] | None = None,
) -> list[str]:
    result = report.requirement_recall
    by_shape = groups_by_shape(report.match_groups)
    lines = ["## Requirement recall", ""]
    lines.append(
        "For each `true_requirements.json` topic, did the pipeline extract "
        "something whose tender.txt citation overlaps the true one? A pure "
        "text-offset check, not a judgment of meaning — see coverage flags "
        "below for extractions that are technically \"found\" but sloppy."
    )
    lines.append("")
    lines.append(
        f"**Recall: {percent(result.recall)} "
        f"({result.matched_topic_count}/{result.total_topic_count})**"
    )
    lines.append("")
    lines.append(
        f"**Missed** ({len(by_shape.get('unmatched_true', []))}) — no "
        "overlapping predicted requirement at all. \"chunk check\" is a "
        "mechanical (no-LLM) re-chunking of the source document: whether "
        "this topic's matching text ever appeared whole in one chunk "
        "handed to the extraction model, or was split across chunks."
    )
    lines.extend(render_missed(
        by_shape.get("unmatched_true", []), report, missed_chunk_diagnostics,
    ))
    lines.append("")
    lines.append(
        f"**Over-split** ({len(by_shape.get('over_split', []))}) — one "
        "true topic extracted as several separate predicted requirements:"
    )
    lines.extend(render_over_split(by_shape.get("over_split", []), report))
    lines.append("")
    lines.append(
        f"**Over-merge** ({len(by_shape.get('over_merge', []))}) — one "
        "predicted requirement covering several distinct true topics:"
    )
    lines.extend(render_over_merge(by_shape.get("over_merge", []), report))
    lines.append("")
    lines.append(
        f"**Tangled** ({len(by_shape.get('tangled', []))}) — several true "
        "and several predicted requirements all overlapping at once:"
    )
    lines.extend(render_tangled(by_shape.get("tangled", []), report))
    lines.append("")
    return lines


def render_precision_section(
    report: EvaluationReport,
    unexplained_diagnostics: dict[str, str] | None = None,
) -> list[str]:
    result = report.requirement_precision
    diagnostics = unexplained_diagnostics or {}
    lines = ["## Requirement precision", ""]
    lines.append(
        "**Citation-verified rate** (hallucination check): fraction of "
        "predicted requirements whose citation was actually located in "
        "tender.txt (exactly or via fuzzy match)."
    )
    lines.append(f"- rate: {percent(result.citation_verified_rate)}")
    lines.append("- unverified:")
    if not result.unverified_requirement_ids:
        lines.append("  - none")
    for requirement_id in result.unverified_requirement_ids:
        lines.append(f"  - {predicted_line(requirement_id, report)}")
    lines.append("")
    lines.append(
        "**Classification precision**: fraction of predicted requirements "
        "that matched a true requirement."
    )
    lines.append(f"- rate: {percent(result.classification_precision)}")
    lines.append(
        f"- unexplained ({len(result.unexplained_requirement_ids)}) — "
        "the model recognized these as requirements, but they don't match "
        "any true requirement. \"closest true topic\" is a mechanical "
        "(no-LLM) embedding-similarity lookup against every true topic's "
        "description; \"dedup visibility\" checks whether dedup's own "
        "cosine pre-filter would have clustered this candidate with "
        "whatever predicted requirement DID match that topic -- i.e. "
        "whether the dedup LLM call ever had a chance to compare them:"
    )
    if not result.unexplained_requirement_ids:
        lines.append("  - none")
    for requirement_id in result.unexplained_requirement_ids:
        lines.append(f"  - {predicted_text_line(requirement_id, report)}")
        diagnostic = diagnostics.get(requirement_id)
        if diagnostic:
            lines.append(f"    - **similarity check:** {diagnostic}")
    lines.append("")
    return lines
