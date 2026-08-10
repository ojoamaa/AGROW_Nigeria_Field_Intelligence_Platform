@echo off
python -m uvicorn field_api:app --host 0.0.0.0 --port 8080
