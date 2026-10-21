# Task: Debug, Fix, and Validate the Contract Red-Flag Analyzer in NyayaSarathi

You are working on my existing **NyayaSarathi** project. Your task is to investigate and fully fix the Contract Red-Flag Analyzer feature, not merely suggest changes.

## CRITICAL RULE #1 — READ `logs.md` FIRST

Before inspecting, editing, running, or creating any other project file:

1. Locate and read the project's existing `logs.md` from the repository root.
2. If it is not present at the root, search for it and determine whether an existing project-level log file is used elsewhere. Do not create a duplicate until you have checked.
3. Read the complete relevant log history, including previous debugging attempts, implementation decisions, known issues, test failures, and unfinished tasks.
4. Treat the existing logs as project context. Avoid repeating failed approaches or undoing previously completed work.
5. After reading the logs, append a new timestamped entry to `logs.md` stating the task, investigation plan, and current Git branch. Do not overwrite existing log entries.
6. Continue updating `logs.md` as the investigation progresses and after each meaningful implementation or testing milestone.
7. At completion, append a final summary covering the root cause, files changed, fixes implemented, commands executed, test results, unresolved issues, and any remaining manual verification.

**Logging requirements:**
- Use the existing `logs.md` format if one exists.
- Keep entries concise but sufficiently detailed for another developer to understand the investigation.
- Record actual outcomes, not planned or assumed outcomes.
- Never claim a test passed unless you ran it and observed the result.
- Never record secrets, access tokens, passwords, API keys, JWTs, or sensitive contract contents in logs.
- Do not replace or delete historical entries.
- If logging itself fails, report that explicitly and retry safely.

## CRITICAL RULE #2 — INSPECT BEFORE MODIFYING

After reading `logs.md`, inspect the repository and understand the existing implementation before making changes.

Relevant files include, but are not limited to:

- `backend/routers/contracts.py`
- `backend/schemas/contracts.py`
- `backend/services/contracts_service.py`
- `backend/services/ocr/pdf_extractor.py`
- `backend/services/user_repository.py`
- `backend/tests/test_contracts.py`
- `nyayasarathi-app/src/app/contracts/page.tsx`
- Any related database models, migrations, configuration, AI prompts, provider integrations, shared components, and existing tests.

Also inspect:
- The Git working tree, current branch, and recent relevant commits.
- Existing API request and response schemas.
- The complete analysis pipeline, including text extraction, document classification, AI-generated findings, quote verification, deterministic heuristics, risk scoring, executive summary generation, persistence, and frontend rendering.
- Existing error handling, authentication, activity logging, and database fallback behavior.
- Existing dependencies and test conventions.

Do not assume the described architecture is fully accurate. Verify it against the source code.

**Git safety:** Preserve unrelated user changes. Do not reset, clean, force-push, or discard user work. Do not modify unrelated features. Do not commit changes unless explicitly requested.

## 1. REPRODUCE THE ACTUAL BUG

The reported issue is that uploading a Bombay High Court judgment produced:

- Overall Risk Profile: LOW RISK
- Generic text claiming the document contains potentially risky indemnification, liability, restrictive covenant, or renewal clauses.
- High, Medium, and Low finding counts all equal to zero.
- “No Red Flags Found in this View.”
- An executive summary that does not correspond to the uploaded document.

The uploaded document was a Bombay High Court judgment titled `Roma_Rajesh_Tiwari_vs_Rajesh_Dinanath_Tiwari_on_12_October_2017.PDF`, concerning interim maintenance under Section 24 of the Hindu Marriage Act.

This is a judicial decision, not a commercial contract.

Investigate why the system classified it as a contract and why the summary, findings, counts, and overall risk profile disagree.

Reproduce the issue using a sanitized fixture or synthetic document where practical. Do not expose private document content in logs.

Trace the actual code path rather than fixing only the displayed badge.

## 2. ADD A DOCUMENT CLASSIFICATION GATE

Implement a reliable classification step before contract-specific risk analysis.

Support appropriate document types such as:

