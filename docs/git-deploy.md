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

## Если SSH/сборка «висит» (мало RAM на micro)

Один раз добавьте swap 2 GB (после перезагрузки инстанса может пропасть — тогда повторите):

```bash
sudo swapoff -a 2>/dev/null
sudo rm -f /swapfile
sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
free -h
```

Сборку удобно запускать в **фоне** и не держать SSH часами:

```bash
cd /home/ubuntu/project-26-capstone
tmux new -s deploy
DOCKER_BUILDKIT=1 docker compose build --progress=plain 2>&1 | tee /tmp/docker-build.log
docker compose up -d
# Ctrl+B, затем D — отсоединиться от tmux
```

Просмотр лога позже: `tail -f /tmp/docker-build.log` или `tmux attach -t deploy`.

Долгосрочно: инстанс хотя бы **2 GB RAM** сильно ускоряет `npm run build`.

## Если репозиторий приватный

На сервере используйте **Deploy key** или **Personal Access Token** (HTTPS), либо `git pull` с машины, где уже настроен доступ.
