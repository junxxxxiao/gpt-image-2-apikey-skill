# GPT Image 2 API Key Skill

一个用于 Codex 的 Skill：通过单独的私有 API Key 调用 `gpt-image-2` 来生成和编辑图片。

这个 Skill 适合这样的场景：你的 Codex 已经使用某一种认证方式运行，但你希望图片生成和图片编辑走另一套 API Key、账号、额度、计费路径，或者走 OpenAI 兼容的第三方中转站。

## 核心解决的问题

Codex 可能已经通过某个 API Key、Codex 登录态或 ChatGPT 会话完成认证。但这个认证凭据不一定是你希望用于图片生成的凭据。

这个 Skill 通过以下方式解决这个问题：

- 从用户私有配置文件读取图片 API 凭据。
- 避免读取 `OPENAI_API_KEY` 和 Codex 的认证文件。
- 通过隔离的 provider 配置调用 `gpt-image-2` 或兼容图片模型。
- 同时支持文生图和图片编辑。
- 避免把密钥放进 Skill 目录或 GitHub 仓库。

## 使用场景

当你希望 Codex 完成以下任务时，可以使用这个 Skill：

- 使用 `gpt-image-2` 生成 logo、产品图、海报、图标、插画或其他视觉素材。
- 编辑已有图片，同时尽量保留原始布局、主体或准确文字。
- 对参考图进行风格重绘，例如把 logo 改成斜体、应用金属渐变等。
- 使用自定义 `base_url` 连接 OpenAI 兼容代理或第三方图片 provider。
- 让图片 API 的计费和额度与当前 Codex API Key 分开。
- 将生成图片保存到明确的本地路径，便于后续检查或项目使用。

示例请求：

- “Generate a clean logo with the exact text `JunXxxxi`.”
- “Edit this logo: make the letters italic and use a silver-to-black gradient.”
- “Create a product shot with my separate image API key.”
- “Use this reference image and restyle it as a premium technology brand mark.”

## 仓库内容

```text
gpt-image-2-apikey/
├── README.md
├── README.zh.md
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── generate_image.py
```

- `README.md`：英文版 GitHub 说明和设置指南。
- `README.zh.md`：中文版 GitHub 说明和设置指南。
- `SKILL.md`：Codex Skill 指令和触发元数据。
- `agents/openai.yaml`：可选的 Codex UI 元数据。
- `scripts/generate_image.py`：零第三方依赖的 Python 脚本，用于图片生成和编辑。

## 能力

### 文生图

调用：

```text
POST <base_url>/images/generations
```

适用于品牌资产、logo、插画、产品图、海报、UI mockup 以及其他生成式图片。

### 图片编辑

调用：

```text
POST <base_url>/images/edits
```

适用于参考图编辑、风格重绘、logo 处理、背景替换、保留构图的修改，以及带 mask 的局部编辑。

### 多图编辑

多次传入 `--edit-image`，即可发送多张参考图。

### Mask 局部编辑

当 provider 支持 mask 图片编辑时，可以传入 `--mask /path/to/mask.png`。

## 安装

克隆或下载这个仓库，然后把 Skill 文件夹复制到 Codex 的 skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R gpt-image-2-apikey-skill ~/.codex/skills/gpt-image-2-apikey
```

安装后重启 Codex，让 Codex 重新扫描并发现这个 Skill。

如果你手动安装，最终路径应该类似：

```text
~/.codex/skills/gpt-image-2-apikey/SKILL.md
~/.codex/skills/gpt-image-2-apikey/scripts/generate_image.py
```

## 私有配置

在仓库目录之外创建私有配置文件：

```bash
mkdir -p ~/.config/gpt-image-2-apikey
nano ~/.config/gpt-image-2-apikey/config.json
```

配置示例：

```json
{
  "api_key": "put-image-provider-key-here",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-image-2"
}
```

然后收紧文件权限：

```bash
chmod 600 ~/.config/gpt-image-2-apikey/config.json
```

### 配置字段

- `api_key`：必填。专门用于图片 provider 的 API Key。
- `base_url`：可选。默认是 `https://api.openai.com/v1`。
- `model`：可选。默认是 `gpt-image-2`。
- `extra_body`：可选对象，会合并到每次请求体中，用于 provider 特有参数。

如果使用 OpenAI 官方 API，`base_url` 保持在 API 根路径：

```json
{
  "base_url": "https://api.openai.com/v1"
}
```

如果使用第三方 OpenAI 兼容中转站或代理服务，请填写该 provider 提供的 `/v1` API 根路径：

```json
{
  "base_url": "https://your-proxy.example.com/v1"
}
```

除非你有意固定到某个具体 endpoint，否则不要在 `base_url` 中包含 `/images/generations` 或 `/images/edits`。脚本会根据模式自动拼接正确 endpoint。

## 使用方法

在 Skill 文件夹中运行命令。

