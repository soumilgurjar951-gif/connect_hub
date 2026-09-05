# ConnectHub 🚀 — Instagram + Twitter ka Simple MVP

Soumil Gurjar • India • Portfolio-ready Django project • 4-6 weeks MVP

> One-liner: Instagram + Twitter ka developer-friendly simple version.

## Features (MVP)
- Signup/Login (email+password, no verification)
- Profile (@username unique, bio 150, avatar)
- Posts (500 chars + 1-4 images, soft delete)
- Feed (followed users, reverse chronological, 20/page, infinite scroll)
- Follow/Unfollow (unidirectional, self-block)
- Like/Unlike (toggle, unique, AJAX)
- Comments (200 chars, 1-level reply, edit/delete 5 min)
- DM 1-to-1 (polling every 2s)

## Tech
Django 4.x/6.x + DRF + SQLite (local) / PostgreSQL (prod) + Pillow + WhiteNoise + Gunicorn. Frontend vanilla HTML/CSS/JS. Deploy Railway/Render.

## Quick Start (Windows)
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser  # admin / admin123 already exists
python manage.py runserver
# http://127.0.0.1:8000/  http://127.0.0.1:8000/admin/
```

## Project Structure
```
connect_hub/
  manage.py
  connect_hub/ (settings, urls, api_views, api_urls)
  accounts/ (Profile, Follow)
  posts/ (Post, PostImage, Like, Comment)
  chat/ (Message)
  templates/ (base, accounts/*, posts/*, chat/*)
  static/css, static/js
  media/avatars, media/post_images
```

## API (DRF) — base /api/
- POST /api/signup/ {username, email, password, bio}
- POST /api/login/ {username, password}
- GET /api/profile/me/ , GET /api/profile/<username>/ PUT
- GET /api/posts/ POST , GET /api/posts/<id>/ DELETE (soft)
- GET /api/feed/ (followed + own, paginated 20)
- POST /api/posts/<id>/like/ (toggle)
- GET/POST /api/posts/<id>/comments/
- POST /api/follow/<username>/ (toggle)
- GET /api/conversations/ , GET/POST /api/messages/<username>/

### Curl Examples
```bash
# Signup
curl -X POST http://127.0.0.1:8000/api/signup/ -H "Content-Type: application/json" -d '{"username":"soumil2","email":"s2@test.com","password":"Pass12345"}' -c cookies.txt
# Login
curl -X POST http://127.0.0.1:8000/api/login/ -H "Content-Type: application/json" -d '{"username":"soumil2","password":"Pass12345"}' -c cookies.txt -b cookies.txt
# Create post
curl -X POST http://127.0.0.1:8000/api/posts/ -H "Content-Type: application/json" -b cookies.txt -d '{"content":"Hello API"}'
# Feed
curl http://127.0.0.1:8000/api/feed/ -b cookies.txt
# Like toggle
curl -X POST http://127.0.0.1:8000/api/posts/1/like/ -b cookies.txt
# Follow
curl -X POST http://127.0.0.1:8000/api/follow/admin/ -b cookies.txt
```

## Deployment — Railway / Render (Free Tier)
1. Push to GitHub (see Git Strategy below)
2. Railway: New Project → Deploy from GitHub → add PostgreSQL → Variables: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=your-app.up.railway.app`, `DATABASE_URL` auto. Or Render: Web Service → Build `pip install -r requirements.txt` → Start `gunicorn connect_hub.wsgi --log-file -` → add Postgres.
3. `python manage.py migrate` via Railway Run Command / Render Shell
4. `python manage.py createsuperuser` / `collectstatic` auto via WhiteNoise
5. Media: Local `MEDIA_ROOT` for dev; prod me S3/R2 optional (django-storages). Quick: keep WhiteNoise + `MEDIA_ROOT` but ephemeral — prod me S3 recommended.

Env (.env):
```
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=app.railway.app,localhost
DATABASE_URL=postgres://...
```

## Common Errors
- `Pillow not installed` → `pip install Pillow`
- `DisallowedHost testserver` → settings already adds testserver
- `No file was submitted` → form enctype multipart + CSRF
- `ClearableFileInput multiple` → custom MultipleFileInput or manual getlist (fixed)
- Avatar 404 → check `MEDIA_URL` + `urls.py static()` when DEBUG
- `self-follow` → CheckConstraint blocks

## Git Strategy
```bash
git init; git add .; git commit -m "Part 1: setup"
git commit -m "Part 2: models 7"
git commit -m "Part 3: auth & profile"
git commit -m "Part 4: posts & feed"
git commit -m "Part 5: like & comment"
git commit -m "Part 6: DM polling"
git commit -m "Part 7: DRF API"
git commit -m "Part 8: frontend polish"
```
Meaningful messages, push after each part.

## Manual Testing Checklist
- [ ] Signup → auto login → /profile/<username>
- [ ] Login/Logout
- [ ] Edit profile avatar → media/avatars/
- [ ] Create post 1-4 images → feed shows → detail
- [ ] Pagination ?page=2 → infinite scroll
- [ ] Follow/unfollow → count update, self-block
- [ ] Like toggle AJAX → count
- [ ] Comment → reply → nested block → edit/delete 5min window
- [ ] DM: list → send → polling → read ✓✓
- [ ] Admin: all models visible, soft deleted posts hidden
- [ ] API via curl/Postman (see above)
- [ ] Mobile responsive (600px) + dark toggle

## License
MIT — portfolio use.
