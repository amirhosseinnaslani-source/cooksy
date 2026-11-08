#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR=/opt/apps/cooksy
IMAGE="cooksy:${GIT_COMMIT:-manual}"
LOCK=/tmp/cooksy-deploy.lock

exec 9>"$LOCK"
flock -n 9 || { echo "Cooksy deployment already running"; exit 1; }

docker network inspect app-net >/dev/null
mkdir -p "$APP_DIR"
# Keep deployment-owned files together; leave persistent runtime files alone.
install -m 0644 Dockerfile index.html healthz compose.yml .dockerignore "$APP_DIR/"
docker build -t "$IMAGE" "$APP_DIR"

OLD_IMAGE="$(docker inspect -f '{{.Config.Image}}' cooksy-web 2>/dev/null || true)"
cd "$APP_DIR"
export COOKSY_IMAGE="$IMAGE"
docker compose config --quiet

restore() {
    echo "Cooksy health check failed; attempting rollback"
    if [[ -n "$OLD_IMAGE" ]] && docker image inspect "$OLD_IMAGE" >/dev/null 2>&1; then
        COOKSY_IMAGE="$OLD_IMAGE" docker compose up -d --no-deps --force-recreate web
    else
        echo "No previous Cooksy image is available to roll back to" >&2
    fi
}
trap restore ERR
docker compose up -d --no-deps --force-recreate web

healthy=0
for i in $(seq 1 30); do
    if [[ "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' cooksy-web 2>/dev/null || true)" == "healthy" ]]; then
        healthy=1
        break
    fi
    sleep 2
done
[[ "$healthy" == "1" ]] || { echo "Cooksy did not become healthy" >&2; exit 1; }
docker exec edge-nginx wget -q -O /dev/null http://cooksy-web/healthz
trap - ERR
echo "Cooksy deployed: $IMAGE"
