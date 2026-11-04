# Three stories, five inputs each

[manifest.json](manifest.json) is the input catalogue. These published files live
in `docs/examples/` and are served at `/examples/`. Each story has identical text
across its formats. [stories.json](stories.json) freezes the text, expected
outcomes and source selectors. Expectations are synthetic demonstration labels,
not saved model results or an accuracy measurement.

| Story | IDs | Expected behavior |
| --- | --- | --- |
| A · Wrong period | `a-text`, `a-image`, `a-pdf`, `a-audio`, `a-video` | Apple annual revenue attributed to Q4; correct $416.2B to $102.5B |
| B · All correct | `b-text`, `b-image`, `b-pdf`, `b-audio`, `b-video` | Three supported numbers; nothing to correct |
| C · Mixed | `c-text`, `c-image`, `c-pdf`, `c-audio`, `c-video` | Supported Microsoft value, exact ×1000 Meta unit error, third-party forecast not judged, Nintendo scope claim insufficient |

The committed build has nine ready files (TXT, PNG and native-text PDF for each
story). Six explicit `.pending.txt` files stand in for MP3/MP4; they are not
playable media. The capability-only probe in
[voice-capability.json](validation/voice-capability.json) found no MPS device in
this sandbox. No substitute voice, model verification or OCR/ASR call was made.

## Filed numbers

Every manifest entry includes `fixture_citations`: fixture and provenance hashes,
original snapshot hash, exact JSON pointer and unmodified SEC row with accession,
period, value and filing date. The builder verifies hashes and computes each
displayed amount from those rows. Ordinary displays round to the nearest 0.1
billion, half up. The C unit error uses no rounding.

| Display | Filed amount / calculation (USD) | Fixture |
| --- | --- | --- |
| A · Amazon Q3 2023 $143.1B | 143,083,000,000 | [Amazon](../../tests/fixtures/sec-offline/companyfacts-CIK0001018724.json) |
| A · NVIDIA FY2024 $60.9B | 60,922,000,000 | [NVIDIA](../../tests/fixtures/sec-offline/companyfacts-CIK0001045810.json) |
| A · Apple $416.2B; correction $102.5B | Annual 416,161,000,000 − nine months 313,695,000,000 = Q4 102,466,000,000 | [Apple](../../tests/fixtures/sec-offline/companyfacts-CIK0000320193.json) |
| B/C · Microsoft FY2025 $281.7B | 281,724,000,000 | [Microsoft](../../tests/fixtures/sec-offline/companyfacts-CIK0000789019.json) |
| B · Alphabet FY2024 $350.0B | 350,018,000,000 | [Alphabet](../../tests/fixtures/sec-offline/companyfacts-CIK0001652044.json) |
| B/C · Meta FY2024 $164.5B / deliberate $164,501B | Filed 164,501,000,000 = 164,501 million; C states 164,501,000,000,000, exactly ×1000 | [Meta](../../tests/fixtures/sec-offline/companyfacts-CIK0001326801.json) |

C reuses Microsoft's filed amount as a forecast threshold; this is not evidence
for the forecast. The Nintendo record-high statement is an intentionally
unresolved non-US scope probe without a numerical revenue amount. Its extraction
may abstain. No Nintendo filed result is asserted by the manifest.

## Rebuild and verify offline

```sh
uv run --frozen python scripts/build_examples.py
uv run --frozen python scripts/build_examples.py --check
bash scripts/verify.sh
```

Normal builds regenerate TXT, PNG, PDF and placeholders byte for byte, using
locked Pillow and a bundled, OFL-licensed Latin subset of Noto Serif TC, the
site's document font family. PDFs embed that same font and retain selectable
text. [Font metrics and source provenance](fonts/metrics.json) and
[font license](fonts/OFL.txt) are retained. Images are 1280×720. The manifest
enforces ≤2,000,000 bytes for every input and ≤20 seconds for ready MP3/MP4.

## Prepare audio/video on the host

