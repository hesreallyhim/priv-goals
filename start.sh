#!/bin/bash

# Function to activate venv and run app.py
start_app() {
  source venv/bin/activate
  python app.py
}

# To have the venv persist, run the following command in the terminal:
# source start.sh

start_app
