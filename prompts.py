REQUIREMENT_EXTRACTION_PROMPT = """\
You are analyzing a chunk of a tender (RFP) requirements document.
Extract every distinct requirement stated in this chunk that is
addressed to the bidder/offeror and that the bidder's application
must satisfy or demonstrate. Ignore text addressed to someone other
than the bidder, such as instructions to the contracting officer or
the government evaluator, descriptions of how the government will
conduct its evaluation, or obligations that only apply to the
contractor after contract award rather than to the application
itself. Only extract text that imposes something checkable on the
bidder's application.

For each requirement, return its exact verbatim text as it appears
in the chunk below. Do not paraphrase, summarize, or merge separate
requirements together. If a requirement appears cut off at the very
start or end of the chunk, still extract the visible portion as-is.

For each requirement, also decide whether it is mandatory. Mark it
mandatory if the text uses language such as "shall", "must", "is
required to", or "NO EXCEPTIONS". Mark it not mandatory if the text
explicitly frames it as encouraged, recommended, or optional, such
as "is urged to", "is encouraged to", or "preferably". Do not
extract purely encouraged/optional language as a requirement unless
it still imposes some concrete, checkable expectation on the
bidder.

For each requirement, also decide whether it is verifiable from the
application's text alone: whether a reader could confirm the
requirement is satisfied purely by reading what the bidder wrote in
their application. Mark it not verifiable from text if satisfying it
depends on a fact that cannot be confirmed from the application text
itself, even if the application contains a statement about it — for
example, whether a registration is genuinely active, whether a
represented fact is actually true, or whether a referenced attachment
genuinely exists.

Chunk text:
{chunk_text}
"""

DEDUP_GROUPING_PROMPT = """\
Below is a numbered list of requirement candidates extracted from
different, possibly overlapping parts of the same tender document.
Some candidates may be exact or partial duplicates of each other,
describing the same underlying requirement. Others may look
superficially similar but describe genuinely different
requirements.

Group the candidates into non-overlapping groups such that every
candidate in a group expresses the same underlying requirement. A
group may contain a single candidate if it has no duplicates. For
each group, provide a single canonical requirement text that
captures the full requirement, drawing on all candidates in the
group, and state whether the merged requirement is mandatory
(true if any candidate in the group is phrased as mandatory) and
whether it is verifiable from the application's text alone (false
if any candidate in the group is marked not verifiable from text).

Candidates:
{numbered_candidates}
"""

VERDICT_GENERATION_PROMPT = """\
You are assessing whether a bidder's tender application satisfies a
specific requirement from the tender's requirements document.

Requirement:
{requirement_text}

Relevant excerpts from the bidder's application:
{evidence_text}

Decide one of the following verdicts:
- compliant: the application clearly satisfies the requirement.
- non_compliant: the application clearly fails to satisfy the
  requirement.
- insufficient_information: the excerpts do not contain enough
  information to decide either way.
- contradictory: the excerpts contain statements that conflict with
  each other regarding this requirement.

For every excerpt you rely on, quote it verbatim and label whether
it supports, contradicts, or is inconclusive with respect to the
requirement. Explain your reasoning briefly.
"""

CONDITION_EXTRACTION_PROMPT = """\
Below is the text of a single tender requirement. Determine whether
it expresses one or more numeric threshold conditions that could be
checked automatically (for example, a minimum number of years of
experience, a maximum price, a minimum warranty period). A single
requirement may contain more than one such condition, for example a
range ("between 20 and 45 days") expressed as two threshold
conditions that must both hold. For each condition found, extract
the field name being constrained, the comparison operator, the
numeric value, and the unit if any. If the requirement contains no
numeric threshold condition, return an empty list.

Requirement:
{requirement_text}
"""

VALUE_EXTRACTION_PROMPT = """\
Below are excerpts from a bidder's tender application. Extract
every numeric value that corresponds to the field "{field_name}"
(unit: {unit}). If the excerpts state more than one value for this
field, extract all of them, even if they conflict with each other.

Excerpts:
{evidence_text}
"""
