#!/usr/bin/env python3
"""Generate or edit images with the OpenAI Images API (the model behind ChatGPT images).

Standard library only. Reads the API key from OPENAI_API_KEY.

Examples:
  generate.py --prompt "A watercolor fox in a snowy forest" --size 1024x1536
  generate.py --prompt "Make the sky purple" --edit photo.png
"""
import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

API_BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
DEFAULT_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prompt", required=True)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--size", default="1024x1024", help="1024x1024 | 1024x1536 | 1536x1024 | auto")
    p.add_argument("--quality", default="auto", help="low | medium | high | auto")
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--background", default=None, help="transparent | opaque | auto")
    p.add_argument("--format", dest="fmt", default="png", choices=["png", "jpeg", "webp"])
    p.add_argument("--edit", action="append", default=[], help="input image to edit (repeatable)")
    p.add_argument("--mask", default=None, help="PNG mask for edits; transparent areas are changed")
    p.add_argument("--out", default="generated-images", help="output directory")
    return p.parse_args()


def multipart(fields, files):
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    for name, path in files:
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            data = f.read()
        head = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
            f'filename="{os.path.basename(path)}"\r\nContent-Type: {ctype}\r\n\r\n'
        ).encode()
        parts.append(head + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def call(url, body, content_type, key):
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error", {}).get("message", "")
        except Exception:
            msg = ""
        sys.exit(f"OpenAI API error {e.code}: {msg or e.reason}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error: {e.reason}")


def main():
    a = parse_args()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY is not set. Export it, or use prompt mode and paste the prompt into ChatGPT.")

    opts = {"model": a.model, "prompt": a.prompt, "size": a.size, "quality": a.quality,
            "n": a.n, "output_format": a.fmt}
    if a.background:
        opts["background"] = a.background

    if a.edit:
        files = [("image[]" if len(a.edit) > 1 else "image", p) for p in a.edit]
        if a.mask:
            files.append(("mask", a.mask))
        body, ctype = multipart({k: str(v) for k, v in opts.items()}, files)
        resp = call(f"{API_BASE}/images/edits", body, ctype, key)
    else:
        resp = call(f"{API_BASE}/images/generations", json.dumps(opts).encode(), "application/json", key)

    os.makedirs(a.out, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", a.prompt.lower()).strip("-")[:40] or "image"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    saved = []
    for i, item in enumerate(resp.get("data", []), 1):
        path = os.path.join(a.out, f"{stamp}-{slug}-{i}.{a.fmt}")
        if item.get("b64_json"):
            with open(path, "wb") as f:
                f.write(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            urllib.request.urlretrieve(item["url"], path)
        else:
            continue
        saved.append(os.path.abspath(path))
        if item.get("revised_prompt"):
            print(f"revised prompt: {item['revised_prompt']}")

    if not saved:
        sys.exit(f"No images returned: {json.dumps(resp)[:500]}")
    for s in saved:
        print(f"saved: {s}")


if __name__ == "__main__":
    main()
