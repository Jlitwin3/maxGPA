#!/bin/sh
set -eu

PACKAGE_NAME="MaxGPA_install_package"
DIST_DIR="dist"
PACKAGE_PATH="${DIST_DIR}/${PACKAGE_NAME}.tar.gz"
TMP_DIR="$(mktemp -d)"
STAGE_DIR="${TMP_DIR}/${PACKAGE_NAME}"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$DIST_DIR"
rm -f "$PACKAGE_PATH"
mkdir -p "$STAGE_DIR"

printf 'Creating %s...\n' "$PACKAGE_PATH"

rsync -a \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='Flask/.venv' \
  --exclude='__pycache__' \
  --exclude='*/__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='*.swp' \
  --exclude='.DS_Store' \
  --exclude='dist' \
  --exclude='test_graph.png' \
  --exclude='test_all_instructors_graph.png' \
  ./ "$STAGE_DIR/"

tar -czf "$PACKAGE_PATH" -C "$TMP_DIR" "$PACKAGE_NAME"

printf 'Done: %s\n' "$PACKAGE_PATH"
printf '\nTo install/run on another machine without cloning:\n'
printf '  tar -xzf %s\n' "$PACKAGE_PATH"
printf '  cd %s\n' "$PACKAGE_NAME"
printf '  Double-click "Start MaxGPA.command"\n'
printf '\nCommand-line alternative:\n'
printf '  ./INSTALL_AND_RUN.sh\n'