- Commercial contract or agreement
- Employment agreement
- Non-disclosure agreement
- Service or vendor agreement
- Lease or rental agreement
- Court judgment or judicial order
- Legal notice
- Legal opinion or legal memorandum
- Other legal document
- Unknown or insufficient content

Use a combination of document structure, extracted text, relevant legal terminology, and AI classification if the existing architecture supports it.

Examples of judicial-document indicators include:
- Court or tribunal name and case number
- Petitioner/respondent or appellant/respondent headings
- Judgment, order, writ petition, or appeal terminology
- Coram, judicial reasoning, and operative order sections

Do not classify a document as a contract simply because it contains legal language, statutory references, parties' names, monetary amounts, or words such as “agreement” in an unrelated context.

The classifier must return a structured result with:
- Document type
- Classification confidence, if supportable
- Brief evidence for the classification
- Whether contract risk analysis is applicable

Do not fabricate confidence scores. If classification is uncertain, use an explicit unknown or review-required state.

### Required audit statuses

Introduce compatible, explicit statuses such as:

- `COMPLETED`
- `DOCUMENT_TYPE_MISMATCH`
- `INSUFFICIENT_CONTENT`
- `PARTIAL_ANALYSIS`
- `FAILED`

Adapt these to existing project conventions rather than introducing unnecessary duplicate models.

### Expected behavior for a court judgment

The API should return a valid, structured response that the frontend can render, with semantics equivalent to:

- Document type: Court Judgment
- Contract audit status: Not applicable
- Overall risk profile: Not assessed
- Findings: None generated by contract-specific analysis
- Explanation: The uploaded document is a judicial decision rather than a commercial agreement.
- Next action: Upload a contract or agreement to perform a contract risk audit.

Do not label this document LOW RISK.

Do not treat zero findings as proof that the document is safe.

Do not run contract-specific heuristics on a judicial decision merely because the AI classifier is uncertain.

If classification is ambiguous, return an explicit review-required or insufficient-content result rather than a misleading risk assessment.

## 3. FIX THE COMPLETE BACKEND PIPELINE

Inspect and correct the flow in `contracts_service.py` and its dependencies.

### A. Ingestion and extraction

Preserve existing PDF, DOCX, TXT, and OCR support.

Verify:
- Empty and unreadable documents are rejected or reported clearly.
- Scanned PDFs are handled through the existing OCR pipeline.
- Page-level extracted text is preserved where available.
- Original page numbers and clause locations remain accurate.
- Extraction failures are distinguishable from a genuine document with no risky clauses.

Do not introduce a new OCR provider or dependency without a demonstrated need.

### B. Classification before analysis

Run document classification after sufficient text extraction and before the contract-specific AI audit or heuristic engine.

Do not allow downstream code to overwrite a mismatch status with `COMPLETED` or LOW RISK.

### C. AI findings and evidence grounding

Preserve and strengthen the existing verbatim-grounding checks.

Every finding must be tied to evidence in the actual uploaded document.

Validate:
- The quoted text exists in the extracted document, using an appropriately normalized comparison where necessary.
- The quote identifies the correct clause or page when available.
- The explanation actually relates to the cited text.
- The statutory provision or precedent is relevant to the alleged issue.
- Recommendations are connected to the finding.
- Invalid or unsupported findings are rejected or marked for review, with useful internal diagnostics.

Do not silently turn a document with rejected AI findings into a “safe” document.

If all proposed findings are rejected, determine whether the analysis can be completed reliably using existing deterministic checks. Otherwise return an explicit partial-analysis or review-required status.

Do not fabricate clauses, legal authorities, citations, page numbers, or legal conclusions.

### D. Indian-law heuristic engine

Review the existing heuristics for these categories:

1. Indemnity and allocation of liability
2. Post-termination restraints and non-compete provisions
3. Liquidated damages and penalties
4. Asymmetric limitations of liability
5. Unilateral modifications
6. Arbitrator appointment and dispute resolution
7. Unilateral termination and cure periods
8. Automatic renewal and lock-in
9. Payment terms and late-payment penalties
10. Intellectual property and confidentiality

Improve only what the investigation shows to be incorrect or incomplete.

