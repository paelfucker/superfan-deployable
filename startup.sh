#!/bin/bash
# Used by Azure App Service. Cloud Run uses the Dockerfile instead.
[ -f antenv/bin/activate ] && source antenv/bin/activate
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
