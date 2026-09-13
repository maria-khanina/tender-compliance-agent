# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9722,
  "requirement_recall_matched": 35,
  "requirement_recall_total": 36,
  "requirement_precision": 0.3125,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.7,
  "is_mandatory_scored": 10,
  "is_text_verifiable_accuracy": 0.7,
  "is_text_verifiable_scored": 10,
  "verdict_clean_match_count": 4,
  "verdict_accuracy": 0.75,
  "false_compliant_rate": 0.0,
  "false_issue_rate": 0.1429,
  "evidence_citation_verified_rate": 1.0,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": 0.8824,
  "verdict_only_scored": 17
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 97.2% (35/36)**

**Missed** (1) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `sam_registration_active` — "The FBI may verify product configuration, OEM authorization, warranty eligibility, business size, SAM registration, and other award eligibility information prior to award."
    - **chunk check:** [4864:5035] whole, in chunk 3 -- the model saw this text intact

**Over-split** (0) — one true topic extracted as several separate predicted requirements:
- none

**Over-merge** (3) — one predicted requirement covering several distinct true topics:
- predicted [7bbcb142] "Quotes must provide exact brand-name, factory-new, genuine OEM products through authorized U.S. channels, with valid OEM warranties; gray-market, used, or refurbished items are prohibited." — verdict: compliant, citation: fuzzy match — worth a second look lumps together 3 true requirements:
  - true `authorized_reseller_distributor_evidence` — "Contract holders may furnish the required products as authorized resellers or distributors, provided the products quoted are the exact brand-name products and configurations required. The Government may require evidence of OEM or reseller authorization, warranty/support eligibility, and product authenticity."
  - true `brand_name_only_no_alternates` — "This RFQ is for brand-name-only products. The Government requires the exact manufacturers, products, models, configurations, quantities, warranty/support, and delivery requirements identified in this RFQ and Attachment 1. Alternate, substitute, equivalent, or “or equal” products will not be considered and will be rated Technically Unacceptable for the applicable award group."
  - true `oem_new_no_gray_market_certification` — "State that the quoted products are the exact brand-name products required by this RFQ and are new, genuine OEM products eligible for the required OEM warranty/support. ... Certify that all quoted items are factory-new and will be delivered with an OEM/manufacturer warranty valid in the United States. The quote shall not include gray-market, used, refurbished, recertified, reconditioned, demo, open-box, previously owned, or previously placed-in-service products."
- predicted [aa388c39] "Quotes must include a detailed breakdown of all items, quantities, configurations, warranty/support, delivery schedules, and unit/extended prices, with all shipping and handling charges included in the firm-fixed price." — verdict: non_compliant lumps together 2 true requirements:
  - true `item_identification_completeness` — "For every quoted item, identify the exact manufacturer, product/model, manufacturer part number or SKU (when applicable), configuration, quantity, warranty/support, delivery schedule, unit price, and extended price."
  - true `pricing_inclusive_of_all_charges` — "Include all shipping, handling, warranty/support, and other charges in the quoted firm-fixed price."
