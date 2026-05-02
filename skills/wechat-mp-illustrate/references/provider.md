# OpenRouter Image Provider Notes

The OpenRouter script path generates one image per command through
`/api/v1/chat/completions`.

Required environment variable:

```text
OPENROUTER_API_KEY
```

Optional environment variable:

```text
OPENROUTER_IMAGE_MODEL=google/gemini-3-pro-image-preview
```

`--openrouter-api-key` and `--model` override the environment for a single run.
The scripts do not load `.env` files.

Text-to-image requests send the prompt as the user message content. Image-to-image
requests send a content array with one text block followed by one `image_url`
block per reference image. Local references are encoded as base64 data URLs;
remote references remain URLs.

If image generation fails, report the OpenRouter error and do not invent image
paths.
