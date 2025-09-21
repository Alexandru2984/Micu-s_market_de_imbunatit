# Micu’s Market — Django Marketplace

A production‑ready Django marketplace for listing & buying/selling items.  
Includes authentication with email confirmation (django‑allauth), category tree with icons, image galleries per listing, user profiles with avatars, favorites, reviews, pagination, and a clean production deploy (Gunicorn + Nginx + HTTPS).

> Project root assumed as `/home/micu/Micu_market`. Adjust paths for your environment.

---

## ✨ Features

- **Listings**: title, price, condition, negotiable, slug URLs, location (county/city), contact phone, status, images (gallery).
- **Categories**: parent/child hierarchy, `order` for sorting, `icon` (Font Awesome class), `is_active` toggle.
- **Auth**: email login & verification via **django‑allauth**; custom templates in `templates/account/`.
- **Profiles**: avatar (stored in `media/`), basic user info.
- **Reviews & ratings**: per user, average + pagination (template: `reviews/user_reviews.html`).
- **Favorites**, **search & filters**, **pagination**.
- **.env‑driven settings** (DEBUG, DB, email, hosts, CSRF, security).
- **Prod setup**: Gunicorn (systemd) + Nginx + Let’s Encrypt certificates.

---

## 🧱 Stack

- Python **3.12**
- Django **5.x** (logs show 5.2.5)
- PostgreSQL (recommended)
- django‑allauth
- Pillow (image processing)
- Gunicorn + Nginx (prod)
- Font Awesome (icons)

---

## 🗂️ Structure (overview)

```
Micu_market/
├─ manage.py
├─ .env                      # NOT committed
├─ requirements.txt
├─ Micu_market/              # settings/urls/wsgi
├─ accounts/                 # auth, custom views/forms/adapters
├─ categories/               # category models & views
├─ listings/                 # listing models/views/forms/images
├─ reviews/                  # user reviews
├─ favorites/                # saved items
├─ templates/
│  ├─ base.html
│  ├─ base_auth.html         # extends base.html
│  ├─ account/               # allauth overrides
│  └─ reviews/user_reviews.html
├─ static/
└─ media/
```

---

## 🚀 Local Development

1. **Clone & enter**
```bash
git clone <repo-url> Micu_market
cd Micu_market
```

2. **Virtualenv & deps**
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -U pip wheel
pip install -r requirements.txt
```

3. **Configuration** — create **`.env`** (see template below or download `.env.example`).

4. **Database** (Postgres)
```bash
sudo -u postgres psql
CREATE DATABASE micu_market ENCODING 'UTF8';
CREATE USER micu_market_user WITH PASSWORD 'change-me';
GRANT ALL PRIVILEGES ON DATABASE micu_market TO micu_market_user;
\q
```

5. **Migrate & superuser**
```bash
python manage.py migrate
python manage.py createsuperuser
```

6. **Run dev server**
```bash
python manage.py runserver
```
Open http://127.0.0.1:8000/

> **Dev email**: set `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` in `.env` so allauth confirmation links print in your terminal.

---

## 🔐 `.env` Example

Create `.env` in the project root:

```dotenv
# ----- Core -----
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=True
SITE_ID=1

# Hosts & CSRF (comma-separated)
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,market.micutu.com
CSRF_TRUSTED_ORIGINS=http://127.0.0.1,http://localhost,https://market.micutu.com

# ----- Database -----
DB_NAME=micu_market
DB_USER=micu_market_user
DB_PASSWORD=change-me
DB_HOST=127.0.0.1
DB_PORT=5432
# Or, if settings support it:
# DATABASE_URL=postgres://micu_market_user:change-me@127.0.0.1:5432/micu_market

# ----- Email (allauth) -----
# Dev:
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# Prod SMTP:
EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=notifications@market.micutu.com
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL="Micu's Market <notifications@market.micutu.com>"
EMAIL_TIMEOUT=5
ACCOUNT_DEFAULT_HTTP_PROTOCOL=http

# ----- Security (prod; enable when DEBUG=False) -----
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

Make sure `settings.py` reads these via `os.getenv`/`environ`. Keep `.env` out of git.

---

## ✉️ Email / Allauth

Useful settings:
```python
LOGIN_URL = '/accounts/custom/login/'
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.getenv('ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'https' if not DEBUG else 'http')
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/'
```
For slow SMTP, prefer port **587 + TLS** and `EMAIL_TIMEOUT=5`. In production, consider sending emails asynchronously (Celery or a threaded override of `DefaultAccountAdapter.send_mail`).

---

## 🗃️ Static & Media

- Run `python manage.py collectstatic` to populate `STATIC_ROOT` (e.g., `/home/micu/Micu_market/staticfiles/`).
- Media uploads live in `MEDIA_ROOT` (e.g., `/home/micu/Micu_market/media/`).
- Nginx should serve `/static/` and `/media/` directly (see deploy).

---

## 🧪 Seed Data

> Works with your models: `Category` (`name`, `slug`, `icon`, `parent`, `order`, `is_active`) and `Listing` (+ `ListingImage` with `related_name='images'`).

