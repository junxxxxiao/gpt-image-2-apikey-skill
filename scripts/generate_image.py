#!/usr/bin/env python3
"""Generate or edit images with a private API-key-backed GPT Image 2 provider."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request


DEFAULT_CONFIG = Path(
    os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
) / "gpt-image-2-apikey" / "config.json"


class SkillError(Exception):
    pass


def load_config(path: Path) -> dict:
    if not path.exists():
        raise SkillError(
            f"Missing config file: {path}\n"
            "Create it with fields: api_key, base_url, model."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SkillError(f"Config is not valid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SkillError("Config must be a JSON object.")
    if not data.get("api_key"):
        raise SkillError(f"Config is missing required field 'api_key': {path}")
    return data


def endpoint_from_base(base_url: str, operation: str) -> str:
    base = base_url.rstrip("/")
    endpoint = "edits" if operation == "edit" else "generations"
    if base.endswith(f"/images/{endpoint}"):
        return base
    if base.endswith("/images/generations") or base.endswith("/images/edits"):
        return f"{base.rsplit('/images/', 1)[0]}/images/{endpoint}"
    return f"{base}/images/{endpoint}"


def request_json(url: str, api_key: str, body: dict, timeout: int) -> dict:
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise SkillError(f"Provider returned HTTP {exc.code}: {err}") from exc
    except urllib.error.URLError as exc:
        raise SkillError(f"Provider request failed: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SkillError(f"Provider returned non-JSON response: {raw[:500]}") from exc


def encode_multipart(fields: dict, files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    boundary = f"gpt-image-2-apikey-{int(time.time() * 1000)}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        if value is None:
            continue
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )

    for name, path in files:
        if not path.exists():
            raise SkillError(f"Input file does not exist: {path}")
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{path.name}"\r\n'
                ).encode("utf-8"),
                f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
                path.read_bytes(),
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), boundary


def request_multipart(
    url: str,
    api_key: str,
    fields: dict,
    files: list[tuple[str, Path]],
    timeout: int,
) -> dict:
    payload, boundary = encode_multipart(fields, files)
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise SkillError(f"Provider returned HTTP {exc.code}: {err}") from exc
    except urllib.error.URLError as exc:
        raise SkillError(f"Provider request failed: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SkillError(f"Provider returned non-JSON response: {raw[:500]}") from exc


def download_url(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "gpt-image-2-apikey-skill"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        raise SkillError(f"Could not download image URL: {exc}") from exc


def output_path_for(base: Path, index: int, output_format: str) -> Path:
    suffix = base.suffix or f".{output_format}"
    if index == 0:
        return base if base.suffix else base.with_suffix(suffix)
    return base.with_name(f"{base.stem}-{index + 1}{suffix}")


def decode_images(response: dict, timeout: int) -> list[bytes]:
    data = response.get("data")
    if not isinstance(data, list) or not data:
        raise SkillError(
            "Provider response did not contain data[]. "
            f"Top-level keys: {', '.join(response.keys())}"
        )

    images: list[bytes] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("b64_json"):
            images.append(base64.b64decode(item["b64_json"]))
            continue
        if item.get("url"):
            images.append(download_url(item["url"], timeout))

    if not images:
        raise SkillError("Provider response contained no b64_json or url image payloads.")
    return images


def build_body(args: argparse.Namespace, config: dict) -> dict:
    body = {
        "model": args.model or config.get("model") or "gpt-image-2",
        "prompt": args.prompt,
    }
    if args.size:
        body["size"] = args.size
    if args.quality:
        body["quality"] = args.quality
    if args.n:
        body["n"] = args.n
    if args.format:
        body["output_format"] = args.format

    extra = config.get("extra_body")
    if extra:
        if not isinstance(extra, dict):
            raise SkillError("Config field 'extra_body' must be an object when present.")
        body.update(extra)
    return body


def build_edit_fields(args: argparse.Namespace, config: dict) -> dict:
    fields = build_body(args, config)
    fields.pop("output_format", None)
    if args.format:
        fields["output_format"] = args.format
    return fields


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or edit images through a private gpt-image-2 API key config."
    )
    parser.add_argument("--prompt", required=True, help="Image prompt.")
    parser.add_argument("--out", help="Output image path.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Private config path.")
    parser.add_argument("--model", help="Override model from config.")
    parser.add_argument(
        "--edit-image",
        action="append",
        default=[],
        help="Input image path for /v1/images/edits. Repeat for multi-image edits.",
    )
    parser.add_argument("--mask", help="Optional PNG mask path for image edits.")
    parser.add_argument("--size", default="1024x1024", help="Provider-supported image size.")
    parser.add_argument(
        "--quality",
        default="auto",
        choices=["low", "medium", "high", "auto"],
        help="Generation quality.",
    )
    parser.add_argument("--n", type=int, default=1, help="Number of images.")
    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "jpeg", "webp"],
        help="Output format.",
    )
    parser.add_argument("--timeout", type=int, default=600, help="HTTP timeout in seconds.")
    parser.add_argument("--dry-run", action="store_true", help="Print redacted request only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser()
    try:
        config = load_config(config_path)
        base_url = config.get("base_url") or "https://api.openai.com/v1"
        operation = "edit" if args.edit_image else "generate"
        url = endpoint_from_base(str(base_url), operation)
        body = build_edit_fields(args, config) if operation == "edit" else build_body(args, config)

        if args.dry_run:
            print(
                json.dumps(
                    {
                        "config": str(config_path),
                        "endpoint": url,
                        "auth": "Bearer ***redacted***",
                        "operation": operation,
                        "body": body,
                        "files": {
                            "image": [str(Path(p).expanduser()) for p in args.edit_image],
                            "mask": str(Path(args.mask).expanduser()) if args.mask else None,
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if operation == "edit":
            files = [("image[]", Path(p).expanduser()) for p in args.edit_image]
            if args.mask:
                files.append(("mask", Path(args.mask).expanduser()))
            response = request_multipart(url, str(config["api_key"]), body, files, args.timeout)
        else:
            response = request_json(url, str(config["api_key"]), body, args.timeout)
        images = decode_images(response, args.timeout)
        out = Path(args.out) if args.out else Path(f"gpt-image-2-{int(time.time())}.{args.format}")
        out = out.expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)

        saved: list[str] = []
        for i, image in enumerate(images):
            path = output_path_for(out, i, args.format)
            path.write_bytes(image)
            saved.append(str(path))

        print(json.dumps({"ok": True, "output_paths": saved}, ensure_ascii=False))
        return 0
    except SkillError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
