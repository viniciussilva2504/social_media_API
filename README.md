# ant.social — anti social media

A minimalist Twitter clone built with Django + Django REST Framework.
*"go read a book"*

---

## Features

- **Authentication**: Register, login, logout with token-based auth (API) and session-based auth (web)
- **Profiles**: Display name, bio, profile picture, password change
- **Follow system**: Follow/unfollow users, see followers/following lists
- **Feed**: Posts from people you follow (+ your own)
- **Posts**: Create, edit, delete (280 char limit)
- **Likes**: Toggle likes on posts
- **Comments**: Comment on any post
- **Search**: Find users by username
- **REST API**: Full API at `/antisocial/v1/`

---

## Tech Stack

- **Backend**: Python 3.14 + Django 6.0 + Django REST Framework
- **Database**: SQLite (dev) / PostgreSQL (Docker/prod)
- **Frontend**: Django Templates + Vanilla JS
- **Containerization**: Docker + Docker Compose

---

## Quick Start (Local)

```bash
# 1. Clone the repo
git clone https://github.com/viniciussilva2504/social_media_API.git
cd social_media_API

# 2. Install dependencies
poetry install --only main --no-root

# 3. Run migrations
poetry run python manage.py migrate

# 4. Create superuser (optional)
poetry run python manage.py createsuperuser

# 5. Run server
poetry run python manage.py runserver
```

Open **http://127.0.0.1:8000/**

---

## Docker Setup

### Build and Run

```bash
# Build and start containers
docker compose build
docker compose up -d

# Run migrations inside container
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser
```

### Using Makefile

```bash
make build          # Build Docker image
make run            # Start containers
make migrate        # Apply migrations
make superuser      # Create superuser
make stop           # Stop containers
make shell          # Access container shell
make clean          # Remove everything
```

### Docker Environment Variables

Edit `env.dev` for development:

```
DEBUG=1
SECRET_KEY=your-secret-key
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=basic_dev_db
SQL_USER=basic_dev
SQL_PASSWORD=basic_dev
SQL_HOST=db
SQL_PORT=5432
```

---

## REST API Endpoints

Base URL: `/antisocial/v1/`

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/antisocial/v1/register/` | Register new user |
| POST | `/antisocial/v1/login/` | Login (returns token) |
| POST | `/api-token-auth/` | Get auth token |

### Profiles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/antisocial/v1/profile/` | List all profiles |
| GET | `/antisocial/v1/profile/{username}/` | Get profile |
| PATCH | `/antisocial/v1/profile/me/` | Update own profile |
| GET | `/antisocial/v1/users/?q=search` | Search users |

### Follow
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/antisocial/v1/follow/toggle/{username}/` | Follow/Unfollow |
| GET | `/antisocial/v1/follow/followers/{username}/` | Get followers |
| GET | `/antisocial/v1/follow/following/{username}/` | Get following |

### Posts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/antisocial/v1/post/` | List all posts |
| POST | `/antisocial/v1/post/` | Create post |
| GET | `/antisocial/v1/post/{id}/` | Get post |
| PUT/PATCH | `/antisocial/v1/post/{id}/` | Edit post |
| DELETE | `/antisocial/v1/post/{id}/` | Delete post |

### Feed
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/antisocial/v1/feed/` | Get feed (followed users' posts) |

### Likes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/antisocial/v1/like/toggle/{post_id}/` | Like/Unlike post |

### Comments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/antisocial/v1/comment/?post_id={id}` | List comments |
| POST | `/antisocial/v1/comment/` | Create comment |
| DELETE | `/antisocial/v1/comment/{id}/` | Delete comment |

### API Authentication

Use Token auth header:
```
Authorization: Token your-token-here
```

---

## Deploy to PythonAnywhere

### Step-by-step guide

