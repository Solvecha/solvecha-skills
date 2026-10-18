#!/usr/bin/env python3
"""Solve a reCAPTCHA v2 image challenge, or report Google's verdict.

Needs SOLVECHA_API_KEY. Uses only the Python standard library.

  solve_recaptcha.py --task "Select all images with buses" --grid 3x3 --image grid.png
  solve_recaptcha.py --report JOB_ID --verdict accepted --grid 3x3
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = os.environ.get("SOLVECHA_API_URL", "https://api.solvecha.com").rstrip("/")
ERRORS = {
    9: "temporary error or unsolvable image: retry once with a fresh screenshot",
    10: "invalid request: check task, grid and image",
    11: "rate limit: wait 30 seconds",
    15: "wrong or missing API key",
    16: "out of credit: ask the user to top up; do not retry",
}


def call(method, path, key, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(API + path, data=data, method=method)
    request.add_header("Authorization", "Bearer " + key)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            return json.load(error)
        except ValueError:
            return {"error": 9, "message": f"HTTP {error.code}"}


def fail(message):
    print(json.dumps({"error": message}), file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--task")
    parser.add_argument("--grid", choices=["3x3", "4x4", "1x1"])
    parser.add_argument("--image", action="append", help="PNG/JPEG file; repeat for several 1x1 tiles")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--report", metavar="JOB_ID")
    parser.add_argument("--verdict", choices=["accepted", "rejected"])
    args = parser.parse_args()

    key = os.environ.get("SOLVECHA_API_KEY", "")
    if not key:
        fail("SOLVECHA_API_KEY is not set. Create a key at https://solvecha.com/dashboard")

    if args.report:
        if not (args.verdict and args.grid):
            fail("--report needs --verdict and --grid")
        answer = call("POST", "/v1/feedback", key, {"job_id": args.report, "verdict": args.verdict, "grid": args.grid})
        print(json.dumps(answer))
        return

    if not (args.task and args.grid and args.image):
        fail("--task, --grid and --image are required")
    images = []
    for path in args.image:
        with open(path, "rb") as handle:
            images.append(base64.b64encode(handle.read()).decode())
    job = call("POST", "/v1/recognition/recaptcha", key, {"task": args.task, "grid": args.grid, "image_data": images})
    if "data" not in job:
        code = job.get("error")
        fail(f"Solvecha error {code}: {ERRORS.get(code, job.get('message'))}")
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        time.sleep(1)
        answer = call("GET", f"/v1/recognition/recaptcha?id={job['data']}", key)
        if answer.get("error") == 14:  # still working
            continue
        if "data" in answer:
            tiles = [i + 1 for i, picked in enumerate(answer["data"]) if picked]
            print(json.dumps({"job_id": job["data"], "selected_tiles": tiles, "answer": answer["data"]}))
            return
        code = answer.get("error")
        fail(f"Solvecha error {code}: {ERRORS.get(code, answer.get('message'))}")
    fail(f"no answer in {args.timeout} seconds (job {job['data']})")


if __name__ == "__main__":
    main()
