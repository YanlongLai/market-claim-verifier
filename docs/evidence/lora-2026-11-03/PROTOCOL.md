# Muse Spark Open LoRA attempt protocol

Registered 2026-11-03 UTC before any training or inference tokens. Task cap:
**$15 USD total Fireworks estimated charges**, including failures and retries.
This directory uses UTC dates; the owner's local date at registration is Nov 2.

## Feasibility gate

Check official documentation, authenticated public model metadata, and the
account's compatible deployment shapes. A shape-match request discovers a
configuration; it does not create a deployment. Check whether the supplied key
can open a serverless LoRA session for
`accounts/fireworks/models/muse-spark-open-nvfp4`. If a session is created, close
it after inspection. Session/model initialization is a control operation; do not
submit training batches or generation requests during this gate. Do not create
an on-demand GPU deployment to probe feasibility.

Retain failed probes, sanitized API responses, official source URLs, retrieval
times, hashes, and a cost ledger. Never retain credentials or account balances.
If training, matching tokenization, evaluation, or affordable serving cannot be
established with the available access, stop and document the limitation. A
feasibility stop is not a trained model or an extraction-quality result.

## Conditional experiment

Only after the gate passes, freeze and hash a development-only dataset and a
separate held-out extraction set before paid execution. Permitted sources are
v2 development material, development post reports, and generated posts with
known answers. Never use v2 held-out claims or real-world evaluation items for
training. Prefer independently generated synthetic posts so no evaluation file
has to be opened to prepare training examples.

Target 256 training examples, one epoch, rank 8, seed 20261103. Final prompt,
schema, tokenizer, learning rate, batch size, split membership, and exact token
counts must be frozen in a separate experiment manifest before execution.
Reserve at most $8 for training, $4 for paired evaluation, and $3 contingency;
unused partitions do not authorize exceeding the $15 task total. Include all
rendered tokens in training estimates, even masked prompt tokens. Reserve each
paid request before sending; retain the reservation on unknown usage or failure.
Do not retry paid operations automatically.

Evaluate the same frozen held-out posts with base and adapter, recording JSON
validity, exact quote spans, ticker, metric, period, and stated-number accuracy,
missing/extra claims, per-attempt latency, raw redacted outputs, and estimated
costs. Keep checkpoint sampling separate from chat endpoint serving and avoid
attributing differences between quantizations or endpoints solely to LoRA.

Only a measured win with an available serving route justifies the opt-in
`fireworks-lora` CLI provider. Otherwise retain the outcome without introducing
an unverified provider. Run the complete offline verification entry point,
retain its log, add README/judge pointers, and commit locally without a push.
