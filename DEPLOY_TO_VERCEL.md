# 🚀 Deploying CORRUGATE IQ to Vercel

All required Vercel configuration files have been prepared:
- `vercel.json` (Serverless URL rewrites)
- `api/index.py` (Vercel Serverless WSGI entry point)
- `requirements.txt` (Dependencies including Flask, Pandas, OpenPyXL)
- `.vercelignore` (Clean deployment bundle)

---

## Method 1: Deploy via GitHub (Recommended & Easiest)

1. **Push your code to a GitHub repository:**
   ```powershell
   cd corrugate-iq
   git init
   git add .
   git commit -m "Production release: CORRUGATE IQ"
   git branch -M main
   git remote add origin https://github.com/<your-username>/corrugate-iq.git
   git push -u origin main
   ```

2. **Deploy on Vercel:**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Click **Import** next to your `corrugate-iq` repository.
   - *(Note: If you pushed the parent `dashboard` folder, set **Root Directory** to `corrugate-iq`)*.
   - Click **Deploy**.
   - Your live URL will be ready in under 60 seconds (e.g., `https://corrugate-iq.vercel.app`)!

---

## Method 2: Deploy Directly via Terminal (Vercel CLI)

1. Open your terminal and run:
   ```powershell
   cd corrugate-iq
   npx vercel
   ```

2. Follow the 3 prompts:
   - **Log in** (opens your browser to authenticate with GitHub or email).
   - **Set up and deploy?** Press `y` (Yes).
   - **Which scope?** Press `Enter`.
   - **Link to existing project?** Press `n` (No).
   - **Project name?** Press `Enter` (or type `corrugate-iq`).

3. Once preview deployment finishes, deploy to **Production**:
   ```powershell
   npx vercel --prod
   ```
   Vercel will print your live production URL!

