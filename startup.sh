#!/bin/bash
source antenv/bin/activate
exec gunicorn backend.main:app --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000 --timeout 300 --chdir backend
