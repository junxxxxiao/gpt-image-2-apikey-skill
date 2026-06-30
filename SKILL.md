---
name: gpt-image-2-apikey
description: Generate or edit images through a separate API-key-backed GPT Image 2 provider without using Codex's own OpenAI/Codex credentials. Use when the user asks Codex to create, render, draw, generate, edit, modify, restyle, or transform an image with gpt-image-2/image-2 via an isolated API key stored in a private user config file, especially when the current Codex session is already authenticated with a different API key.
---

# GPT Image 2 API Key

## Overview

Generate or edit images with a separately configured `gpt-image-2` provider by running `scripts/generate_image.py`. Use this skill when image generation should be billed to, authenticated by, and isolated from a dedicated image API key instead of Codex's current OpenAI/Codex credentials.

The skill deliberately does not read `OPENAI_API_KEY`, Codex auth files, or ChatGPT/Codex session credentials. It reads only the private config file selected by `--config`, or the default config file documented below.

## What This Solves

This skill addresses a common Codex workflow problem: the current Codex session may already be authenticated with one API key, while image generation should use another key, another account, another quota, or an OpenAI-compatible proxy.

Use this skill to:

- Keep image-generation credentials separate from Codex's own credentials.
- Call a `gpt-image-2` or compatible image endpoint from Codex without exposing the key in prompts, commands, or repository files.
- Generate images through `/v1/images/generations`.
- Edit existing images through `/v1/images/edits` with multipart upload.
- Use one or more reference images for edits, restyles, logo treatments, product mockups, and image-to-image transformations.
- Optionally provide a mask image for region-limited edits.
- Save generated outputs to explicit local paths that Codex can display, inspect, or pass to later steps.

## Use Cases

Use this skill for requests such as:

- "Generate a logo with the exact text `JunXxxxi`."
- "Use this reference image and make the wordmark italic."
- "Change this logo text to a silver-to-black metallic gradient."
- "Create a product image using gpt-image-2, but use my separate image API key."
- "Edit this image while preserving the original composition."
- "Use an OpenAI-compatible image provider with a custom base URL."

Prefer deterministic local image processing instead of this skill when the requested change is a simple pixel-level transformation that must preserve exact geometry, such as cropping, resizing, alpha conversion, or a fully deterministic color remap. Prefer this skill when the user wants model-based visual interpretation, restyling, or generation.

## Contents

```text
gpt-image-2-apikey/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── generate_image.py
```

- `SKILL.md`: Codex-facing workflow and human-readable usage documentation.
- `agents/openai.yaml`: optional Codex UI metadata.
- `scripts/generate_image.py`: zero-dependency Python 3 script that calls generation or edit endpoints.

The script supports both `b64_json` and URL-style image responses. URL responses are downloaded immediately and written to the requested output path.

## Private Config

Default config path:

```text
~/.config/gpt-image-2-apikey/config.json
```

The config must contain the image provider key, not the current Codex API key:

```json
{
  "api_key": "put-image-provider-key-here",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-image-2"
}
```

Set private permissions after creating the file:

```bash
chmod 600 ~/.config/gpt-image-2-apikey/config.json
```

Use `--config /path/to/config.json` only when the user explicitly wants another private config file.

### Config Fields

- `api_key`: required. The image provider key. Do not use Codex's current API key unless that is explicitly intended.
- `base_url`: optional. Defaults to `https://api.openai.com/v1`. For OpenAI-compatible providers, keep this at the API root, such as `https://example.com/v1`.
- `model`: optional. Defaults to `gpt-image-2`.
- `extra_body`: optional object. Values are merged into the request body for provider-specific fields.

Good `base_url` examples:

```json
{
  "base_url": "https://api.openai.com/v1"
}
```

```json
{
  "base_url": "https://www.packyapi.com/v1"
}
```

Do not include `/images/generations` or `/images/edits` in `base_url` unless you are intentionally pinning one exact endpoint. The script normally appends the right endpoint automatically.

## Usage

Run from the skill directory:

```bash
python3 scripts/generate_image.py \
  --prompt "A clean product photo of a matte black mechanical keyboard on a walnut desk" \
  --out /absolute/path/to/output.png \
  --size 1024x1024 \
  --quality high
```

If `--edit-image` is omitted, the script calls:

```text
POST <base_url>/images/generations
```

Edit one or more reference images by adding `--edit-image`:

```bash
python3 scripts/generate_image.py \
  --prompt "Turn this logo into italic silver-to-black gradient text while preserving the exact spelling" \
  --edit-image /absolute/path/to/input.png \
  --out /absolute/path/to/edited.png \
  --size 1024x1024 \
  --quality high
```

If `--edit-image` is present, the script calls:

```text
POST <base_url>/images/edits
```

For masked edits, add `--mask /absolute/path/to/mask.png`:

```bash
python3 scripts/generate_image.py \
  --prompt "Only change the background to a clean studio gray, preserving the subject" \
  --edit-image /absolute/path/to/source.png \
  --mask /absolute/path/to/mask.png \
  --out /absolute/path/to/edited.png \
  --quality high
```

Repeat `--edit-image` for multi-image edits:

