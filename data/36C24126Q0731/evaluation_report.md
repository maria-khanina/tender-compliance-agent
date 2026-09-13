# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9565,
  "requirement_recall_matched": 22,
  "requirement_recall_total": 23,
  "requirement_precision": 0.5,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.9,
  "is_mandatory_scored": 20,
  "is_text_verifiable_accuracy": 0.75,
  "is_text_verifiable_scored": 20,
  "verdict_clean_match_count": 13,
  "verdict_accuracy": 0.8462,
  "false_compliant_rate": 0.0667,
  "false_issue_rate": 0.0667,
  "evidence_citation_verified_rate": 1.0,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": 0.9444,
  "verdict_only_scored": 18
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 95.7% (22/23)**

**Missed** (1) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `uei_must_be_preexisting` — "Due to the requirement falling in the 4th Quarter of FY26, this competition will require an existing SAM UEI."
    - **chunk check:** [11808:11917] whole, in chunk 9 -- the model saw this text intact

**Over-split** (2) — one true topic extracted as several separate predicted requirements:
- true `terms_and_conditions_acceptance_statement` — "To facilitate the award process, all quotes must include a statement regarding the terms and conditions herein as follows: "The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition." OR "The terms and conditions in the solicitation are acceptable to be included in the award document with the exception, deletion, or addition of the following:" Quoters shall list exception(s) and rationale for the exception(s), if any." split into 2 predicted requirements:
  - predicted [c71dd4a8] "Quoters shall list exception(s) and rationale for the exception(s), if any." — verdict: compliant
  - predicted [dd4f3800] "The quote must include a statement specifying the extent of agreement with the solicitation's terms and conditions, either confirming full acceptance without modification or detailing any specific exceptions, deletions, or additions." — verdict: compliant
- true `submission_deadline_and_channel` — "All quotations shall be emailed to: carlos.ortiz3@va.gov ... E-mailed quotes will be accepted. Submission shall be received no later than 11:00 AM EDT 09/18/26." split into 2 predicted requirements:
  - predicted [37427a32] "Quotes must be submitted via email to the designated Government point of contact." — verdict: compliant
  - predicted [42a52b5d] "Submission shall be received no later than 11:00 AM EDT 09/18/26." — not verifiable by text

**Over-merge** (2) — one predicted requirement covering several distinct true topics:
- predicted [d689404a] "The offeror must comply with all Limitations on Subcontracting (LOS) requirements and must explicitly assert this compliance in the email accompanying their quote." — verdict: non_compliant lumps together 2 true requirements:
  - true `los_compliance_assertion` — "Compliance with the LOS clauses must be asserted by the offeror in the email accompanying their quote."
  - true `los_requirements_met` — "Offeror must meet LOS (Limitations on Subcontracting) requirements and per the LOS listed clauses below."
