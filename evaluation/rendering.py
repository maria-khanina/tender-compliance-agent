from evaluation.matching import MatchGroup
from evaluation.orchestrator import EvaluationReport
from evaluation.requirement_metrics import CoverageFlag


PERCENT_SCALE = 100.0
SHORT_ID_LENGTH = 8


def _percent(ratio: float) -> str:
    return f"{ratio * PERCENT_SCALE:.1f}%"


def _expected_line(topic_id: str, report: EvaluationReport) -> str:
    description = report.expected_descriptions.get(
        topic_id, "(no description found)"
    )
    return f"expected `{topic_id}` — {description}"


def _citation_status_suffix(requirement_id: str, report: EvaluationReport) -> str:
    status = report.actual_citation_status.get(requirement_id, "precise")
    if status == "unverified":
        return ", citation: UNVERIFIED — not located in tender.txt"
    if status == "fuzzy":
        return ", citation: fuzzy match — worth a second look"
    return ""


def _actual_line(requirement_id: str, report: EvaluationReport) -> str:
    text = report.actual_texts.get(requirement_id, "(text unavailable)")
    short_id = requirement_id[:SHORT_ID_LENGTH]
    verdict = report.actual_verdict_labels.get(requirement_id)
    if verdict:
        verdict_suffix = f" — verdict: {verdict}"
    else:
        verdict_suffix = " — no verdict"
    citation_suffix = _citation_status_suffix(requirement_id, report)
    return f'actual [{short_id}] "{text}"{verdict_suffix}{citation_suffix}'


def _groups_by_shape(
    groups: list[MatchGroup],
) -> dict[str, list[MatchGroup]]:
    grouped: dict[str, list[MatchGroup]] = {}
    for group in groups:
        grouped.setdefault(group.shape, []).append(group)
    return grouped