- predicted [d103012f] "The forensic workstation must meet the specified hardware configuration, including Intel Core Ultra 9 285K, liquid cooling, 192GB DDR5 RAM, specified storage drives, NVIDIA RTX PRO 4000 24GB, RAID controller, hot-swap bays, USB hubs, 1700W PSU, Windows 11 Pro, chassis dimensions, and a three-year warranty." — verdict: non_compliant lumps together 23 true requirements:
  - true `chassis_aluminum_thickness_spec` — "Aluminum Thickness = 0.118 (or 3.00mm)"
  - true `chassis_fan_size_spec` — "Fan size(s) = 120mm"
  - true `chassis_open_525_bays_spec` — "Open 5.25 Bays = 11"
  - true `chassis_pci_expansion_slots_spec` — "PCI Chassis Expansion Slots = 8"
  - true `chassis_size_spec` — "Size: 15 W x 19.06 H x 20.06 D (381mm x 484mm x 510mm)"
  - true `cpu_processor_spec` — "Intel Core Ultra 9 285K | 3.7 GHz (5.7 GHz Boost) | 8P-16E Cores 24 Threads Processor"
  - true `gpu_spec` — "NVIDIA RTX PRO 4000 Blackwell | 24GB GDDR7 Graphics Card"
  - true `hot_swap_bay_25_eight_trays_spec` — "One (1) 2.5” Hot Swap Bay with Eight (8) Removable Trays"
  - true `hot_swap_bay_25_four_trays_spec` — "One (1) 2.5” Hot Swap Bay with Four (4) Removable Trays"
  - true `hot_swap_bay_35_three_drives_spec` — "One (1) 3.5” Hot Swap Bay for Three (3) Drives"
  - true `liquid_cooling_spec` — "Liquid Cooling for the CPU Providing Maximum Performance"
  - true `nvme_ssd_database_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for Database(s)"
  - true `nvme_ssd_operating_system_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for the Operating System"
  - true `nvme_ssd_processing_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for Processing"
  - true `nvme_ssd_temporary_files_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for Temporary Files"
  - true `operating_system_spec` — "- Windows 11 Only ... Microsoft Windows 11 Pro 64 Bit"
  - true `power_supply_spec` — "One (1) 1700 Watt Power Supply Unit"
  - true `raid5_eight_ssd_storage_spec` — "Eight (8) 1TB SSDs in RAID 5 for Data Storage"
  - true `raid_card_spec` — "ARC-1883i RAID Card"
  - true `ram_capacity_spec` — "192GB of DDR5 4800 MHz RAM"
  - true `usb_2_0_ten_port_hub_spec` — "One (1) 10 Port USB 2.0 Hub (USB-A)"
  - true `usb_3_0_four_port_hub_spec` — "One (1) 4 Port USB 3.0 Hub (2x USB-A, 2x USB-C)"
  - true `warranty_spec` — "Three (3) Year Standard Warranty"

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 31.2%
- unexplained (22) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [035c4942] "Invoices must be submitted electronically via the IPP system in accordance with FBI-0023, with all supporting documentation uploaded, submitted at least monthly, and finalized within 30 days of the period of performance end date."
    - **similarity check:** closest true topic: `submission_deadline_and_channel` (cosine=0.60); vs matched predicted [e0197e92]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [0c60ffc6] "Non-U.S. citizens are prohibited from performing work involving access to or development of DOJ IT systems; non-IT requirements met by non-U.S. citizens must be clearly described."
    - **similarity check:** closest true topic: `submission_deadline_and_channel` (cosine=0.56); vs matched predicted [e0197e92]: cosine=0.60 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [0c6b5f35] "Unless otherwise provided in the Schedule, offers may not be submitted for quantities less than those specified."
    - **similarity check:** closest true topic: `exceptions_conditions_disclosure` (cosine=0.62); vs matched predicted [26f448ee]: cosine=0.50 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [1db9105d] "Contractors must manage foreign suppliers by counting and examining goods, ensuring no direct shipping to the FBI, and using approved shipping labels that do not reference the FBI."
    - **similarity check:** closest true topic: `pra_national_security_cooperation` (cosine=0.66); vs matched predicted [750ebee5]: cosine=0.76 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [21e554d6] "The offeror agrees to hold prices firm for 30 calendar days from the date specified for receipt of offers, unless otherwise specified."
    - **similarity check:** closest true topic: `pricing_inclusive_of_all_charges` (cosine=0.60); vs matched predicted [aa388c39]: cosine=0.64 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [27e4b6bd] "The Contractor agrees to comply with non-discrimination requirements, provide access to records, report subcontractor violations, and include these requirements in subcontracts."
    - **similarity check:** closest true topic: `exceptions_conditions_disclosure` (cosine=0.63); vs matched predicted [26f448ee]: cosine=0.55 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [2a409209] "A quote will be rated Technically Acceptable for an award group only if it demonstrates compliance with all mandatory requirements for that group, including ... all other material RFQ terms"
    - **similarity check:** closest true topic: `exceptions_conditions_disclosure` (cosine=0.59); vs matched predicted [26f448ee]: cosine=0.52 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [2b6d9be8] "Offers must be signed, dated, and submitted to the specified office by the deadline, including all required information such as solicitation number, offeror details, technical descriptions, warranty terms, pricing, and required certifications."
    - **similarity check:** closest true topic: `unique_entity_identifier_annotation` (cosine=0.62); vs matched predicted [fd63ac59]: cosine=0.65 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [316b27c8] "The Contractor shall ensure that its Electronic Business Point of Contact in SAM.gov is current."
    - **similarity check:** closest true topic: `sam_registration_active` (cosine=0.63); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [35ce80c2] "The Contractor shall inform employees of whistleblower rights in writing, include this requirement in subcontracts over the simplified acquisition threshold, and provide confirmation of distribution within 45 days of award."
    - **similarity check:** closest true topic: `pra_national_security_cooperation` (cosine=0.60); vs matched predicted [750ebee5]: cosine=0.72 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [42a076a0] "Offers received after the exact time specified are considered late and will not be considered, except under specific conditions defined by the Contracting Officer."
    - **similarity check:** closest true topic: `unique_entity_identifier_annotation` (cosine=0.60); vs matched predicted [fd63ac59]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [49ea88dc] "Contractors are not authorized to work during a furlough unless directed by the Contracting Officer and must coordinate rescheduling for deliveries affected by Government closures."
    - **similarity check:** closest true topic: `authorized_reseller_distributor_evidence` (cosine=0.60); vs matched predicted [7bbcb142]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [5f71e8f1] "Contractors shall not disclose contract-related information without prior written consent from the FBI, must protect proprietary information, and must disclose any Organizational Conflicts of Interest (OCI)."
    - **similarity check:** closest true topic: `submission_deadline_and_channel` (cosine=0.65); vs matched predicted [e0197e92]: cosine=0.70 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [74b70a7f] "If a vendor objects to disclosure of proprietary information to non-Government advisors, the vendor shall identify the specific information and basis for the objection in its quote."
    - **similarity check:** closest true topic: `exceptions_conditions_disclosure` (cosine=0.65); vs matched predicted [26f448ee]: cosine=0.47 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [8412e696] "Nongovernment (voluntary) standards must be obtained from the organization responsible for their preparation, publication, or maintenance."
    - **similarity check:** closest true topic: `exceptions_conditions_disclosure` (cosine=0.56); vs matched predicted [26f448ee]: cosine=0.39 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [9f7c58b2] "Quotes shall be submitted through the NASA SEWP Quote Request Tool (QRT) by August 20, 2026, at 12:00 PM Eastern Time."
    - **similarity check:** closest true topic: `submission_deadline_and_channel` (cosine=0.70); vs matched predicted [e0197e92]: cosine=0.67 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [9f9fc688] "ICT supplies and services must meet 36 C.F.R. Part 1194 accessibility standards, and an Accessibility Conformance Report (ACR) must be provided when requested."
    - **similarity check:** closest true topic: `authorized_reseller_distributor_evidence` (cosine=0.63); vs matched predicted [7bbcb142]: cosine=0.70 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [b4b8579f] "Protests filed directly with the DOJ must indicate the intent to protest, be filed with the Contracting Officer, state the preferred decision-maker, indicate the presentation format, and include required FAR information."
    - **similarity check:** closest true topic: `exceptions_conditions_disclosure` (cosine=0.60); vs matched predicted [26f448ee]: cosine=0.62 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [b678a1a8] "To be rated Technically Acceptable, a quote must satisfy all mandatory requirements, including exact manufacturer, product, configuration, quantity, warranty/support, and delivery requirements; alternate or 'or equal' products are unacceptable."
    - **similarity check:** closest true topic: `exceptions_conditions_disclosure` (cosine=0.69); vs matched predicted [26f448ee]: cosine=0.54 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [bfb1296c] "Product samples must be submitted at or prior to the time specified for receipt of offers at no expense to the Government, unless otherwise specified."
    - **similarity check:** closest true topic: `oem_new_no_gray_market_certification` (cosine=0.61); vs matched predicted [7bbcb142]: cosine=0.65 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [c94186af] "No additional cost may be incurred without prior written authorization."
    - **similarity check:** closest true topic: `pricing_inclusive_of_all_charges` (cosine=0.59); vs matched predicted [aa388c39]: cosine=0.55 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f9222d0c] "Offers may be withdrawn by written notice, in person, or via authorized electronic methods before the exact time set for receipt of offers."
    - **similarity check:** closest true topic: `unique_entity_identifier_annotation` (cosine=0.58); vs matched predicted [fd63ac59]: cosine=0.62 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (1) — the predicted citation misses part of the true one:
