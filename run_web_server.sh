#!/bin/bash

if [ ! -d "venv" ]
then
    echo "venv not exist."
    virtualenv --python=python3 venv &&\
    source venv/bin/activate &&\
    pip install -r requirements.txt &&\
    deactivate
fi
source venv/bin/activate && python app.py
