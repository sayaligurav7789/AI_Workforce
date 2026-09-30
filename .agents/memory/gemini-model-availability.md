---
name: Gemini model availability
description: Account-specific Gemini model retirement and capacity behavior discovered during provider integration.
---

Keep the Gemini generation model configurable and verify it against the account's live model list when provider errors report retirement, capacity problems, or truncated structured output. Model names can be exposed by the API but still be temporarily unavailable, while another current model may accept the same structured JSON request. For large schema responses, prefer the account's lighter structured-capable model and use the SDK's native parsed response when available.

**Why:** The initial configured model was retired, a newer preview model returned repeated 503 high-demand responses and then hit MAX_TOKENS on a large structured response, while a live-listed lite model returned complete parsed analysis.

**How to apply:** Treat 404 model errors as a configuration/update issue, 503 high-demand errors as transient capacity, and MAX_TOKENS with malformed JSON as an output-budget/model-fit issue. Test a current generateContent-capable model with the actual response schema before changing the default; never fabricate an analysis during provider failure.