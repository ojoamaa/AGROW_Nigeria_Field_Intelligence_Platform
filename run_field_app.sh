#!/usr/bin/env bash
python -m uvicorn field_api:app --host 0.0.0.0 --port ${PORT:-8080}
