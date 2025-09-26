# BE/app.py
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.get("/healthz")
def healthz():
    return "1ok", 200