#### 1. Create PythonAnywhere Account
- Go to [pythonanywhere.com](https://www.pythonanywhere.com/)
- Sign up for a free account (or paid for custom domain)
- Your site will be at: `https://YOURUSERNAME.pythonanywhere.com`

#### 2. Open a Bash Console
On PythonAnywhere dashboard → **"Consoles"** → **"Bash"**

#### 3. Clone the Repository

```bash
cd ~
git clone https://github.com/viniciussilva2504/social_media_API.git
```

#### 4. Create Virtual Environment

```bash
cd ~/social_media_API
python3.10 -m venv .venv
source .venv/bin/activate
```

> **Note**: PythonAnywhere may not have Python 3.14. Use the latest available version (e.g., 3.10, 3.12). Check with: `python3 --version`

#### 5. Install Dependencies

```bash
pip install django djangorestframework Pillow
```

#### 6. Configure Settings for Production

Edit `social_media/settings.py` or create environment variables:

```bash
export SECRET_KEY='your-strong-random-secret-key-here'
export DEBUG=0
export DJANGO_ALLOWED_HOSTS='YOURUSERNAME.pythonanywhere.com'
```

**Or** edit `social_media/settings.py` directly:

```python
DEBUG = 0
ALLOWED_HOSTS = ['YOURUSERNAME.pythonanywhere.com']
SECRET_KEY = 'generate-a-strong-key-here'
```

To generate a secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### 7. Run Migrations

```bash
cd ~/social_media_API
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

#### 8. Configure Web App on PythonAnywhere

Go to **"Web"** tab → **"Add a new web app"**:

1. Choose **"Manual configuration"** (NOT Django)
2. Select the Python version matching your virtualenv

#### 9. Set Virtualenv Path

In the Web tab, under **"Virtualenv"**:
```
/home/YOURUSERNAME/social_media_API/.venv
```

#### 10. Configure WSGI File

Click on the WSGI configuration file link (`/var/www/YOURUSERNAME_pythonanywhere_com_wsgi.py`)

Replace ALL contents with:

```python
import os
import sys

# Add your project directory to the sys.path
project_home = '/home/YOURUSERNAME/social_media_API'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'social_media.settings'
os.environ['SECRET_KEY'] = 'your-strong-random-secret-key-here'
os.environ['DEBUG'] = '0'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'YOURUSERNAME.pythonanywhere.com'

# Activate your virtual env
activate_this = '/home/YOURUSERNAME/social_media_API/.venv/bin/activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

> **Replace `YOURUSERNAME`** with your actual PythonAnywhere username.

#### 11. Configure Static Files

In the Web tab, under **"Static files"**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOURUSERNAME/social_media_API/staticfiles` |
| `/media/` | `/home/YOURUSERNAME/social_media_API/media` |

#### 12. Create Media Directory

```bash
mkdir -p ~/social_media_API/media/profile_pics
```

#### 13. Reload Web App

Click **"Reload"** button on the Web tab.

Your app is now live at: `https://YOURUSERNAME.pythonanywhere.com/`

---

### Updating the Deployed App

```bash
cd ~/social_media_API
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt  # if dependencies changed
python manage.py migrate         # if models changed
python manage.py collectstatic --noinput
```

Then click **"Reload"** on the Web tab.

---

### Exporting requirements.txt (for PythonAnywhere)

If PythonAnywhere doesn't support Poetry, export to requirements.txt:

```bash
# On your local machine
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

Or create `requirements.txt` manually:
```
django>=5.0,<7.0
djangorestframework>=3.14,<4.0
Pillow>=10.0,<12.0
```

---

## Project Structure

```
social_media_API/
├── social_media/           # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/               # User auth, profiles, follows
│   ├── models/
│   │   ├── profile.py
│   │   └── follow.py
│   ├── serializers/
│   │   ├── auth_serializer.py
│   │   ├── profile_serializer.py
│   │   └── follow_serializer.py
│   ├── viewsets/
│   │   ├── auth_viewset.py
│   │   ├── profile_viewset.py
│   │   └── follow_viewset.py
│   ├── views.py            # Template views
│   ├── urls.py             # Web URLs
│   └── api_urls.py         # REST API URLs
├── posts/                  # Posts, likes, comments, feed
│   ├── models/
│   │   ├── post.py
│   │   ├── like.py
│   │   └── comment.py
│   ├── serializers/
│   │   ├── post_serializer.py
│   │   ├── like_serializer.py
│   │   └── comment_serializer.py
│   ├── viewsets/
│   │   ├── post_viewset.py
│   │   ├── like_viewset.py
│   │   ├── comment_viewset.py
│   │   └── feed_viewset.py
│   ├── views.py            # Template views
│   ├── urls.py             # Web URLs
│   └── api_urls.py         # REST API URLs
├── templates/              # HTML templates
├── static/                 # CSS + JS
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── env.dev
```

---

## License

MIT