Important legal safeguards:
- Do not treat every indemnity, termination-for-convenience clause, renewal clause, or liability cap as inherently unlawful.
- Distinguish commercial risk from legal invalidity.
- For Section 27 of the Indian Contract Act, 1872, distinguish post-contract restraints from potentially permissible restrictions during a contract and account for applicable legal exceptions and context.
- For Section 74, do not assert that proof of actual loss is invariably required in every case. Analyze reasonable compensation and the applicable legal principles.
- For arbitration provisions, assess the actual appointment mechanism and relevant statutory principles and precedent instead of relying only on keywords.
- Do not declare a clause void or unenforceable solely because a regex matched it.
- Where the law or its application is uncertain or fact-dependent, state the uncertainty.

Treat the analyzer as assistive legal intelligence, not a substitute for advice from a qualified advocate.

### E. Risk calculation and calibration

Trace the exact function that determines the overall risk profile.

Ensure:
- The score is based on validated findings from the current document.
- Unsupported or rejected findings do not inflate the score.
- A document mismatch cannot receive a LOW, MEDIUM, or HIGH contract-risk label.
- An extraction failure cannot be interpreted as zero risk.
- An incomplete analysis cannot silently become a completed low-risk assessment.
- No findings means “No red flags detected in the analyzed content,” not “This contract is safe.”
- Any numeric scoring, thresholds, or severity weighting remain consistent with the project's existing design and are documented.

Do not invent a new scoring model without first understanding the current one.

### F. Executive summary

Generate the executive summary from the final validated analysis result.

It must never use generic text that mentions categories not found in the document or findings that were not validated.

For mismatch, insufficient content, partial analysis, or failed analysis, show an appropriate status-specific explanation.

For completed audits, summarize actual findings, important limitations, and the analyzed scope.

## 4. KEEP THE API SCHEMA AND FRONTEND CONSISTENT

Inspect `backend/schemas/contracts.py`, `backend/routers/contracts.py`, and the frontend together before changing response fields.

Make backward-compatible changes where practical.

The response should clearly distinguish:
- Document classification
- Audit status
- Overall risk profile
- Validated findings
- Severity counts
- Executive summary
- Limitations or warnings
- Recommended next action

In `nyayasarathi-app/src/app/contracts/page.tsx`:

1. Display the document type and audit status.
2. Display “Not Assessed” instead of a risk badge when the audit is not applicable or not completed.
3. Show a clear explanation when a court judgment, legal notice, or other non-contract document is uploaded.
4. Provide a useful next action, such as uploading an appropriate agreement.
5. Keep severity filters and counts synchronized with the validated findings.
6. Avoid showing “No Red Flags Found” when analysis failed, was incomplete, or was not applicable.
7. Show “No red flags detected in the analyzed content” only for a successfully completed analysis with zero validated findings.
8. Remove unsupported generic executive-summary language.
9. Preserve upload functionality, authentication, progress indicators, search, copy controls, and other working UI behavior.
10. Handle older API responses gracefully if backward compatibility is necessary.

Ensure frontend state is reset appropriately when a new document is selected or an analysis fails, so results from a previous upload are not displayed for the new document.

## 5. VERIFY ACTIVITY LOGGING AND PERSISTENCE

Inspect `backend/services/user_repository.py`, the actual `user_activity_history` schema, and all code paths that write contract-analysis activity.

Confirm exactly which fields are stored and whether both Supabase and SQLite are genuinely supported fallbacks.

Ensure the activity log records the correct analysis outcome, including:
- Document filename, when appropriate
- Document type
- Audit status
- Overall risk profile only when assessed
- Validated red-flag count
- Creation timestamp

A mismatch or failed analysis must not be recorded as a successful LOW RISK audit.

Avoid persisting the full uploaded document or unnecessary sensitive contract text in activity metadata.

Preserve existing user isolation, authentication, database behavior, and fallback logic. Do not invent database columns or claim a migration exists unless it has actually been implemented.

If a schema change is required, implement the appropriate migration or backward-compatible storage strategy and document it.

## 6. ADD REGRESSION TESTS

Inspect the existing test suite before editing it. Preserve useful tests and conventions.

Add or update tests for at least these scenarios:

