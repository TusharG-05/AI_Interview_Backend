# Frontend Instructions

The frontend is now separated from the backend.

## How to Run

1.  **Start the Backend**:
    *   Navigate to the project root.
    *   Run `python main.py` or use the provided `run_app.ps1` script (or `uvicorn main:app --reload`).
    *   Ensure the backend is running at `http://localhost:8000`.

2.  **Run the Frontend**:
    *   You can simply open the HTML files in your browser (e.g., double-click `frontend/login.html`).
    *   **Recommended**: Serve the frontend using a simple static server to avoid potential browser security restrictions with `file://` protocol.
        *   If you have Python installed:
            ```powershell
            cd frontend
            python -m http.server 8080
            ```
        *   Then open `http://localhost:8080/login.html` in your browser.

## Configuration

*   The API URL is configured in each HTML file as `const API_BASE_URL = 'http://localhost:8000';`.
*   If you change the backend port, update this variable in `login.html`, `register.html`, `dashboard_admin.html`, `dashboard_candidate.html`, and `interview.html`.
