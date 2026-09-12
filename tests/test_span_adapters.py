from evaluation.fixtures import (
    SourceSpan,
    TrueEvidenceSpan,
    TrueRequirement,
    TrueRequirementsFixture,
    TrueSource,
    TrueVerdict,
)
from evaluation.matching import MatchGroup, SpanRef, find_overlapping_pairs
from evaluation.span_adapters import (
    group_lookup_by_topic,
    predicted_requirement_spans,
    topics_with_matched_requirement,
    true_requirement_spans,
)
from schemas import Requirement, TextSpan


def _verdict_with_evidence(topic_id: str) -> TrueVerdict:
    return TrueVerdict(
        topic_id=topic_id,
        acceptable_verdicts=["compliant"],
        rationale="",
        evidence=[
            TrueEvidenceSpan(
                document_path="application.txt",
                quote="some evidence",
                start_char=0,
                end_char=13,
            )
        ],
    )


def _citation(
    start_char: int,
    end_char: int,
    used_for_matching: bool = True,
) -> TextSpan:
    return TextSpan(
        document_path="tender.txt",
        quote="quote",
        start_char=start_char,
        end_char=end_char,
        citation_verified=True,
        used_for_matching=used_for_matching,
    )


def test_predicted_lead_in_citation_excluded_from_matching() -> None:
    requirement = Requirement(
        requirement_id="req_1",
        text="shared lead-in ... specific condition",
        is_mandatory=True,
        is_text_verifiable=True,
        citations=[
            _citation(100, 150, used_for_matching=False),
            _citation(150, 160),
        ],
        conditions=[],
    )

    spans = predicted_requirement_spans([requirement])

    assert len(spans) == 1
    assert (spans[0].start_char, spans[0].end_char) == (150, 160)


def test_topic_with_no_matched_requirement_is_excluded() -> None:
    topics = [
        _verdict_with_evidence("found_topic"),
        _verdict_with_evidence("missed_topic"),
    ]
    groups = [
        MatchGroup(
            true_topic_ids=["found_topic"],
            predicted_node_ids=["req_1"],
            shape="clean",
        ),
        MatchGroup(
            true_topic_ids=["missed_topic"],
            predicted_node_ids=[],
            shape="unmatched_true",
        ),
    ]
    group_by_topic = group_lookup_by_topic(groups)

    scorable = topics_with_matched_requirement(topics, group_by_topic)

    assert [verdict.topic_id for verdict in scorable] == ["found_topic"]


def _topic_with_shared_lead_in(
    topic_id: str,
    own_span: SourceSpan,
    lead_in_used_for_matching: bool,
) -> TrueRequirement:
    return TrueRequirement(
        topic_id=topic_id,
        description=f"Description for {topic_id}",
        is_mandatory=True,
        is_text_verifiable=True,
        source=TrueSource(
            document_path="tender.txt",
            quote="shared lead-in ... " + topic_id,
            spans=[
                SourceSpan(
                    start_char=100,
                    end_char=150,
                    used_for_matching=lead_in_used_for_matching,
                ),
                own_span,
            ],
        ),
    )


def test_shared_lead_in_excluded_from_matching_does_not_cross_match() -> None:
    fixture = TrueRequirementsFixture(
        notes=[],
        requirements=[
            _topic_with_shared_lead_in(
                "topic_a", SourceSpan(start_char=150, end_char=160),
                lead_in_used_for_matching=False,
            ),
            _topic_with_shared_lead_in(
                "topic_b", SourceSpan(start_char=300, end_char=310),
                lead_in_used_for_matching=False,
            ),
        ],
    )
    predicted_spans = [SpanRef(
        node_id="pred_1",
        document_path="tender.txt",
        start_char=100,
        end_char=160,
    )]

    true_spans = true_requirement_spans(fixture)
    edges = find_overlapping_pairs(true_spans, predicted_spans, 0.5)

    assert {span.node_id for span in true_spans} == {"topic_a", "topic_b"}
    assert [edge.true_topic_id for edge in edges] == ["topic_a"]


def test_shared_lead_in_kept_in_matching_does_cross_match() -> None:
    fixture = TrueRequirementsFixture(
        notes=[],
        requirements=[
            _topic_with_shared_lead_in(
                "topic_a", SourceSpan(start_char=150, end_char=160),
                lead_in_used_for_matching=True,
            ),
            _topic_with_shared_lead_in(
                "topic_b", SourceSpan(start_char=300, end_char=310),
                lead_in_used_for_matching=True,
            ),
        ],
    )
    predicted_spans = [SpanRef(
        node_id="pred_1",
        document_path="tender.txt",
        start_char=100,
        end_char=160,
    )]

    true_spans = true_requirement_spans(fixture)
    edges = find_overlapping_pairs(true_spans, predicted_spans, 0.5)

    matched_topics = {edge.true_topic_id for edge in edges}
    assert matched_topics == {"topic_a", "topic_b"}
