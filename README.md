# GPT Image 2 API Key Skill

A Codex skill for generating and editing images with `gpt-image-2` through a separate, private API key.

This skill is designed for users who run Codex with one authentication setup, but want image generation and image editing to use a different API key, account, quota, billing path, or OpenAI-compatible provider.

## Core Problem

Codex may already be authenticated with an API key or a Codex/ChatGPT session. That credential is not always the credential you want to use for image generation.

This skill solves that by:

- Reading image API credentials from a private user config file.
- Avoiding `OPENAI_API_KEY` and Codex auth files.
- Calling `gpt-image-2` or a compatible image model through an isolated provider config.
- Supporting both text-to-image generation and image editing.
- Keeping secrets out of the skill folder and out of GitHub.

## Use Cases

Use this skill when you want Codex to:

- Generate a logo, product image, poster, icon, illustration, or visual asset with `gpt-image-2`.
- Edit an existing image while preserving layout, subject, or exact text.
- Restyle a reference image, such as changing a logo to italic or applying a metallic gradient.
- Use an OpenAI-compatible proxy or image provider with a custom `base_url`.
- Keep image API billing and quota separate from Codex's current API key.
- Save generated images to explicit local paths for later inspection or project use.

Example requests:

- "Generate a clean logo with the exact text `JunXxxxi`."
- "Edit this logo: make the letters italic and use a silver-to-black gradient."
- "Create a product shot with my separate image API key."
- "Use this reference image and restyle it as a premium technology brand mark."

## Repository Contents

```text
gpt-image-2-apikey/
├── README.md
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── generate_image.py
```

- `README.md`: GitHub-facing overview and setup guide.
- `SKILL.md`: Codex skill instructions and trigger metadata.
- `agents/openai.yaml`: optional Codex UI metadata.
- `scripts/generate_image.py`: zero-dependency Python script for generation and editing.

## Capabilities

### Text-to-image

Calls:

```text
POST <base_url>/images/generations
```

Use this for brand assets, logos, illustrations, product shots, posters, UI mockups, and other generated images.

### Image editing

Calls:

```text
POST <base_url>/images/edits
```

Use this for reference-image edits, restyling, logo treatments, background changes, composition-preserving edits, and masked edits.

### Multi-image edits

Pass `--edit-image` more than once to send multiple reference images.

### Masked edits

Pass `--mask /path/to/mask.png` when the provider supports masked image editing.

## Installation

Clone or download this repository, then copy the skill folder into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R gpt-image-2-apikey-skill ~/.codex/skills/gpt-image-2-apikey
```

Restart Codex after installing so it can discover the skill.

If you install it manually, the final path should look like:

```text
~/.codex/skills/gpt-image-2-apikey/SKILL.md
~/.codex/skills/gpt-image-2-apikey/scripts/generate_image.py
```

## Private Configuration

Create a private config file outside the repository:

```bash
mkdir -p ~/.config/gpt-image-2-apikey
nano ~/.config/gpt-image-2-apikey/config.json
```

Example config:

```json
{
  "api_key": "put-image-provider-key-here",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-image-2"
}
```

Then restrict file permissions:

```bash
chmod 600 ~/.config/gpt-image-2-apikey/config.json
```

### Config fields

- `api_key`: required. The dedicated image provider API key.
- `base_url`: optional. Defaults to `https://api.openai.com/v1`.
- `model`: optional. Defaults to `gpt-image-2`.
- `extra_body`: optional object merged into every request body for provider-specific settings.

For OpenAI official API, keep `base_url` at the API root:

```json
{
  "base_url": "https://api.openai.com/v1"
}
```

For a third-party OpenAI-compatible relay or proxy, use that provider's `/v1` API root:

```json
{
  "base_url": "https://your-proxy.example.com/v1"
}
```

Do not include `/images/generations` or `/images/edits` in `base_url` unless you intentionally want to pin a specific endpoint. The script normally appends the right endpoint automatically.

## Usage

Run commands from the skill folder.

### Generate an image

```bash
python3 scripts/generate_image.py \
  --prompt "A clean product photo of a matte black mechanical keyboard on a walnut desk" \
  --out /absolute/path/to/output.png \
  --size 1024x1024 \
  --quality high
```

### Edit an image

```bash
python3 scripts/generate_image.py \
  --prompt "Turn this logo into italic silver-to-black gradient text while preserving the exact spelling" \
  --edit-image /absolute/path/to/input.png \
  --out /absolute/path/to/edited.png \
  --quality high
```

### Use a mask

```bash
python3 scripts/generate_image.py \
  --prompt "Only change the selected region to a clean studio gray background" \
  --edit-image /absolute/path/to/source.png \
  --mask /absolute/path/to/mask.png \
  --out /absolute/path/to/edited.png
```

### Use multiple reference images

```bash
python3 scripts/generate_image.py \
  --prompt "Combine the product from image 1 with the lighting style from image 2" \
  --edit-image /absolute/path/to/product.png \
  --edit-image /absolute/path/to/style-reference.png \
  --out /absolute/path/to/combined.png
```

### Dry run

Use `--dry-run` to verify routing and request structure without calling the provider:

```bash
python3 scripts/generate_image.py \
  --prompt "dry run only" \
  --edit-image /absolute/path/to/input.png \
  --out /absolute/path/to/output.png \
  --dry-run
```

Dry-run output redacts authorization as:

```text
Bearer ***redacted***
```

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

## Prompting Tips

For generated images:

- Describe the asset type, subject, style, layout, and intended use.
- Quote exact visible text.
- Add "no extra text, no watermark" for logos and posters.
- Use `--quality high` for final deliverables and text-heavy images.
- Use `--quality low` for cheap drafts.

For edits:

- Describe the change, not the entire image, unless a full reinterpretation is desired.
- State what must remain unchanged.
- Repeat exact spelling and capitalization for wordmarks and UI text.
- Use masks for precise region edits when the provider supports them.

Example:

```text
Edit the provided logo image. Preserve the exact text "JunXxxxi" and the same wordmark layout. Make the lettering italic/slanted to the right. Change the letter fill to a metallic gradient from bright silver on the left/top to deep black on the right/bottom. Keep a clean white background. Do not add extra words, icons, watermarks, borders, or decorative elements.
```

## Security Notes

- Do not commit `~/.config/gpt-image-2-apikey/config.json`.
- Do not put real API keys in `SKILL.md`, `README.md`, shell history examples, or issue comments.
- Do not rely on `OPENAI_API_KEY`; this script intentionally ignores it.
- Keep the private config file mode at `600`.
- Treat generated images and prompts as provider-visible data.
- Network calls may incur charges on the configured provider account.

This repository's `.gitignore` excludes common local config, secret, token, and generated image files.

## Limitations

- This is an API wrapper, not a full graphics editor.
- Model-based image editing may alter exact text, kerning, geometry, or layout. Inspect outputs before delivery.
- Edit endpoint compatibility differs across OpenAI-compatible providers.
- The script sends edit images using multipart field name `image[]` for multi-image compatibility. Some providers may require a different field name.
- Transparent backgrounds depend on provider/model support; verify alpha channels when transparency matters.

## Validation

Basic validation commands:

```bash
python3 -m py_compile scripts/generate_image.py
python3 scripts/generate_image.py --prompt "test" --out /tmp/test.png --dry-run
```

If you have the Codex skill validator available:

```bash
python3 path/to/quick_validate.py /path/to/gpt-image-2-apikey
```

## License

Add your preferred license before redistributing in contexts that require an explicit license.
