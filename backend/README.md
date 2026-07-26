# NyayaSarathi Backend

This is the API support server for **NyayaSarathi** (AI-Powered Judicial Case Intelligence & Decision Support System). It is built using **FastAPI** and **Uvicorn** to provide high-performance, asynchronous REST endpoints for analyzing legal briefs and retrieving judicial precedents.

---

## 📁 Directory Structure

*   **`main.py`**: The entrypoint of the FastAPI application. Sets up routes, enables CORS middleware for React connection, and defines case analysis logic.
*   **`requirements.txt`**: Pinpoints dependencies required for the backend environment.

---

## 🔌 API Endpoints

### 1. Root Handshake
*   **Endpoint**: `GET /`
*   **Response**:
    ```json
    {
      "message": "Welcome to NyayaSarathi API Support Server. Ready for legal briefs analysis."
    }
    ```

### 2. Case Analysis & Decision Support
*   **Endpoint**: `POST /api/analyze`
*   **Payload Schema**:
    ```json
    {
      "case_type": "civil | criminal",
      "description": "Factual narrative or appeal text..."
    }
    ```
*   **Response Schema**:
    ```json
    {
      "probability": "Estimated win/loss chance and target party",
      "legalPrecedents": ["List of relevant precedents or judgments"],
      "keyTakeaway": "Actionable decision support summary",
      "confidence": "Analysis confidence score (e.g. 88%)"
    }
    ```

---

## 🚀 Installation & Local Run

### Prerequisites

Ensure you have **Python 3.8+** installed.

### Setup Steps

1.  **Navigate to the backend folder**:
    ```bash
    cd backend
    ```

2.  **Create and activate a Virtual Environment (Recommended)**:
    *   **Windows**:
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    *   **macOS/Linux**:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the API Dev Server**:
    ```bash
    python main.py
    ```
    *The server will start at `http://localhost:8000` with hot-reloading active.*

---

## 🔒 CORS Configuration

The server enables cross-origin resource sharing (CORS) configured specifically to accept incoming requests from:
- `http://localhost:5173`
- `http://127.0.0.1:5173`

To deploy this in production, make sure to update the list of allowed origins in `main.py` to match your domain.
