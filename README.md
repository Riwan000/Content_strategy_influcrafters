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