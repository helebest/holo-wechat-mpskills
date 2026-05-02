# OpenRouter Provider Notes

The illustrator scripts use OpenRouter chat completions for both visual planning and image generation.

Required environment variable:

```text
OPENROUTER_API_KEY
```

Optional environment variables:

```text
TEXT_MODEL=google/gemini-3-pro-preview
IMAGE_MODEL=google/gemini-3-pro-image-preview
MAX_DOC_LEN=5000
```

If image generation fails, keep the generated visual plan and report which scene failed instead of inventing image paths.
