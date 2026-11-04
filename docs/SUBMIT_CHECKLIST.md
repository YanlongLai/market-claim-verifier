# Pre-submission checklist

The Owner completes these publication checks for the exact code and video being submitted through [Cerebral Valley](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit). The [submission draft](SUBMISSION.md) is ready for review; account and video placeholders still need completion.

## Repository and verification

- [ ] The [repository](https://github.com/YanlongLai/market-claim-verifier) is public and the intended submission commit is accessible while signed out. Private drafts and generated local outputs remain excluded by the [ignore rules](../.gitignore).
- [ ] `UV_OFFLINE=1 sh scripts/verify.sh` passes on that commit, including both Python suites, standalone Node tests, figure checks/rebuild, byte-identical data rebuilds, and local Markdown links. Follow the [prerequisites and expected final output](../AGENTS.md#offline-verification); [the runner](../scripts/verify.py) enforces offline verification without credentials.
- [ ] [Offline verification CI](https://github.com/YanlongLai/market-claim-verifier/actions/workflows/verify.yml) is green for the exact published commit. The [workflow](../.github/workflows/verify.yml) runs the same entry point; a local pass does not establish remote CI status.

## Website and links

- [ ] The [site](https://hackathon.dappgo.com/) and [results explorer](https://hackathon.dappgo.com/explorer/) load while signed out. Check a saved claim, its filing excerpt, and its original-filing link; keep the saved-replay description clear. ([Site build record](site/BUILD_SUMMARY.md).)
- [ ] Replace the video placeholders in the [submission draft](SUBMISSION.md#links), [video metadata](VIDEO_METADATA.md), and private publication copy. Update pending video references in the [README](../README.md#try-it), [judge guide](../JUDGES.md#60-second-path), and [opening handoff](../demo/JUDGE_INTRO.md) with the same public URL.
- [ ] Project, repository, explorer, and video URLs resolve from the form preview and video description while signed out. No placeholder or local-only path remains in public copy. Run `python3 scripts/check_links.py` after final documentation edits; [external checking](../scripts/check_links.py) reports blocked/unverifiable HTTP responses separately, so inspect those links rather than treating them as verified.

## Video

- [ ] The final video is public on YouTube or Vimeo, playable while signed out, and no longer than **3:00 including the opening disclosure** (submission requirement supplied by the Owner; recheck in the authenticated [form](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit)). Measure the actual uploaded cut. The [approved render record](../demo/runs/20261029T054349020504Z-v006.json) is not evidence of the length of a later edit.
- [ ] Before the product opening, the uploaded cut visibly or audibly states: **“Nothing in this repository pre-existed the hackathon.”** Follow the [opening disclosure](../demo/JUDGE_INTRO.md). That handoff states the disclosure has not been rendered into the approved video; description text alone does not complete this item.
- [ ] The final title, description, chapters, captions, and on-screen results match the uploaded cut and [recorded evidence](SUBMISSION.md#recorded-results). Keep corrected-gold, development-set, and post-hoc labels wherever those results appear; preserve [media attribution](../CREDITS.md#media-and-dependencies).

## Actual form fields

- [ ] Team Name — `DappGo`.
- [ ] Team Members — `Yanlong (solo)`; no additional teammates are claimed.
- [ ] Which track are you submitting to? — `Indie Developer Track`.
- [ ] Which problem statement did you build towards? — `Build for Your World`.
- [ ] Most Viral Track — X post link — paste the published X URL.
- [ ] Public GitHub Repository — paste `https://github.com/YanlongLai/market-claim-verifier`.
- [ ] 3-Minute Demo Video — paste the public YouTube/Vimeo URL.
- [ ] Partner technologies feedback — paste the answer at **≤150 characters**.
- [ ] How likely to build with Meta Model API? — paste the selected response.
- [ ] Overall opinion of Meta Model API — paste the selected response.
- [ ] Permission checkbox — accept it.
- [ ] Recommend Meta Model API (0–5) — paste the selected score.
- [ ] Recommend Muse Code (0–5) — paste the selected score.
- [ ] Biggest obstacle — paste the selected response and evidence-backed explanation.
- [ ] Compared with other models for this work — paste the selected response.
- [ ] What matters most when choosing a model — paste the selected response.
- [ ] Hardest part of switching models — paste the selected response.
- [ ] What would stop production use — paste the selected response.
- [ ] Project Description — paste the answer at **≤3,000 characters**; its first two lines must retain the headline result.
- [ ] Describe your use of Meta products — paste the answer at **≤3,000 characters**.
- [ ] Why are Meta's models important to your solution? — paste the answer at **≤3,000 characters**.
- [ ] Complete any account name, email, profile, or other required form controls not represented in the draft; review the full preview for unresolved placeholders.
- [ ] The new-work disclosure matches the [build log](../BUILD_LOG.md#build-log) and [dated history](../CHANGELOG.md): all repository code and demo work were created during the hackathon; the existing DappGo product's code is outside this submission.

## Last 90 minutes — do these in order

1. Upload the final public video, confirm it is no longer than 3:00, and confirm the opening disclosure is visible or audible.
2. Set the YouTube title, description, chapters, links, tags, and captions from [VIDEO_METADATA.md](VIDEO_METADATA.md).
3. Publish the X post and copy its public URL.
4. Open the authenticated form and confirm the team, track, problem statement, and solo-member entries.
5. Paste the X URL, repository URL, and public video URL.
6. Paste the partner feedback, permission, scores, and remaining short-form answers.
7. Paste the three long answers, check the 3,000-character limits, and run the English-only test.
8. Review the complete form preview for the evidence scope, corrected-gold label, disclosure, and missing placeholders.
9. Submit by **Wednesday, November 4, 2026, 18:00 PT (21:00 ET)** and save the confirmation.
10. Post the [Discord announcement](VIDEO_METADATA.md#discord-announcement) with the final public video URL.

## Deadline

- [ ] The Owner submits by **Wednesday, November 4, 2026, 18:00 PT (21:00 ET)**. The [event's Key Dates](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit) lists the submission deadline; recheck the event/form for any update. The [repository build window](../BUILD_LOG.md#build-log) ends on that date.
- [ ] After submitting, the Owner saves the confirmation and checks that the submitted repository, site, video, and solo-team details match the reviewed preview.
