# Feature — OCR → Legal Research Integration

## Objective

Allow a user to process a legal document through OCR and directly send the resulting extracted text to the existing Legal Research module.

## Required Flow

Document Upload
    ↓
OCR
    ↓
Layout Analysis
    ↓
Reading Order
    ↓
Structured Legal Text
    ↓
Send to Legal Research
    ↓
Existing Document/RAG Pipeline
    ↓
Legal Research

## Requirements

1. Add a "Send to Legal Research" action after successful OCR.
2. Do not make the user upload the same document again.
3. Pass the OCR output to the existing Legal Research ingestion pipeline.
4. Preserve:
   - document name
   - document ID
   - page numbers
   - extracted text
   - OCR confidence where available
   - page/section metadata where available
5. Reuse the existing Legal Research/RAG ingestion logic.
6. Do not create a second RAG pipeline.
7. Do not duplicate document-processing logic.
8. Preserve the existing OCR reading-order implementation.
9. Show clear processing states:
   - OCR Processing
   - OCR Complete
   - Sending to Legal Research
   - Ready for Legal Research
10. If ingestion fails, show an error without losing the OCR result.
11. The user must be able to retry sending the OCR result to Legal Research without running OCR again.

## Backend Design

Create a clean integration boundary between:

OCR service
    ↓
Legal Research ingestion service

Prefer passing the structured OCR response rather than raw OCR strings.

The existing Legal Research/RAG processor should remain responsible for:
- document ingestion
- chunking
- embeddings
- indexing
- retrieval
- answering

OCR should remain responsible only for:
- validation
- extraction
- OCR
- layout analysis
- reading-order reconstruction
- structured OCR output.

## Frontend

After OCR succeeds, show:

[ Send to Legal Research ]

After successful ingestion:

[ Open in Legal Research ]

Do not build a separate Legal Research UI.

Reuse the existing NyayaSarathi Legal Research page and routing.

## Testing

Test:

1. Digital PDF → OCR → Legal Research
2. Scanned PDF → OCR → Legal Research
3. DOCX → OCR/extraction → Legal Research
4. Image → OCR → Legal Research
5. Failed ingestion → OCR result remains available
6. Retry ingestion without rerunning OCR
7. Existing Legal Research/RAG tests remain passing
8. Existing OCR tests remain passing

## Definition of Done

A user can:

Upload legal document
→ Run OCR
→ Review extracted text
→ Click "Send to Legal Research"
→ Open Legal Research
→ Ask questions about that exact document

without uploading the document a second time.