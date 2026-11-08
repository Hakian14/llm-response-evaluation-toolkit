# Graded sample 01 — General assistant · technical Q&A

Rubric: [`general_assistant_v1`](../../rubrics/general_assistant_v1.yaml) · Grader: Ha Kieu Anh

## Task

**User prompt**

> I have a pandas script that reads a 2 GB CSV and it takes about 4 minutes just to load. How can I make it faster? I'm on a laptop with 16 GB RAM.

**Model response (graded verbatim)**

> Here are the main ways to speed up reading a large CSV with pandas:
>
> 1. **Use `low_memory=False`** — `pd.read_csv("file.csv", low_memory=False)` lets pandas read the file in one pass instead of chunks, which is faster.
> 2. **Specify dtypes and only the columns you need** — passing `dtype={...}` and `usecols=[...]` avoids type inference and skips columns you never use. This is usually the single biggest win.
> 3. **Switch to the PyArrow engine** — `pd.read_csv("file.csv", engine="pyarrow")` is 10–20× faster than the default C engine in every case.
> 4. **Read in chunks** — use `nrows=1_000_000` to process the file one million rows at a time so it never has to fit in memory.
> 5. **Convert to Parquet once** — read the CSV one time, save with `df.to_parquet()`, and load the Parquet file from then on. Parquet is columnar and compressed, so loads take seconds.
> 6. **Use Dask for anything bigger** — Dask is included with pandas by default and lets you work on data larger than RAM with the same API.
>
> Start with 2 and 3; that alone usually brings a 4-minute load down to well under a minute.

## Before reading the response: what a complete answer needs

- Measure first: is the 4 minutes parsing (dates, inference), I/O, or memory pressure/swapping? (16 GB with a 2 GB CSV can mean a 6–10 GB DataFrame.)
- The high-impact levers: `usecols`, explicit `dtype` (and `category` for low-cardinality strings), `engine="pyarrow"` or `dtype_backend="pyarrow"`, avoiding `parse_dates` on many columns (parse after load with a known format).
- Convert once to Parquet.
- Chunking via `chunksize` when the full frame does not fit.
- Honest expectation-setting: speed-ups depend on the file (many text columns vs numeric).

## Scores

| Dimension (weight) | Score | Evidence |
|---|---|---|
| Instruction following (2.0) | **4** | Answers the question asked, in the asked form (a list of concrete changes). Loses a point for ignoring the stated 16 GB constraint: item 1 *increases* peak memory and item 4 does not do what it claims for memory. |
| Factual accuracy (2.0) | **2** | Three errors, two of them consequential. (a) `low_memory=False` does not make reading faster; it reads the whole file into memory before inferring types — on this laptop it is more likely to cause swapping. (b) `nrows=1_000_000` reads **only the first million rows**; the chunking parameter is `chunksize`. A user following this would silently lose 90% of their data. (c) Dask is **not** included with pandas; it is a separate install. Item 3's "10–20× faster in every case" is over-claimed; it is often 2–5× and depends on the data. Items 2 and 5 are correct. |
| Reasoning and depth (1.5) | **3** | Lists options but never asks *why* it is slow — no mention of measuring, of date parsing (the most common cause of multi-minute loads), or of memory pressure. The closing prioritisation ("start with 2 and 3") is sound. |
| Completeness (1.5) | **3** | Covers the essentials (dtypes, usecols, pyarrow, Parquet). Omits `parse_dates`/`format`, `category` dtype, and the diagnose-first step an expert would lead with. |
| Safety (1.0) | **5** | Benign technical request, handled appropriately. |
| Clarity and formatting (1.0) | **4** | Well-structured numbered list, bold leads, correct length. Minor: item 6 is an aside that dilutes the list. |

**Weighted score: 3.33 / 5 (normalised 0.58)** — computed with `rubric.weighted_score`; no gate triggered.

## Overall verdict

A fluent, well-organised answer that would cost the user data if followed literally. The structure and the two strongest recommendations are right, which is exactly why the errors are dangerous: nothing about the response signals that items 1, 4 and 6 are wrong. The `nrows` error alone should keep this response out of any "preferred" bucket.

## Calibration note

Where another grader might differ: some would score **instruction following 5** on the grounds that every instruction was followed. I hold it at 4 because the prompt stated a constraint (16 GB) that the response contradicts twice — following instructions includes not undermining the stated constraints. Factual accuracy at 2 rather than 1: the *central* recommendation (dtypes + pyarrow) is correct, so the response is not "built on a false claim"; it is a correct answer with several wrong attachments.

What I verified: ran `pd.read_csv(..., nrows=1_000_000)` on a 3M-row file to confirm it returns only 1M rows; checked the pandas documentation for `low_memory`; confirmed Dask is a separate package.
