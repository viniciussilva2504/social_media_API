# ant.social

> *go read a book* — a minimalist anti-social media platform

**Live:** https://vjsilva250490.pythonanywhere.com

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.17-A30000)](https://www.django-rest-framework.org)
[![JWT](https://img.shields.io/badge/Auth-JWT%20%2B%20Token-0ea5e9)](https://django-rest-framework-simplejwt.readthedocs.io)
[![CI](https://github.com/viniciussilva2504/social_media_API/actions/workflows/ci.yml/badge.svg)](https://github.com/viniciussilva2504/social_media_API/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

**ant.social** is a full-stack social media platform built with Python, Django 6 and Django REST Framework. It ships a complete web UI (Django templates) alongside a production-ready REST API — both living in the same codebase, deployed to PythonAnywhere.

The identity is intentionally minimal and typographic, with a Bauhaus-inspired design: primary colours (red, blue, yellow), Roboto Flex, and a morse-code logo spelling out `ant.social`.

---

## Screenshots

<p align="center">
  <img src="IMG/home.png" alt="Home" width="600"/>
  <br><br>
  <img src="IMG/feed.png" alt="Feed" width="600"/>
  <br><br>
  <img src="IMG/profile.png" alt="Profile" width="600"/>
  <br><br>
  <img src="IMG/post-detail.png" alt="Post detail" width="600"/>
  <br><br>
  <img src="IMG/register.png" alt="Register" width="600"/>
  <br><br>
  <img src="IMG/api-docs.png" alt="API docs (Swagger)" width="600"/>
</p>

---

## Why this project matters

| Dimension | What it demonstrates |
|---|---|
| **Backend ownership** | API + database + auth + permissions from scratch |
| **Full-stack delivery** | Web UI + REST API in a single Django project |
| **Engineering maturity** | CI pipeline, request tracing, versioned cache, throttling |
| **Frontend-ready** | OpenAPI schema, Swagger/Redoc, CORS configured |
| **Production ops** | Docker Compose, Gunicorn, WhiteNoise, PythonAnywhere deploy |

---

## Core features

**Authentication**
- Session auth (web UI)
- DRF Token auth
- JWT auth (access + refresh via simplejwt)
- Auth throttling: register `5/min`, login `10/min`

**Profiles & social graph**
- Display name, bio, profile picture (extension + MIME + size validation)
- Follow / unfollow, followers, following lists

**Content**
- Posts with optional image upload (Polaroid-style UI)
- Soft delete (posts remain in DB, marked inactive)
- Likes (toggle) and comments (CRUD)

**Feed**
- Personalized feed: followed users + own posts
- Response-level cache with per-user versioned keys
- Event-driven invalidation (post, like, comment, follow events)

**Ops**
- Healthcheck endpoint at `/health/`
- `X-Request-ID` tracing: accepted, generated, echoed in headers and logs
- Content moderation hook (Google Perspective API, optional)

---

## Web UI pages

| Page | Description |
|---|---|
| `/` | Home with morse-code logo, rotating tagline, join/login |
| `/feed/` | Post feed with inline like/comment, compose box |
| `/post/<id>/` | Post detail, comments, edit/delete (if owner) |
| `/profile/<username>/` | Profile picture, bio, stats, posts |
| `/edit-profile/` | Update name, bio, profile picture |
| `/followers/` `/following/` | Social connections list |
| `/search/` | Search users by username |
| `/login/` `/register/` | Authentication forms |

---

## Architecture overview

```text
Browser / API Client
        │
        ▼
  Django URL Router
    ├── accounts/  (auth · profile · follow)
    ├── posts/     (post · feed · like · comment)
    └── health/    (healthcheck · OpenAPI docs)
        │
        ▼
  DRF ViewSets → Serializers → Models
        │
        ├── SQLite  (local dev)
        └── PostgreSQL  (production / Docker)
        │
        ▼
  Cache Layer
  (per-user versioned feed · event-driven invalidation)
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Framework | Django 6 + Django REST Framework 3.17 |
| Auth | Session · DRF Token · JWT (simplejwt) |
| API docs | drf-spectacular (OpenAPI 3, Swagger, Redoc) |
| Database | SQLite (dev) · PostgreSQL (prod) |
| Storage | Local filesystem · Cloudinary (optional) |
| Moderation | Google Perspective API (optional) |
| Deploy | PythonAnywhere · Docker Compose · Gunicorn · WhiteNoise |
| CI | GitHub Actions |

---

## Quick start (local)

```bash
git clone https://github.com/viniciussilva2504/social_media_API.git
cd social_media_API

# with pip + venv
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

set DEBUG=1
set SECRET_KEY=any-local-dev-key
set DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1

python manage.py migrate
python manage.py runserver
```

Open: http://127.0.0.1:8000/

```bash
# with Poetry
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

---

## Docker (local with PostgreSQL)

```bash
docker compose build
docker compose up -d
docker compose exec web python manage.py migrate
```

Open: http://127.0.0.1:8000/

---

## API endpoints

Base path: `/antisocial/v1/`

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/register/` | Create account |
| `POST` | `/login/` | Session login |
| `POST` | `/auth/jwt/token/` | Get JWT access + refresh |
| `POST` | `/auth/jwt/refresh/` | Refresh JWT access token |
| `POST` | `/api-token-auth/` | Get DRF token |

### Profile & Users
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/profile/` | List profiles |
| `GET` | `/profile/{username}/` | Get profile |
| `PATCH` | `/profile/me/` | Update own profile |
| `GET` | `/users/?q=search` | Search users |

### Follow
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/follow/toggle/{username}/` | Follow / unfollow |
| `GET` | `/follow/followers/{username}/` | Followers list |
| `GET` | `/follow/following/{username}/` | Following list |

### Posts & Feed
| Method | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/post/` | List / create posts |
| `GET/PATCH/DELETE` | `/post/{id}/` | Retrieve / edit / delete |
| `GET` | `/feed/` | Personalized feed |

### Social interactions
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/like/toggle/{post_id}/` | Like / unlike |
| `GET` | `/comment/?post_id={id}` | List comments |
| `POST` | `/comment/` | Add comment |
| `DELETE` | `/comment/{id}/` | Delete comment |

### Docs & Health
| Endpoint | Description |
|---|---|
| `/api/schema/` | OpenAPI 3 schema (YAML) |
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | Redoc |
| `/health/` | Healthcheck |

---

## Security highlights

- Django password validators (length, common password, similarity)
- Profile picture hardening: extension + file size (model) · MIME + image decoding (serializer)
- Auth throttling: `5/min` register · `10/min` login · `120/min` authenticated
- `X-Request-ID` tracing: accepted or auto-generated, echoed in response headers and logs
- `SECURE_CONTENT_TYPE_NOSNIFF`, `X-Frame-Options`, CORS explicitly configured

---

## Performance

- `select_related` / `prefetch_related` on feed and post queries
- Annotation-based like/comment counts (no N+1)
- Feed response cache with per-user versioned keys
- Cache invalidation triggered on: post create/delete · comment create/delete · like toggle · follow/unfollow

---

## Testing

```bash
python manage.py test -v 2
```

Coverage includes auth, feed, posts, comments, likes, follows, permissions, healthcheck, and request ID propagation.

---

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and PR:
1. Install dependencies
2. Run migrations
3. Run full test suite

---

## License

MIT