- predicted [aaff0ad7] "The quoter must provide the specified Sorna Vertex 25ei & CD Burner products as described in the Statement of Work and solicitation documents, and submit a quote for these items." — verdict: compliant lumps together 2 true requirements:
  - true `brand_name_no_substitutes` — "The quotations shall be brand name for the for Sorna Vertex 25ei & CD Burner listed in the Product Chart above and as described in detail in the combined synopsis solicitation, Intent to Compete/ RFQ as posted on Contract Opportunities starting on Page 1 (P1). ... No substitutions can be considered."
  - true `single_best_price_quote` — "(e) Multiple Quotes. Quoters are requested to submit one (1) quote presenting their best price for the required Sorna Vertex 25ei & CD Burner."

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 50.0%
- unexplained (22) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [09bcabca] "The offeror must be a veteran-owned small business (VOSB) verified and listed in the VA's Vendor Information Pages (VIP) database, and must maintain this eligibility at the time of offer submission and award."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.77); vs matched predicted [bf425bc7]: cosine=0.88 (>= dedup threshold 0.7) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [0c29f3aa] "The SDVOSB prime contractor must comply with limitations on subcontracting as defined by contract type (services, supplies, or construction) and ensure that subcontractors are VIP-listed SDVOSBs to count as similarly situated, including specific percentage caps on payments to non-VIP-listed firms and requirements for non-manufacturer supply chains."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.69); vs matched predicted [bf425bc7]: cosine=0.78 (>= dedup threshold 0.7) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [0d03865b] "An otherwise eligible firm must comply with the required certification requirements in this solicitation, specifically referencing 852.219-75 and/or 852.219-76 as applicable."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.71); vs matched predicted [ba0b3d9e]: cosine=0.70 (>= dedup threshold 0.7) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [0d8db7df] "When a contract includes both supply and services, the 50 percent limitation shall apply only to the supply portion of the contract."
    - **similarity check:** closest true topic: `los_requirements_met` (cosine=0.61); vs matched predicted [d689404a]: cosine=0.65 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [23d7a8b9] "Deliver to: VAMC CWM (Northampton) 421 N. Main Street Leeds, MA 01053"
    - **similarity check:** closest true topic: `remit_to_address_stated` (cosine=0.48); vs matched predicted [3ee40f1c]: cosine=0.51 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [398c811a] "An SDVOSB or VOSB shall comply with the limitations on subcontracting by the end of the performance period for each order issued under the contract."
    - **similarity check:** closest true topic: `warranty_terms_stated` (cosine=0.56); vs matched predicted [d8055ed1]: cosine=0.56 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [46aa4479] "The business must comply with VAAR subpart 819.70 and SBA regulations regarding small business size and government contracting programs at 13 CFR parts 121 and 125, with references to SDVO SBCs or VOSBs construed to apply to VA-verified and VIP-listed entities."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.79); vs matched predicted [bf425bc7]: cosine=0.85 (>= dedup threshold 0.7) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [4808634c] "An SDVOSB or VOSB shall comply with the limitations on subcontracting by the end of the base term of the contract or order, and then by the end of each subsequent option period."
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.60); vs matched predicted [2745b06c]: cosine=0.61 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [49031281] "The business ... meets Federal small business size standards for the applicable North American Industry Classification System (NAICS) code identified in the solicitation document;"
    - **similarity check:** closest true topic: `technical_description_stated` (cosine=0.62); vs matched predicted [28cff8be]: cosine=0.62 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [49f7e97a] "The quoter agrees to hold the prices in its quote firm for 30 calendar days from the date specified for receipt of quotes unless another time period is specified in an addendum to the solicitation."
    - **similarity check:** closest true topic: `time_specified_for_receipt_stated` (cosine=0.71); vs matched predicted [1805a913]: cosine=0.66 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [57c15691] "it is anticipated that there are ample SD/VOSB resellers who meet the other three (3) NMR requirements per 13 CFR 121.406(b) (i-iii): ... 3) take possession of the product as soon as it ships/is released."
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.58); vs matched predicted [2745b06c]: cosine=0.50 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [61a61862] "Delivery (Must be <$250.00) *"
    - **similarity check:** closest true topic: `shipping_cost_handling` (cosine=0.66); vs matched predicted [18cbb241]: cosine=0.69 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [6eda9124] "This platform is required to maintain operational efficiency and to sustain the quality of patient healthcare provided by Diagnostic Imaging Services at CWM."
    - **similarity check:** closest true topic: `technical_description_stated` (cosine=0.50); vs matched predicted [28cff8be]: cosine=0.48 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [75f52564] "it is anticipated that there are ample SD/VOSB resellers who meet the other three (3) NMR requirements per 13 CFR 121.406(b) (i-iii): ... 1) Fewer than 500 employees"
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.53); vs matched predicted [ba0b3d9e]: cosine=0.60 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [89913c72] "Quoters are responsible for ensuring quotes reach the designated Government office by the time specified in the solicitation."
    - **similarity check:** closest true topic: `time_specified_for_receipt_stated` (cosine=0.81); vs matched predicted [1805a913]: cosine=0.77 (>= dedup threshold 0.7) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [8c95d0dc] "Any questions or concerns regarding this solicitation must be forwarded in writing via e-mail to the Point of Contact listed below."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.67); vs matched predicted [ba0b3d9e]: cosine=0.69 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [91784af1] "The VOSB prime contractor must comply with limitations on subcontracting as defined by contract type (services, supplies, or construction) and ensure that subcontractors are VIP-listed VOSBs to count as similarly situated, including specific percentage caps on payments to non-VIP-listed firms and requirements for non-manufacturer supply chains."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.67); vs matched predicted [bf425bc7]: cosine=0.75 (>= dedup threshold 0.7) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [958cc067] "A joint venture agrees that, in the performance of the contract, the applicable percentage specified in paragraph (d) of this clause will be performed by the aggregate of the joint venture participants."
    - **similarity check:** closest true topic: `los_compliance_assertion` (cosine=0.55); vs matched predicted [d689404a]: cosine=0.62 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [9b779910] "The Department of Veterans Affairs requires a Sorna Vertex 25ei System Package and accessories to produce high-density, medical-grade CDs of radiology files."
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.62); vs matched predicted [aaff0ad7]: cosine=0.64 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [ddca3a25] "When a contract includes both services and supplies, the 50 percent limitation shall apply only to the portion of the contract with the preponderance of the expenditure upon which the assigned NAICS is based."
    - **similarity check:** closest true topic: `los_requirements_met` (cosine=0.61); vs matched predicted [d689404a]: cosine=0.65 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [e494633b] "Unless otherwise provided in the schedule, ... quotations may not be submitted for quantities less than those specified."
    - **similarity check:** closest true topic: `amendment_acknowledgment` (cosine=0.70); vs matched predicted [f07a87ec]: cosine=0.63 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [fb525d1f] "When a contract includes both services and supplies, the 50 percent limitation shall apply only to the service portion of the contract."
    - **similarity check:** closest true topic: `los_requirements_met` (cosine=0.61); vs matched predicted [d689404a]: cosine=0.64 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (1) — the predicted citation is padded beyond the true one:
- true `quote_signed_and_dated` is contained in predicted [225c564f] — 72.5%:
    predicted: "Submit signed and dated quotes to the office specified in this Combined Synopsis: Intent to Compete/RFQ at or before the exact time specified."
    true: "Submit signed and dated quotes to the office specified in this Combined Synopsis: Intent to Compete/RFQ"

**Requirements captured incompletely** (2) — the predicted citation misses part of the true one:
- predicted [28cff8be] is contained in true `technical_description_stated` — 65.3%:
    predicted: "As a minimum, quotes must show— ... (4) A technical description of the items being quoted in sufficient detail to evaluate compliance with the requirements in the solicitation."
    true: "(4) A technical description of the items being quoted in sufficient detail to evaluate compliance with the requirements in the solicitation. This may include product literature, or other documents, if necessary."

- predicted [966c727e] is contained in true `far_52_212_3_reps_and_certs` — 51.1%:
    predicted: "As a minimum, quotes must show— ... (8) A completed copy of the representations and certifications under the Federal Acquisition Regulation (FAR) 52.212-3"
    true: "(8) A completed copy of the representations and certifications under the Federal Acquisition Regulation (FAR) 52.212-3 (see FAR 52.212-3(b) for those representations and certifications that the quoter shall complete electronically)."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 90.0% (20 groups)**

Mismatched:
- true: `eft_indicator_if_applicable`=False; predicted: `18f9c8dc`=True — "The quoter also must enter its Electronic Funds Transfer (EFT) indicator, if applicable."
- true: `brand_name_no_substitutes`=True, `single_best_price_quote`=False; predicted: `aaff0ad7`=True — "The quotations shall be brand name for the for Sorna Vertex 25ei & CD Burner listed in the Product Chart above and as described in detail in the combined synopsis solicitation, Intent to Compete/ RFQ as posted on Contract Opportunities starting on Page 1 (P1). ... No substitutions can be considered."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 75.0% (20 groups)**