```bash
python3 scripts/generate_image.py \
  --prompt "Combine the product from image 1 with the background mood from image 2" \
  --edit-image /absolute/path/to/product.png \
  --edit-image /absolute/path/to/background-reference.png \
  --out /absolute/path/to/combined.png
```

Always provide an absolute `--out` path when the user needs the file in a specific location. If omitted, the script writes a timestamped PNG in the current working directory.

## Command Reference

```text
--prompt       Required image prompt or edit instruction.
--out          Output image path. Extra outputs use -2, -3, etc. before the extension.
--config       Private config path. Defaults to ~/.config/gpt-image-2-apikey/config.json.
--model        Override model from config.
--size         Provider-supported image size. Default: 1024x1024.
--quality      low, medium, high, or auto. Default: auto.
--n            Number of images. Default: 1.
--format       png, jpeg, or webp. Default: png.
--edit-image   Input image path for /v1/images/edits. Repeatable.
--mask         Optional PNG mask path for edits.
--timeout      HTTP timeout in seconds. Default: 600.
--dry-run      Print redacted endpoint, body, and file list without calling the API.
```

Use `--dry-run` before a real call when checking config, endpoint routing, or whether an edit will use the intended input file:

```bash
python3 scripts/generate_image.py \
  --prompt "dry run only" \
  --edit-image /absolute/path/to/input.png \
  --out /absolute/path/to/output.png \
  --dry-run
```

The dry-run output redacts authorization as `Bearer ***redacted***`.

## Prompting Guidance

For generation:

- State the asset type, subject, style, layout, and required text explicitly.
- Put exact visible text in quotes.
- Include "no extra text, no watermark" when working on logos, posters, or UI graphics.
- Use `quality high` for final logos, typography-heavy images, product shots, and polished deliverables.
- Use `quality low` for cheap exploration and quick drafts.

For edits:

- Describe the change, not the whole image, unless the whole image should be reinterpreted.
- Explicitly name what must be preserved: text spelling, layout, composition, face identity, product shape, colors, or background.
- For text-heavy graphics, repeat the exact spelling and capitalization in the prompt.
- Use masks for surgical edits when supported by the provider.

Example edit prompt:

```text
Edit the provided logo image. Preserve the exact text "JunXxxxi" and the same wordmark layout. Make the lettering italic/slanted to the right. Change the letter fill to a metallic gradient from bright silver on the left/top to deep black on the right/bottom. Keep a clean white background. Do not add extra words, icons, watermarks, borders, or decorative elements.
```

## Isolation Rules

- Do not pass or copy Codex's current API key into this skill.
- Do not read `OPENAI_API_KEY`; the script intentionally ignores it.
- Do not print `api_key` or config contents. The script only reports a redacted config summary in `--dry-run`.
- If the config is missing, tell the user to create the private config file. Do not create it with a real secret on their behalf unless explicitly asked.
- If a provider uses an OpenAI-compatible endpoint, set `base_url` in the private config. The script appends `/images/generations` for generation and `/images/edits` for edits.

## Configuration Notes

- Keep `config.json` out of Git. Never commit real API keys.
- Use file mode `600` for the private config.
- Keep `base_url` at the API root (`.../v1`) unless the provider documents otherwise.
- If the provider requires custom request fields, place them under `extra_body`.
- If the provider does not support `gpt-image-2`, set `model` to the provider's compatible model name.
- If the provider only supports URL responses, the script will download the returned URL.
- If the provider returns base64 images in `b64_json`, the script will decode them directly.
- Network calls may incur charges on the configured provider account.

Example with provider-specific fields:

```json
{
  "api_key": "put-image-provider-key-here",
  "base_url": "https://example.com/v1",
  "model": "gpt-image-2",
  "extra_body": {
    "moderation": "auto"
  }
}
```

## Failure Handling

- Missing config or missing `api_key`: report the config path and required fields.
- HTTP error: surface status code and the provider's error body, but never include the key.
- Unsupported provider response: report the top-level response keys and save no file.
- Multiple images: the first image uses `--out`; additional images get `-2`, `-3`, etc. before the extension.

## Limitations

- This skill is an API wrapper, not a full graphics editor. Use deterministic local tooling for exact crops, resizes, vector exports, or guaranteed pixel-perfect typography changes.
- Model-based image editing may alter exact text, kerning, or geometry. For logos and wordmarks, inspect the result before delivery.
- Multipart edit compatibility can vary across OpenAI-compatible providers. If edits fail but generation works, check whether the provider supports `/v1/images/edits` with multipart `image` uploads.
- The script currently sends edit images with multipart field name `image[]` for multi-image compatibility. If a provider requires a different field name, adjust `scripts/generate_image.py` for that provider.
- True transparent-background behavior depends on provider/model support. If transparent PNGs are required, verify the alpha channel after generation.

## Publishing Notes

When publishing this skill to GitHub:

- Include `SKILL.md`, `agents/openai.yaml`, and `scripts/generate_image.py`.
- Do not include `~/.config/gpt-image-2-apikey/config.json`.
- Do not include generated images unless they are intentional examples.
- Add `.gitignore` entries for local configs, outputs, and temporary images if this skill lives in a larger repository.
