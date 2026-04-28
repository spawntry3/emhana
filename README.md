# i-Emhana — учёт приёмов поликлиники

Веб-приложение для регистратуры поликлиники: ведение пациентов, врачей и приёмов, BI-дашборд с графиками, живой поиск, пагинация. Написано на **Python / Django 5 / Bootstrap 5 / Chart.js**.

## Возможности

- Авторизация сотрудников (Django auth).
- Регистрация пациентов и приёмов (формы с серверной валидацией ИИН и телефона).
- Список приёмов с **пагинацией**, фильтрами (статус, врач) и **AJAX-поиском** по ИИН/ФИО.
- BI-дашборд:
  - KPI-виджеты (пациентов / приёмов сегодня / за период / в ожидании);
  - линейный график динамики приёмов с **переключателем периода** (7д / 30д / 6м / 1г);
  - круговая диаграмма (Doughnut) распределения статусов.
- Адаптивная вёрстка под мобильные.
- Кастомные management-команды:
  - `import_json` — импорт начальных данных из JSON;
  - `seed_fake` — генерация 1000+ записей через Faker.
- Готовая к продакшену конфигурация (env-переменные, HSTS, secure cookies, `collectstatic`).

## Стек

| Слой        | Технология                  |
|-------------|-----------------------------|
| Backend     | Python 3.11+, Django 5.2    |
| Frontend    | Bootstrap 5, Chart.js, FontAwesome |
| База данных | SQLite (dev) / PostgreSQL (prod, опц.) |
| Prod-сервер | Gunicorn + Nginx            |

---

## Локальный запуск (Windows / macOS / Linux)

```bash
git clone <repo-url> emhana
cd emhana

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser

# Опционально — данные:
python manage.py import_json mock_data.json     # ручной набор
python manage.py seed_fake --patients 500 --appointments 2000   # генерация

python manage.py runserver
```

Откройте `http://127.0.0.1:8000/`. Админка — `/admin/`.

---

## Структура проекта

```text
emhana/
├── config/                  # настройки Django-проекта
│   ├── settings.py
│   └── urls.py
├── emhana/                  # приложение
│   ├── models.py            # Patient, Doctor, Appointment
│   ├── views.py             # дашборд, список, создание, AJAX
│   ├── admin.py
│   ├── urls.py
│   ├── templates/           # base, login, dashboard, appointment_*
│   │   └── partials/        # фрагменты для AJAX
│   ├── static/emhana/       # исходные CSS/JS приложения (коммитятся)
│   └── management/commands/
│       ├── import_json.py
│       └── seed_fake.py
├── mock_data.json           # пример данных
├── requirements.txt
├── .env.example             # шаблон переменных окружения
└── manage.py
```

---

## Переменные окружения

Скопируйте `.env.example` → `.env` и заполните. На проде значения выставляются через systemd / панель хостинга / `export`.

| Переменная                     | Назначение                              | Пример (prod)                              |
|--------------------------------|-----------------------------------------|--------------------------------------------|
| `DJANGO_SECRET_KEY`            | секрет Django (50+ случайных символов)  | `xK9#mPq...`                               |
| `DJANGO_DEBUG`                 | режим отладки                            | `False`                                     |
| `DJANGO_ALLOWED_HOSTS`         | домены через запятую                    | `i-emhana.kz,www.i-emhana.kz`              |
| `DJANGO_CSRF_TRUSTED_ORIGINS`  | origin'ы со схемой через запятую         | `https://i-emhana.kz`                      |

Сгенерировать новый `SECRET_KEY`:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Деплой на Linux-сервер (Ubuntu 22.04 + Nginx + Gunicorn)

### 1. Подготовка сервера

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git
# Если используете PostgreSQL:
# sudo apt install -y postgresql libpq-dev
```

### 2. Деплой кода

```bash
sudo mkdir -p /var/www/emhana && sudo chown $USER:$USER /var/www/emhana
cd /var/www/emhana
git clone <repo-url> .

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Создаём `.env`

```bash
cp .env.example .env
nano .env   # вписываем реальные значения
```

### 4. Миграции и статика

```bash
set -a; source .env; set +a   # экспортируем переменные в текущую сессию
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 5. systemd-сервис для Gunicorn

`/etc/systemd/system/emhana.service`:

```ini
[Unit]
Description=Emhana Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/emhana
EnvironmentFile=/var/www/emhana/.env
ExecStart=/var/www/emhana/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/run/emhana.sock \
          config.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo chown -R www-data:www-data /var/www/emhana
sudo systemctl daemon-reload
sudo systemctl enable --now emhana
sudo systemctl status emhana
```

### 6. Конфиг Nginx

`/etc/nginx/sites-available/emhana`:

```nginx
server {
    listen 80;
    server_name i-emhana.kz www.i-emhana.kz;

    # Перенаправление на HTTPS (после получения сертификата)
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name i-emhana.kz www.i-emhana.kz;

    ssl_certificate     /etc/letsencrypt/live/i-emhana.kz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/i-emhana.kz/privkey.pem;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/emhana/staticfiles/;
        expires 30d;
        access_log off;
    }

    location /media/ {
        alias /var/www/emhana/media/;
    }

    location / {
        proxy_pass http://unix:/run/emhana.sock;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/emhana /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 7. SSL (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d i-emhana.kz -d www.i-emhana.kz
```

### 8. Обновление кода

```bash
cd /var/www/emhana
source venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart emhana
```

---

## Проверка безопасности

После настройки запустите:
```bash
python manage.py check --deploy
```
Все ошибки должны быть устранены. Предупреждение `security.W008` (`SECURE_SSL_REDIRECT`) допустимо, если редирект http→https делает Nginx.

---

## Лицензия

MIT — учебный проект.
