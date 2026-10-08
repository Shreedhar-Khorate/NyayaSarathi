PRD --- Legal Document OCR & Text Extraction Module
1. Product Overview
Product Name
Legal Document OCR & Extraction Module
Purpose
A standalone backend-focused module that accepts legal documents in PDF,
DOC, DOCX, JPG, and PNG formats and converts them into a standardized
text representation.
The module must intelligently determine whether a document already
contains machine-readable text or consists primarily of scanned images.
It should use direct text extraction when possible and OCR only when
required.
This module is intentionally being developed separately from the main
application. The final module will later be merged into an existing
project that uses:
- Backend: FastAPI + Python
- Frontend: React + Vite
The standalone frontend is only a lightweight testing interface. The
primary engineering focus is the backend, document processing pipeline,
OCR quality, standardized output, logging, and clean modular
architecture.
2. Goals
Primary Goals
1. Accept multiple legal document formats.
2. Detect whether a document is text-based or scanned.
3. Avoid OCR when reliable text already exists.
4. Convert scanned documents into images.
5. Preprocess document images before OCR.
6. Extract text using PaddleOCR.
7. Preserve page-level information.
8. Preserve OCR confidence information where available.
9. Return a consistent JSON structure for every supported document.
10. Build the module so it can later be merged into the main FastAPI
    application.
11. Keep all processing components modular and replaceable.
12. Maintain a development log in log.md.
Secondary Goals
- Extract basic legal metadata in a later phase.
- Support tables and structured text as much as practical.
- Preserve page boundaries.
- Provide meaningful processing errors.
- Make the module easy to test independently.
3. Non-Goals for the Initial Version
The first version will NOT focus on:
- A polished production UI
- User authentication
- User accounts
- Payments
- Cloud storage
- Advanced legal reasoning
- Legal advice generation
- Case outcome prediction
- Automatic legal opinion generation
- Training a custom OCR model
- Fine-tuning an LLM
- Full legal entity extraction
These can be added after the OCR pipeline is stable.
4. Supported Input Formats
Required
  Format   Initial Support   Processing
  PDF      Yes               Detect text or scanned pages
  DOCX     Yes               Extract text
  DOC      Later/optional    Convert or support through LibreOffice
  JPG      Yes               OCR
  JPEG     Yes               OCR
  PNG      Yes               OCR
File Size
Initial recommended limit:
50 MB
This should be configurable through environment variables.
Page Limit
Initial recommended limit:
100 pages
This should also be configurable.
5. High-Level System Flow
                    USER
                      |
                      v
              Upload Document
                      |
                      v
             FastAPI Upload API
                      |
                      v
             File Validation
                      |
                      v
             Document Detection
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
         PDF         DOCX       IMAGE
          |           |           |
          v           v           v
   Text Available?  Extract     Preprocess
      |       |       Text          |
     YES      NO                    v
      |       |                  OCR
      |       |                    |
      |       +--------+-----------+
      |                |
      +----------------+
               |
               v
       Unified Text Representation
               |
               v
       Page-Level Structured Data
               |
               v
          JSON Response
               |
               v
       Future Legal AI Layer
6. Detailed Processing Flow
Step 1 --- Upload
The frontend sends the document using multipart/form-data.
Example:
POST /api/v1/documents/upload
Content-Type: multipart/form-data
The backend validates:
- File exists
- File extension
- MIME type
- File size
- Filename
- Maximum page count where applicable
7. Step 2 --- File Validation
Create a validation service.
Recommended checks:
filename
extension
content type
file size
file signature / magic bytes
Do not trust only the filename extension.
For example, a file named:
case.pdf
should not automatically be trusted to actually be a PDF.
8. Step 3 --- Document Type Detection
The backend determines the processing path.
PDF
Use PyMuPDF (fitz) to inspect pages.
For each page:
1. Attempt to extract text.
2. Measure extracted text length.
3. Inspect whether the page contains images.
4. Determine whether the PDF is likely digital or scanned.
Possible classification:
TEXT_PDF
SCANNED_PDF
MIXED_PDF
DOCX
Use python-docx.
Extract:
- Paragraphs
- Tables
- Headings where available
Images
Directly send:
JPG
JPEG
PNG
to the image preprocessing pipeline.
9. PDF Classification Logic
A PDF can contain:
Case A --- Digital PDF
PDF
 |
 └── selectable text
       |
       └── Direct extraction