Run from this worktree, with the locked voice reference in the video worktree:

```sh
uv run --frozen python scripts/build_examples.py --synthesize --device mps \
  --video-repo /Users/yan/git/market-claim-verifier-video \
  --breeze /Users/yan/ml-engines/breeze-tts
uv run --frozen python scripts/build_examples.py --check
```

This uses Breeze-TTS-2 clone mode, seed 2026, the exact reference transcript and
SHA-256 `43346fa72fb56df38918f318012c0cf2856fba03728b18544d0a864d50f6a6c4`.
Code/model pins must match the locked pipeline. Every attempt gets a new
`production/<timestamp>/` directory with frozen jobs, input hashes, pins, log,
exit receipt and original WAVs. Failed attempts are retained. CPU execution is
available only by explicitly choosing `--device cpu`.

FFmpeg encodes mono 64 kbps MP3 and a 720p still-image H.264/AAC MP4. A full
narration exceeding the target is accelerated with `atempo`, never cut mid-post;
an overlong clip requiring more than 2× speed fails. Output bounds are measured
with ffprobe. To re-encode the selected retained WAVs without another synthesis:

```sh
uv run --frozen python scripts/build_examples.py --render-media
uv run --frozen python scripts/build_examples.py --check
```

The same WAVs and FFmpeg build/flags reproduce the encoded bytes. The encoder
version and hashes are retained in `narration/<story>.json`. Fixed-seed Breeze
does not promise identical output across different devices or runtime versions.
Normal offline builds validate retained media; they never invoke Breeze,
FFmpeg, ffprobe or a paid API.

## Record the production examples on the host

After these exact assets and the API supporting these IDs are deployed, run:

```sh
LIVE_CHECK_PASSWORD_FILE=/absolute/path/to/live-check-password \
  uv run --frozen python scripts/run_example_records.py \
  --origin https://hackathon.dappgo.com --max-spend-usd 3 --execute
uv run --frozen python scripts/build_examples.py
uv run --frozen python scripts/build_examples.py --check
```

The default is all 15 IDs in story/format order. Before preparing narration,
the ready inputs can be recorded explicitly:

```sh
LIVE_CHECK_PASSWORD_FILE=/absolute/path/to/live-check-password \
  uv run --frozen python scripts/run_example_records.py --max-spend-usd 3 \
  --ids a-text a-image a-pdf b-text b-image b-pdf c-text c-image c-pdf --execute
```

If that subset is already recorded, select only
`--ids a-audio a-video b-audio b-video c-audio c-video` after preparing narration;
previously saved cases are never executed again implicitly.

The recorder verifies the deployed manifest, freezes the selected cases and
budget before execution, and explicitly requests Baseten
`meta-models/muse-spark-open-1026`. Meta preprocessing remains separate in each
API receipt. The entire server daily allowance must fit the supplied cap; the
recorder stops at exhaustion or a daily reset. It never prints the password,
retries a request, overwrites a saved result or silently substitutes text for a
media input.

Complete live envelopes are saved as `docs/site/data/examples/<id>.json` with
`mode: recorded`, preserved receipt/preprocessing/claims/evidence/corrections and
hash-linked recording provenance. All responses, including failures and partial
attempts, are retained with secrets redacted under
`docs/evidence/example-records/<timestamp>/`. Raw wire hashes and stored-response
hashes are distinguished. The API's public envelope does not expose
provider-private response bodies. Nothing in this commit invents an OCR/ASR
transcript or saved verdict.

Rebuild the catalogue after recording (including a partial run). This validates
each saved envelope byte for byte against its retained response and receipt,
then adds its `saved_result` URL. Offline verification repeats that check; it
never calls the live service to recreate a saved result.

## Validation records

[validation/](validation/) retains development runs, including the first failed
checks. Synthetic WAV encoding tests exercise byte stability and media bounds;
they do not test narration or extraction accuracy. PNGs and all three rendered
PDF pages were visually reviewed with PDFium (Poppler was absent).