- predicted [26f448ee] is contained in true `exceptions_conditions_disclosure` — 33.8%:
    predicted: "State any exception, condition, or assumption."
    true: "State any exception, condition, or assumption. An exception to a material RFQ requirement may render the quote technically unacceptable."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 70.0% (10 groups)**

Mismatched:
- true: `authorized_reseller_distributor_evidence`=False, `brand_name_only_no_alternates`=True, `oem_new_no_gray_market_certification`=True; predicted: `7bbcb142`=True — "Contract holders may furnish the required products as authorized resellers or distributors, provided the products quoted are the exact brand-name products and configurations required. The Government may require evidence of OEM or reseller authorization, warranty/support eligibility, and product authenticity."
- true: `exceptions_conditions_disclosure`=False; predicted: `26f448ee`=True — "State any exception, condition, or assumption. An exception to a material RFQ requirement may render the quote technically unacceptable."
- true: `chassis_finish_spec`=True; predicted: `d8d8c0c4`=False — "Finish = Powder Coated Black with Black Appointments"

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 70.0% (10 groups)**

Mismatched:
- true: `pra_national_security_cooperation`=False; predicted: `750ebee5`=True — "The prospective awardee shall timely provide all information requested by the FBI to complete the PRA, including acquisition-risk, ownership/control, key-management, source, product, supply-chain, and subcontractor information as applicable."
- true: `kaspersky_telecom_prohibition_compliance`=False; predicted: `da312307`=True — "52.204-23 | Prohibition on Contracting for Hardware, Software, and Services Developed or Provided by Kaspersky Lab Covered Entities"
- true: `submission_deadline_and_channel`=False; predicted: `e0197e92`=True — "Late Quotations. Quotations received after September 17, 2026, at 12:00 PM Eastern Time will not be considered for award. Vendors are solely responsible for ensuring that their complete quotation is successfully submitted to rtiggle@fbi.gov before the stated deadline."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 4

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 1 | 1 | 0 | 0 |
| `non_compliant` | 0 | 1 | 0 | 0 |
| `contradictory` | 0 | 0 | 0 | 0 |
| `insufficient_information` | 0 | 0 | 0 | 1 |