### A) Seed a small category tree + demo listings
```py
from django.utils.text import slugify
from decimal import Decimal
import random
from django.contrib.auth import get_user_model
from categories.models import Category
from listings.models import Listing

User = get_user_model()
owner, _ = User.objects.get_or_create(email="seed@micutu.com", defaults={"username":"seed_user"})
if not owner.has_usable_password():
    owner.set_password("seed1234"); owner.save(update_fields=["password"])

CATS = [
    ("Electronice", "fa-solid fa-mobile-screen", [
        ("Telefoane", "fa-solid fa-mobile-screen-button"),
        ("Laptopuri", "fa-solid fa-laptop"),
        ("Audio", "fa-solid fa-headphones-simple"),
    ]),
    ("Vehicule", "fa-solid fa-car", [
        ("Autoturisme", "fa-solid fa-car-side"),
        ("Motociclete", "fa-solid fa-motorcycle"),
    ]),
]

order = 0
leaf = []
for name, icon, subs in CATS:
    order += 10
    parent = Category.objects.get_or_create(
        slug=slugify(name),
        defaults=dict(name=name, icon=icon, parent=None, order=order, is_active=True)
    )[0]
    sub_order = 0
    for sname, sicon in subs:
        sub_order += 1
        sub = Category.objects.get_or_create(
            slug=slugify(f"{name}-{sname}"),
            defaults=dict(name=sname, icon=sicon, parent=parent, order=sub_order, is_active=True)
        )[0]
        leaf.append(sub)

CONDITIONS = ["new","like_new","good","fair","poor"]
for cat in leaf:
    for i in range(2):
        Listing.objects.create(
            owner=owner,
            title=f"{cat.name} – produs {i+1}",
            description=f"Anunț demo în {cat.name}. #SEED",
            price=Decimal(random.choice([49.99, 120, 199.9, 299, 899])),
            negotiable=random.choice([True, False]),
            status="active",
            condition=random.choice(CONDITIONS),
            category=cat,
            county="București", city="București", location="Sector 3",
            contact_phone="07" + "".join(str(random.randint(0,9)) for _ in range(8)),
        )
print("Seed OK")
```

### B) Add placeholder images (Pillow required)
```py
from io import BytesIO
from PIL import Image, ImageDraw
from django.core.files.base import ContentFile
from listings.models import Listing, ListingImage

created = 0
for lst in Listing.objects.all():
    if not lst.images.exists():
        img = Image.new("RGB", (1200, 800), color=(235,235,235))
        d = ImageDraw.Draw(img); d.text((40,40), (lst.title or "Anunț")[:28], fill=(50,50,50))
        buf = BytesIO(); img.save(buf, format="JPEG", quality=85)
        ListingImage.objects.create(listing=lst, image=ContentFile(buf.getvalue(), name=f"{(lst.slug or 'listing')}_placeholder.jpg"))
        created += 1
print("Placeholders:", created)
```

### C) Cleanup seed
```py
from listings.models import Listing, ListingImage
ListingImage.objects.filter(image__icontains='_placeholder.jpg').delete()
Listing.objects.filter(description__contains='#SEED').delete()
```

---

## ☁️ VPS Deploy (Ubuntu + Gunicorn + Nginx + HTTPS)

### 0) Prereqs
- DNS `A` → `market.micutu.com` to your VPS
- Packages:
```bash
sudo apt update
sudo apt install -y python3.12-venv python3-pip nginx postgresql certbot python3-certbot-nginx
```

### 1) App setup
```bash
cd /home/micu/Micu_market
python3.12 -m venv venv
source venv/bin/activate
pip install -U pip wheel
pip install -r requirements.txt

# env
cp .env.example .env  # or create based on README
# IMPORTANT: set DEBUG=False in production, set allowed hosts and CSRF trusted origins properly

python manage.py migrate
python manage.py collectstatic --noinput
```

### 2) Gunicorn (systemd)
`/etc/systemd/system/gunicorn.service`
```ini
[Unit]
Description=Gunicorn for Micu_market
After=network.target

[Service]
User=micu
Group=www-data
WorkingDirectory=/home/micu/Micu_market
Environment="PATH=/home/micu/Micu_market/venv/bin"
ExecStart=/home/micu/Micu_market/venv/bin/gunicorn -w 3 -b 127.0.0.1:8000 Micu_market.wsgi:application
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

### 3) Nginx
`/etc/nginx/sites-available/micu_market`
```nginx
server {
    listen 80;
    server_name market.micutu.com www.market.micutu.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name market.micutu.com www.market.micutu.com;

    ssl_certificate     /etc/letsencrypt/live/market.micutu.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/market.micutu.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 20M;

    location /static/ { alias /home/micu/Micu_market/staticfiles/; }
    location /media/  { alias /home/micu/Micu_market/media/; }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable & reload:
```bash
sudo ln -sf /etc/nginx/sites-available/micu_market /etc/nginx/sites-enabled/micu_market
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### 4) HTTPS
```bash
sudo certbot --nginx -d market.micutu.com -d www.market.micutu.com
```

### 5) Django production flags
```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.getenv('ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'https')
```
Also set **Sites** (Django admin) to `market.micutu.com`.

---

## 🛠️ Troubleshooting

- **TemplateDoesNotExist** (`account/login.html`) → keep templates in `templates/account/…` (singular). Restart Gunicorn.
- **BadMigrationError (no Migration class)** → delete placeholder/bad migration files and rerun `python manage.py migrate`.
- **Old code served** → kill stray Gunicorn instances; manage via systemd (`sudo systemctl restart gunicorn`).
- **Signup slow** → SMTP; use port 587 + `EMAIL_TIMEOUT=5` or async sending.
- **Detail page fails with no images** → add placeholder or template fallback.

---

## 📦 Requirements

Example `requirements.txt`:
```
Django>=5.0,<6.0
django-allauth
psycopg[binary]
Pillow
python-dotenv
gunicorn
```

Install:
```bash
pip install -r requirements.txt
```

---

## 🧹 Helpers

Dump/load:
```bash
python manage.py dumpdata categories.Category listings.Listing listings.ListingImage --indent 2 > backup_seed.json
python manage.py loaddata backup_seed.json
```

Delete user by email (shell):
```py
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(email__iexact="test@exemplu.com").exclude(is_superuser=True).delete()
```

---

## © License

Private project. All rights reserved.
