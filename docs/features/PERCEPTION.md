# Perceptual Layer ("The Eyes")

**Feature:** Perceptual Layer
**Module:** `perception/llm_parser.py`
**Introduced:** November 2025
**Status:** Core Component

---

## 1. Overview

The Perceptual Layer bridges the gap between unstructured natural language observations (e.g., TextWorld output) and the structured graph representation required by the Cognitive Agent.

**Problem:** Regex-based parsing is brittle. "An apple is on the table" vs "On the table sits an apple."
**Solution:** Use a Vision-Language Model (or LLM) as a semantic encoder to translate text into a strict JSON schema.

## 2. How It Works

### The Encoder (`gpt-4o-mini`)
We use `gpt-4o-mini` via the `llm` Python package. It is fast, cheap, and capable of following complex schemas.

### The Schema
We define a strict **JSON Schema** that forces the model to output:
-   **Room Name:** Canonical name of the location.
-   **Exits:** List of available directions.
-   **Items:** List of objects with `name`, `state` (open/closed/locked), and `location`.

```json
{
  "type": "object",
  "properties": {
    "room_name": {"type": "string"},
    "exits": {"type": "array", "items": {"type": "string"}},
    "items": {"type": "array", "items": {...}}
  }
}
```

## 3. Architecture

### `LLMPerception` Class
Located in `perception/llm_parser.py`.

```python
class LLMPerception:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model = llm.get_model(model_name)
        
    def parse(self, text: str) -> dict:
        # Returns structured dictionary matching the schema
```

## 4. Performance

Verified against TextWorld samples (`validation/test_perception.py`):
-   **Accuracy:** 100% on test set (Kitchen, Living Room).
-   **Robustness:** Correctly handles complex phrasing ("You find yourself in...", "A glass door leads south").
-   **Latency:** ~1-2 seconds per observation (acceptable for turn-based games).

## 5. Future Work

-   **Vision Support:** The `llm` package supports multi-modal models. We can easily swap `gpt-4o-mini` for a model that accepts images if we move to visual domains.
-   **Caching:** Cache common descriptions to save API costs.
