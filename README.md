# Self-Evolving Agent

LLM inference with Google Gemini and Weave tracing.

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# Add your GOOGLE_API_KEY to .env
```

3. Run:
```bash
python main.py
```

## Usage

```python
from src.llm import run_inference

response = run_inference("Your prompt here")
```
