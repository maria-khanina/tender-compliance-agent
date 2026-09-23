REQUIREMENT_EXTRACTION_PROMPT = """\
You are analyzing a chunk of a tender (RFP) requirements document.
Extract every distinct requirement stated in this chunk that is
addressed to the bidder/offeror and that the bidder's application
must satisfy or demonstrate. Ignore text addressed to someone other
than the bidder, such as instructions to the contracting officer or
the government evaluator, descriptions of how the government will
conduct its evaluation, or obligations that only apply to the
contractor after contract award rather than to the application
itself. Judge whether text is a requirement by its meaning, never by
scanning for words like "must" or "shall": extract it if it states
something checkable that the bidder's application or offered product
needs to satisfy, regardless of grammatical mood, sentence form, or
how neighboring text in the same sentence, list, or section happens
to be phrased. A plain declarative statement, or one entry in a list
of specifications where only some other entries contain "must", is
just as much a requirement as an explicit "shall" clause, as long as
it describes something checkable. Conversely, text with no
independently checkable content of its own is never a requirement no
matter how it reads -- this covers a definition of a term used
elsewhere ("X means...") and any sentence whose entire substance is
deferred to another part of the same tender document set (a bare
reference to another clause by number and title alone with no
substantive text attached, but also a sentence like "the equal
product must conform to the characteristics in Attachment B" or "must
comply with the specifications in Section 2.3.1") -- in these cases
extract the requirements from the referenced attachment or section
instead, wherever it appears in the chunks you are given, rather than
also extracting the sentence that points to it.

For each requirement, return its exact verbatim text as it appears
in the chunk below, as two parts:
- "quote": the complete text of this one requirement, from where it
  begins to where it naturally ends. Do not trim it down to only the
  shortest fragment that differs from other requirements — include
  any conditional, exception, or qualifying clause that affects its
  meaning or when it applies, unless that clause is a shared lead-in
  covered by "lead_in_quote" below. Do not paraphrase, summarize, or
  merge separate requirements together. If a requirement appears cut
  off at the very start or end of the chunk, still extract the
  visible portion as-is.
- "lead_in_quote": an optional shared introductory clause this
  requirement's meaning depends on, ONLY when that same clause also
  introduces one or more OTHER, different requirements elsewhere in
  this chunk (for example, "the Government will not enter into a
  contract with any corporation that--" followed by several unrelated
  conditions, each its own requirement). Leave this null in every
  other case, even if the requirement technically follows some
  introductory sentence — most requirements do not need one.
Do not extract a sentence whose only role is to introduce or refer to
a list of other requirements (for example "Offers shall submit the
following information:") — extract the individual items of that list
instead, not the sentence that introduces them, UNLESS the items are
inseparable parts of one overall determination with no independent
pass/fail meaning of its own per item — for example, the blank
fields of one certification block a bidder signs once, or the
scenario-by-scenario sub-paragraphs of a single regulatory clause
that only describe how to compute one overall figure or
determination differently depending on contract type (a bidder does
not pass or fail each sub-paragraph separately; only the overall
determination matters). In that case extract the whole thing as a
single requirement instead of one requirement per item.

For each requirement, also decide whether it is mandatory. Mark it
mandatory if the text uses language such as "shall", "must", "is
required to", or "NO EXCEPTIONS" -- including when that obligation
only applies conditionally (see below); conditional obligation is
still obligation once the condition holds, not optionality. Mark it
not mandatory only if the text explicitly frames it as encouraged,
recommended, or optional regardless of any condition, such as "is
urged to", "is encouraged to", or "preferably". Do not extract purely
encouraged/optional language as a requirement unless it still imposes
some concrete, checkable expectation on the bidder.

For each requirement, also decide whether its applicability is itself
conditional on a fact about the bidder or its offer that may or may
not hold (for example "if applicable", "if vendor is an FSS contract
holder", "in any case an amendment was posted", "if offering an equal
product"). If so, return "applicability_condition_quote": the exact
verbatim text of the clause stating that condition, as it appears in
the chunk -- this may be part of the same sentence as the requirement
itself, or a separate lead-in sentence. Leave it null when the
requirement applies to every bidder unconditionally.

For each requirement, also decide whether it is verifiable from the
application's text alone: whether a reader could confirm the
requirement is satisfied purely by reading what the bidder wrote in
their application. Mark it not verifiable from text in either of
these two cases:
- Satisfying it depends on a fact that cannot be confirmed from the
  application text itself, even if the application contains a
  statement about it — for example, whether a registration is
  genuinely active, whether a represented fact is actually true, or
  whether a referenced attachment genuinely exists.
- It concerns the process of submitting the offer itself — such as
  the manner, channel, destination, or timing of submission — rather
  than something the application's content must contain or
  demonstrate.

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
{condition_section}
Relevant excerpts from the bidder's application:
{context_text}

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

VERDICT_CONDITION_SECTION = """\
This requirement only applies if the following condition holds for
this bidder:
{condition_text}

First decide "condition_holds": true if the excerpts show this
condition applies to this bidder, false if the excerpts show it does
not apply. If the excerpts never establish whether the condition
applies at all, make your best-guess determination of
"condition_holds" from the available context, but do not conclude
non_compliant merely because the excerpts are silent about it --
silence about an unconfirmed condition is not evidence that the
condition applies. In that situation prefer insufficient_information,
or compliant if the silence is exactly what "the condition never
applied" would look like; reserve non_compliant for cases where the
excerpts show the condition did apply and the bidder failed to act on
it.
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
{context_text}
"""
