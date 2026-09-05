# Deployment Guide — Railway / Render (Beginner)

## 1. Prepare
- `requirements.txt` has gunicorn + whitenoise + psycopg2-binary + dj-database-url
- `settings.py` already handles `DATABASE_URL`, `ALLOWED_HOSTS`, `WhiteNoise`, `STATIC_ROOT`
- `.env.example` → copy to `.env` for local, never push `.env`
- Procfile not needed for Railway, for Render optional: `web: gunicorn connect_hub.wsgi`

## 2. Push GitHub
```bash
git init
git add .
git commit -m "ConnectHub MVP ready"
git branch -M main
git remote add origin https://github.com/soumil/connecthub.git
git push -u origin main
```

## 3A. Railway
- railway.app → New Project → Deploy from GitHub → select repo
- Add PostgreSQL plugin → DATABASE_URL auto injected
- Variables → `SECRET_KEY` (generate: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"), `DEBUG=False`, `ALLOWED_HOSTS=your-app.up.railway.app`
- Settings → Generate Domain
- Deployments → Run Command: `python manage.py migrate && python manage.py collectstatic --noinput`
- Create superuser: Railway Shell → `python manage.py createsuperuser`

## 3B. Render
- render.com → New Web Service → connect GitHub
- Build: `pip install -r requirements.txt`
- Start: `gunicorn connect_hub.wsgi:application --log-file -`
- Add PostgreSQL → copy Internal DATABASE_URL to Web Service Env `DATABASE_URL`
- Env: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=your-app.onrender.com`, `PYTHON_VERSION=3.11.0`
- Manual Deploy → Shell: `python manage.py migrate`

## 4. Media (Images)
Local `MEDIA_ROOT` works but Railway/Render filesystem ephemeral. For portfolio ok. For prod: add Cloudflare R2/S3:
```
pip install django-storages boto3
# settings.py add DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# Env: AWS_S3_... keys
```

## 5. Checklist Before Live
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS has domain
- [ ] SECRET_KEY from env, not hardcoded
- [ ] migrate done
- [ ] superuser created
- [ ] static collected (WhiteNoise)
- [ ] media folder exists (or S3)
- [ ] test /api/feed/ and /admin/

## 6. Free Tier Limits
Railway $5 trial, Render sleeps after 15 min. For always-on, use Fly.io or keep Render warm.

## 7. Custom Domain (Optional)
Railway/Render → Settings → Custom Domain → add CNAME → update ALLOWED_HOSTS