No OCR should be performed.
Case B --- Scanned PDF
PDF
 |
 └── page images
       |
       └── PDF → image
              |
              └── preprocessing
                     |
                     └── OCR
Case C --- Mixed PDF
Some pages contain text while others are scanned.
The system should process each page independently.
Page 1 → Direct extraction
Page 2 → Direct extraction
Page 3 → OCR
Page 4 → OCR
Page 5 → Direct extraction
This is important for real legal documents because attachments and
annexures may use different formats.
10. Step 4 --- PDF to Image Conversion
For scanned PDF pages, render each page at a reasonable DPI.
Recommended initial setting:
DPI = 200–300
Higher DPI improves OCR in some cases but increases:
- RAM usage
- CPU usage
- processing time
- temporary storage
Start with 250 DPI and make the value configurable.
Use:
- PyMuPDF for rendering
- PIL/Pillow for image handling
11. Step 5 --- Image Preprocessing
Preprocessing should be modular.
Recommended pipeline:
Input Image
    |
    v
Resize / Resolution Check
    |
    v
Grayscale
    |
    v
Noise Reduction
    |
    v
Contrast Enhancement
    |
    v
Deskew
    |
    v
Optional Thresholding
    |
    v
OCR-ready Image
Do not apply aggressive preprocessing to every document blindly.
Some legal documents are already high quality and aggressive
thresholding may reduce OCR accuracy.
The preprocessing service should eventually support configurable
strategies.
12. Recommended Python Packages
Core API
FastAPI
Purpose:
- REST API
- File upload
- Validation
- JSON responses
Package:
fastapi
Uvicorn
Purpose:
Run the FastAPI application.
uvicorn
13. Document Processing Packages
PyMuPDF
Package:
PyMuPDF
Import:
import fitz
Use for:
- Reading PDFs
- Extracting text
- Detecting images
- Rendering PDF pages
- Getting page metadata
This should be the primary PDF library.
python-docx
Package:
python-docx
Use for:
- DOCX text extraction
- Paragraph extraction
- Table extraction
Pillow
Package:
Pillow
Use for:
- Image loading
- Image conversion
- Resizing
- Rotation
- Basic image manipulation
14. OCR Engine
PaddleOCR
Package:
paddleocr
PaddleOCR should be the primary OCR engine for the initial version.
Reasons:
- Good document OCR support
- Text detection + recognition
- Bounding boxes
- Confidence scores
- Better extensibility for document processing than a basic text-only
  OCR workflow
The OCR service must be isolated behind a class/interface so that
another OCR engine can be added later.
Example conceptual interface:
class OCREngine:
    def extract(self, image):
        pass
Then:
class PaddleOCREngine(OCREngine):
    def extract(self, image):
        pass
This prevents the entire application from depending directly on
PaddleOCR implementation details.
15. OpenCV
Package:
opencv-python
Use for:
- Deskewing
- Image preprocessing
- Thresholding
- Noise reduction
- Contour analysis
- Rotation detection
- Image enhancement
Import:
import cv2
16. NumPy
Package:
numpy
Use for:
- Image arrays
- Numerical image operations
- OpenCV integration
17. Configuration
Use:
python-dotenv
Environment variables:
MAX_FILE_SIZE_MB=50
MAX_PAGES=100
PDF_RENDER_DPI=250
OCR_LANGUAGE=en
UPLOAD_DIR=uploads
TEMP_DIR=temp
Do not hard-code operational settings.
18. Recommended requirements.txt
Initial dependency list:
fastapi
uvicorn[standard]
python-multipart
PyMuPDF
python-docx
Pillow
opencv-python
numpy
paddleocr
python-dotenv
pydantic
Additional Paddle/PaddlePaddle dependencies may vary by operating
system, Python version, and CPU/GPU setup. Install the compatible Paddle
runtime separately according to the target environment before locking
the final production requirements.
19. Project Structure
legal-document-module/
│
├── backend/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── documents.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── validator.py
│   │   │   ├── detector.py
│   │   │   ├── pdf_extractor.py
│   │   │   ├── docx_extractor.py
│   │   │   ├── image_preprocessor.py
│   │   │   ├── ocr.py
│   │   │   └── document_processor.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── document.py
│   │   │
│   │   └── core/
│   │       ├── __init__.py
│   │       └── config.py
│   │
│   ├── uploads/
│   ├── temp/
│   ├── tests/
│   │   ├── test_validator.py
│   │   ├── test_pdf_extractor.py
│   │   ├── test_docx_extractor.py
│   │   ├── test_ocr.py
│   │   └── test_api.py
│   │
│   ├── requirements.txt
│   ├── .env
│   └── .gitignore
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/
│   │       └── FileUpload.jsx
│   ├── package.json
│   └── vite.config.js
│
├── PRD.md
└── log.md
20. Backend Architecture
Use a layered structure:
Route Layer
    ↓
