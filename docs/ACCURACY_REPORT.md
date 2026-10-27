# Retrieval and document-text accuracy investigation

## Reported issue

The user asked for panel clinics in Damansara and received an unrelated document. The actual clinic PDF and production database were not available in this workspace. No claim is made that the real document contains a Damansara clinic, or that the live deployment has been verified.

## Confirmed causes in the code

- Keyword queries included conversational filler such as “I want to know” and common words. Those words could rank unrelated documents.
- Filenames were not included in retrieval. A clinic administrator or paper title present only in the filename could not be found.
- LSA projection could produce a positive similarity even without expanded word evidence, especially in small collections. RRF promotes positive rankings without judging whether they actually answer the question.
- Section creation collapsed all whitespace, losing line breaks that help readers interpret lists and tables.
- DOCX extraction moved all tables after all paragraphs, changing their original order.

## Repeatable diagnostic fixture

`python scripts/evaluate_retrieval.py --output docs/accuracy-after.json`

The fixture has **12 fictional documents and 23 manually labelled queries**: 20 answerable queries and 3 no-answer queries. It includes literal words, filenames, simple synonyms, paraphrases, and clinic-location distractors. Fictional clinic names are test data, not recommendations or an approved clinic list.

| Mode | Before: correct first result | After: correct first result | Before: no-answer queries correctly empty | After: no-answer queries correctly empty |
|---|---:|---:|---:|---:|
| Keyword | 17/20 (85%) | 19/20 (95%) | 0/3 | 3/3 |
| Meaning | 16/20 (80%) | 19/20 (95%) | 0/3 | 3/3 |
| Hybrid | 17/20 (85%) | 19/20 (95%) | 0/3 | 3/3 |

On this fixture, Recall@3 and MRR@3 equal the first-result accuracy: every successful query ranks its expected document first, and unsuccessful queries fail to retrieve it within three results. Each answerable query has one labelled relevant document. The denominator for first-result accuracy excludes no-answer queries. Before/after query-level outputs are in `accuracy-baseline.json` and `accuracy-after.json`. The baseline was evaluated from the pre-change engine at commit `7da37e1` on exactly the same fixture.

**These are in-sample diagnostic results.** The fixes were developed using this fixture, not a blind held-out benchmark. The collection is tiny and synthetic, labels have not been independently reviewed, and general relevance percentages cannot be inferred from it. A 95% fixture result does not establish 95% accuracy on the user's clinic documents.

## Damansara case

The query “i want to know panel clinic in damansara area” is tested against a Damansara clinic, a Shah Alam clinic, and an unrelated Damansara shopping document. The correct clinic ranks first in all three search modes. Separate regression checks verify that a clinic section with no Damansara reference is marked as missing that query term.

The application may still return partial matches when no section satisfies the whole query. It now shows a visible warning listing absent words. It does not validate addresses or infer approval status. A word appearing in a section or filename is not proof that the clinic has the requested location.

## Changes

English and conversational filler is filtered, a small explicit singular-word map handles terms such as clinics/clinic, filenames are searched, and meaning scores blend expanded TF-IDF evidence with LSA. LSA-only projected matches are suppressed. Weighted normalized RRF remains the final fusion formula. Original source text is returned without inserting filename text into the displayed section.

Line breaks inside sections are preserved. DOCX tables remain between the paragraphs that originally surrounded them. This does not reconstruct PDF page layout or guarantee that extracted tables preserve every row/column relationship. Previously uploaded documents need deletion and re-upload to receive the extraction/section-formatting changes; ranking changes apply to their existing text automatically.

## Remaining demonstrated limitation

“How do I get my money back?” still fails to retrieve the refund document because the local semantic pipeline does not reliably understand that paraphrase. No new refund-specific synonym was added to make the benchmark pass. Pretrained embeddings may improve this, but would require a separately evaluated model/deployment change.

## Tests and real-data next step

Automated regressions cover clinic-location distractors, no-answer questions, filename search, missing-location disclosure, line-break preservation, and DOCX table order. The browser scenario tests the exact reported query against an isolated fictional library and checks the partial-match warning.

A real-data evaluation needs the user's actual source PDF, representative questions, and manually verified clinic names/locations or relevant source sections. It should also include locations absent from the document and ambiguous clinic names. Until those are evaluated, the system is a developing retrieval tool, not an authoritative clinic-directory service.
