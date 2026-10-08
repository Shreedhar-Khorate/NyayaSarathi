
Next Steps — Legal Document OCR & Extraction Module
1. Purpose
This document defines the next implementation phase for the existing standalone Legal Document OCR & Text Extraction Module.
This is a continuation of the current project. The existing implementation must not be rebuilt from scratch.
The current project already has:
- FastAPI backend
- React + Vite testing frontend
- File upload and validation
- PDF extraction using PyMuPDF
- DOCX extraction using python-docx
- Scanned PDF detection
- OpenCV/Pillow image preprocessing
- PaddleOCR integration
- Image extraction
- Unified Pydantic response schema
- CORS configuration
- Initial automated tests
The current development log states that Milestones 1–7 are complete and Milestone 8 (Testing) is in progress. fileciteturn0file0L109-L117
2. Current Technical Baseline
Backend
- Python
- FastAPI
- Uvicorn
- Pydantic
Document Processing
- PyMuPDF
- python-docx
- Pillow
- OpenCV
- NumPy
OCR
- PaddleOCR
- PaddlePaddle
The current stable OCR versions are intentionally locked to:
paddlepaddle==2.6.2
paddleocr==2.8.1
The project previously encountered a C++ runtime problem with PaddlePaddle 3.3.1 beta on Windows CPU, so the stable versions were selected. fileciteturn0file0L143-L149
Testing
- pytest
- pytest-asyncio
- httpx
Six tests are currently passing for the existing API and validation functionality. fileciteturn0file0L171-L183
3. Target Pipeline
PDF / DOCX / Court Scan
          |
          v
   Document Type Detection
          |
    +-----+-----+
    |           |
 Digital      Scanned
    |           |
    v           v
Direct       Preprocessing
Text             |
Extraction       v
    |         OCR Engine
    |           |
    +-----+-----+
          |
          v
    Layout Analysis
          |
          v
 Reading-Order
 Reconstruction
          |
          v
 Structured Legal Text
          |
          v
 Legal Metadata
 Extraction
The main focus is printed/typed legal documents, especially Indian court judgments and scanned court reports.
Handwritten OCR is not part of this project scope.
4. Phase A — Complete Milestone 8 Testing
Objective
Finish the testing work already planned in the current log.
The current log specifically identifies the next tests as:
- PDFExtractor
- DOCXExtractor
- DocumentProcessor
fileciteturn0file0L187-L195
A1. PDFExtractor Tests
Test:
- Single-page digital PDF
- Multi-page digital PDF
- Text extraction
- Page numbers
- Empty pages
- Scanned-page routing
- Mixed PDF
Expected:
Digital page -> direct extraction
Scanned page -> preprocessing + OCR
Mixed PDF    -> page-specific routing
A2. DOCXExtractor Tests
Test:
- Paragraph extraction
- Multiple paragraphs
- Tables
- Empty paragraphs
- Standardized output
A3. ImageExtractor Tests
Test:
- JPG
- JPEG
- PNG
- OCR invocation
- Unified response
A4. DocumentProcessor Tests
Verify:
.pdf  -> PDFExtractor
.docx -> DOCXExtractor
.jpg  -> ImageExtractor
.png  -> ImageExtractor
Also test unsupported formats.
A5. DocumentDetector Tests
Test:
- Text PDF
- Scanned PDF
- Mixed PDF
- Blank page
A6. Full Test Run
Use:
python -m pytest
The project already records that this is the reliable way to run tests when the Windows pytest.exe wrapper is blocked. fileciteturn0file0L179-L183
Definition of Done
- All existing tests pass.
- New extractor tests pass.
- Processor tests pass.
- Detector tests pass.
- No existing behavior is broken.
5. Phase B — Real Court Document Benchmark
After automated tests are stable, test with real printed Indian court documents.
Test Categories
test_documents/
├── digital/
├── scanned/
├── mixed/
├── docx/
└── images/
Include:
- Digital Indian Supreme Court judgment
- Scanned Supreme Court judgment
- Mixed PDF
- Multi-page scanned judgment
- Court document with headings
- Multi-column document where available
- Footnotes/page numbers
- Low-quality scans
- Tables where available
The benchmark must evaluate both:
1. Text recognition
2. Correct visual reading order
A page such as a Supreme Court report should preserve:
Citation
  ↓
Case Title
  ↓
Case Number
  ↓
Date
  ↓
Bench/Judges
  ↓
Issue for Consideration
  ↓
