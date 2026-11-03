# Media review provenance correction

The authoring agent visually inspected the two supplied cards before paid OCR and wrote the frozen paraphrases and review-only notes. **No independent human reference transcript or human truth adjudication was supplied.** The field `human_visual_review_before_ocr: true` in the original [media gold](media-gold.jsonl), and the protocol's corresponding word “human”, were inaccurate provenance wording. They refer to the authoring agent's visual review, not a separate person's annotation.

Original gold and protocol bytes remain unchanged. Both cards already had unresolved/review-only labels and no factual-accuracy or OCR-recall denominator; this correction changes no labels, inputs, settings, outcomes or scores. Actual `claimcheck ingest` OCR and extraction outputs are separately recorded, with full raw responses retained locally. A future OCR-recall study needs an independent reference transcript established before its paid run.

The [machine-readable correction](MEDIA_REVIEW_PROVENANCE.json) binds this notice to the original media-gold hash. [Other protocol provenance errata](PROTOCOL_METADATA_ERRATA.md) concern inherited News fields.
