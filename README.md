# 📰 IUBAT Campus Newspaper Portal

A complete campus newspaper web application for the **International University of
Business Agriculture and Technology (IUBAT)**, built with Django 5, Django REST
Framework, Tailwind CSS and Alpine.js.

The portal supports a full editorial workflow: students submit articles, editors
review/approve/reject them, faculty can auto-publish, readers comment and react,
and a newsletter system reaches subscribers. A REST API with JWT authentication
is included for mobile/SPA clients.

---

## Table of contents

1. [Features](#-features)
2. [Tech stack](#-tech-stack)
3. [Roles & permissions](#-roles--permissions)
4. [Project structure](#-project-structure)
5. [Quick start](#-quick-start)
6. [Environment variables](#-environment-variables)
7. [Seed data & demo accounts](#-seed-data--demo-accounts)
8. [REST API](#-rest-api)
9. [Models overview](#-models-overview)
10. [Editorial workflow](#-editorial-workflow)
11. [Testing](#-testing)
12. [Deployment](#-deployment)
13. [9-week learning roadmap](#-9-week-learning-roadmap)
14. [Migrations notes](#-migrations-notes)

---

## ✨ Features

- **Homepage** — featured hero, latest news, weekly trending (view-based
  analytics), breaking-news ticker, per-category sections (cached).
- **7 sections** — Campus News, Events, Sports, Academic, Clubs, Achievements,
  Notice Board.
- **Article detail** — rich text (TinyMCE), featured image + caption, threaded
  comments (one level of replies), 👍/❤️/💡 reactions, share menu, reading
  time, related stories, JSON-LD `NewsArticle` structured data.
- **Search & filtering** — full-text-style Q-object search, category, tag,
  author, year/month archives, featured flag, sorting (newest/oldest/popular),
  pagination.
- **Submission & approval workflow** — draft → pending → published/rejected,
  rejection reasons, faculty/editor auto-publish, author "my articles" queue.
- **Editor dashboard** — stats, Chart.js visuals (views/day, articles per
  category, users per role), pending queue, review screen, comment moderation.
- **Admin user & category management** — role changes, verification, active
  flags, category CRUD.
- **Comments** — verified users post instantly; unverified users join a
  moderation queue; editors approve/hide/delete.
- **Newsletter** — footer subscribe (AJAX + no-JS fallback), tokenised
  unsubscribe, staff composer, BCC bulk send.
- **SEO** — slugs auto-generated for every model, meta/OG tags, sitemap.xml,
  robots.txt, canonical URLs, `noindex` on unpublished work.
- **IUBAT branding** — green `#006400` + white theme, fully responsive
  (mobile menu, responsive grids).
- **Caching & pagination** — local-memory cache for trending/sections,
  per-IP hourly view throttling.
- **REST API** — JWT auth, viewsets, nested serializers, django-filter
  filtering/search/ordering, custom permissions.

## 🧰 Tech stack

| Layer        | Technology                                              |
|--------------|---------------------------------------------------------|
| Backend      | Django 5.1, Class-Based Views                           |
| API          | Django REST Framework, djangorestframework-simplejwt    |
| Database     | SQLite (dev) / PostgreSQL via `DATABASE_URL` (prod)     |
| Frontend     | Django templates, Tailwind CSS (CDN config), Alpine.js  |
| Rich text    | django-tinymce                                           |
| Images       | Pillow (local media; Cloudinary hook optional)          |
| Filtering    | django-filter                                            |
| Auth         | Django auth + custom user model, SimpleJWT               |
| Static prod  | WhiteNoise                                               |
| Config       | python-decouple (`.env`), dj-database-url                |

## 👥 Roles & permissions

| Capability                         | Reader | Student | Faculty | Editor | Admin |
|------------------------------------|:------:|:-------:|:-------:|:------:|:-----:|
| Read published articles            |   ✅   |   ✅    |   ✅    |  ✅    |  ✅   |
| Comment / react                    |   ✅   |   ✅    |   ✅    |  ✅    |  ✅   |
| Submit articles                    |   ❌   |   ✅    |   ✅    |  ✅    |  ✅   |
| Auto-publish (skip approval)       |   ❌   |   ❌    |   ✅    |  ✅    |  ✅   |
| Approve / reject articles          |   ❌   |   ❌    |   ❌    |  ✅    |  ✅   |
| Moderate comments                  |   ❌   |   ❌    |   ❌    |  ✅    |  ✅   |
| Manage categories / newsletters    |   ❌   |   ❌    |   ❌    |  ✅    |  ✅   |
| Manage users                       |   ❌   |   ❌    |   ❌    |  ❌    |  ✅   |
| Django admin                       |   ❌   |   ❌    |   ❌    |  ✅    |  ✅   |

Role logic lives in `apps/accounts/roles.py` (single source of truth) with
helper properties on `CustomUser` (`can_submit_articles`, `can_auto_publish`,
`is_editor_role`, …), view mixins in `apps/accounts/mixins.py`, function
decorators in `apps/accounts/decorators.py`, and DRF permissions in
`apps/api/permissions.py`.

---

## 📁 Project structure

```text
iubatnewsPaper/
├── manage.py
├── requirements.txt
├── .env.example
├── config/                         # Django project package
│   ├── settings.py                 # All configuration (dev/prod aware)
│   ├── urls.py                     # Root routes + sitemap
│   ├── wsgi.py / asgi.py
├── apps/
│   ├── accounts/                   # Custom user, roles, profiles, auth
│   │   ├── models.py managers.py roles.py mixins.py decorators.py
│   │   ├── forms.py views.py urls.py admin.py signals.py tests.py
│   ├── articles/                   # Categories, tags, articles, comments…
│   │   ├── models.py managers.py forms.py views.py urls.py
│   │   ├── admin.py signals.py context_processors.py tests.py
│   │   └── management/commands/seed.py
│   ├── core/                       # Homepage view, about/contact, sitemaps
│   ├── dashboard/                  # Editor/admin panels, analytics
│   ├── newsletter/                 # Subscribers & campaigns
│   └── api/                        # DRF viewsets, serializers, JWT routes
├── templates/                      # base.html + per-app templates
│   ├── articles/ accounts/ dashboard/ newsletter/ core/ includes/
├── static/                         # css/main.css, js/main.js, img/
└── media/                          # Uploaded images (git-ignored)
```

---

## 🚀 Quick start

```bash
# 1. Clone & enter
git clone https://github.com/Mausd34/iubatnewsPaper.git
cd iubatnewsPaper

# 2. Virtual environment
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env        # SQLite is used if DATABASE_URL is empty

# 5. Migrate
python manage.py migrate

# 6. Seed demo content (categories, users, 16 articles, comments, views…)
python manage.py seed

# 7. Run
python manage.py runserver
```

Open <http://127.0.0.1:8000>.

Useful extras:

```bash
python manage.py createsuperuser     # your own superuser
python manage.py seed --reset        # wipe articles/comments/views & reseed
python manage.py test apps           # run the test suite (45 tests)
python manage.py collectstatic       # production static bundling
```

## 🔐 Environment variables

Copy `.env.example` to `.env`. Key settings (see `config/settings.py`):

| Variable               | Purpose                                             |
|------------------------|-----------------------------------------------------|
| `SECRET_KEY`           | Django secret (change in production)                |
| `DEBUG`                | `True` locally, `False` in production               |
| `ALLOWED_HOSTS`        | Comma-separated hostnames                           |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins for HTTPS deploys           |
| `DATABASE_URL`         | Empty = SQLite; e.g. `postgres://user:pass@host/db` |
| `EMAIL_BACKEND`        | Console in dev; SMTP in production                  |
| `DEFAULT_FROM_EMAIL`   | From address for newsletters/contact mail           |
| `CLOUDINARY_*`         | Optional cloud media storage                        |

## 🌱 Seed data & demo accounts

`python manage.py seed` is **idempotent** (uses `get_or_create`, safe to
re-run) and `--reset` wipes editorial data first.

| Account  | Password     | Role                |
|----------|--------------|---------------------|
| `admin`  | `admin123`   | Admin (superuser)   |
| `editor` | `editor123`  | Editor              |
| `faculty`| `faculty123` | Faculty (auto-publish) |
| `student`| `student123` | Student contributor |
| `reader` | `reader123`  | Reader              |

It creates the 7 categories, 17 tags, 16 published articles (with views,
reactions, comments), 2 pending articles, 1 rejected article with feedback,
and 4 newsletter subscribers.

> Change these passwords immediately in any real deployment.

---

## 🔌 REST API

Browsable API: <http://127.0.0.1:8000/api/>

### Authentication (JWT)

```bash
# Obtain a token pair
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"student","password":"student123"}'

# Use the access token
curl http://localhost:8000/api/articles/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Refresh when the access token expires (60 min)
POST /api/token/refresh/   {"refresh": "..."}
```

### Endpoints

| Method & URL                              | Access                | Notes                                        |
|-------------------------------------------|-----------------------|----------------------------------------------|
| `GET /api/articles/`                      | public                | pagination, `?search=`, `?category=slug`, `?tag=slug`, `?author=username`, `?status=`, `?featured=`, `?created_after=`, `?ordering=views_count` |
| `GET /api/articles/{id}/`                 | public (+ owner/staff see unpublished) | nested author/category/tags, reaction counts |
| `POST /api/articles/`                     | contributors          | body field `workflow`: `save_draft`/`submit`/`publish` |
| `PATCH/PUT/DELETE /api/articles/{id}/`    | author or editor      | `IsAuthorOrEditor`                           |
| `GET /api/articles/featured/`             | public                | hero/featured feed                           |
| `GET /api/articles/trending/`             | public                | most viewed in the trailing 7 days           |
| `POST /api/articles/{id}/publish/`        | editor/admin          | immediate publish                            |
| `POST /api/articles/{id}/reject/`         | editor/admin          | `{"reason": "10+ chars"}`                    |
| `GET/POST /api/categories/`               | GET public / POST editor+ | `IsEditorOrAdmin`                        |
| `PATCH/DELETE /api/categories/{slug}/`    | editor+               | lookup by slug                               |
| `GET /api/tags/`                          | public                | read-only                                    |
| `GET/POST /api/comments/`                 | GET public / POST auth | filter `?article=slug&approved=true`        |
| `PATCH/DELETE /api/comments/{id}/`        | owner or editor       | `IsOwnerOrReadOnly`                          |
| `GET/POST /api/reactions/`                | POST auth             | one reaction per user; repeat toggles/updates |

Example article creation as a student (enters the pending queue):

```bash
curl -X POST http://localhost:8000/api/articles/ \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{
    "title": "My Campus Story",
    "category_slug": "campus-news",
    "tag_slugs": ["tech"],
    "excerpt": "A 20–300 character summary of the story.",
    "content": "<p>The body HTML.</p>",
    "workflow": "submit"
  }'
```

---

## 🗃 Models overview

**accounts** — `CustomUser(AbstractUser)`: `role`, `student_id`, `department`,
`batch`, `profile_picture`, `bio`, `phone`, `is_verified`; custom
`CustomUserManager`; role permission properties; signals sync the Django
`is_staff`/`is_superuser` flags and auto-verify faculty.

**articles**
- `Category(name, slug, description, icon, order, is_active)`
- `Tag(name, slug)`
- `Article(title, slug, author FK, category FK, tags M2M, featured_image,
  image_caption, excerpt, content, status, is_featured, is_breaking,
  views_count, rejection_reason, reviewed_by, submitted_at, published_at,
  timestamps)` — workflow methods `submit()`, `publish(reviewer)`,
  `reject(reason, reviewer)`, plus `reading_time`, `related_articles()`,
  `reaction_counts()`.
- `Comment(article, user, body, parent self-FK, is_approved, timestamps)`
- `Reaction(article, user, reaction_type)` — unique per user+article.
- `ArticleView(article, user, ip, user_agent, referrer, timestamp)` —
  analytics; a `post_save` signal atomically bumps `views_count`.

**newsletter**
- `Subscriber(email, full_name, is_active, token UUID, subscribed_at,
  unsubscribed_at)`
- `NewsletterEmail(subject, slug, body, status, recipients_count, created_by,
  sent_at)` with a `send(user)` helper (BCC via `EmailMultiAlternatives`).

All slugs are auto-generated by `apps/articles/signals.py` with uniqueness
loops. Managers add `Article.objects.published()/.pending()/.featured()/
.trending()/.popular()/.search(q)`, `Category.objects.active()/
.with_article_counts()`, and `Comment.objects.approved()/
.pending_moderation()`. Every model has `Meta` ordering/indexes/verbose names,
`__str__`, and public models implement `get_absolute_url()`.

## 🔁 Editorial workflow

```text
Student writes ──► Draft ──submit──► Pending ──editor approves──► Published
                     ▲                  │
                     │              editor rejects (reason)
                     └──────────► Rejected ──edit/resubmit──► Pending

Faculty / Editor: Draft ──► Published directly ("Publish now")
```

1. Student contributors see **Save draft** and **Submit for approval**.
2. Editors get a pending-queue badge in the dashboard sidebar.
3. Review screen shows the full story with **Approve & publish** and a
   **Reject with feedback** (reason required, min 10 chars).
4. Rejected students see the reason on the article and in "My articles", and
   can edit and resubmit.
5. Same workflow is available through the API (`workflow` field +
   `publish`/`reject` actions).

## 🧪 Testing

45 tests across the apps cover roles/signals, slug generation, managers,
the approval workflow, public pages, view throttling, comments, reactions,
newsletter subscriptions/campaigns, and the JWT API with permission checks:

```bash
python manage.py test apps            # all tests
python manage.py test apps.api        # just the API tests
```

---

## ☁️ Deployment

### PostgreSQL (local check)

```bash
createdb iubat_news
export DATABASE_URL="postgres://user:password@localhost:5432/iubat_news"
pip install "psycopg[binary]"
python manage.py migrate
```

### Production settings checklist

- `DEBUG=False`, strong `SECRET_KEY`, locked-down `ALLOWED_HOSTS` and
  `CSRF_TRUSTED_ORIGINS`.
- Collect static files (WhiteNoise serves them with cache hashing):
  `python manage.py collectstatic --no-input`.
- Use a real email backend (SMTP/SendGrid/Mailgun).
- Run `gunicorn config.wsgi:application --bind 0.0.0.0:8000`
  (`pip install gunicorn`).
- Run migrations on release; seed only if you want demo data.
- Security headers (HSTS, secure cookies) are enabled automatically when
  `DEBUG=False`.

### Railway / Render

1. New Web Service from this repo, start command
   `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`.
2. Add the managed PostgreSQL service → it sets `DATABASE_URL` automatically.
3. Set `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=<your-app>.up.railway.app`
   and the same host in `CSRF_TRUSTED_ORIGINS` (`https://…`).
4. Release command: `python manage.py migrate && python manage.py
   collectstatic --no-input`.
5. Persistent disk mounted at `/app/media` for uploads (or use Cloudinary).

### Cloudinary (optional)

`pip install cloudinary`, then set `CLOUDINARY_CLOUD_NAME`,
`CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`. Swap the `default` storage in
`STORAGES` for `cloudinary_storage.storage.MediaCloudinaryStorage`.

### PythonAnywhere

Use the manual virtualenv + WSGI (`/var/www/...`) setup, configure the
Postgres or MySQL database, run `collectstatic`, and point the static files
mapping at `staticfiles/`.

---

## 📅 9-week learning roadmap

This is the suggested build/learning sequence. The repository already
contains the finished code for every week — use the roadmap to rebuild and
learn it yourself.

### Week 1 — Project setup (detailed below)
Virtualenv, Django install, project + apps, settings (static/media/templates),
custom user model + first migration, Git + `.gitignore`.
**Delivered:** `config/settings.py`, `apps/accounts/`, this week's code.

### Week 2 — Core models
All models with fields/validators/Meta/`__str__`/`get_absolute_url`,
custom managers, signals (slugs, view counts, comment auto-moderation),
full `admin.py` registrations, then the `seed` command and shell testing.
- Run: `python manage.py makemigrations && python manage.py migrate`
- Learn: Django ORM relationships, `select_related`/`prefetch_related`,
  aggregation, the admin.
- Resources: [Django models](https://docs.djangoproject.com/en/5.0/topics/db/models/),
  [managers](https://docs.djangoproject.com/en/5.0/topics/db/managers/),
  [signals](https://docs.djangoproject.com/en/5.0/topics/signals/).

### Week 3 — Authentication & roles
Register/login/logout views, role-based mixins & decorators, profile detail/
edit pages, verification badge, navbar account menu.
- Resources: [Django auth](https://docs.djangoproject.com/en/5.0/topics/auth/default/),
  [Using auth views](https://docs.djangoproject.com/en/5.0/topics/auth/default/#module-django.contrib.auth.views).

### Week 4 — Article CRUD & workflow
Create/update/delete CBVs with image upload, TinyMCE, the draft/pending/
published/rejected state machine, editor approve/reject screens, "my articles".
- Resources: [Class-based views](https://docs.djangoproject.com/en/5.0/topics/class-based-views/generic-display/),
  [file uploads](https://docs.djangoproject.com/en/5.0/topics/http/file-uploads/).

### Week 5 — Frontend templates
`base.html`, homepage hero/sections, list & detail pages, Tailwind
configuration/branding, responsive nav, partials (`article_card`, pagination).
- Resources: [Tailwind docs](https://tailwindcss.com/docs),
  [Alpine.js](https://alpinejs.dev/start-here), Django template language.

### Week 6 — Comments, reactions, search
AJAX comment form with JSON responses, threaded replies, reaction toggles,
Q-object search, filters (category/tag/date/author/sort).
- Resources: [Q objects](https://docs.djangoproject.com/en/5.0/topics/db/queries/#complex-lookups-with-q-objects),
  [Fetch API](https://developer.mozilla.org/docs/Web/API/Fetch_API/Using_Fetch).

### Week 7 — Dashboard & analytics
Stat cards, Chart.js line/doughnut charts fed by ORM aggregation,
comment moderation, user management (admin), category CRUD.
- Resources: [Chart.js](https://www.chartjs.org/docs/latest/),
  [Django aggregation](https://docs.djangoproject.com/en/5.0/topics/db/aggregation/).

### Week 8 — API, newsletter, SEO
DRF serializers/viewsets/routers, SimpleJWT, django-filter, custom
permissions; newsletter subscribe/unsubscribe/composer/send; sitemap,
robots.txt, Open Graph & JSON-LD.
- Resources: [DRF tutorial](https://www.django-rest-framework.org/tutorial/quickstart/),
  [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/),
  [sitemaps](https://docs.djangoproject.com/en/5.0/ref/contrib/sitemaps/).

### Week 9 — Testing & deployment
Write tests (models, views, permissions, API), configure PostgreSQL,
WhiteNoise/Gunicorn, deploy to Railway/Render/PythonAnywhere, optionally
Cloudinary; set up CI.
- Resources: [Testing in Django](https://docs.djangoproject.com/en/5.0/topics/testing/overview/),
  [DRDF testing](https://www.django-rest-framework.org/api-guide/testing/),
  [Django deployment checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/).

---

### 🗓 Week 1 in detail

**Goal:** a running Django project with six apps, working settings, and the
custom user migrated *before* any other data.

**1.1 — Virtual environment & Django (commands)**

```bash
mkdir iubatnewsPaper && cd iubatnewsPaper
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install "Django>=5.0,<5.2" djangorestframework \
  djangorestframework-simplejwt django-filter Pillow django-cors-headers \
  python-decouple dj-database-url django-tinymce whitenoise
pip freeze > requirements.txt
django-admin startproject config .
python manage.py migrate
python manage.py runserver           # confirm the welcome screen works
```

**1.2 — Create the six apps inside an `apps/` package**

```bash
mkdir -p apps && touch apps/__init__.py
# startapp needs the target folder to exist, then pass [name] [directory]:
for app in accounts articles core dashboard newsletter api; do
  mkdir -p apps/$app
  python manage.py startapp $app apps/$app
  touch apps/$app/migrations/__init__.py
done
```

Then edit each `apps/<app>/apps.py` to read:

```python
class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
```

and add `"apps.accounts"`, … to `INSTALLED_APPS` in `config/settings.py`.

**1.3 — Settings to configure (all already done in this repo)**

- `INSTALLED_APPS`: DRF, SimpleJWT, filter, corsheaders, tinymce, sitemaps,
  sites, humanize + the six local apps.
- `TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]`.
- `STATIC_URL`/`STATICFILES_DIRS`/`STATIC_ROOT`, `MEDIA_URL`/`MEDIA_ROOT`;
  in dev, serve media from `config/urls.py` with `static(...)`.
- `AUTH_USER_MODEL = "accounts.CustomUser"` **before the first migration**.
- `REST_FRAMEWORK` (JWT + session auth, pagination, filter backends),
  `SIMPLE_JWT` token lifetimes.
- Login/logout redirect URLs, `TIME_ZONE = "Asia/Dhaka"`, the cache config,
  and the `IUBAT_BRAND` dictionary used by templates.
- `.env` values via `python-decouple`; SQLite default with a
  `DATABASE_URL` override for PostgreSQL.

**1.4 — Custom user model (minimum viable version)**

```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        READER = "reader", "Reader"
        STUDENT = "student", "Student Contributor"
        FACULTY = "faculty", "Faculty Author"
        EDITOR = "editor", "Editor"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices,
                            default=Role.READER)
```

Set `AUTH_USER_MODEL`, then:

```bash
python manage.py makemigrations accounts
python manage.py migrate
python manage.py createsuperuser    # confirm admin works
```

**1.5 — Git**

```bash
git init
# Use the provided .gitignore (ignores .venv, db.sqlite3, media, .env…)
git add .
git commit -m "Week 1: project setup and custom user model"
```

**Week 1 checklist:** project runs, `/admin/` logs in, six apps appear in
`INSTALLED_APPS`, the custom-user migration is applied, static and media
paths resolve, and `.env`/`.gitignore` are in place.

---

## 📝 Migrations notes

- The custom user migration (`accounts/0001_initial`) **must** precede
  migrations that FK to the user. All apps are already ordered correctly in
  the committed migrations.
- `Article.author` and `Article.category` use `on_delete=PROTECT` so
  published history isn't destroyed accidentally; `ArticleView.user` is
  `SET_NULL`.
- Category deletion is also guarded at the view level (a category with
  articles cannot be removed until articles are moved/deleted).
- Adding fields later? Always `makemigrations` after model changes and
  provide defaults for non-nullable additions:
  ```bash
  python manage.py makemigrations
  python manage.py sqlmigrate articles 0002   # inspect the SQL
  python manage.py migrate
  ```
- PostgreSQL: enable `pg_trxm`/full-text search later by swapping the
  `search()` Q queries for a `SearchVectorField` + GIN index.

---

## License

Built as an academic student project for IUBAT. Content templates are free to
adapt for your campus newspaper.
