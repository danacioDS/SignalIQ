#!/bin/bash
cd ~/repo_lab/SignalIQ/backend
export PYTHONPATH="$PWD:$PYTHONPATH"
export $(grep -v '^#' ~/repo_lab/SignalIQ/.env | xargs)
python app/main.py
