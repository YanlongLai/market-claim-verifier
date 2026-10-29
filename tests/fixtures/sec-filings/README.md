# First-filing iXBRL for the site

These 11 complete SEC primary documents were downloaded from EDGAR on 2026-10-29.
They are losslessly gzip-compressed UTF-8 HTML, with no trimming, rewritten cells
or synthetic contexts. [The manifest](manifest.json) records the original URLs,
filing metadata, byte counts and SHA-256 hashes of both the HTML and gzip files.
The source is the **U.S. Securities and Exchange Commission, EDGAR**
([credits](../../../CREDITS.md), [data policy](../../../docs/DATA_SOURCES.md)).

The [site builder](../../../docs/scripts/build_site.py) selects each fact's first
accession from the [frozen companyfacts snapshots](../sec-offline/README.md),
extracts the original iXBRL row from these documents, and checks the displayed
value and filing date. Both years of growth comparisons and both components of
the derived Apple quarter are included. Recorded reports and benchmark results
remain unchanged; these documents correct the site's choice of displayed paper.
All first-filed values match the recorded checks; no comparative fallback is used.

Check every document and fact without network access:

```sh
python3 scripts/build_site_filing_fixtures.py --check
```

To record them again from SEC (downloads are maintenance, never verification):

```sh
python3 scripts/build_site_filing_fixtures.py --cache /tmp/site-first-filings
```

The [fixture reader](../../../docs/scripts/filing_excerpts.py) verifies hashes,
metadata and accession/URL agreement before using a document. Offline verification
does not read the author's ignored SEC cache.
