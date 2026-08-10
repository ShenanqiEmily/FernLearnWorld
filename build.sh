#!/usr/bin/env bash
# Render build script. Configure as Build Command: `bash build.sh`
# (invoking via `bash` avoids needing the executable bit to survive git).
set -o errexit

pip install -r requirements/production.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input
