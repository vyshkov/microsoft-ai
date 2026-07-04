# MS Azure AI Foundry - AI-103 Preparation Project

An empty Python project scaffold initialized for **Azure AI Foundry (AI-103 exam preparation)**.

## Getting Started

Follow these instructions to configure and run the project:

### 1. Select the Virtual Environment (`.venv`)

A virtual environment (`.venv`) is already created in the project root.

*   **In VS Code**:
    1. Open any Python file (e.g., `hello_ai.py`).
    2. Click on the Python version display in the bottom-right status bar, or press `Ctrl + Shift + P` and type `Python: Select Interpreter`.
    3. Choose the interpreter inside the `.venv` folder: `.\.venv\Scripts\python.exe`.
*   **In Command Prompt (CMD)**:
    ```cmd
    .venv\Scripts\activate.bat
    ```
*   **In PowerShell**:
    ```powershell
    .venv\Scripts\Activate.ps1
    ```

---

### 2. Install Dependencies

To install or update the latest Microsoft AI Foundry SDK libraries:

1. Open your terminal in the project directory.
2. Run the following command (ensure your virtual environment is activated):
   ```bash
   pip install -r requirements.txt
   ```

---

### 3. Run the Python Script

To run the verification hello world file from the command line:

```bash
python hello_ai.py
```

*Note: To connect to an active Azure AI Foundry resource, copy `.env.template` to a new file named `.env`, fill in your `PROJECT_CONNECTION_STRING`, and authenticate using `az login`.*
