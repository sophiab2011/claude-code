---
name: chatgpt-image
description: Generate pictures with ChatGPT / OpenAI image models. Use when the user wants a picture, illustration, photo, logo, icon, poster or other image "in ChatGPT", "with GPT", "with DALL·E", or "with OpenAI". Writes a paste-ready ChatGPT image prompt, and when OPENAI_API_KEY is set can generate or edit the image directly through the OpenAI Images API and save it to disk.
argument-hint: "<what to draw> [--size 1024x1536] [--n 2] [--api]"
---

# ChatGPT image generation

Turn a rough idea into a strong image prompt for ChatGPT's image model, then
either hand the user a prompt to paste into ChatGPT, or generate the image
directly through the OpenAI API.

## 1. Pick the mode

- **API mode** — use it when `OPENAI_API_KEY` is set (check with
  `test -n "$OPENAI_API_KEY" && echo set`) or the user passed `--api`.
  The image is created by `scripts/generate.py` and saved locally.
- **Prompt mode** (default otherwise) — produce a paste-ready prompt for
  chatgpt.com. Never ask the user for their API key in chat; if they want API
  mode without a key, tell them to set `OPENAI_API_KEY` in their environment.

## 2. Gather only what's missing

Ask at most one short question, and only if the request is too vague to draw
(e.g. "make a pic"). Otherwise fill gaps with sensible defaults and state them.
Things worth knowing:

| Field | Default if unstated |
|---|---|
| Subject & action | — (required) |
| Style / medium | photorealistic for real-world subjects, clean digital illustration otherwise |
| Aspect ratio | square 1024x1024; portrait 1024x1536 for posters/phone wallpapers; landscape 1536x1024 for banners/thumbnails |
| Text in image | none — if wanted, quote it exactly |
| Background | appropriate scene; `transparent` for logos, icons, stickers |
| Count | 1 |

## 3. Write the prompt

ChatGPT's image model follows long, natural-language descriptions well. Build
the prompt in this order, as flowing sentences rather than a tag list:

1. **Format** — what kind of image it is ("A vertical movie poster…", "A flat vector app icon…").
2. **Subject** — who/what, with concrete details (age, clothing, materials, colors, count).
3. **Action & composition** — pose, framing (close-up, wide shot, top-down), placement in frame.
4. **Setting** — location, time of day, weather, background elements.
5. **Style** — medium (photo, watercolor, 3D render, pixel art, anime…), era, art movement; for photos add lens/camera feel ("shot on 35mm, shallow depth of field").
6. **Lighting & mood** — golden hour, soft studio light, neon, moody, cheerful.
7. **Color palette** — named colors or hex codes when brand-sensitive.
8. **Exact text** — in quotes, with font feel and placement: `the title "SUMMER CAMP" in bold rounded white letters across the top`.
9. **Constraints** — what to avoid ("no extra text, no watermark, hands with five fingers").

Rules:
- Be specific and visual; replace vague words ("nice", "cool") with what they look like.
- Keep in-image text short (≤ ~8 words per line) and spell it exactly.
- Don't name living artists or copy trademarked characters/logos; describe the style instead ("loose ink-wash style with bold black outlines").
- Don't generate realistic images of real, identifiable people, sexual content, or anything that would violate OpenAI's usage policies — ChatGPT will refuse these anyway. Offer a compliant alternative.

## 4a. Prompt mode — deliver

Reply with:

1. The final prompt in a single fenced code block so it can be copied in one click.
2. One line: "Paste this into ChatGPT (chatgpt.com, any model with image generation) — you can say *make it 16:9* or *make it more vivid* afterwards to iterate."
3. Two or three optional variations as one-liners (different style, angle, or mood).

For edits to an existing picture: tell the user to upload the image in
ChatGPT and send an edit prompt that names what to change **and** what to keep
("Keep the person and pose exactly the same; change the background to a snowy
forest at dusk").

## 4b. API mode — generate

Run the bundled script (stdlib only, no installs):

```bash
python3 .claude/skills/chatgpt-image/scripts/generate.py \
  --prompt "<final prompt>" \
  --size 1024x1024 \
  --quality high \
  --n 1 \
  --out generated-images
```

`--size` is `1024x1024`, `1024x1536`, `1536x1024` or `auto`; `--quality` is
`low`, `medium`, `high` or `auto`.

Optional flags:
- `--background transparent` (PNG/WebP only) for logos, icons, stickers.
- `--format png|jpeg|webp`.
- `--edit path/to/image.png` (repeatable) to edit or combine existing images instead of generating from scratch; add `--mask mask.png` to limit the edit to transparent areas of the mask.
- `--model` overrides the model (default: `$OPENAI_IMAGE_MODEL` or `gpt-image-1`).

Then:
1. Report the saved file path(s) the script prints.
2. Look at each image with the Read tool and check it against the request
   (subject, text spelling, aspect, obvious artifacts). If something is off,
   tighten the prompt and regenerate once before reporting — say what you
   changed.
3. Send the image to the user (SendUserFile with `display: "render"` when
   available) and include the final prompt so they can reuse it in ChatGPT.

If the script exits with an API error, show the error message plainly
(e.g. content-policy rejection, billing, invalid size) and suggest the fix —
don't retry the same prompt blindly.
