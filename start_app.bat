@echo off

REM Start the FastAPI backend
start cmd /k ".venv\Scripts\activate && cd backend && uvicorn main:app --reload"

REM Give the backend a moment to start
timeout /t 5 /nobreak

REM Start the Streamlit frontend
start cmd /k ".venv\Scripts\activate && cd frontend && streamlit run app.py"


exit