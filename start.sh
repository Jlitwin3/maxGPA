#!/bin/sh
set -eu

docker compose up -d --build

PORT_LINE="$(docker compose port maxgpa-service 5000)"
HOST_PORT="${PORT_LINE##*:}"
URL="http://localhost:${HOST_PORT}/"

printf 'Opening %s\n' "$URL"
open "$URL"

docker compose logs -f maxgpa-service
