#!/bin/bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install flask-sqlalchemy

chmod +x setup.sh
source setup.sh