Mismatched:
- true: `sam_registration_required`=False; predicted: `dda3d4b9`=True — "Offeror must be registered in SAM."
- true: `sdvosb_certification_required`=False; predicted: `bf425bc7`=True — "Offeror must be certified/verified as an SD/VOSB in the SBA SBS VIP (Veteran Information Pages) VetCert as an SD/VOSB."
- true: `los_compliance_assertion`=True, `los_requirements_met`=False; predicted: `d689404a`=True — "Compliance with the LOS clauses must be asserted by the offeror in the email accompanying their quote."
- true: `quote_signed_and_dated`=True; predicted: `225c564f`=False — "Submit signed and dated quotes to the office specified in this Combined Synopsis: Intent to Compete/RFQ"
- true: `submission_deadline_and_channel`=False; predicted: `37427a32`=True, `42a52b5d`=False — "All quotations shall be emailed to: carlos.ortiz3@va.gov ... E-mailed quotes will be accepted. Submission shall be received no later than 11:00 AM EDT 09/18/26."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 13

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 8 | 2 | 0 | 0 |
| `non_compliant` | 0 | 2 | 0 | 0 |
| `contradictory` | 0 | 1 | 0 | 0 |
| `insufficient_information` | 0 | 0 | 0 | 0 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `uei_provided_on_quote` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "The quoter must enter, in the block with its name and address on the cover page of its quote, the annotation "Unique Entity Identifier" followed by the unique entity identifier that identifies the quoter's name and address."
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 [...truncated]"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quotin [...truncated]"
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w [...truncated]"
  - **model's evidence (what it chose to cite):** "Quoter name, address, and telephone number: Meridian Medical Systems, LLC 88 Harborview Drive, Suite 210 Providence, RI 02903 Telephone: (401) 555-0142 Unique Entity Identifier: NL8K4TQ9XPW3"
  - **model's reasoning:** The requirement specifies that the quoter must enter the annotation 'Unique Entity Identifier' followed by the identifier in the block with its name and address. While the bidder provided the identifier, they failed to include the specific required annotation 'Unique Entity Identifier' as a label or prefix immediately preceding the identifier within the name and address block; instead, they listed it as a separate line item.
  - **expected evidence (true_verdicts.json):** "Unique Entity Identifier: NL8K4TQ9XPW3"
  - **expected reasoning:** UEI is entered in the cover block, annotated as required.

