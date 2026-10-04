#!/usr/bin/env bash
# Deploy (build + start) the app on the Docker host from inside the dev container, over SSH.
#
#   DEPLOY_USER=<mac username> DEPLOY_PATH=<folder on the Mac that holds this project> ./deploy.sh
#
# Requirements: on the Mac, Remote Login (SSH) enabled and your key loaded into the agent
# (`ssh-add`), so the forwarded agent in this container can authenticate. The host is reached
# as host.docker.internal. Override with DEPLOY_HOST if needed.
set -euo pipefail
: "${DEPLOY_USER:?set DEPLOY_USER to your Mac username}"
: "${DEPLOY_PATH:?set DEPLOY_PATH to the project folder on the Mac, e.g. /Users/you/casa-theory}"
HOST="${DEPLOY_HOST:-host.docker.internal}"
echo "Deploying to ${DEPLOY_USER}@${HOST}:${DEPLOY_PATH}"
ssh -o ConnectTimeout=10 "${DEPLOY_USER}@${HOST}" bash -s "${DEPLOY_PATH}" <<'REMOTE'
set -euo pipefail
cd "$1"
export PATH="$PATH:/usr/local/bin:/opt/homebrew/bin:$HOME/.docker/bin"
docker version --format 'Docker {{.Server.Version}} on the host' 
docker compose up -d --build
docker compose ps
echo "Waiting for the health check..."
for i in $(seq 1 30); do
  if curl -fsS http://localhost:8081/healthz >/dev/null 2>&1; then echo "App is up: http://localhost:8081"; exit 0; fi
  sleep 2
done
echo "The container started but /healthz did not answer within 60 s; check: docker compose logs -f" >&2
exit 1
REMOTE