Validation Layer
    ↓
Document Processor
    ↓
Format-specific Extractor
    ↓
Preprocessor
    ↓
OCR Engine
    ↓
Normalizer
    ↓
Response Schema
The route should remain thin.
Bad approach:
@app.post("/upload")
def upload():
    # 300 lines of OCR logic
Preferred approach:
@app.post("/upload")
async def upload_document(file: UploadFile):
    return await document_processor.process(file)
21. API Design
Health Check
GET /api/v1/health
Response:
{
  "status": "ok"
}
Upload Document
POST /api/v1/documents/upload
Form field:
file
Response:
{
  "document_id": "uuid",
  "filename": "judgment.pdf",
  "document_type": "scanned_pdf",
  "pages": 24,
  "extraction_method": "paddleocr",
  "status": "completed",
  "text": "...",
  "pages_data": []
}
22. Standardized Output Schema
All input types should eventually produce the same structure.
Example:
{
  "document_id": "abc-123",
  "filename": "case.pdf",
  "document_type": "scanned_pdf",
  "status": "completed",
  "pages": 3,
  "extraction_method": "paddleocr",
  "text": "Full normalized document text...",
  "pages_data": [
    {
      "page_number": 1,
      "text": "Page text...",
      "confidence": 0.94,
      "blocks": [
        {
          "text": "IN THE HIGH COURT...",
          "confidence": 0.97,
          "bbox": [100, 120, 800, 180]
        }
      ]
    }
  ]
}
23. Why Page-Level Data Is Required
Do not return only one large text string.
Legal AI features will later require citations such as:
Page 17
Paragraph 4
Therefore the system should preserve:
- Page number
- Extracted text
- OCR confidence
- Bounding box
- Block/line information where available
This will make future RAG citations much easier.
24. Legal Metadata Extraction --- Future Phase
After OCR is stable, add a separate service:
legal_metadata_extractor.py
Potential fields:
{
  "case_number": "",
  "court": "",
  "case_title": "",
  "judges": [],
  "parties": [],
  "advocates": [],
  "dates": [],
  "acts": [],
  "sections": []
}
This should NOT be mixed directly into the OCR engine.
OCR answers:
What text is present?

Legal extraction answers:
What information does this text represent?

Keep these layers separate.
25. Error Handling
The API must handle:
Unsupported file
{
  "error": "Unsupported file format"
}
File too large
{
  "error": "File exceeds maximum allowed size"
}
Corrupt PDF
{
  "error": "Unable to read PDF"
}
OCR failure
{
  "error": "OCR processing failed",
  "document_id": "abc-123"
}
Never expose raw Python stack traces to the frontend.
Detailed stack traces should go to server logs.
26. Logging Requirements
Use Python's built-in logging package initially.
Log:
- Upload received
- File validation
- File type detection
- Number of pages
- Text extraction decision
- OCR start
- OCR completion
- Processing duration
- Errors
- Final processing status
Example:
INFO  Document received: judgment.pdf
INFO  File type detected: PDF
INFO  Pages detected: 24
INFO  Page 1: scanned
INFO  Starting OCR
INFO  OCR completed in 18.4 seconds
INFO  Document processing completed
Do not log:
- Passwords
- API keys
- Authentication tokens
- Sensitive credentials
Be careful with legal document content. Avoid logging the full extracted
text by default.
27. log.md Development Log
Maintain a separate log.md.
Each development entry should contain:
## YYYY-MM-DD — Task Name

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
Example:
## 2026-10-07 — Initial Setup

### Completed
- Created standalone legal document OCR module.
- Defined backend architecture.
- Selected FastAPI and PaddleOCR.
- Defined PDF/DOCX/image processing flow.

### Files Changed
- PRD.md
- log.md

### Tests
- Not started.

### Issues
- PaddleOCR environment compatibility needs to be verified.

### Decisions
- Use PyMuPDF for PDF processing.
- Use python-docx for DOCX.
- Use PaddleOCR for scanned documents.
- Keep frontend intentionally minimal.