def _render_missed(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        for topic_id in group.expected_topic_ids:
            lines.append(f"- {_expected_line(topic_id, report)}")
    return lines


def _render_over_split(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        topic_id = group.expected_topic_ids[0]
        lines.append(
            f"- {_expected_line(topic_id, report)} was split into "
            f"{len(group.actual_node_ids)} separate actual requirements:"
        )
        for requirement_id in group.actual_node_ids:
            lines.append(f"  - {_actual_line(requirement_id, report)}")
    return lines


def _render_over_merge(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        requirement_id = group.actual_node_ids[0]
        lines.append(
            f"- {_actual_line(requirement_id, report)} lumps together "
            f"{len(group.expected_topic_ids)} expected requirements:"
        )
        for topic_id in group.expected_topic_ids:
            lines.append(f"  - {_expected_line(topic_id, report)}")
    return lines


def _render_tangled(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for group in groups:
        lines.append(
            "- a tangle of "
            f"{len(group.expected_topic_ids)} expected and "
            f"{len(group.actual_node_ids)} actual requirements, all "
            "overlapping each other's citation spans — pick apart by hand:"
        )
        for topic_id in group.expected_topic_ids:
            lines.append(f"  - {_expected_line(topic_id, report)}")
        for requirement_id in group.actual_node_ids:
            lines.append(f"  - {_actual_line(requirement_id, report)}")
    return lines


def _render_recall_section(report: EvaluationReport) -> list[str]:
    result = report.requirement_recall
    by_shape = _groups_by_shape(report.match_groups)
    lines = ["## Requirement recall", ""]
    lines.append(
        "What this measures: for every topic in `expected_requirements.json`, "
        "did the pipeline extract *something* whose citation into tender.txt "
        "overlaps the expected citation enough? This is a pure text-offset "
        "comparison, not a judgment of meaning — a topic can be \"found\" "
        "here and still be extracted badly (see coverage flags below)."
    )
    lines.append("")
    lines.append(
        f"**Recall: {_percent(result.recall)} "
        f"({result.matched_topic_count}/{result.total_topic_count} "
        "expected topics matched by at least one actual requirement)**"
    )
    lines.append("")
    lines.append(
        f"**Missed** ({len(by_shape.get('unmatched_expected', []))}) — "
        "expected topics with no overlapping actual requirement at all:"
    )
    lines.extend(_render_missed(by_shape.get("unmatched_expected", []), report))
    lines.append("")
    lines.append(
        f"**Over-split** ({len(by_shape.get('over_split', []))}) — one "
        "expected topic whose text the pipeline extracted as multiple "
        "separate actual requirements instead of one:"
    )
    lines.extend(_render_over_split(by_shape.get("over_split", []), report))
    lines.append("")
    lines.append(
        f"**Over-merge** ({len(by_shape.get('over_merge', []))}) — one "
        "actual requirement whose citation span covers several distinct "
        "expected topics at once, i.e. the pipeline collapsed separate "
        "requirements into one:"
    )
    lines.extend(_render_over_merge(by_shape.get("over_merge", []), report))
    lines.append("")
    lines.append(
        f"**Tangled** ({len(by_shape.get('tangled', []))}) — several "
        "expected topics and several actual requirements all overlap each "
        "other's spans at once, so there is no clean one-to-one or "
        "one-to-many split; this needs manual reading to untangle:"
    )
    lines.extend(_render_tangled(by_shape.get("tangled", []), report))
    lines.append("")
    return lines


def _render_precision_section(report: EvaluationReport) -> list[str]:
    result = report.requirement_precision
    lines = ["## Requirement precision", ""]
    lines.append(
        "This is split into two separate numbers because they point at "
        "two different failure modes and need two different fixes."
    )
    lines.append("")
    lines.append(
        "**Citation-verified rate** (hallucination proxy): of all actual "
        "requirements, what fraction have a citation that was actually "
        "located in tender.txt (exactly or via fuzzy match)? A requirement "
        "with an unlocatable citation is a candidate for the model having "
        "invented or badly garbled a quote."
    )
    lines.append(f"- rate: {_percent(result.citation_verified_rate)}")
    lines.append("- unverified:")
    if not result.unverified_requirement_ids:
        lines.append("  - none")
    for requirement_id in result.unverified_requirement_ids:
        lines.append(f"  - {_actual_line(requirement_id, report)}")
    lines.append("")
    lines.append(
        "**Classification precision**: of all actual requirements, what "
        "fraction are \"explained\" — either matched to a real expected "
        "topic (recall side, above) or recognized as overlapping a known "
        "`excluded_clauses` trap (text that looks like a requirement but "
        "isn't bidder-facing)? The remainder (\"unexplained\") is not "
        "automatically counted as a mistake: it's a fixture gap that needs "
        "a human to decide whether the pipeline over-extracted, or the "
        "fixture's expected/excluded lists are still incomplete."
    )
    lines.append(f"- rate: {_percent(result.classification_precision)}")
    lines.append(
        f"- unexplained ({len(result.unexplained_requirement_ids)}, needs "
        "manual triage):"
    )
    if not result.unexplained_requirement_ids:
        lines.append("  - none")
    for requirement_id in result.unexplained_requirement_ids:
        lines.append(f"  - {_actual_line(requirement_id, report)}")
    lines.append("")
    return lines


def _render_coverage_flag(flag: CoverageFlag, report: EvaluationReport) -> list[str]:
    lines = []
    for topic_id in flag.expected_topic_ids:
        lines.append(f"  - {_expected_line(topic_id, report)}")
    for requirement_id in flag.actual_node_ids:
        lines.append(f"  - {_actual_line(requirement_id, report)}")
    lines.append(
        f"    expected_covered={_percent(flag.expected_covered_ratio)} "
        "(how much of the expected citation's characters are covered by "
        "the actual one — low means incomplete capture), "
        f"actual_explained={_percent(flag.actual_explained_ratio)} "
        "(how much of the actual citation's characters are covered by the "
        "expected one — low means the actual citation is padded with "
        "extra, unrelated text)"
    )
    return lines


def _render_coverage_section(report: EvaluationReport) -> list[str]:
    flags = report.coverage_flags
    lines = ["## Coverage flags", ""]
    lines.append(
        "Even a matched pair (recall counted it as found) can still be a "
        "bad extraction if the citations barely overlap in size. This "
        "section flags every matched pair below a coverage threshold in "
        "either direction, so a clean recall number doesn't hide a sloppy "
        "citation."
    )
    lines.append("")
    if not flags:
        lines.append("None flagged.")
    for flag in flags:
        lines.extend(_render_coverage_flag(flag, report))
    lines.append("")
    return lines


def _render_is_mandatory_section(report: EvaluationReport) -> list[str]:
    result = report.is_mandatory_accuracy
    lines = ["## is_mandatory accuracy", ""]
    lines.append(
        "For every cleanly-matched pair (1 expected topic : 1 actual "
        "requirement — split/merge pairs are excluded, since there's no "
        "single correct answer to compare against there), does the "
        "pipeline's `is_mandatory` flag agree with the fixture's?"
    )
    lines.append("")
    lines.append(
        f"**Accuracy: {_percent(result.accuracy)} "
        f"({result.scored_topic_count} clean pairs scored)**"
    )
    lines.append("Mismatched:")
    if not result.mismatched_topic_ids:
        lines.append("- none")
    for topic_id in result.mismatched_topic_ids:
        lines.append(f"- {_expected_line(topic_id, report)}")
    lines.append("")
    return lines


def _render_confusion_matrix(report: EvaluationReport) -> list[str]:
    matrix = report.verdict_accuracy.confusion_matrix
    if not matrix:
        return ["- none"]
    lines = []
    for cell in matrix:
        lines.append(
            f"- expected `{cell.expected_verdict}`, pipeline said "
            f"`{cell.actual_verdict}`: {cell.count} time(s)"
        )
    return lines


def _render_verdict_group_list(
    groups: list[MatchGroup],
    report: EvaluationReport,
) -> list[str]:
    if not groups:
        return ["- none"]
    lines = []
    for index, group in enumerate(groups, start=1):
        lines.append(f"- group {index}:")
        for topic_id in group.expected_topic_ids:
            acceptable = report.acceptable_verdicts_by_topic.get(topic_id)
            lines.append(
                f"  - {_expected_line(topic_id, report)} "
                f"(acceptable: {acceptable})"
            )
        for requirement_id in group.actual_node_ids:
            lines.append(f"  - {_actual_line(requirement_id, report)}")
    return lines


def _render_verdict_section(report: EvaluationReport) -> list[str]:
    result = report.verdict_accuracy
    lines = ["## Verdict accuracy", ""]
    lines.append(
        "The confusion matrix below only covers clean 1:1 matched pairs "
        "(one expected topic, one actual requirement) — split/merge groups "
        "don't have a single unambiguous expected-vs-actual pair to plot, "
        "so they're excluded from the matrix but still counted in the two "
        "rates below."
    )
    lines.append("")
    lines.append(f"Clean matches scored: {result.clean_match_count}")
    lines.append("Confusion matrix:")
    lines.extend(_render_confusion_matrix(report))
    lines.append("")
    lines.append(
        "**False-compliant rate** — the dangerous direction: a group "
        "where the fixture says a real problem should have been found "
        "(any acceptable verdict for that topic other than `compliant`), "
        "but every actual verdict in the group came back `compliant`. "
        "This is the pipeline confidently telling the reviewer everything "
        "is fine when it isn't."
    )
    lines.append(f"- rate: {_percent(result.false_compliant_rate)}")
    lines.extend(
        _render_verdict_group_list(result.false_compliant_groups, report)
    )
    lines.append(
        "**False-issue rate** — the mirror, less dangerous direction: the "
        "fixture says `compliant` is the only acceptable verdict, but the "
        "pipeline raised an issue anyway."
    )
    lines.append(f"- rate: {_percent(result.false_issue_rate)}")
    lines.extend(
        _render_verdict_group_list(result.false_issue_groups, report)
    )
    lines.append(
        "**Unscored** — split/merge groups excluded from the confusion "
        "matrix above (still counted in the two rates above):"
    )
    lines.extend(_render_verdict_group_list(result.unscored_groups, report))
    lines.append(
        "**Not verifiable** — the matched actual requirement(s) never got "
        "a verdict at all, most likely because extraction marked "
        "`is_text_verifiable: false`. Excluded from every number above, "
        "since there's no verdict to compare:"
    )
    lines.extend(
        _render_verdict_group_list(result.not_verifiable_groups, report)
    )
    lines.append("")
    return lines


def _render_evidence_section(report: EvaluationReport) -> list[str]:
    citation_result = report.evidence_citation_verified
    recall_result = report.evidence_recall
    lines = ["## Evidence", ""]
    lines.append(
        "**Citation-verified rate (evidence-level)**: of every quote a "
        "verdict cited from application.txt, what fraction was actually "
        "located there? Same idea as the requirement-level rate above, "
        "but for the evidence quotes verdicts cite, not the requirement "
        "citations into tender.txt."
    )
    lines.append(
        f"- rate: {_percent(citation_result.citation_verified_rate)} "
        f"({citation_result.unverified_evidence_count} unverified of "
        f"{citation_result.total_evidence_count})"
    )
    lines.append("")
    lines.append(
        "**Evidence recall**: `expected_verdicts.json` names, for some "
        "topics, exactly where in application.txt the answer should be. "
        "This checks whether that expected span actually appeared "
        "somewhere in the *full* set of application chunks retrieved for "
        "the matched requirement — before the verdict step chose what to "
        "cite. It only runs one direction (expected → retrieved): the "
        "retrieved set is allowed to contain extra, unrelated chunks. A "
        "miss here means retrieval itself never surfaced the right text, "
        "which is a different bug from the verdict model misreading text "
        "it was actually shown."
    )
    lines.append(
        f"- recall: {_percent(recall_result.recall)} "
        f"({recall_result.matched_topic_count}/"
        f"{recall_result.total_topic_count})"
    )
    lines.append(
        "- missed (the expected evidence quote below, from "
        "`expected_verdicts.json`, was not found in anything retrieved "
        "for the matched requirement):"
    )
    if not recall_result.missed_topic_ids:
        lines.append("  - none")
    for topic_id in recall_result.missed_topic_ids:
        lines.append(f"  - {_expected_line(topic_id, report)}")
        evidence_quotes = report.expected_evidence_by_topic.get(topic_id, [])
        for quote in evidence_quotes:
            lines.append(f'    expected evidence: "{quote}"')
    lines.append("")
    return lines


def render_report_as_markdown(report: EvaluationReport) -> str:
    sections = ["# Evaluation report", ""]
    sections.extend(_render_recall_section(report))
    sections.extend(_render_precision_section(report))
    sections.extend(_render_coverage_section(report))
    sections.extend(_render_is_mandatory_section(report))
    sections.extend(_render_verdict_section(report))
    sections.extend(_render_evidence_section(report))
    return "\n".join(sections)
