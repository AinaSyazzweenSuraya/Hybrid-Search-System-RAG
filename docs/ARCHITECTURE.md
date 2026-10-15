# Architecture and operational limits

## Request flow

1. Browser submits one file per multipart request, with chunk size and overlap.
2. FastAPI checks extension and a 10 MiB input limit. ZIP-based Office files also have a 50 MiB declared expanded-size limit. PDFs have a 500-page limit. Extracted text is capped at two million characters per document.
3. Format parsers extract plain text. Whitespace-separated windows become passages with stable UUIDs, document IDs, and one-based passage numbers.
4. A SQLite transaction writes metadata and all passages together. Only extracted text is retained. SQL uses bound parameters.
5. Search reads the selected corpus and computes keyword and semantic scores. The server returns passages and evidence; the browser renders untrusted content with DOM text nodes rather than HTML.
6. Deletion atomically removes metadata and all associated passages.

## Retrieval mathematics

BM25 uses lowercase Unicode word tokens, `k1=1.5`, and `b=0.75`. For each query term:

`IDF = ln(1 + (N - df + 0.5) / (df + 0.5))`

`score += IDF * tf * (k1 + 1) / (tf + k1 * (1 - b + b * length / average_length))`

Semantic retrieval fits TF-IDF unigrams and bigrams with sublinear term frequency over the current candidate corpus. A deterministic truncated SVD (`random_state=42`, up to 128 components, bounded by corpus dimensions) projects passages and the query into a shared latent space. L2-normalized projected vectors use cosine similarity, clipped at zero. With fewer than three corpus dimensions the implementation uses expanded TF-IDF cosine instead of SVD. Empty vocabularies return zero semantic scores.

A small explicit synonym map expands concepts such as car/automobile/vehicle and holiday/vacation/leave. See `CONCEPTS` in `app/engine.py` for the complete map. This aids cold starts but can also introduce irrelevant matches, especially ambiguous terms such as “leave.” LSA learns co-occurrence rather than understanding language like a pretrained transformer. No claim of universal semantic equivalence is made.

Each channel ranks positive matches. Its normalized reciprocal-rank score is `61 / (60 + rank)`; nonmatching passages contribute zero. Hybrid fusion is `(1-alpha) * keyword_rank_score + alpha * semantic_rank_score`. The result threshold is applied after fusion. Individual BM25 and semantic cosine scores are returned for inspection. The displayed fused score is neither an answer confidence nor a calibrated similarity.

## RAG boundary

The evidence payload selects up to three returned passages, each with a citation number, filename, passage position, and text. It is suitable as context for a separately implemented RAG generator. This release deliberately exposes source text instead of pretending to generate an answer. Passage numbers refer to ingestion windows, not original PDF pages or spreadsheet cell locations.

## Persistence and scale

Local SQLite or optional persistent PostgreSQL runs one transaction per upload or deletion. Vercel requires PostgreSQL via DATABASE_URL. Connections have a 30-second lock timeout. The database survives process restarts; browser state does not. Use one Uvicorn worker for this development workflow. Index vectors are reconstructed at search time, so latency and memory grow with library size. This is intended for small development collections, not millions of passages. The current implementation has no background ingestion queue or cancellation. Large or malicious parser inputs can still consume CPU despite size limits.

## Security and privacy

- No authentication, authorization, rate limiting, malware scanning, tenant separation, or TLS termination is included. Bind to `127.0.0.1` for development. Add these capabilities before shared or internet-facing deployment.
- Do not upload untrusted files in a privileged environment. Size and ZIP checks are defense in depth, not a parser sandbox.
- Raw filenames are reduced to basenames. Source text and filenames are rendered as text, not executable HTML. Search and SQL parameters are validated or bound.
- No permissive cross-origin policy is enabled. There is no external AI or font traffic.
- SQLite contains readable document text. Disk encryption and backups are deployment responsibilities. Deletion removes live records; deleted text may persist in storage pages and backups until secure maintenance.
- Legacy `.doc`, `.ppt`, `.xls`, scanned PDFs, embedded images, macros, charts, and OCR are unsupported. Password-protected files fail ingestion. XLSX uses cached values and does not execute formulas.

## Next production milestones

Evaluate retrieval quality with representative relevance labels before choosing embeddings or thresholds; add a pretrained embedding adapter and persistent vector index; add an optional grounded LLM generator with citation validation; add authentication, resource isolation, background ingestion, and deployment controls. These are future extensions, not tested features in this release.
