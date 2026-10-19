#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip3 install flask flask-sqlalchemy --break-system-packages

chmod +x setup.sh
source setup.sh
