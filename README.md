# ant.social API

- https://vjsilva250490.pythonanywhere.com

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5%2B-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.16%2B-A30000)
![JWT](https://img.shields.io/badge/Auth-JWT%20%2B%20Token-0ea5e9)
![CI](https://github.com/viniciussilva2504/social_media_API/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/License-MIT-yellow)

A minimalist social platform backend and web UI built with Django + Django REST Framework.

This project is designed as a production-minded portfolio piece: authentication, social graph, feed, API docs, tests, rate limiting, caching, and deployment support.

## Why this project matters

- Real backend ownership: API + database + auth + permissions.
- Frontend integration ready: REST API with schema/docs.
- Engineering maturity: CI pipeline, request tracing, healthcheck, cache invalidation strategy.

## Core features

- Authentication
- Session auth (web)
- Token auth (DRF token)
- JWT auth (access + refresh)
- Profiles
- Display name, bio, profile picture (file type and size validation)
- Follow system
- Follow/unfollow, followers, following
- Feed
- Personalized feed (followed users + own posts)
- Response caching with invalidation on social events
- Posts
- Create, edit, soft delete, list with pagination
- Likes and comments
- Like/unlike toggle, comment CRUD
- API docs
- OpenAPI schema, Swagger, Redoc
- Ops and observability
- Healthcheck endpoint
- Request ID propagation in logs and response headers

## Architecture overview

```text
Browser / API Client
        |
        v
Django URL Router
  |-- accounts app (auth, profile, follow)
  |-- posts app (post, feed, like, comment)
  |-- docs/health endpoints
        |
        v
DRF ViewSets -> Serializers -> Models -> SQLite/PostgreSQL
        |
        v
Cache Layer (feed response cache with versioned invalidation)
```

## Tech stack

- Python 3.12+
- Django 5+
- Django REST Framework
- drf-spectacular (OpenAPI)
- djangorestframework-simplejwt
- SQLite (local) / PostgreSQL (Docker)
- Docker + Docker Compose
- GitHub Actions CI

## Quick start (local)

```bash
git clone https://github.com/viniciussilva2504/social_media_API.git
cd social_media_API

# Poetry
poetry install --only main --no-root
poetry run python manage.py migrate
poetry run python manage.py runserver

# or pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open: http://127.0.0.1:8000/

## Docker

```bash
docker compose build
docker compose up -d
docker compose exec web python manage.py migrate
```

## API endpoints

Base path: `/antisocial/v1/`

- Auth
- `POST /register/`
- `POST /login/`
- `POST /auth/jwt/token/`
- `POST /auth/jwt/refresh/`
- `POST /api-token-auth/`
- Profile and users
- `GET /profile/`
- `GET /profile/{username}/`
- `PATCH /profile/me/`
- `GET /users/?q=search`
- Follow
- `POST /follow/toggle/{username}/`
- `GET /follow/followers/{username}/`
- `GET /follow/following/{username}/`
- Posts and feed
- `GET /post/`
- `POST /post/`
- `GET /post/{id}/`
- `PATCH /post/{id}/`
- `DELETE /post/{id}/`
- `GET /feed/`
- Social interactions
- `POST /like/toggle/{post_id}/`
- `GET /comment/?post_id={id}`
- `POST /comment/`
- `DELETE /comment/{id}/`

## API docs and health

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`
- Redoc: `/api/redoc/`
- Healthcheck: `/health/`

## Security and reliability highlights

- Password validation via Django validators.
- Upload hardening for profile pictures:
- extension and file size validation at model level
- MIME and image decoding validation at serializer level
- Auth endpoint throttling:
- register: `5/minute`
- login: `10/minute`
- Global throttling for anon and authenticated users.
- Request tracing:
- `X-Request-ID` accepted or generated
- echoed in response headers
- included in application logs

## Performance strategy

- Query optimization with `select_related` and annotation counts.
- Feed response cache with per-user versioned keys.
- Cache invalidation on:
- post create/delete
- comment create/delete
- like toggle
- follow/unfollow

## Testing

```bash
python manage.py test -v 2
```

Test coverage includes:

- API auth/register/login/JWT
- Feed, posts, comments, likes, follows
- Permissions and ownership rules
- Healthcheck and request ID header presence

## CI pipeline

GitHub Actions workflow at `.github/workflows/ci.yml` runs on push/PR:

- install dependencies
- run migrations
- run test suite

## Suggested next milestones

- Add `pytest-cov` gate in CI (minimum coverage threshold).
- Add Sentry for production error tracking.
- Add Redis cache backend for production feed caching.
- Ship a Next.js frontend consuming this API as a dedicated full-stack showcase.

## License

MIT