### 生成图片

```bash
python3 scripts/generate_image.py \
  --prompt "A clean product photo of a matte black mechanical keyboard on a walnut desk" \
  --out /absolute/path/to/output.png \
  --size 1024x1024 \
  --quality high
```

### 编辑图片

```bash
python3 scripts/generate_image.py \
  --prompt "Turn this logo into italic silver-to-black gradient text while preserving the exact spelling" \
  --edit-image /absolute/path/to/input.png \
  --out /absolute/path/to/edited.png \
  --quality high
```

### 使用 mask

```bash
python3 scripts/generate_image.py \
  --prompt "Only change the selected region to a clean studio gray background" \
  --edit-image /absolute/path/to/source.png \
  --mask /absolute/path/to/mask.png \
  --out /absolute/path/to/edited.png
```

### 使用多张参考图

```bash
python3 scripts/generate_image.py \
  --prompt "Combine the product from image 1 with the lighting style from image 2" \
  --edit-image /absolute/path/to/product.png \
  --edit-image /absolute/path/to/style-reference.png \
  --out /absolute/path/to/combined.png
```

### Dry run

使用 `--dry-run` 可以只验证 endpoint 路由和请求结构，不真正调用 provider：

```bash
python3 scripts/generate_image.py \
  --prompt "dry run only" \
  --edit-image /absolute/path/to/input.png \
  --out /absolute/path/to/output.png \
  --dry-run
```

Dry-run 输出会把认证信息隐藏为：

```text
Bearer ***redacted***
```

## 命令参数参考

```text
--prompt       必填。图片提示词或编辑指令。
--out          输出图片路径。多张输出会在扩展名前追加 -2、-3 等。
--config       私有配置文件路径。默认是 ~/.config/gpt-image-2-apikey/config.json。
--model        覆盖配置文件中的 model。
--size         provider 支持的图片尺寸。默认：1024x1024。
--quality      low、medium、high 或 auto。默认：auto。
--n            图片数量。默认：1。
--format       png、jpeg 或 webp。默认：png。
--edit-image   /v1/images/edits 的输入图片路径。可重复传入。
--mask         可选 PNG mask 路径，用于图片编辑。
--timeout      HTTP 超时时间，单位秒。默认：600。
--dry-run      打印脱敏后的 endpoint、请求体和文件列表，不调用 API。
```

## Prompt 建议

生成图片时：

- 明确描述素材类型、主体、风格、布局和用途。
- 对需要出现在图中的精确文字使用引号。
- 生成 logo 或海报时，加入 “no extra text, no watermark”。
- 最终交付物和文字较多的图片建议使用 `--quality high`。
- 探索草稿可以使用 `--quality low` 降低成本。

编辑图片时：

- 描述要改什么，而不是重新描述整张图，除非你希望模型重新理解整个图。
- 明确说明哪些内容必须保持不变。
- 对 wordmark、UI 文案等重复写明精确拼写和大小写。
- provider 支持时，使用 mask 做精确区域编辑。

示例：

```text
Edit the provided logo image. Preserve the exact text "JunXxxxi" and the same wordmark layout. Make the lettering italic/slanted to the right. Change the letter fill to a metallic gradient from bright silver on the left/top to deep black on the right/bottom. Keep a clean white background. Do not add extra words, icons, watermarks, borders, or decorative elements.
```

## 安全注意事项

- 不要提交 `~/.config/gpt-image-2-apikey/config.json`。
- 不要把真实 API Key 写进 `SKILL.md`、`README.md`、shell 历史示例或 issue 评论。
- 不要依赖 `OPENAI_API_KEY`；这个脚本会刻意忽略它。
- 私有配置文件建议保持 `600` 权限。
- 生成的图片和 prompt 会被配置的 provider 看到，请按需处理敏感内容。
- 网络调用可能产生 provider 账号费用。

本仓库的 `.gitignore` 已排除常见本地配置、secret、token 和生成图片文件。

## 限制

- 这是一个 API wrapper，不是完整图形编辑器。
- 模型式图片编辑可能改变精确文字、字距、几何结构或布局，交付前应检查结果。
- 不同 OpenAI 兼容 provider 对编辑 endpoint 的兼容性可能不同。
- 脚本为了兼容多图编辑，会用 multipart 字段名 `image[]` 发送编辑图片。某些 provider 可能要求不同字段名。
- 透明背景取决于 provider 和模型支持情况；如果需要透明 PNG，请验证 alpha 通道。

## 验证

基础验证命令：

```bash
python3 -m py_compile scripts/generate_image.py
python3 scripts/generate_image.py --prompt "test" --out /tmp/test.png --dry-run
```

如果你有 Codex skill validator：

```bash
python3 path/to/quick_validate.py /path/to/gpt-image-2-apikey
```

## License

在需要明确许可协议的分发场景中，请添加你偏好的 license。
