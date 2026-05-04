#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Collect static files
python project/manage.py collectstatic --noinput
