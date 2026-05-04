#!/bin/sh
set -eu

APP_URL="http://localhost:5001/"

if ! command -v docker >/dev/null 2>&1; then
  printf 'Docker is required. Install Docker Desktop, start it, then run this script again.\n' >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  printf 'Docker Compose is required. Install/update Docker Desktop, then run this script again.\n' >&2
  exit 1
fi

printf 'Starting MaxGPA with Docker Compose...\n'
docker compose up -d --build

printf 'Waiting for MaxGPA to respond on %s\n' "$APP_URL"
attempt=0
while [ "$attempt" -lt 60 ]; do
  if curl -fsS "$APP_URL" >/dev/null 2>&1; then
    break
  fi
  attempt=$((attempt + 1))
  sleep 1
done

if [ "$attempt" -eq 60 ]; then
  printf 'MaxGPA did not respond within 60 seconds. Check logs with: docker compose logs maxgpa-service\n' >&2
  exit 1
fi

printf 'Opening %s\n' "$APP_URL"
if command -v open >/dev/null 2>&1; then
  open "$APP_URL"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$APP_URL"
else
  printf 'Open this URL in your browser: %s\n' "$APP_URL"
fi

printf '\nMaxGPA is running.\n'
printf 'Student/Admin chooser: %s\n' "$APP_URL"
printf 'Admin upload page:     http://localhost:5001/admin\n'
printf '\nTo stop MaxGPA later, run: docker compose down\n'
