#!/usr/bin/env bash
cd "$(dirname "$0")"
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
