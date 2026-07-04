import os
from flask import Flask

app = Flask(__name__)

# APP_VERSION lets you visibly prove a new version rolled out during the canary demo.
VERSION = os.environ.get("APP_VERSION", "1.0")


@app.route("/")
def home():
    return f"Hello from Harness demo — version {VERSION}\n"


@app.route("/healthz")
def healthz():
    # Used by the Kubernetes readiness/liveness probes.
    return {"status": "ok", "version": VERSION}, 200


if __name__ == "__main__":
    # 0.0.0.0 so it's reachable inside the container/pod.
    app.run(host="0.0.0.0", port=8080)