1. **Court judgment uploaded as a contract**
   - Classified as a court judgment.
   - Returns `DOCUMENT_TYPE_MISMATCH` or the project's equivalent.
   - Overall contract risk is not assessed.
   - No fabricated contract findings are returned.
   - The executive summary explains the mismatch.

2. **Valid commercial contract with no detected red flags**
   - Returns a completed audit only when analysis actually completes successfully.
   - Zero findings does not imply guaranteed legal safety.

3. **Explicit unilateral termination clause**
   - The actual clause is cited.
   - Severity and legal reasoning are supported by the text.

4. **Broad indemnity clause**
   - Evidence grounding is verified.
   - The analysis distinguishes commercial exposure from automatic legal invalidity.

5. **Post-termination non-compete**
   - The analysis considers Section 27 and applicable context without making unsupported blanket conclusions.

6. **Unreadable, empty, or incomplete PDF**
   - Returns a meaningful error, insufficient-content, or partial-analysis result.
   - Never returns LOW RISK simply because extraction failed.

7. **Scanned PDF**
   - Tests the existing OCR path or mocks it appropriately.

8. **AI returns fabricated clause quotes**
   - Unsupported findings are rejected.
   - The resulting status and summary remain accurate.

9. **AI provider failure**
   - Existing fallback behavior works correctly, or the API reports a clear partial/failure status.

10. **Frontend severity counts and filters**
    - Counts match the validated findings.
    - Mismatch and failure states do not show misleading empty-risk messages.

11. **Activity history**
    - The stored status matches the actual result.
    - Mismatch or failed analysis is not logged as LOW RISK.

12. **Mixed or ambiguous legal document**
    - Classification uncertainty is handled explicitly.

Use mocks or fixtures where necessary to keep tests deterministic and avoid live AI-provider calls. Do not require external API keys for ordinary unit tests.

Run the existing relevant test suite and any additional checks practical for the changed code.

Fix regressions introduced by your changes.

## 7. IMPLEMENTATION RULES

- Work within the existing project architecture.
- Read before editing; trace the actual cause before choosing a fix.
- Avoid unnecessary dependencies and broad refactors.
- Preserve unrelated user changes.
- Do not hardcode the sample judgment as a special-case filename or use document-specific text matching as the primary solution.
- Use general document classification and reliable status handling.
- Do not fabricate test results, legal authorities, or successful API calls.
- Do not claim zero-retention unless all relevant temporary files, logs, database records, caches, and provider behavior have been verified.
- Do not expose contract text or secrets in logs.
- Update `logs.md` throughout the task.

## 8. REQUIRED EXECUTION ORDER

Follow this order strictly:

1. Read the existing `logs.md` completely.
2. Append the initial investigation entry to `logs.md`.
3. Inspect Git status and current branch without modifying user work.
4. Read the relevant backend, schema, frontend, persistence, OCR, and test files.
5. Trace and reproduce the incorrect result.
6. Document the verified root cause in `logs.md`.
7. Implement document classification and explicit audit statuses.
8. Fix backend risk scoring, evidence validation, and executive summary consistency.
9. Fix frontend state handling, risk badges, counts, filters, and mismatch messages.
10. Correct activity-history persistence if required.
11. Add regression tests.
12. Run relevant backend tests, frontend checks, and any available integration tests.
13. Resolve failures caused by the implementation.
14. Review the final diff for accidental or unrelated changes.
15. Append the final results to `logs.md`.

If a test cannot run because a dependency, service, or environment variable is missing, record the exact blocker. Do not skip reporting it.

## 9. FINAL RESPONSE FORMAT

When finished, provide:

### Root Cause
The actual verified cause of the incorrect risk result.

### Changes Made
Files changed and what each change accomplishes.

### Validation
Commands executed, number of tests passed/failed, and frontend checks performed. Include only observed results.

### Logging
Confirm the path to `logs.md` and summarize the entries added.

### Remaining Issues
Any unresolved problems, limitations, or manual verification still required.

### Git Status
Current branch and a concise summary of changed files. Do not commit or push unless requested.

**Start by reading `logs.md`. Do not edit any other file before doing so. Then continue through the complete workflow and implement the fix.**