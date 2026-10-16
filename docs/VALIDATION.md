# Validation record

Validated on 15 October 2026 with Python 3.12.14 and Chromium in the cloud development environment.

## Completed checks

| Check | Outcome |
|---|---|
| Locked dependency installation and repeat installation | Passed |
| `pip check` | No broken requirements |
| `python -m pytest -q` | 22 passed; no failures or skips |
| Application startup | Uvicorn starts successfully on loopback port 8000 |
| Live health request | HTTP 200; local LSA engine reported |
| Live functional hybrid search | Employee handbook returned first for `vacation policy`, with source evidence |
| Automated Chromium scenario | Passed; no JavaScript runtime errors |
| Narrow screen layout | Passed at 390 × 844, with no horizontal overflow |

The dependency stack emits one Starlette/AnyIO deprecation warning about `BlockingPortal`; it did not affect execution. This is recorded rather than suppressed.

## Backend suite coverage

Eleven extension cases exercise extraction and searchable contents: TXT, MD, CSV, JSON, HTML, HTM, PDF, DOCX, PPTX, XLSX, RTF. Office and PDF payloads are generated as real file containers in the test suite. HTML and HTM are one format with two extensions.

Additional checks cover:

- document upload → keyword/semantic/hybrid search → evidence → deletion;
- query expansion finding “holiday” content for “vacation,” where keyword mode returns no match;
- persistent records after reloading the application and reopening the database;
- unsupported files, empty text, malformed PDF/JSON, and upload size rejection;
- empty queries, invalid modes, alpha, threshold, and result-count bounds;
- hybrid weights 0 and 1 reproducing their corresponding individual ranking modes;
- document filters, result limits, strict minimum rank filtering;
- chunk overlap, empty libraries, the health endpoint, and HTML delivery.

These tests validate behavior, not general semantic relevance. The small synonym example is not a retrieval-quality benchmark.

## Browser scenario

`tests/browser_check.py` starts a separate server with a temporary database and cleans it up when finished. It exercises:

1. Initial explorer and healthy engine status.
2. Unsupported upload with a visible error.
3. Sample ingestion and immediate hybrid retrieval.
4. Evidence visibility and editable semantic weight.
5. Semantic mode retrieval.
6. Real browser file upload followed by exact keyword retrieval.
7. Library totals and document deletion confirmation.
8. Mobile viewport and horizontal-overflow assertion.
9. JavaScript runtime error collection.

Screenshots in `docs/screenshots/` were captured during this run and inspected for the desktop explorer. The current screenshots show sample data only.

## Limits and unrun checks

No production load, accessibility audit, hostile-file sandbox, arbitrary-corpus relevance benchmark, OCR, external model, or generated-answer quality tests were run. They are not shipped capabilities. The library has no authentication and is a local development service.

## Reuse and configuration

`install_script` and `start_skill` were saved in the cloud environment configuration draft. The install script uses the lockfile and backend tests. Startup instructions include loopback service startup, health verification, a representative search, persistent storage handling, and safe temporary-document cleanup. Saving these fields does not publish an environment or commit/push repository files. A fresh-task restoration has not been verified.

## Deployment preparation follow-up

After adding Vercel configuration and PostgreSQL storage, the full 22-test suite passed against both SQLite and a real PostgreSQL 17 instance. Browser validation was rerun against SQLite. Vercel production deployment was attempted but the CLI reported no existing credentials. Requests to Vercel domains also returned HTTP 403 under the current environment network policy. No cloud deployment URL or successful remote build is claimed.

## White-and-blue theme update

Changed the interface to light surfaces, blue controls and accents, and dark readable text, including uploads, parameters, results, evidence, library actions, and notifications. The complete browser scenario passed again with no JavaScript errors. Desktop (1440 px) and mobile (390 px) screenshots were regenerated and visually inspected; no horizontal overflow was detected.

## Hybrid Search Engine usability update

Renamed the product and API title to Hybrid Search Engine. Added first-use steps, a How to use dialog, plain-language mode explanations, a settings reset action, and an upload-to-search action. Technical retrieval scores remain available in expandable details. Mobile navigation now displays readable labels. Browser checks additionally verified help, mode descriptions and pressed states, disabling the irrelevant meaning slider in Keyword/Meaning modes, reset defaults, upload-to-search focus, and updated results after deletion. The full 22-test backend suite passed. Desktop and mobile screenshots were regenerated and visually inspected.

## Upload error and Supabase pooler follow-up — 16 October 2026

Disabled psycopg automatic prepared statements for transaction-pooler compatibility, removed NUL characters from extracted document text before storage, added safe JSON database/server errors with references, and replaced generic unreadable-response messages with HTTP-specific guidance.

SQLite: 27 tests passed, one PostgreSQL-only test skipped. Disposable PostgreSQL 17: all 28 tests passed, including repeated statements producing no prepared statements. Browser checks passed, including simulated non-JSON HTTP 500/413/504 responses, JSON database failures with references, and successful upload recovery afterward. Error tests confirmed internal exception text and a synthetic password were absent from responses and application log messages.

The reported live URL is https://hybrid-search-system.vercel.app/. Direct verification was blocked by the cloud environment's egress proxy (CONNECT HTTP 403), so the cause of the original live upload failure and post-deployment recovery remain unverified. The domain was added to the saved environment network draft for review; saving does not apply it to the running environment.
