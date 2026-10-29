# SEC snapshots for cache-independent tests

These **23 trimmed public SEC companyfacts snapshots** support [generator tests](../../test_v2.py), the [Amazon period regression](../../test_eval_fixes.py), and the [stamp-card](../../test_site_stamps.py) and [gap](../../test_gap.py) regressions. The offline [site builder](../../../docs/scripts/build_site.py) uses them to revalidate post dates. The [stamp fixture](../../conftest.py) writes only to a temporary filing cache. They are test inputs, not a replacement benchmark or new gold answers. Existing benchmark claims/results are unchanged.

Each raw input was verified against the original snapshot hash in the [recorded v2 run manifest](../../../docs/evidence/eval-v2-2026-10-27/manifest.json). [provenance.json](provenance.json) records original and trimmed hashes. The [trimmer](../../../scripts/build_offline_fixtures.py) keeps the generator's US-GAAP concepts and rows ending on/after 2022-01-01, preserving their original fields and values; the ticker map is restricted to the [evaluation company inventory](../../../eval/v2/MANIFEST.json).

Verify the committed fixture hashes, with no cache or network:

```sh
python3 scripts/build_offline_fixtures.py --check
```

Maintainers who already possess the exact original snapshots can regenerate with `python3 scripts/build_offline_fixtures.py --cache <local-snapshot-directory>`. This regeneration is not required for tests or clean-clone verification. These files credit the **U.S. Securities and Exchange Commission, EDGAR** ([data policy](../../../docs/DATA_SOURCES.md), [credits](../../../CREDITS.md)).
