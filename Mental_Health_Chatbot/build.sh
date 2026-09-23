#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt

mkdir -p media/profile_pics
if [ ! -f media/default.jpg ] && [ -f static/images/account.png ]; then
    cp static/images/account.png media/default.jpg
fi

python manage.py collectstatic --no-input
python manage.py migrate