Issue paragraph
  ↓
Headnotes
  ↓
Headnote paragraph
6. Phase C — Inspect Raw PaddleOCR Output
Before implementing layout reconstruction, inspect the actual PaddleOCR output from a court page.
Create a temporary/debug script if needed:
scripts/inspect_ocr_output.py
It should expose:
- text
- confidence
- bounding boxes
- line/block position
Example:
{
  "text": "Sameem Begum and Others",
  "confidence": 0.98,
  "bbox": [200, 100, 700, 140]
}
Do not log the full legal document in application logs. The existing project decision is to avoid logging full legal document text by default. fileciteturn0file0L79-L97
7. Phase D — Layout Analysis
Create:
backend/app/services/layout_analyzer.py
The service receives OCR blocks and coordinates.
Initially identify approximate regions:
- Header
- Citation
- Case title
- Case number
- Date
- Bench/Judges
- Heading
- Paragraph
- Footer
- Page number
Start with deterministic geometry. Do not introduce an LLM for layout analysis.
8. Phase E — Reading-Order Reconstruction
Create:
backend/app/services/reading_order.py
Responsibilities:
1. Group blocks by page.
2. Detect simple columns/regions.
3. Group nearby blocks into lines/paragraphs.
4. Sort top-to-bottom.
5. Sort same-line content left-to-right.
6. Handle columns without jumping incorrectly between them.
7. Preserve headings before their paragraphs.
8. Preserve page boundaries.
Input:
OCR blocks + bounding boxes
Output:
ordered OCR blocks
Start with geometry-based ordering. Do not use an LLM for this first version.
9. Phase F — Structured Legal Text
Create:
backend/app/services/legal_structure.py
Potential output:
{
  "page_number": 1,
  "sections": [
    {
      "type": "citation",
      "text": "[2026] 9 S.C.R. 112 : 2026 INSC 864"
    },
    {
      "type": "case_title",
      "text": "Sameem Begum and Others v. K. Venkat Swamy and Another"
    },
    {
      "type": "case_number",
      "text": "Civil Appeal No. 10738 of 2026"
    },
    {
      "type": "date",
      "text": "14 August 2026"
    },
    {
      "type": "bench",
      "text": "..."
    },
    {
      "type": "heading",
      "text": "Issue for Consideration"
    },
    {
      "type": "paragraph",
      "text": "..."
    },
    {
      "type": "heading",
      "text": "Headnotes"
    },
    {
      "type": "paragraph",
      "text": "..."
    }
  ]
}
Do not assume every legal document contains all fields.
10. Phase G — Legal Metadata Extraction
Create:
backend/app/services/legal_metadata.py
Initial fields:
case_number
case_title
court
date
judges
parties
advocates
acts
sections
citations
Start with deterministic/rule-based extraction.
Examples:
- Civil Appeal No. 10738 of 2026 → case number
- 14 August 2026 → date
- Section 166 → legal section
- Motor Vehicles Act, 1988 → act
Do not use an LLM for simple pattern extraction.
11. Phase H — Extend Unified API Response
The unified response is already implemented. The project log confirms that extractors return the same structure and the frontend consumes the standardized text field. fileciteturn0file0L203-L239
Only extend it when necessary.
Possible future structure:
{
  "document_id": "...",
  "filename": "...",
  "document_type": "scanned_pdf",
  "status": "completed",
  "pages": 10,
  "extraction_method": "paddleocr",
  "text": "...",
  "pages_data": [],
  "legal_metadata": {
    "case_number": "...",
    "case_title": "...",
    "court": "...",
    "date": "...",
    "judges": [],
    "parties": [],
    "acts": [],
    "sections": []
  }
}
Maintain backward compatibility.
12. Phase I — OCR Quality Evaluation
Create:
backend/evaluation/
├── ground_truth/
├── outputs/
└── evaluate_ocr.py
Evaluate:
- Text recognition
- Reading order
- Layout preservation
CER
CER =
Edit Distance(reference, prediction)
-------------------------------------
Number of reference characters
WER
WER =
Substitutions + Deletions + Insertions
---------------------------------------
Number of reference words
Do not claim an OCR accuracy percentage without a defined ground-truth dataset.
13. Phase J — Reading-Order Evaluation
Create manually verified expected sequences for benchmark pages.
Example:
1. Citation
2. Case title
3. Case number
4. Date
5. Bench
6. Issue heading
7. Issue paragraph
8. Headnotes heading
9. Headnote paragraph
A test should fail if the words are recognized correctly but returned in the wrong order.
14. Phase K — Update log.md
Do not delete or rewrite historical entries.
Append a new dated entry after each meaningful milestone:
## YYYY-MM-DD — Layout Analysis

