# Деплой через Git

Секреты (**`.env`**, **`*.pem`**) в репозиторий не коммитятся (см. `.gitignore`).

## На своём ПК

```bash
git add -A
git status   # убедитесь, что нет .env и ключей
git commit -m "Описание изменений"
git push origin main
```

## На сервере Ubuntu (EC2)

Один раз клонировать:

```bash
cd /home/ubuntu
git clone https://github.com/Alenik007/project-26-capstone.git
cd project-26-capstone
cp .env.example .env
nano .env   # OPENAI_API_KEY и при необходимости остальное
```

Дальше при каждом обновлении кода:

```bash
cd /home/ubuntu/project-26-capstone
git pull origin main
docker compose up --build -d
curl -s http://127.0.0.1/api/health
```

Проверка в браузере: `http://13.60.91.191` и `http://13.60.91.191/api/health`.

## Если репозиторий приватный

На сервере используйте **Deploy key** или **Personal Access Token** (HTTPS), либо `git pull` с машины, где уже настроен доступ.