Why some rows are empty:
- `contradictory` row is empty: true `gpu_spec` — over_merge match — no single pair to plot

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `unique_entity_identifier_annotation` — acceptable: ['compliant', 'insufficient_information'], predicted: non_compliant
  - **requirement:** "The offeror shall enter its Unique Entity Identifier and Electronic Funds Transfer (EFT) indicator on the cover page of its offer."
  - **retrieved context (shown to the model):** "From: quotes@meridianforensic.com To: rtiggle@fbi.gov Subject: Quote for RFQ SHOP-PR-26-002435 - Sumuri Talino Workstations Dear Mr. Tiggle, Meridian Forensic Solutions, LLC is pleased to submit the following firm-fixed-price quote in response to RFQ SHOP-PR-26-002435. Vendor Inf [...truncated]"
  - **retrieved context (shown to the model):** "Authorized Reseller Status: Meridian Forensic Solutions, LLC is an authorized SUMURI reseller. A copy of our current SUMURI authorized-reseller certificate is enclosed as Attachment A to this quote. Configuration furnished per unit (all 15 units identical): - Processor: Intel Cor [...truncated]"
  - **model's evidence (what it chose to cite):** "Meridian Forensic Solutions, LLC Unique Entity Identifier: HF3K9QZ8YL72 2210 Rutherford Court, Suite 400 Herndon, VA 20171"
  - **model's reasoning:** The requirement mandates that the offeror enter both its Unique Entity Identifier (UEI) and its Electronic Funds Transfer (EFT) indicator on the cover page of the offer. While the bidder provided their UEI in the vendor information section, the application contains no mention of an EFT indicator.
  - **expected evidence (true_verdicts.json):** "Meridian Forensic Solutions, LLC Unique Entity Identifier: HF3K9QZ8YL72"
  - **expected reasoning:** Application enters the Unique Entity Identifier annotation together with the vendor's name and address.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 0.0%

- none

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 14.3%

