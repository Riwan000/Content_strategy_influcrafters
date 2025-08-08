# Content Strategy Influcrafters

A content strategy application with FastAPI backend and Streamlit frontend.

## Deployment to Render

This application can be deployed to Render using the Blueprint feature. Follow these steps:

### 1. Create a Render Account

If you don't have a Render account, sign up at [render.com](https://render.com).

### 2. Connect Your GitHub Repository

1. Push your code to a GitHub repository
2. In the Render dashboard, click on "Blueprints" in the sidebar
3. Click "New Blueprint Instance"
4. Connect your GitHub account if you haven't already
5. Select the repository containing this code
6. Render will automatically detect the `render.yaml` file

### 3. Configure and Deploy

1. Review the services that will be created (backend and frontend)
2. Click "Apply" to start the deployment process
3. Render will build and deploy both services
4. Once deployment is complete, you can access your application using the provided URLs

### 4. Environment Variables

The following environment variables should be set in the Render dashboard for the backend service:

- `EMAIL_HOST`: SMTP server for sending emails
- `EMAIL_PORT`: SMTP port
- `EMAIL_USER`: Email username/address
- `EMAIL_PASS`: Email password

## Manual Deployment

If you prefer to deploy the services manually:

### Backend Deployment

1. In the Render dashboard, click "New Web Service"
2. Connect your GitHub repository
3. Configure the service:
   - Name: `influcrafters-backend`
   - Root Directory: `backend`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add the required environment variables
5. Click "Create Web Service"

### Frontend Deployment

1. In the Render dashboard, click "New Web Service"
2. Connect your GitHub repository
3. Configure the service:
   - Name: `influcrafters-frontend`
   - Root Directory: `frontend`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port $PORT --server.headless true --server.enableCORS false`
4. Add the environment variable `BACKEND_URL` with the URL of your deployed backend service
5. Click "Create Web Service"

## Local Development

To run the application locally:

```bash
# Start the backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Start the frontend (in a separate terminal)
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Or use the provided `start_app.bat` script on Windows.
```

## Deployment to Replit

Replit is an online IDE and hosting platform that allows you to deploy both your backend and frontend services without requiring credit card details for basic usage.

### 1. Create a Replit Account

If you don't have a Replit account, sign up at [replit.com](https://replit.com).

### 2. Create a New Repl

1.  Log in to Replit.
2.  Click on the "+" icon (Create Repl) or "New Repl" button.
3.  Select "Import from GitHub" and provide the URL to your GitHub repository.
4.  Choose "Python" as the language if prompted, or let Replit detect it.
5.  Click "Import Repl".

### 3. Configure Replit for Backend and Frontend

Replit will try to guess your project's setup. For this application, you'll need to configure it to run both the FastAPI backend and Streamlit frontend.

#### Option A: Using a Single Repl (Recommended for Simplicity)

This approach runs both services within the same Repl, which is simpler to manage for demo purposes.

1.  **Install Dependencies:**
    Open the `Shell` tab in Replit and install all dependencies:
    ```bash
    pip install -r backend/requirements.txt
    pip install -r frontend/requirements.txt
    ```
2.  **Create a Startup Script:**
    Create a new file in your project's root directory (e.g., `start_replit.sh`) with the following content:
    ```bash
    #!/bin/bash

    # Start the FastAPI backend in the background
    cd backend
    uvicorn main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..

    echo "FastAPI backend started with PID: $BACKEND_PID"

    # Wait a moment for the backend to start
    sleep 5

    # Set the backend URL for the frontend
    export BACKEND_URL="http://localhost:8000"

    # Start the Streamlit frontend
    cd frontend
    streamlit run app.py --server.port 8501 --server.headless true --server.enableCORS false

    # Clean up: kill the backend process when Streamlit exits
    kill $BACKEND_PID
    ```
3.  **Configure Run Command:**
    In Replit, open the `.replit` file (it might be hidden, enable "Show hidden files" in the file explorer if you don't see it). Modify the `run` command to execute your startup script:
    ```toml
    run = "bash start_replit.sh"
    ```

#### Option B: Using Two Separate Repls (More Complex)

If you prefer to separate the services, you can create two Repls, one for the backend and one for the frontend. This is similar to the manual Render deployment.

1.  **Backend Repl:**
    *   Create a new Repl, import your repository, and set the `run` command to `uvicorn main:app --host 0.0.0.0 --port 8000` in the `backend` directory.
    *   Install `backend/requirements.txt`.
2.  **Frontend Repl:**
    *   Create another Repl, import your repository, and set the `run` command to `streamlit run app.py --server.port 8501 --server.headless true --server.enableCORS false` in the `frontend` directory.
    *   Install `frontend/requirements.txt`.
    *   **Crucially:** You will need to set the `BACKEND_URL` environment variable in the Frontend Repl's "Secrets" (Environment Variables) to the URL of your deployed Backend Repl. Replit provides a URL for each Repl.

### 4. Environment Variables (Secrets)

For both deployment options, you will need to set the environment variables listed in <mcfile name=".env.example" path=".env.example"></mcfile> as "Secrets" in your Replit project. Go to the "Secrets" tab (lock icon) in the sidebar and add each variable name and its corresponding value.

*   `BACKEND_EMAIL_PASSWORD`
*   `OPENROUTER_API_KEY`
*   `REDDIT_CLIENT_ID`
*   `REDDIT_CLIENT_SECRET`
*   `REDDIT_USER_AGENT`
*   `REDDIT_USERNAME`
*   `REDDIT_PASSWORD`

### 5. Run and Test

Click the "Run" button in Replit. Your application should start, and you will see the Streamlit frontend in the webview pane. Ensure both the backend and frontend are functioning correctly.