# Deploying to Render.com

Step-by-step guide to deploy the Signals & Systems Web Platform to Render.com.

## Prerequisites

- GitHub account with this repository
- Render.com account (free tier works)

## Deployment Steps

### Step 1: Connect GitHub to Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click **New +** → **Blueprint**
3. Connect your GitHub account if not already connected
4. Select this repository

### Step 2: Deploy Using Blueprint (Recommended)

The `render.yaml` file in this directory defines both services automatically.

1. After connecting the repo, Render will detect `render.yaml`
2. Review the services:
   - **signals-backend**: Python web service
   - **signals-frontend**: Static site
3. Click **Apply**
4. Wait for both services to deploy (5-10 minutes)

### Step 3: Manual Deployment (Alternative)

If the blueprint doesn't work, deploy manually:

#### Deploy Backend First

1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `signals-backend`
   - **Root Directory**: `signals-web-platform/backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**:
     ```
     gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120
     ```
4. Add Environment Variables:
   - `PYTHON_VERSION` = `3.11.0`
   - `LOG_LEVEL` = `INFO`
   - `CACHE_MAX_SIZE` = `10000`
5. Click **Create Web Service**
6. **Copy the service URL** (e.g., `https://signals-backend.onrender.com`)

#### Deploy Frontend

1. Click **New +** → **Static Site**
2. Connect the same repository
3. Configure:
   - **Name**: `signals-frontend`
   - **Root Directory**: `signals-web-platform/frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. Add Environment Variable:
   - `VITE_API_URL` = `https://signals-backend.onrender.com` (your backend URL from step 6)
5. Click **Create Static Site**

### Step 4: Verify Deployment

Once both services are live:

```bash
# Check backend health
curl https://signals-backend.onrender.com/health
# Expected: {"status": "ok"}

# Check API
curl https://signals-backend.onrender.com/api/v1/simulations
# Expected: List of 13 simulations

# Visit frontend
open https://signals-frontend.onrender.com
```

### Step 5: Set Up Auto-Deploy (Optional)

To enable automatic deployments on git push:

1. Go to each service's **Settings**
2. Under **Build & Deploy**, ensure **Auto-Deploy** is set to "Yes"
3. Now every push to `main` will trigger a new deployment

### Step 6: Configure GitHub Actions (Optional)

For CI/CD with testing before deploy:

1. Go to Render Dashboard → Each Service → **Settings**
2. Copy the **Deploy Hook URL** for each service
3. In GitHub, go to **Settings** → **Secrets and variables** → **Actions**
4. Add secrets:
   - `RENDER_BACKEND_HOOK` = Backend deploy hook URL
   - `RENDER_FRONTEND_HOOK` = Frontend deploy hook URL
5. Add variables:
   - `RENDER_BACKEND_URL` = `https://signals-backend.onrender.com`

## Service URLs

After deployment, your services will be available at:

| Service | URL |
|---------|-----|
| Frontend | `https://signals-frontend.onrender.com` |
| Backend API | `https://signals-backend.onrender.com` |
| API Docs | `https://signals-backend.onrender.com/docs` |
| Health Check | `https://signals-backend.onrender.com/health` |

## Custom Domain (Optional)

1. Go to your frontend service → **Settings** → **Custom Domains**
2. Add your domain (e.g., `simulations.yourdomain.com`)
3. Update DNS with the provided CNAME record
4. Render provides free SSL automatically

## Troubleshooting

### Backend won't start

Check logs in Render dashboard. Common issues:
- Missing dependencies: Ensure `requirements.txt` is complete
- Port binding: Use `$PORT` environment variable (Render sets this)

### Frontend shows "Network error"

- Verify `VITE_API_URL` environment variable is set correctly
- Ensure backend is running and healthy
- Check browser console for CORS errors

### Slow cold starts (Free tier)

Free tier services spin down after 15 minutes of inactivity:
- First request after idle takes 30-60 seconds
- Upgrade to Starter ($7/mo) for always-on service

### WebSocket connections failing

- Render supports WebSockets on all plans
- Ensure backend URL uses `https://` (WebSocket will use `wss://`)

## Scaling for Production

For 100+ concurrent users:

1. Upgrade backend to **Starter** plan ($7/mo)
2. Increase instance count:
   - Go to backend service → **Settings** → **Instance Type**
   - Select appropriate tier
3. Consider adding a Redis cache for session storage

## Cost Estimate

| Tier | Backend | Frontend | Total |
|------|---------|----------|-------|
| Free | $0 | $0 | $0/mo |
| Starter | $7 | $0 | $7/mo |
| Standard | $25 | $0 | $25/mo |

Static sites (frontend) are always free on Render.