- group of 23 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `chassis_aluminum_thickness_spec` — "Aluminum Thickness = 0.118 (or 3.00mm)" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions chassis material thickness.
  - true `chassis_fan_size_spec` — "Fan size(s) = 120mm" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions fan size.
  - true `chassis_open_525_bays_spec` — "Open 5.25 Bays = 11" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions open 5.25" bay count.
  - true `chassis_pci_expansion_slots_spec` — "PCI Chassis Expansion Slots = 8" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions PCI chassis expansion slot count.
  - true `chassis_size_spec` — "Size: 15 W x 19.06 H x 20.06 D (381mm x 484mm x 510mm)" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions chassis dimensions.
  - true `cpu_processor_spec` — "Intel Core Ultra 9 285K | 3.7 GHz (5.7 GHz Boost) | 8P-16E Cores 24 Threads Processor" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "- Processor: Intel Core Ultra 9 285K, liquid-cooled"
      - **expected reasoning:** Application offers the exact required processor, liquid-cooled as specified.
  - true `gpu_spec` — "NVIDIA RTX PRO 4000 Blackwell | 24GB GDDR7 Graphics Card" (acceptable: ['contradictory'])
      - **expected evidence (true_verdicts.json):** "- Graphics: NVIDIA RTX PRO 4000 Blackwell 24GB GDDR7 graphics card"
      - **expected evidence (true_verdicts.json):** "card is listed as an NVIDIA RTX A4000 16GB card"
      - **expected reasoning:** The configuration list states the exact required NVIDIA RTX PRO 4000 Blackwell 24GB GDDR7 card, but a later note says the graphics card is actually an NVIDIA RTX A4000 16GB card -- a direct contradiction about the same item's GPU.
  - true `hot_swap_bay_25_eight_trays_spec` — "One (1) 2.5” Hot Swap Bay with Eight (8) Removable Trays" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions any hot-swap bay.
  - true `hot_swap_bay_25_four_trays_spec` — "One (1) 2.5” Hot Swap Bay with Four (4) Removable Trays" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions any hot-swap bay.
  - true `hot_swap_bay_35_three_drives_spec` — "One (1) 3.5” Hot Swap Bay for Three (3) Drives" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions any hot-swap bay.
  - true `liquid_cooling_spec` — "Liquid Cooling for the CPU Providing Maximum Performance" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "- Processor: Intel Core Ultra 9 285K, liquid-cooled"
      - **expected reasoning:** Application confirms liquid cooling for the CPU in the same configuration line as the processor.
  - true `nvme_ssd_database_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for Database(s)" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions a dedicated database drive; storage is described generically plus an 8-drive RAID 5 array.
  - true `nvme_ssd_operating_system_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for the Operating System" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application describes storage only as 'NVMe solid-state storage as required' plus a separate 8x1TB RAID 5 data array -- neither confirms a dedicated OS drive, and the RAID 5 array architecture is inconsistent with having 4 separately dedicated drives at all.
  - true `nvme_ssd_processing_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for Processing" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions a dedicated processing drive; storage is described generically plus an 8-drive RAID 5 array.
  - true `nvme_ssd_temporary_files_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for Temporary Files" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions a dedicated temporary-files drive; storage is described generically plus an 8-drive RAID 5 array.
  - true `operating_system_spec` — "- Windows 11 Only ... Microsoft Windows 11 Pro 64 Bit" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "- Operating System: Microsoft Windows 11 Pro 64-bit"
      - **expected reasoning:** Application offers the exact required Microsoft Windows 11 Pro 64-bit operating system.
  - true `power_supply_spec` — "One (1) 1700 Watt Power Supply Unit" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "- Power: One (1) 1700 Watt Power Supply Unit"
      - **expected reasoning:** Application offers the exact required 1700 Watt power supply unit.
  - true `raid5_eight_ssd_storage_spec` — "Eight (8) 1TB SSDs in RAID 5 for Data Storage" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "- Data storage array: Eight (8) 1TB SSDs configured in RAID 5"
      - **expected reasoning:** Application offers exactly eight 1TB SSDs configured in RAID 5, as required.
  - true `raid_card_spec` — "ARC-1883i RAID Card" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "- RAID controller: ARC-1883i RAID Card"
      - **expected reasoning:** Application offers the exact required ARC-1883i RAID card.
  - true `ram_capacity_spec` — "192GB of DDR5 4800 MHz RAM" (acceptable: ['non_compliant'])
      - **expected evidence (true_verdicts.json):** "- Memory: 128GB DDR5 system memory"
      - **expected reasoning:** Application offers 128GB DDR5 memory, short of the required 192GB.
  - true `usb_2_0_ten_port_hub_spec` — "One (1) 10 Port USB 2.0 Hub (USB-A)" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application only says 'two front-panel USB hubs for high-speed peripheral connectivity', without confirming a 10-port USB 2.0 hub specifically.
  - true `usb_3_0_four_port_hub_spec` — "One (1) 4 Port USB 3.0 Hub (2x USB-A, 2x USB-C)" (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application only says 'two front-panel USB hubs for high-speed peripheral connectivity', without confirming a 4-port USB 3.0 hub with this exact port mix.
  - true `warranty_spec` — "Three (3) Year Standard Warranty" (acceptable: ['non_compliant'])
      - **expected evidence (true_verdicts.json):** "- Warranty: One (1) year manufacturer warranty, extendable at additional cost"
      - **expected reasoning:** Application offers only a one-year manufacturer warranty (extendable at additional cost) instead of the required three-year standard warranty.
  - **retrieved context (shown to the model):** "Authorized Reseller Status: Meridian Forensic Solutions, LLC is an authorized SUMURI reseller. A copy of our current SUMURI authorized-reseller certificate is enclosed as Attachment A to this quote. Configuration furnished per unit (all 15 units identical): - Processor: Intel Cor [...truncated]"
  - **retrieved context (shown to the model):** "From: quotes@meridianforensic.com To: rtiggle@fbi.gov Subject: Quote for RFQ SHOP-PR-26-002435 - Sumuri Talino Workstations Dear Mr. Tiggle, Meridian Forensic Solutions, LLC is pleased to submit the following firm-fixed-price quote in response to RFQ SHOP-PR-26-002435. Vendor Inf [...truncated]"
  - predicted verdicts in this group:
    - predicted [d103012f] "The forensic workstation must meet the specified hardware configuration, including Intel Core Ultra 9 285K, liquid cooling, 192GB DDR5 RAM, specified storage drives, NVIDIA RTX PRO 4000 24GB, RAID controller, hot-swap bays, USB hubs, 1700W PSU, Windows 11 Pro, chassis dimensions, and a three-year warranty." — verdict: non_compliant
      - **model's evidence (what it chose to cite):** "Memory: 128GB DDR5 system memory"
      - **model's evidence (what it chose to cite):** "Warranty: One (1) year manufacturer warranty, extendable at additional cost"
      - **model's evidence (what it chose to cite):** "Graphics card note: please also see our cover summary, where the offered graphics card is listed as an NVIDIA RTX A4000 16GB card"
      - **model's reasoning:** The bidder failed to meet several mandatory hardware and service requirements. Specifically, they offered 128GB of RAM instead of the required 192GB, a one-year warranty instead of the required three-year warranty, and the graphics card specifications are inconsistent and do not match the required NVIDIA RTX PRO 4000 24GB.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `authorized_reseller_distributor_evidence` — "Contract holders may furnish the required products as authorized resellers or distributors, provided the products quoted are the exact brand-name products and configurations required. The Government may require evidence of OEM or reseller authorization, warranty/support eligibility, and product authenticity." (acceptable: ['compliant'])
  - true `brand_name_only_no_alternates` — "This RFQ is for brand-name-only products. The Government requires the exact manufacturers, products, models, configurations, quantities, warranty/support, and delivery requirements identified in this RFQ and Attachment 1. Alternate, substitute, equivalent, or “or equal” products will not be considered and will be rated Technically Unacceptable for the applicable award group." (acceptable: ['compliant'])
  - true `oem_new_no_gray_market_certification` — "State that the quoted products are the exact brand-name products required by this RFQ and are new, genuine OEM products eligible for the required OEM warranty/support. ... Certify that all quoted items are factory-new and will be delivered with an OEM/manufacturer warranty valid in the United States. The quote shall not include gray-market, used, refurbished, recertified, reconditioned, demo, open-box, previously owned, or previously placed-in-service products." (acceptable: ['compliant'])
  - predicted [7bbcb142] "Quotes must provide exact brand-name, factory-new, genuine OEM products through authorized U.S. channels, with valid OEM warranties; gray-market, used, or refurbished items are prohibited." — verdict: compliant, citation: fuzzy match — worth a second look
- group 2:
  - true `item_identification_completeness` — "For every quoted item, identify the exact manufacturer, product/model, manufacturer part number or SKU (when applicable), configuration, quantity, warranty/support, delivery schedule, unit price, and extended price." (acceptable: ['non_compliant'])
  - true `pricing_inclusive_of_all_charges` — "Include all shipping, handling, warranty/support, and other charges in the quoted firm-fixed price." (acceptable: ['insufficient_information'])
  - predicted [aa388c39] "Quotes must include a detailed breakdown of all items, quantities, configurations, warranty/support, delivery schedules, and unit/extended prices, with all shipping and handling charges included in the firm-fixed price." — verdict: non_compliant
- group 3:
  - true `chassis_aluminum_thickness_spec` — "Aluminum Thickness = 0.118 (or 3.00mm)" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `chassis_fan_size_spec` — "Fan size(s) = 120mm" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `chassis_open_525_bays_spec` — "Open 5.25 Bays = 11" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `chassis_pci_expansion_slots_spec` — "PCI Chassis Expansion Slots = 8" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `chassis_size_spec` — "Size: 15 W x 19.06 H x 20.06 D (381mm x 484mm x 510mm)" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `cpu_processor_spec` — "Intel Core Ultra 9 285K | 3.7 GHz (5.7 GHz Boost) | 8P-16E Cores 24 Threads Processor" (acceptable: ['compliant'])
  - true `gpu_spec` — "NVIDIA RTX PRO 4000 Blackwell | 24GB GDDR7 Graphics Card" (acceptable: ['contradictory'])
  - true `hot_swap_bay_25_eight_trays_spec` — "One (1) 2.5” Hot Swap Bay with Eight (8) Removable Trays" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `hot_swap_bay_25_four_trays_spec` — "One (1) 2.5” Hot Swap Bay with Four (4) Removable Trays" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `hot_swap_bay_35_three_drives_spec` — "One (1) 3.5” Hot Swap Bay for Three (3) Drives" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `liquid_cooling_spec` — "Liquid Cooling for the CPU Providing Maximum Performance" (acceptable: ['compliant'])
  - true `nvme_ssd_database_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for Database(s)" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `nvme_ssd_operating_system_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for the Operating System" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `nvme_ssd_processing_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for Processing" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `nvme_ssd_temporary_files_spec` — "One (1) 1TB Gen4 M.2 NVMe SSD for Temporary Files" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `operating_system_spec` — "- Windows 11 Only ... Microsoft Windows 11 Pro 64 Bit" (acceptable: ['compliant'])
  - true `power_supply_spec` — "One (1) 1700 Watt Power Supply Unit" (acceptable: ['compliant'])
  - true `raid5_eight_ssd_storage_spec` — "Eight (8) 1TB SSDs in RAID 5 for Data Storage" (acceptable: ['compliant'])
  - true `raid_card_spec` — "ARC-1883i RAID Card" (acceptable: ['compliant'])
  - true `ram_capacity_spec` — "192GB of DDR5 4800 MHz RAM" (acceptable: ['non_compliant'])
  - true `usb_2_0_ten_port_hub_spec` — "One (1) 10 Port USB 2.0 Hub (USB-A)" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `usb_3_0_four_port_hub_spec` — "One (1) 4 Port USB 3.0 Hub (2x USB-A, 2x USB-C)" (acceptable: ['insufficient_information', 'non_compliant'])
  - true `warranty_spec` — "Three (3) Year Standard Warranty" (acceptable: ['non_compliant'])
  - predicted [d103012f] "The forensic workstation must meet the specified hardware configuration, including Intel Core Ultra 9 285K, liquid cooling, 192GB DDR5 RAM, specified storage drives, NVIDIA RTX PRO 4000 24GB, RAID controller, hot-swap bays, USB hubs, 1700W PSU, Windows 11 Pro, chassis dimensions, and a three-year warranty." — verdict: non_compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 100.0% (0 unverified of 36)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (17/17)
- missed:
  - none

## Verdict-only evaluation

Runs verdict generation directly on true_requirements.json's own text and citations against application.txt, bypassing requirement extraction and match-group sequencing entirely -- isolates whether generate_verdict, given a perfect requirement, makes the right call. Only mismatches are listed below.

**Accuracy: 88.2% (15/17)**

- `brand_name_only_no_alternates` — acceptable: ['compliant'], predicted: contradictory
  - **requirement:** "Only the exact brand-name products, models, and configurations identified in the RFQ and Attachment 1 are acceptable; alternate, substitute, equivalent, or “or equal” products will not be considered and will be rated Technically Unacceptable."
  - **retrieved context (shown to the model):** "From: quotes@meridianforensic.com To: rtiggle@fbi.gov Subject: Quote for RFQ SHOP-PR-26-002435 - Sumuri Talino Workstations Dear Mr. Tiggle, Meridian Forensic Solutions, LLC is pleased to submit the following firm-fixed-price quote in response to RFQ SHOP-PR-26-002435. Vendor Information: Meridian Forensic Solutions, LLC Unique Entity Identifier: HF3K9QZ8YL72 2210 Rutherford Court, Suite 400 Herndon, VA 20171 Item Offered: SUMURI TALINO Intel Workstation, Qty 15. We take no exceptions, conditions, or assumptions to any requirement of this RFQ. Quote Validity: This quote remains valid for 30 days from the date of this letter. Certifications: Meridian Forensic Solutions, LLC certifies that the quoted TALINO workstations are the exact brand-name SUMURI products required by this RFQ, are new, genuine OEM products eligible for the required OEM warranty/support, and are factory-new. The quote does not include any gray-market, used, refurbished, recertified, reconditioned, demo, open-box, previously owned, or previously placed-in-service products. Authorized Reseller Status: Meridian Forensic Solutions, LLC is an authorized SUMURI reseller. A copy of our current SUMURI authorized-reseller certificate is enclosed as Attachment A to this quote."
  - **retrieved context (shown to the model):** "Authorized Reseller Status: Meridian Forensic Solutions, LLC is an authorized SUMURI reseller. A copy of our current SUMURI authorized-reseller certificate is enclosed as Attachment A to this quote. Configuration furnished per unit (all 15 units identical): - Processor: Intel Core Ultra 9 285K, liquid-cooled - Memory: 128GB DDR5 system memory - Storage: NVMe solid-state storage as required for the workstation's forensic imaging, processing, and database workloads - Data storage array: Eight (8) 1TB SSDs configured in RAID 5 - Graphics: NVIDIA RTX PRO 4000 Blackwell 24GB GDDR7 graphics card - RAID controller: ARC-1883i RAID Card - Expansion: two front-panel USB hubs for high-speed peripheral connectivity - Power: One (1) 1700 Watt Power Supply Unit - Operating System: Microsoft Windows 11 Pro 64-bit - Warranty: One (1) year manufacturer warranty, extendable at additional cost Graphics card note: please also see our cover summary, where the offered graphics card is listed as an NVIDIA RTX A4000 16GB card; the workstation configuration above reflects our standard TALINO build sheet. Unit Price: $17,733.33 Extended Price (15 units): $266,000.00 Delivery: 30 calendar days after receipt of order. FOB Destination. Please let us know if you require any additional information. Sincerely, Denise Okafor Contracts Manager Meridian Forensic Solutions, LLC"
  - **model's evidence (what it chose to cite):** "We take no exceptions, conditions, or assumptions to any requirement of this RFQ."
  - **model's evidence (what it chose to cite):** "Graphics card note: please also see our cover summary, where the offered graphics card is listed as an NVIDIA RTX A4000 16GB card; the workstation configuration above reflects our standard TALINO build sheet."
  - **model's reasoning:** The bidder claims to take no exceptions to the RFQ requirements, which mandate the exact brand-name products and configurations. However, the bidder provides conflicting information regarding the graphics card, noting a discrepancy between their 'standard build sheet' and the card listed in their cover summary, which suggests a deviation from the required configuration.
  - **expected evidence (true_verdicts.json):** "Certifications: Meridian Forensic Solutions, LLC certifies that the quoted TALINO workstations are the exact brand-name SUMURI products required by this RFQ, are new, genuine OEM products eligible for the required OEM warranty/support, and are factory-new. The quote does not include any gray-market, used, refurbished, recertified, reconditioned, demo, open-box, previously owned, or previously placed-in-service products."
  - **expected reasoning (true_verdicts.json):** Application certifies the quoted TALINO workstations are the exact brand-name SUMURI products required by this RFQ; no alternate/substitute product is offered.

- `exceptions_conditions_disclosure` — acceptable: ['compliant'], predicted: contradictory
  - **requirement:** "If the vendor takes any exception, condition, or assumption to a material RFQ requirement, it must be stated in the quote."
  - **retrieved context (shown to the model):** "From: quotes@meridianforensic.com To: rtiggle@fbi.gov Subject: Quote for RFQ SHOP-PR-26-002435 - Sumuri Talino Workstations Dear Mr. Tiggle, Meridian Forensic Solutions, LLC is pleased to submit the following firm-fixed-price quote in response to RFQ SHOP-PR-26-002435. Vendor Information: Meridian Forensic Solutions, LLC Unique Entity Identifier: HF3K9QZ8YL72 2210 Rutherford Court, Suite 400 Herndon, VA 20171 Item Offered: SUMURI TALINO Intel Workstation, Qty 15. We take no exceptions, conditions, or assumptions to any requirement of this RFQ. Quote Validity: This quote remains valid for 30 days from the date of this letter. Certifications: Meridian Forensic Solutions, LLC certifies that the quoted TALINO workstations are the exact brand-name SUMURI products required by this RFQ, are new, genuine OEM products eligible for the required OEM warranty/support, and are factory-new. The quote does not include any gray-market, used, refurbished, recertified, reconditioned, demo, open-box, previously owned, or previously placed-in-service products. Authorized Reseller Status: Meridian Forensic Solutions, LLC is an authorized SUMURI reseller. A copy of our current SUMURI authorized-reseller certificate is enclosed as Attachment A to this quote."
  - **retrieved context (shown to the model):** "Authorized Reseller Status: Meridian Forensic Solutions, LLC is an authorized SUMURI reseller. A copy of our current SUMURI authorized-reseller certificate is enclosed as Attachment A to this quote. Configuration furnished per unit (all 15 units identical): - Processor: Intel Core Ultra 9 285K, liquid-cooled - Memory: 128GB DDR5 system memory - Storage: NVMe solid-state storage as required for the workstation's forensic imaging, processing, and database workloads - Data storage array: Eight (8) 1TB SSDs configured in RAID 5 - Graphics: NVIDIA RTX PRO 4000 Blackwell 24GB GDDR7 graphics card - RAID controller: ARC-1883i RAID Card - Expansion: two front-panel USB hubs for high-speed peripheral connectivity - Power: One (1) 1700 Watt Power Supply Unit - Operating System: Microsoft Windows 11 Pro 64-bit - Warranty: One (1) year manufacturer warranty, extendable at additional cost Graphics card note: please also see our cover summary, where the offered graphics card is listed as an NVIDIA RTX A4000 16GB card; the workstation configuration above reflects our standard TALINO build sheet. Unit Price: $17,733.33 Extended Price (15 units): $266,000.00 Delivery: 30 calendar days after receipt of order. FOB Destination. Please let us know if you require any additional information. Sincerely, Denise Okafor Contracts Manager Meridian Forensic Solutions, LLC"
  - **model's evidence (what it chose to cite):** "We take no exceptions, conditions, or assumptions to any requirement of this RFQ."
  - **model's evidence (what it chose to cite):** "Graphics card note: please also see our cover summary, where the offered graphics card is listed as an NVIDIA RTX A4000 16GB card; the workstation configuration above reflects our standard TALINO build sheet."
  - **model's reasoning:** The bidder explicitly states in the cover letter that they take no exceptions, conditions, or assumptions to the RFQ requirements. However, they subsequently provide a note regarding the graphics card that indicates a discrepancy between their standard build sheet and the offered product, which constitutes an assumption or condition regarding the technical specifications of the equipment being quoted.
  - **expected evidence (true_verdicts.json):** "We take no exceptions, conditions, or assumptions to any requirement of this RFQ."
  - **expected reasoning (true_verdicts.json):** Application explicitly states it takes no exceptions, conditions, or assumptions to any RFQ requirement.