### Completed
- ...

### Files Changed
- ...

### Tests
- ...

### Issues
- ...

### Decisions
- ...

### Next Step
- ...
This matches the existing development-log structure. fileciteturn0file0L121-L135
15. Exact Implementation Order
Follow this sequence:
1. Read log.md
        ↓
2. Inspect current codebase
        ↓
3. Run existing tests
        ↓
4. Fix existing failures
        ↓
5. Complete extractor tests
        ↓
6. Complete DocumentProcessor tests
        ↓
7. Complete DocumentDetector tests
        ↓
8. Test real court scan
        ↓
9. Inspect raw PaddleOCR output
        ↓
10. Implement LayoutAnalyzer
        ↓
11. Implement ReadingOrder
        ↓
12. Test reading order
        ↓
13. Implement Structured Legal Text
        ↓
14. Implement Legal Metadata
        ↓
15. Extend API schema carefully
        ↓
16. Run full regression tests
        ↓
17. Evaluate real court documents
        ↓
18. Update log.md
16. Expected New Files
Only create files that are actually required.
Likely:
backend/app/services/
├── layout_analyzer.py
├── reading_order.py
├── legal_structure.py
└── legal_metadata.py
Tests:
backend/tests/
├── test_layout_analyzer.py
├── test_reading_order.py
├── test_legal_structure.py
├── test_legal_metadata.py
├── test_pdf_extractor.py
├── test_docx_extractor.py
└── test_document_processor.py
Evaluation:
backend/evaluation/
└── evaluate_ocr.py
17. Do Not Do These Yet
Do not:
- Rebuild FastAPI.
- Rebuild the upload system.
- Redesign the React UI.
- Replace the unified schema unnecessarily.
- Upgrade PaddleOCR/PaddlePaddle without testing.
- Add handwriting OCR.
- Add an LLM for basic OCR/layout.
- Add RAG yet.
- Add a vector database yet.
- Add authentication yet.
- Add a database yet.
- Remove existing tests.
- Rewrite historical log.md entries.
18. Definition of Done
The phase is complete when:
Testing
- [ ] PDFExtractor tests pass
- [ ] DOCXExtractor tests pass
- [ ] ImageExtractor tests pass
- [ ] DocumentProcessor tests pass
- [ ] DocumentDetector tests pass
- [ ] Full test suite passes
OCR
- [ ] Digital PDFs bypass OCR
- [ ] Scanned PDFs use OCR
- [ ] Mixed PDFs route pages correctly
- [ ] OCR confidence is preserved
- [ ] Bounding boxes are preserved
Layout
- [ ] OCR blocks are analyzed spatially
- [ ] Single-column documents work
- [ ] Basic multi-column documents work
- [ ] Reading order is reconstructed
- [ ] Page boundaries are preserved
Legal Structure
- [ ] Headings can be identified where reliable
- [ ] Paragraphs remain grouped
- [ ] Case information remains ordered
- [ ] Structured legal text is generated
Metadata
- [ ] Case number extraction works for supported patterns
- [ ] Date extraction works for supported patterns
- [ ] Case title extraction works where reliable
- [ ] Judge/bench extraction works where reliable
- [ ] Acts/sections extraction works where reliable
Documentation
- [ ] log.md updated
- [ ] Test results recorded
- [ ] Known limitations recorded
19. What Comes After This Phase
Do not immediately start RAG.
The recommended progression is:
Testing
   ↓
Layout Analysis
   ↓
Reading Order
   ↓
Structured Legal Text
   ↓
Legal Metadata
   ↓
OCR Evaluation
   ↓
Document Chunking
   ↓
Embeddings
   ↓
Vector Database
   ↓
RAG
   ↓
Legal Q&A
The extraction layer should be reliable before the AI layer is added.
20. Final Target
The standalone module should eventually accept:
scanned Indian court judgment.pdf
and produce:
Document Type
      ↓
Scanned PDF
      ↓
OCR
      ↓
Correct reading order
      ↓
Structured legal text
      ↓
Legal metadata
The final objective is:
Convert an unstructured scanned or typed legal document into a structured, page-aware, correctly ordered legal representation that can later be safely consumed by the Legal AI/RAG layer.