- `eft_indicator_if_applicable` — acceptable: ['compliant', 'insufficient_information'], predicted: non_compliant
  - **requirement:** "The quoter also must enter its Electronic Funds Transfer (EFT) indicator, if applicable."
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w [...truncated]"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quotin [...truncated]"
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 [...truncated]"
  - **model's evidence (what it chose to cite):** "Quoter name, address, and telephone number: Meridian Medical Systems, LLC 88 Harborview Drive, Suite 210 Providence, RI 02903 Telephone: (401) 555-0142"
  - **model's evidence (what it chose to cite):** ""Remit to" address: Same as the mailing address listed above."
  - **model's reasoning:** The requirement explicitly states that the quoter must enter its Electronic Funds Transfer (EFT) indicator. A review of the provided application documents shows that while the bidder provided contact information, a Unique Entity Identifier, and business status, they failed to include an EFT indicator.
  - **expected evidence (true_verdicts.json):** none
  - **expected reasoning:** The application never mentions an EFT indicator. Since the requirement is conditional ('if applicable'), text alone cannot distinguish 'not applicable to this quoter' from 'applicable but omitted' -- both compliant (nothing was owed) and insufficient_information (can't tell) are defensible; non_compliant would wrongly assume it was owed.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 6.7%

- group of 2 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `brand_name_no_substitutes` — "The quotations shall be brand name for the for Sorna Vertex 25ei & CD Burner listed in the Product Chart above and as described in detail in the combined synopsis solicitation, Intent to Compete/ RFQ as posted on Contract Opportunities starting on Page 1 (P1). ... No substitutions can be considered." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "We are quoting the Sorna Vertex 25ei Platform with integrated Sorna CD Burner, brand name, exactly as specified in the Product Chart. This is the identical brand-name system required by the solicitation; Meridian is not offering a substitute or equivalent product."
      - **expected reasoning:** Application states the exact brand-name product is quoted, no substitute.
  - true `single_best_price_quote` — "(e) Multiple Quotes. Quoters are requested to submit one (1) quote presenting their best price for the required Sorna Vertex 25ei & CD Burner." (acceptable: ['non_compliant'])
      - **expected evidence (true_verdicts.json):** "We are also pleased to offer an alternative configuration for your consideration: Option A (as priced above): Standard configuration, grand total $22,940.00. Option B: Extended 5-year warranty configuration, grand total $23,100.00. Please let us know which option you would prefer to award."
      - **expected reasoning:** Application offers two priced options instead of one best price.
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w [...truncated]"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quotin [...truncated]"
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 [...truncated]"
  - predicted verdicts in this group:
    - predicted [aaff0ad7] "The quoter must provide the specified Sorna Vertex 25ei & CD Burner products as described in the Statement of Work and solicitation documents, and submit a quote for these items." — verdict: compliant
      - **model's evidence (what it chose to cite):** "We are quoting the Sorna Vertex 25ei Platform with integrated Sorna CD Burner, brand name, exactly as specified in the Product Chart. This is the identical brand-name system required by the solicitation; Meridian is not offering a substitute or equivalent product."
      - **model's evidence (what it chose to cite):** "Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00."
      - **model's reasoning:** The bidder explicitly states they are providing the exact brand-name Sorna Vertex 25ei Platform with integrated CD Burner as required by the solicitation and includes this item in their price quote.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 6.7%

- `uei_provided_on_quote` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "The quoter must enter, in the block with its name and address on the cover page of its quote, the annotation "Unique Entity Identifier" followed by the unique entity identifier that identifies the quoter's name and address."
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 [...truncated]"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quotin [...truncated]"
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w [...truncated]"
  - **model's evidence (what it chose to cite):** "Quoter name, address, and telephone number: Meridian Medical Systems, LLC 88 Harborview Drive, Suite 210 Providence, RI 02903 Telephone: (401) 555-0142 Unique Entity Identifier: NL8K4TQ9XPW3"
  - **model's reasoning:** The requirement specifies that the quoter must enter the annotation 'Unique Entity Identifier' followed by the identifier in the block with its name and address. While the bidder provided the identifier, they failed to include the specific required annotation 'Unique Entity Identifier' as a label or prefix immediately preceding the identifier within the name and address block; instead, they listed it as a separate line item.
  - **expected evidence (true_verdicts.json):** "Unique Entity Identifier: NL8K4TQ9XPW3"
  - **expected reasoning:** UEI is entered in the cover block, annotated as required.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `terms_and_conditions_acceptance_statement` — "To facilitate the award process, all quotes must include a statement regarding the terms and conditions herein as follows: "The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition." OR "The terms and conditions in the solicitation are acceptable to be included in the award document with the exception, deletion, or addition of the following:" Quoters shall list exception(s) and rationale for the exception(s), if any." (acceptable: ['compliant'])
  - predicted [c71dd4a8] "Quoters shall list exception(s) and rationale for the exception(s), if any." — verdict: compliant
  - predicted [dd4f3800] "The quote must include a statement specifying the extent of agreement with the solicitation's terms and conditions, either confirming full acceptance without modification or detailing any specific exceptions, deletions, or additions." — verdict: compliant
- group 2:
  - true `brand_name_no_substitutes` — "The quotations shall be brand name for the for Sorna Vertex 25ei & CD Burner listed in the Product Chart above and as described in detail in the combined synopsis solicitation, Intent to Compete/ RFQ as posted on Contract Opportunities starting on Page 1 (P1). ... No substitutions can be considered." (acceptable: ['compliant'])
  - true `single_best_price_quote` — "(e) Multiple Quotes. Quoters are requested to submit one (1) quote presenting their best price for the required Sorna Vertex 25ei & CD Burner." (acceptable: ['non_compliant'])
  - predicted [aaff0ad7] "The quoter must provide the specified Sorna Vertex 25ei & CD Burner products as described in the Statement of Work and solicitation documents, and submit a quote for these items." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 100.0% (0 unverified of 45)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (15/15)
- missed:
  - none

## Verdict-only evaluation

Runs verdict generation directly on true_requirements.json's own text and citations against application.txt, bypassing requirement extraction and match-group sequencing entirely -- isolates whether generate_verdict, given a perfect requirement, makes the right call. Only mismatches are listed below.

**Accuracy: 94.4% (17/18)**

- `product_chart_full_pricing` — acceptable: ['contradictory', 'non_compliant'], predicted: insufficient_information
  - **requirement:** "Quote must enter pricing for every line item listed in the Product Chart."
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,650.00, Total $1,650.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00. Delivery, Qty 1, Unit Price $1,400.00, Total $1,400.00. Grand total of the line items above: $22,940.00. We are also pleased to offer an alternative configuration for your consideration: Option A (as priced above): Standard configuration, grand total $22,940.00. Option B: Extended 5-year warranty configuration, grand total $23,100.00. Please let us know which option you would prefer to award. Shipping for this order is $150.00 and will be invoiced as a separate line item on the purchase order, not included in the Vertex 25ei/CD Burner unit price above. Please contact us with any questions regarding this quote. Sincerely, Diane Kowalski Contracts Manager Meridian Medical Systems, LLC"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quoting the Sorna Vertex 25ei Platform with integrated Sorna CD Burner, brand name, exactly as specified in the Product Chart. This is the identical brand-name system required by the solicitation; Meridian is not offering a substitute or equivalent product. The package includes the Vertex Host software with unlimited Client and Media Importer licenses, automated DICOM profiles, a pre-configured Windows 11 Professional PC, monitor, keyboard, mouse, disc label design software, and all necessary cabling, matching the Statement of Work in full. Terms of express warranty: The system is covered by the manufacturer's standard 3-year parts-and-labor warranty from the date of installation. Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered. "Remit to" address: Same as the mailing address listed above. Our representations and certifications under FAR 52.212-3 are on file in SAM.gov and available upon request; we have not attached a completed copy to this email. Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition."
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 P0003. We acknowledge the time specified in the solicitation for receipt of quotations as 11:00 AM EDT on 09/18/26, and our quote is submitted ahead of that deadline. Quoter name, address, and telephone number: Meridian Medical Systems, LLC 88 Harborview Drive, Suite 210 Providence, RI 02903 Telephone: (401) 555-0142 Unique Entity Identifier: NL8K4TQ9XPW3 Meridian Medical Systems, LLC is registered and active in the System for Award Management (SAM). Meridian Medical Systems, LLC is a VIP-listed Service-Disabled Veteran-Owned Small Business (SDVOSB), verified under SBA SBS VetCert Case #DV-2024-01187. We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications."
  - **model's evidence (what it chose to cite):** "Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,650.00, Total $1,650.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00. Delivery, Qty 1, Unit Price $1,400.00, Total $1,400.00. Grand total of the line items above: $22,940.00."
  - **model's reasoning:** The bidder provides a Product Chart pricing section containing several line items. However, the text does not include the actual Product Chart from the tender's requirements document, making it impossible to verify whether pricing was entered for every single line item listed in the original Product Chart.
  - **expected evidence (true_verdicts.json):** "Total quoted price for this solicitation: $21,540.00."
  - **expected evidence (true_verdicts.json):** "Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,650.00, Total $1,650.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00. Delivery, Qty 1, Unit Price $1,400.00, Total $1,400.00. Grand total of the line items above: $22,940.00."
  - **expected reasoning (true_verdicts.json):** All five Product Chart line items are priced, but the quote states two different grand totals for the same quote: $21,540.00 up front and $22,940.00 from the itemized breakdown -- a direct numeric contradiction. non_compliant is also acceptable if a pipeline flags the mismatched total as a completeness/accuracy failure instead of naming it a contradiction.