### Next Step
- Create FastAPI project.
- Install dependencies.
- Implement health endpoint.
Update this file after every meaningful development milestone.
28. Testing Strategy
Unit Tests
Test each service independently:
validator
detector
pdf_extractor
docx_extractor
image_preprocessor
ocr
document_processor
Integration Tests
Test:
Upload → Detection → Extraction → Response
Test Documents
Create a test dataset containing:
1. Digital PDF
2. Scanned PDF
3. Mixed PDF
4. DOCX
5. Image
6. Rotated scan
7. Low-quality scan
8. Multi-page document
9. Document with tables
10. Document with stamps/signatures
29. OCR Quality Evaluation
Do not judge OCR only by whether it returns text.
Measure:
- Character accuracy
- Word accuracy
- Missing words
- Incorrect characters
- Layout preservation
- Page ordering
For a labeled test set, calculate:
Character Error Rate
CER = Edit Distance / Number of Reference Characters
Word Error Rate
WER = (Substitutions + Deletions + Insertions)
      / Number of Reference Words
Lower is better.
30. Performance Requirements
Initial targets:
  Operation                Target
  Health endpoint          < 200 ms
  Digital PDF extraction   Fast/local
  Single image OCR         Reasonable local processing
  10-page scanned PDF      Complete without memory failure
  50-page document         Stable processing
  100-page document        Configurable and stable
Do not promise a fixed OCR processing time because hardware and document
complexity vary.
31. Memory Management
Scanned PDFs can consume significant memory.
Do NOT load an entire 100-page document into memory unnecessarily.
Preferred:
PDF
 ↓
Page 1 → process → release
 ↓
Page 2 → process → release
 ↓
Page 3 → process → release
Use temporary files when required.
Clean temporary files after successful or failed processing.
32. Security Requirements
Because legal documents can contain sensitive information:
1. Validate uploaded files.
2. Restrict allowed formats.
3. Limit file size.
4. Generate safe internal filenames.
5. Never execute uploaded files.
6. Store uploads outside executable directories where possible.
7. Clean temporary files.
8. Never log full document contents by default.
9. Never expose filesystem paths to clients.
10. Keep secrets in .env.
11. Add authentication when integrating into the main product.
33. Frontend Scope
The standalone React + Vite frontend should remain intentionally simple.
Required:
- File picker
- Selected filename
- Upload button
- Processing status
- Error display
- Extracted text display
- Page count
- Extraction method
Not required:
- Advanced animations
- Complex dashboard
- User authentication
- Advanced navigation
- Production design system
The final UI will be redesigned during integration into the main
project.
34. Future Architecture
After the OCR module is stable:
                    LEGAL DOCUMENT
                           |
                           v
                    OCR / Extraction
                           |
                           v
                  Structured Document
                           |
              +------------+------------+
              |            |            |
              v            v            v
         Metadata       Chunking      Timeline
         Extraction        |          Generation
                           v
                       Embeddings
                           |
                           v
                     Vector Database
                           |
                           v
                          RAG
                           |
                           v
                    Legal AI Assistant
                           |
              +------------+------------+
              |            |            |
              v            v            v
           Summary       Q&A       Citations
35. Future RAG Requirements
When RAG is implemented:
Each chunk should retain metadata:
{
  "text": "...",
  "page_number": 17,
  "document_id": "abc-123",
  "section": "Arguments",
  "source": "judgment.pdf"
}
This allows answers such as:
The petitioner argued that...

Source:
judgment.pdf — Page 17
The system must not fabricate page references.
36. Merge Strategy With Main Project
The module is deliberately isolated.
Later, the backend can be merged into the main FastAPI application.
Recommended final structure:
main-project/
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── routes/
│       ├── services/
│       │   └── legal_documents/
│       │       ├── detector.py
│       │       ├── pdf_extractor.py
│       │       ├── docx_extractor.py
│       │       ├── image_preprocessor.py
│       │       ├── ocr.py
│       │       └── document_processor.py
│       └── schemas/
│           └── legal_documents.py
│
└── frontend/
    └── src/
        └── features/
            └── legal-documents/
