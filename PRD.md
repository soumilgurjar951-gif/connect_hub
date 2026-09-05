# ConnectHub — Product Requirements Document (PRD)
**Version:** 1.0 • **Date:** 5 Sep 2026 • **Owner:** Soumil Gurjar (India) • **Stack:** Django 4.x + DRF + SQLite/PostgreSQL + Tailwind

---

## 1. Vision
**One-liner:** Instagram + Twitter ka simple, developer-friendly MVP for portfolio. Friendly, youthful, creator-focused.

**Goal:** Working MVP in 4–6 weeks, deployable to Railway/Render, mobile PWA ready.

**Success Metrics:** Signup→Post <2 min, Feed load <1s, Like/Comment <300ms, DM polling 2s, 0 critical 500s.

## 2. Scope

### MVP (Must Have)
- Auth: signup/login (email+password, no verification), logout
- Profile: unique username (slugified, 30), bio 150, avatar, followers/following counts, display_name, interests, onboarding 3-steps
- Post: content 500 + 1–4 images (5MB each), soft delete, location/tagged
- Feed: followed + own, reverse chronological, 20/page, infinite scroll, stories (24h), right-rail suggested
- Follow: unidirectional, self-block, counts
- Like: toggle, unique (user,post)
- Comment: 200 chars, 1-level nested, edit/delete within 5 min
- DM: 1-to-1, polling 2s, WebRTC call/VC (signaling via polling), story views tracking
- Explore: search (people/tags/captions), trending hashtags, grid masonry
- Settings: 6 sections (Account/Privacy/Notifications/Security/Appearance/About) — permanent save
- API: DRF for all above + search, conversations, messages
- Landing (optional), Reels (vertical 9:16), Notifications (bell)

### Nice-to-Have (if time)
- Trending, suggested, dark mode, admin ban/delete

### Out of Scope (v2+)
Video posts, stories reels, group chat, hashtags trending algo, mobile native, monetization

## 3. Personas
- **Gen-Z Creator (18–24):** posts photos, follows creators, DMs friends
- **Portfolio Reviewer:** checks code, design system, deploy

## 4. Tech Stack
Backend Django 4.x/6.x, DRF, Pillow, python-dotenv, corsheaders, whitenoise, gunicorn, dj-database-url, psycopg2-binary, django-storages+boto3 (S3/R2), Channels optional. DB SQLite local, Postgres prod. Media local dev, S3 prod. Frontend HTML5 + Tailwind CDN, vanilla JS. Deploy Railway/Render (Dockerfile, Procfile). PWA manifest + sw.js.

## 5. Data Models
**Profile** user O2O cascade, username unique slug 30, bio 150, avatar, followers/following counts, interests, display_name, onboarding_done, created_at
**Post** author FK cascade, content 500, location 100, tagged 200, is_deleted bool, created_at
**PostImage** post FK cascade, image, order
**Follow** follower/following FK cascade, Unique(follower,following), Check follower!=following
**Like** user/post FK cascade, Unique(user,post)
**Comment** user/post FK cascade, parent_comment FK self null, content 200, created_at, updated_at
**Message** sender/receiver FK cascade, content 1000 (blank allowed), image nullable, is_read, created_at; get_conversation(Q)
**Story** user FK, image, created_at, expires_at (now+24h), is_expired()
**StoryView** story FK, viewer FK, unique(story,viewer)
**CallSignal** caller/receiver FK, type offer/answer/ice/hangup, data, is_video, is_read

## 6. Key Flows
Signup → Onboarding 1 (find people) → 2 (interests) → 3 (photo/bio) → Feed
Login → Feed (stories + posts) → Create → Detail → Like/Comment (5min) → Follow → DM (polling + call/VC) → Explore/Search → Profile (followers/following, tagged, suggested, story views) → Settings → Reels (vertical, any reel, share to WA/FB/Snap) → Notifications → Logout

## 7. API (base /api/, Session auth, PAGE_SIZE 20)
POST /api/signup/, POST /api/login/, GET /api/profile/me/, GET|PUT /api/profile/<username>/, GET|PUT /api/posts/, GET /api/posts/<id>/, DELETE (soft), GET /api/feed/, POST /api/posts/<id>/like/, GET|POST /api/posts/<id>/comments/, POST /api/follow/<username>/, GET /api/search/?q=, GET /api/conversations/, GET|POST /api/messages/<username>/?after=<id>, POST /api/messages/<username>/signal/, POST /api/messages/<username>/ack/

## 8. UI Design System
Brand friendly/youthful: Primary #7C3AED, Secondary #06B6D4, Neutrals #111827/#6B7280/#F9FAFB, Success #10B981 Warning #F59E0B Error #EF4444. Fonts Sora (head) + Inter (body) + Grand Hotel (logo). Spacing 4/8/12/16/24/32/48. Components: btn primary/secondary/ghost, input, card, avatar gradient ring, story ring, post card. Dark via class, Tailwind dark:. Layout: sidebar 220 + feed 630 + right 320; mobile topbar + bottom nav; stories horizontal, reels vertical snap.

## 9. Non-Functional
Perf <1s feed, <300ms like, Security HSTS/SSL/secure cookies/CSRF, S3 for media, PWA installable, a11y labels, 5MB image limit.

## 10. Timeline (6 weeks)
W1 Setup+Auth+Profile, W2 Posts, W3 Feed+Follow, W4 Like+Comment, W5 DM+Call/VC+Stories, W6 Polish+Deploy+Docs

## 11. Risks
Media ephemeral without S3, polling vs WebSocket, spam without rate-limit, 404 for expired stories handled as friendly page.

## 12. Future
S3 done, PWA done, Docker done; next: WebSocket Channels, push, moderation, app (Expo).

---
© 2026 ConnectHub • Soumil Gurjar
