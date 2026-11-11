venv#!/bin/bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install flask-sqlalchemy

chmod +x setup.sh
source setup.sh

git config --global user.name "Allan"
git config --global user.email "allan.bento.santos@escola.pr.gov.br"