Register the final API router:
app.include_router(document_router)
The standalone module should therefore avoid assumptions about the main
application's database, authentication, or frontend.
37. Development Milestones
Milestone 1 --- Project Setup
- Create directory structure
- Create virtual environment
- Install dependencies
- Configure environment variables
- Start FastAPI
- Add health endpoint
Milestone 2 --- Upload
- Implement upload endpoint
- Validate extensions
- Validate MIME type
- Validate size
- Generate document ID
Milestone 3 --- Digital Extraction
- Implement PDF text extraction
- Implement DOCX extraction
- Return page-level text
Milestone 4 --- Scanned PDF Detection
- Detect pages without usable text
- Detect mixed PDFs
- Route scanned pages to OCR
Milestone 5 --- Image Processing
- Render PDF pages
- Resize
- Grayscale
- Deskew
- Denoise
- Contrast enhancement
Milestone 6 --- OCR
- Integrate PaddleOCR
- Extract text
- Extract confidence
- Extract bounding boxes
- Preserve page numbers
Milestone 7 --- Unified Output
- Normalize outputs from all formats
- Create Pydantic response schemas
- Add consistent errors
Milestone 8 --- Testing
- Unit tests
- Integration tests
- OCR quality tests
- Performance tests
Milestone 9 --- Legal Metadata
- Case number
- Court
- Parties
- Judges
- Dates
- Acts
- Sections
Milestone 10 --- Main Project Integration
- Move backend services
- Register FastAPI routes
- Move React feature
- Connect authentication
- Connect database
- Replace standalone UI with production UI
38. Definition of Done --- Initial OCR Version
The initial version is complete when:
- [ ] PDF upload works
- [ ] DOCX upload works
- [ ] JPG/PNG upload works
- [ ] Invalid files are rejected
- [ ] Digital PDFs use direct extraction
- [ ] Scanned PDFs use OCR
- [ ] Mixed PDFs process page-by-page
- [ ] OCR output contains page numbers
- [ ] OCR confidence is preserved where available
- [ ] Bounding boxes are preserved where available
- [ ] API returns standardized JSON
- [ ] Temporary files are cleaned
- [ ] Errors are handled cleanly
- [ ] Logs are written
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] README/setup instructions exist
- [ ] log.md is updated
39. Important Engineering Principles
Principle 1 --- OCR only when needed
Do not OCR digital documents unnecessarily.
Principle 2 --- Keep extraction and AI separate
OCR is document extraction.
RAG/LLM is document understanding.
Principle 3 --- Preserve provenance
Every piece of extracted information should retain its page/source
wherever possible.
Principle 4 --- Build for replacement
OCR engines, embedding models, and LLMs may change.
Use service abstractions so they can be replaced without rewriting the
entire backend.
Principle 5 --- Process large documents incrementally
Avoid loading entire scanned documents into memory.
Principle 6 --- Keep the standalone module independent
Do not tightly couple it to the main project's database, authentication,
or UI.
Principle 7 --- Treat legal text as sensitive
Do not expose document contents through unnecessary logs or error
messages.
40. Final Architecture
                       ┌───────────────────┐
                       │  React + Vite     │
                       │  Simple Test UI   │
                       └─────────┬─────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │     FastAPI       │
                       │   Upload API      │
                       └─────────┬─────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ File Validation   │
                       └─────────┬─────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ Document Detector │
                       └─────────┬─────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
         Digital PDF           DOCX              Scan
              │                  │                  │
              ▼                  ▼                  ▼
       PyMuPDF Extract     python-docx       OpenCV/Pillow
              │                  │                  │
              │                  │                  ▼
              │                  │             PaddleOCR
              │                  │                  │
              └──────────────────┴──────────────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ Unified Document  │
                       │ Representation    │
                       └─────────┬─────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ Legal Extraction  │
                       │    (Future)       │
                       └─────────┬─────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │    RAG / LLM      │
                       │    (Future)       │
                       └───────────────────┘
41. Immediate Next Step
Start with Milestone 1 only.
Create:
legal-document-module/
└── backend/
    ├── app/
    │   ├── main.py
    │   └── core/
    │       └── config.py
    ├── requirements.txt
    ├── .env
    └── .gitignore
Then:
1. Create Python virtual environment.
2. Install FastAPI and Uvicorn.
3. Start the FastAPI server.
4. Verify /api/v1/health.
5. Add dependencies incrementally rather than installing everything
   blindly.
6. Update log.md.
7. Only then implement document upload.
This staged approach will make debugging significantly easier,
especially because PaddleOCR/PaddlePaddle installation can vary by
operating system, Python version, and CPU/GPU environment.