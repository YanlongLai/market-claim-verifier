# Pre-submission checklist

The Owner completes these publication checks for the exact code and video being submitted through [Cerebral Valley](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit). The [submission draft](SUBMISSION.md) is ready for review; account and video placeholders still need completion.

## Repository and verification

- [ ] The [repository](https://github.com/YanlongLai/market-claim-verifier) is public and the intended submission commit is accessible while signed out. Private drafts and generated local outputs remain excluded by the [ignore rules](../.gitignore).
- [ ] `UV_OFFLINE=1 sh scripts/verify.sh` passes on that commit, including both Python suites, standalone Node tests, figure checks/rebuild, byte-identical data rebuilds, and local Markdown links. Follow the [prerequisites and expected final output](../AGENTS.md#offline-verification); [the runner](../scripts/verify.py) enforces offline verification without credentials.
- [ ] [Offline verification CI](https://github.com/YanlongLai/market-claim-verifier/actions/workflows/verify.yml) is green for the exact published commit. The [workflow](../.github/workflows/verify.yml) runs the same entry point; a local pass does not establish remote CI status.

## Website and links

- [ ] The [site](https://hackathon.dappgo.com/) and [results explorer](https://hackathon.dappgo.com/explorer/) load while signed out. Check a saved claim, its filing excerpt, and its original-filing link; keep the saved-replay description clear. ([Site build record](site/BUILD_SUMMARY.md).)
- [ ] Replace `VIDEO_URL_PENDING` in the [submission draft](SUBMISSION.md#links) and private publication copy. Update pending video references in the [README](../README.md#try-it), [judge guide](../JUDGES.md#60-second-path), and [opening handoff](../demo/JUDGE_INTRO.md) with the same public URL.
- [ ] Project, repository, explorer, and video URLs resolve from the form preview and video description while signed out. No placeholder or local-only path remains in public copy. Run `python3 scripts/check_links.py` after final documentation edits; [external checking](../scripts/check_links.py) reports blocked/unverifiable HTTP responses separately, so inspect those links rather than treating them as verified.

## Video

- [ ] The final video is public on YouTube or Vimeo, playable while signed out, and no longer than **3:00 including the opening disclosure** (submission requirement supplied by the Owner; recheck in the authenticated [form](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit)). Measure the actual uploaded cut. The [approved render record](../demo/runs/20261029T054349020504Z-v006.json) is not evidence of the length of a later edit.
- [ ] Before the product opening, the uploaded cut visibly or audibly states: **“Nothing in this repository pre-existed the hackathon.”** Follow the [opening disclosure](../demo/JUDGE_INTRO.md). That handoff states the disclosure has not been rendered into the approved video; description text alone does not complete this item.
- [ ] The final title, description, chapters, captions, and on-screen results match the uploaded cut and [recorded evidence](SUBMISSION.md#recorded-results). Keep corrected-gold, development-set, and post-hoc labels wherever those results appear; preserve [media attribution](../CREDITS.md#media-and-dependencies).

## Form and team

- [ ] Paste the [field-by-field draft](SUBMISSION.md#field-by-field-form-draft) into the actual form, adapting only to its labels and limits. Complete Owner name, email, profile, and video URL; review the full preview for unresolved placeholders.
- [ ] Record the team as **solo**, using the Owner's participating account; no additional teammates are claimed.
- [ ] The new-work disclosure matches the [build log](../BUILD_LOG.md#build-log) and [dated history](../CHANGELOG.md): all repository code and demo work were created during the hackathon; the existing DappGo product's code is outside this submission.

## Deadline

- [ ] The Owner submits by **Wednesday, November 4, 2026, 9:00 PM ET**. The [event's Key Dates](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit) lists the submission deadline; recheck the event/form for any update. The [repository build window](../BUILD_LOG.md#build-log) ends on that date.
- [ ] After submitting, the Owner saves the confirmation and checks that the submitted repository, site, video, and solo-team details match the reviewed preview.
