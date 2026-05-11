# AI Interview Coach

AI Interview Coach — приложение, которое анализирует вакансию, проводит mock-интервью и даёт обратную связь по ответам пользователя.

## Live Demo

- Frontend: http://13.60.91.191
- Backend healthcheck: http://13.60.91.191/api/health

## Возможности

- анализ вакансии с hh.ru (API → fallback на HTML);
- анализ текста вакансии (через LLM);
- генерация вопросов под конкретную вакансию;
- mock-интервью в чате;
- streaming-ответы (SSE);
- RAG по базе знаний интервью (Qdrant + embeddings);
- итоговая обратная связь;
- rate limiting на `/chat`;
- prompt injection protection;
- LangSmith tracing (переменные в `.env.example`).

## Стек

- FastAPI
- LangGraph + LangChain
- OpenAI API
- Qdrant
- Next.js (TypeScript/React)
- Docker + Docker Compose
- AWS EC2 Ubuntu + Nginx
- GitHub Actions

## Локальный запуск (Docker)

```bash
git clone https://github.com/<USERNAME>/project-26-capstone.git
cd project-26-capstone
cp .env.example .env
docker compose up --build
```

Frontend:

- http://localhost:3000

Backend:

- http://localhost:8000/health

## Переменные окружения

См. `.env.example`.

- `OPENAI_API_KEY`: ключ OpenAI
- `OPENAI_MODEL`: модель (по умолчанию `gpt-4o-mini`)
- `QDRANT_URL`: URL Qdrant (в docker-compose `http://qdrant:6333`)
- `QDRANT_COLLECTION`: коллекция для базы знаний
- `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`: LangSmith tracing
- `BACKEND_CORS_ORIGINS`: CORS origins (можно через запятую)
- `RATE_LIMIT_PER_MINUTE`: лимит запросов на IP (по ТЗ 20/min)

## API

### GET `/health`

Проверка сервиса.

Ответ:

```json
{ "status": "ok" }
```

### POST `/chat`

Streaming чат с агентом.

Пример запроса:

```json
{
  "session_id": "demo-session",
  "message": "Вот ссылка на вакансию: https://hh.ru/vacancy/123456"
}
```

Формат ответа: Server-Sent Events (SSE)

```
data: token

data: token

data: [DONE]
```

### GET `/sessions/{session_id}`

История сессии.

## Тесты (backend)

```bash
cd backend
pytest
```

## Deployment (AWS EC2 + Nginx)

Сервер:

- IP: `13.60.91.191`
- User: `ubuntu`

### Запуск через Docker Compose

```bash
ssh -i ./evr_aws.pem ubuntu@13.60.91.191
cd /home/ubuntu/project-26-capstone
cp .env.example .env
nano .env   # вставьте OPENAI_API_KEY
docker compose up --build -d
```

### Nginx reverse proxy

Пример `/etc/nginx/sites-available/interview-coach`:

```nginx
server {
    listen 80;
    server_name 13.60.91.191;

    client_max_body_size 20M;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_buffering off;
        proxy_cache off;

        proxy_set_header Connection '';
        chunked_transfer_encoding on;
    }
}
```

Маршрутизация:

- `http://13.60.91.191/` → frontend
- `http://13.60.91.191/api/*` → backend

## Ограничения

- hh.ru может блокировать парсинг;
- качество feedback зависит от качества описания вакансии;
- RAG-база знаний ограничена подготовленными markdown-файлами;
- история сессии хранится упрощённо (in-memory);
- без авторизации пользователей.

## План развития

- авторизация пользователей;
- сохранение интервью в PostgreSQL;
- экспорт отчёта в PDF;
- поддержка LinkedIn и других job boards;
- голосовой mock-interview;
- аналитика прогресса пользователя;
- расширение базы знаний.

