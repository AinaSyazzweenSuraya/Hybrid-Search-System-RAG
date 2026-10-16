# GitHub and Vercel deployment

## Included configuration

- `api/index.py` exposes the FastAPI ASGI app to Vercel's Python runtime.
- `vercel.json` routes the UI, static assets, OpenAPI docs, and API requests to that app.
- `.python-version` selects Python 3.12.
- `.vercelignore` excludes the local virtual environment, extracted documents, tests, screenshots, and environment files from CLI uploads.
- `.gitignore` excludes credentials, local databases, and Vercel project bindings from Git.
- SQLite remains the default for local development. Set `DATABASE_URL` to use durable PostgreSQL. Vercel deployments refuse to start without it, rather than silently discarding uploaded documents in temporary storage.

## Deploy from GitHub

1. In Vercel, choose **Add New → Project** and import `AinaSyazzweenSuraya/Hybrid-Search-System-RAG`.
2. Use the repository root. The repository includes a Python function build configuration; no frontend build command or output directory is required.
3. Create or connect a PostgreSQL database using Vercel Marketplace (for example, Neon or Supabase), or use an existing PostgreSQL service. Use a pooled connection URL suitable for serverless workloads and the provider's TLS settings. Save it securely as **DATABASE_URL** in the Vercel project's environment variables for the desired deployment environments. Do not put the URL in source code or chat.
4. Deploy. The application creates its tables on the first database-backed request. The database role needs permission to create the `documents`, `chunks`, and index objects in its default schema.
5. Verify `/api/health`: it must return `status: ok` and `storage: postgresql`. Upload a small text document and search for a unique phrase. Revisit after a cold start to confirm the document persists. Delete the test document afterward.

GitHub integration can then deploy subsequent pushes automatically. Keep Vercel deployment protection enabled for private review. This app has a shared library, with no per-user access control: users who can reach it can read and delete indexed documents.

## CLI alternative

Use an authenticated Vercel CLI, select the intended account/team, and link this directory to the project. Configure `DATABASE_URL` securely in project settings, then:

```bash
npx vercel deploy --prod
```

For the coding agent to publish directly, provide a Vercel token securely through environment settings as `VERCEL_TOKEN`, and allow `api.vercel.com` and `vercel.com`. A token grants account access; use a token scoped to the intended team. Existing account/project selection still applies. Never commit the token or paste it into chat.

## Platform limits

Vercel functions have request-size and execution-duration limits. The app limits uploads to **4 MiB on Vercel** (10 MiB locally) to leave room for multipart overhead under the function request ceiling. A larger request may be rejected by Vercel before the application receives it. PDF extraction and corpus-wide LSA are synchronous operations and are intended for small development collections. Function bundle limits may require a different plan or a separate backend if the installed scientific Python stack exceeds the account's current limit. No successful Vercel cloud build is claimed until a deployment URL has been verified.

Moving from local SQLite to PostgreSQL starts a separate library; the local demo documents are not automatically migrated. Do not expose a public service with confidential data until application authentication and deployment controls have been reviewed.

## PostgreSQL validation

The same 22 backend tests were executed successfully against SQLite and a real disposable PostgreSQL 17 server. To reproduce against a disposable database:

```bash
TEST_DATABASE_URL=postgresql://localhost/neon_test .venv/bin/python -m pytest -q
```

**The PostgreSQL test fixture deletes records in the selected test database.** It refuses database names that do not end in `_test`. Never supply a production connection as `TEST_DATABASE_URL`.

## Troubleshooting uploads

The PostgreSQL adapter disables psycopg automatic prepared statements (`prepare_threshold=None`) for Supabase transaction-pooler compatibility. PDF text containing NUL characters is cleaned before insertion because PostgreSQL text columns cannot store NUL.

If an upload fails:

1. Open `/api/health`. A database failure now returns JSON with `DATABASE_UNAVAILABLE` and a safe reference. Check Supabase is active, the pooler username/host/password are correct, special password characters are URL-encoded, and `DATABASE_URL` is set for the active Vercel environment. Redeploy after updating variables.
2. Check Vercel runtime logs for the reference. Application error logs include an exception type and SQLSTATE when available, without raw connection details. Do not share passwords or full database URLs.
3. A non-JSON HTTP 413 response indicates the platform rejected the request size. HTTP 504 indicates a timeout. HTTP 500/502 may indicate a runtime startup or application failure; inspect Vercel logs rather than assuming a file-format problem.
4. If a tiny TXT upload succeeds while a particular PDF fails, try a smaller text-based PDF and check that the original has selectable text. Scanned PDFs need OCR outside the app.

The app cannot format errors emitted before its runtime starts; the frontend reports their HTTP status and recovery guidance instead.
