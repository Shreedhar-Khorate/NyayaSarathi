# NyayaSarathi OCR Integration Work Plan

## Objective

Integrate the completed standalone `OCR/` module into the existing NyayaSarathi project **without breaking the current application**.

The standalone `OCR/` folder is temporary. After successful integration and full testing, it must be deleted.

## Critical Rules

1. Work only on the OCR branch.
2. Do not delete the standalone `OCR/` folder until integration is verified.
3. Do not create a second FastAPI application.
4. Do not create a second React/Vite application.
5. Reuse NyayaSarathi's existing FastAPI and React architecture.
6. Keep OCR logic modular inside the existing architecture.
7. Do not rewrite working OCR algorithms unnecessarily.
8. Do not replace PaddleOCR.
9. Do not add handwriting OCR.
10. Preserve the working PaddleOCR/PaddlePaddle versions unless a real blocker requires change.
11. Do not redesign or implement RAG as part of this integration unless explicitly requested.
12. Do not log complete legal-document text unnecessarily.
13. Do not remove existing NyayaSarathi functionality.
14. Make small, reversible changes and test after each major step.

# Phase 1 — Inspect Existing NyayaSarathi

Before changing anything:
- Inspect the complete NyayaSarathi backend structure.
- Find the existing FastAPI entry point, routes, services, schemas/models, dependencies, tests, and configuration.
- Inspect the React/Vite structure and existing API-client/request pattern.
- Identify existing document upload functionality, if any.
- Identify the existing RAG entry point/interfaces.
- Do not assume paths.
- Record the discovered structure in `logs.md`.

# Phase 2 — Map Standalone OCR to NyayaSarathi

Standalone OCR contains:

```text
OCR/
├── prd.md
├── UP.md
├── log.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── schemas/
│   │   └── services/
│   ├── requirements.txt
│   └── tests/
└── frontend/
```

Important services:

```text
detector.py
pdf_extractor.py
docx_extractor.py
image_extractor.py
image_preprocessor.py
ocr.py
layout_analyzer.py
reading_order.py
document_processor.py
```

Map these into the existing NyayaSarathi architecture. The exact destination must follow the structure discovered in Phase 1.

Preferred conceptual structure:

```text
NyayaSarathi backend
├── existing routes
├── OCR route
├── existing services
└── legal_ocr/
    ├── detector.py
    ├── pdf_extractor.py
    ├── docx_extractor.py
    ├── image_extractor.py
    ├── image_preprocessor.py
    ├── ocr.py
    ├── layout_analyzer.py
    ├── reading_order.py
    └── document_processor.py
```

# Phase 3 — Integrate Backend

## Dependencies

Compare the standalone OCR dependency file with NyayaSarathi dependencies. Add only missing dependencies.

Preserve the currently working OCR versions:

```text
paddlepaddle==2.6.2
paddleocr==2.8.1
```

Do not blindly duplicate dependencies.

## OCR Services

Integrate the required OCR services and update imports carefully. Preserve:

```text
Document detection
        ↓
Digital text extraction
        ↓
Scanned-page preprocessing
        ↓
PaddleOCR
        ↓
Bounding boxes
        ↓
Layout analysis
        ↓
Reading-order reconstruction
        ↓
Unified OCR response
```

Do not remove page numbers, bounding boxes, confidence values, or reading-order information.

## OCR Route

Create an OCR route inside the existing FastAPI application, following existing naming conventions. Conceptually:

```text
POST /api/legal-documents/process
```

The route should validate the upload, call the OCR document processor, return the unified response, and use NyayaSarathi's existing error-handling pattern.

Do not create another `FastAPI()` instance.

## Register Route

Register the OCR router in the existing FastAPI application. Verify startup, existing routes, OpenAPI/docs, and imports.

# Phase 4 — Integrate Frontend

Do not keep the standalone OCR Vite application.

Reuse the existing NyayaSarathi React/Vite application and add only the required OCR UI:

```text
Upload document
      ↓
Send to OCR API
      ↓
Loading/progress
      ↓
Display extracted text
      ↓
Display useful document/page information
```

Follow existing components, API client, styling, routing, and error handling.

# Phase 5 — Backend Testing

Test existing functionality and OCR functionality:
- digital PDF
- scanned PDF
- mixed PDF if supported
- DOCX
- JPG/PNG
- invalid file type
- invalid/empty upload
- multi-page document

Verify the complete pipeline:

```text
Upload → Detection → Extraction/OCR → Layout → Reading Order → Unified Response
```

Most importantly, verify reading order remains correct after integration.

# Phase 6 — Frontend Testing

Verify document selection, upload, API request, loading state, error handling, extracted-text display, and existing frontend pages.

# Phase 7 — RAG Preparation

Do not redesign OCR for RAG. Preserve an interface that can later feed:

```text
OCR → Correct Reading Order → Structured Legal Text → Chunking → 3-Level RAG
```

Preserve useful metadata such as document ID, page number, text, bounding boxes, confidence, and structure where available.

# Phase 8 — Final Cleanup

Only after all integration tests pass:
1. Confirm no code imports from `OCR/...`.
2. Confirm no frontend code depends on `OCR/frontend`.
3. Confirm all required OCR files are in final NyayaSarathi locations.
4. Confirm dependencies are integrated.
5. Run tests/build checks.
6. Delete temporary `NyayaSarathi/OCR/`.
7. Run the complete checks again after deletion.
8. Commit the cleanup.

# Definition of Done

- [ ] Existing backend starts.
- [ ] Existing APIs still work.
- [ ] Existing frontend still works.
- [ ] OCR is part of the main FastAPI application.
- [ ] OCR services are integrated into the main backend.
- [ ] No duplicate FastAPI application remains.
- [ ] No duplicate React/Vite application remains.
- [ ] Digital PDFs work.
- [ ] Scanned PDFs work.
- [ ] DOCX works.
- [ ] Images work.
- [ ] Bounding boxes are preserved where applicable.
- [ ] Reading order remains correct.
- [ ] OCR errors are handled safely.
- [ ] Dependencies are integrated correctly.
- [ ] No code depends on the temporary `OCR/` folder.
- [ ] `OCR/` is deleted only after verification.
- [ ] Final tests/build pass after deletion.
- [ ] `logs.md` contains the complete integration history.

# Agent Working Style

Use:

```text
INSPECT → PLAN → SMALL CHANGE → TEST → LOG → NEXT CHANGE
```

Never make a large uncontrolled rewrite. If NyayaSarathi's existing conventions differ from the standalone OCR structure, adapt OCR to NyayaSarathi rather than duplicating architecture. If something is unclear, inspect the code first instead of guessing. Record every significant change in `logs.md`.
