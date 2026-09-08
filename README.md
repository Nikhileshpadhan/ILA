# ULPF (Universal Log Processing Framework)

ULPF is a log processing engine that consists of a Python-based FastAPI backend and a Vite-based frontend. The framework is designed to ingest, process, and analyze logs using a pipeline, storing them in a SQLite database.

## Project Structure

*   **`api/`**: Contains the FastAPI backend routes, database models, and authentication logic.
*   **`ulpf/`**: The core log processing pipeline engine.
*   **`ulpf-ui/`**: The frontend application built with Vite and React (or similar).
*   **`server.py`**: The FastAPI application entry point for the backend.
*   **`main.py`**: Interactive entry point for the ULPF core engine (can be run directly to test log processing).
*   **`run.py`**: A convenient script to start both the backend and frontend servers concurrently.
*   **`requirements.txt`**: Python dependencies for the backend.
*   **`ulpf.db`**: SQLite database file.

## Prerequisites

*   Python 3.8+
*   Node.js & npm

## Setup & Installation

### Backend Setup

1.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd ulpf-ui
    ```

2.  Install npm dependencies:
    ```bash
    npm install
    ```

## Running the Application

You can start both the backend and frontend concurrently using the provided `run.py` script from the root directory:

```bash
python run.py
```

This script will start:
*   The backend server (uvicorn) on `http://localhost:8000`
*   The frontend server (vite)

### Running Separately

**Backend:**
```bash
uvicorn server:app --reload --port 8000
```

**Frontend:**
```bash
cd ulpf-ui
npm run dev
```

## Demo Users

The application is seeded with several demo users for testing purposes. (Check `server.py` for details, e.g., `demo@ulpf.local` / `demo12345`).

## Core Technologies

*   **Backend:** FastAPI, SQLAlchemy, Uvicorn, Sentence-Transformers, Groq
*   **Frontend:** Vite, npm
*   **Database:** SQLite
