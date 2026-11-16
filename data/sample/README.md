`comtrade_sample.json` contains five unmodified trade records and seven related product definitions from UN Comtrade, with source and retrieval metadata. It is an excerpt, not a complete API response. Regenerate it with `python ingest/fetch.py --write-sample`.

The verified October 28, 2026 run retrieved 1,649 unique U.S. monthly import records across the requested October 2024–September 2026 window, plus the HS reference catalogue. August and September 2026 returned empty arrays. One HTTP 429 was retried successfully; no partitions failed and no records were missing required fields. Eight offline failure-handling tests also passed.

Full responses, counts, and logs are in `data/raw/20261028T143410640631Z/` locally. `data/raw/` is already excluded from Git. The small sample is intended for version control.

Source: [UN Comtrade](https://comtrade.un.org/). Limited publication follows its [redistribution policy](https://uncomtrade.org/docs/re-dissemination-of-data/).
