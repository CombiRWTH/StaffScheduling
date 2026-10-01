#!/bin/sh
# Isolated, credential-free Compose acceptance. Requires Docker Compose, curl and a POSIX shell.
set -eu
cd "$(dirname "$0")/.."
smoke_dir=$(mktemp -d)
export COMPOSE_PROJECT_NAME="foundation-$(basename "$smoke_dir" | tr '[:upper:].' '[:lower:]-')"
export API_PORT=0 WEBAPP_PORT=0 BIND_ADDRESS=127.0.0.1
export DATA_DIR="$smoke_dir/data" DB_PASSWORD_FILE="$smoke_dir/db_password"
mkdir -p "$DATA_DIR/found_solutions" "$DATA_DIR/processed_solutions"
: > "$DB_PASSWORD_FILE"
cat > "$smoke_dir/compose.yaml" <<'YAML'
services:
  api:
    environment:
      DB_SERVER: 127.0.0.1
      DB_NAME: smoke
      DB_USER: smoke
      DB_PASSWORD: smoke-only
      DB_TIMEOUT_SECONDS: "1"
YAML
export COMPOSE_FILE="compose.yaml:$smoke_dir/compose.yaml"
cleanup() {
    result=$?
    trap - EXIT HUP INT TERM
    if [ "$result" -ne 0 ]; then docker compose logs --tail 100 || true; fi
    docker compose down --volumes --rmi local --remove-orphans || result=1
    rm -rf "$smoke_dir"
    exit "$result"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

docker compose up --build --wait --wait-timeout 180
curl --fail --silent --show-error --max-time 30 "http://$(docker compose port api 8000)/status"
curl --fail --silent --show-error --max-time 30 "http://$(docker compose port webapp 3000)/api/health"
docker compose exec -T api python - <<'PY'
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

with urlopen('http://localhost:8000/status', timeout=10) as response:
    assert json.load(response) == {'status': 'healthy'}
with urlopen('http://webapp:3000/api/health', timeout=30) as response:
    assert json.load(response) == {'status': 'healthy', 'api': 'healthy'}
try:
    urlopen('http://localhost:8000/planning/options?year=2026&month=1', timeout=15)
except HTTPError as error:
    assert error.code == 503
    body = json.load(error)
    assert body['stage'] == 'connection'
    assert 'smoke-only' not in str(body)
else:
    raise AssertionError('Unavailable database must return 503')
for directory in ('found_solutions', 'processed_solutions'):
    Path('../data', directory, 'smoke.txt').write_text('persistent\n')
PY
# Stop the API to prove the webapp route performs a real server-side request.
docker compose stop api
docker compose exec -T webapp node -e "fetch('http://localhost:3000/api/health', {signal: AbortSignal.timeout(10000)}).then(async r => { if (r.status !== 503) throw Error('Expected unavailable API'); }).catch(e => { console.error(e); process.exit(1); })"
docker compose down
docker compose up --wait --wait-timeout 180
for directory in found_solutions processed_solutions; do
    test "$(cat "$DATA_DIR/$directory/smoke.txt")" = persistent
done
docker compose exec -T api python - <<'PY'
from pathlib import Path
for directory in ('found_solutions', 'processed_solutions'):
    assert Path('../data', directory, 'smoke.txt').read_text() == 'persistent\n'
PY
docker compose exec -T webapp node -e "fetch('http://localhost:3000/api/health', {signal: AbortSignal.timeout(10000)}).then(r => { if (!r.ok) throw Error('API did not recover'); }).catch(e => { console.error(e); process.exit(1); })"
printf 'Compose smoke passed: HTTP connectivity, unavailable database/API, persistence and recreation.\n'
