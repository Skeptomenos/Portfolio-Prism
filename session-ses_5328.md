# Quick test clarification

**Session ID:** ses_532852589ffeAXCKT0k8LUJgTr
**Created:** 11/29/2025, 3:39:31 AM
**Updated:** 11/29/2025, 3:51:51 AM

---

## User

test

---

## Assistant

---

## User

test

---

## Assistant

---

## User

I want to connect my litellm to opencode

---

## Assistant

```
Tool: webfetch
```

---

## Assistant

```
Tool: webfetch
```

---

## Assistant

```
Tool: webfetch
```

---

## Assistant

OpenCode supports OpenAI-compatible APIs via custom providers. To connect LiteLLM:

1. Run LiteLLM locally (e.g., `litellm --model gpt-4` on port 8000).
2. Add as custom provider: `opencode auth login` → select "Other" → enter ID "litellm" → enter API key if required.
3. Create/update `opencode.json`:
   ```json
   {
     "provider": {
       "litellm": {
         "npm": "@ai-sdk/openai-compatible",
         "name": "LiteLLM",
         "options": { "baseURL": "http://127.0.0.1:8000/v1" },
         "models": { "gpt-4": { "name": "GPT-4 via LiteLLM" } }
       }
     }
   }
   ```
4. Run `/models` in OpenCode to select it.

---

## User

use this config {
  "provider": {
    "litellm": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "LiteLLM Proxy",
      "options": {
        "baseURL": "http://localhost:4000/v1"
      },
      "models": {
        "vertex-ai/claude-opus-4-5": {
          "name": "Claude Opus 4.5 (Vertex AI)"
        }
      }
    }
  }
} 

---

## Assistant

```
Tool: read
```

---

## Assistant

```
Tool: edit
```

---

## Assistant

Updated opencode.json with your LiteLLM config. Run `/models` in OpenCode to select the Claude Opus model. Ensure LiteLLM is running on localhost:4000.

---

## User

i want to configure vertex globally. How to achieve that?

---

## Assistant

```
Tool: webfetch
```

---

## Assistant

```
Tool: bash
```

---

## Assistant

```
Tool: write
```

---

## Assistant

Created global OpenCode config at `~/.config/opencode/opencode.json` with Vertex AI provider.

To complete setup:

1. Set environment variables:
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export VERTEX_LOCATION=us-central1  # optional, defaults to global
   ```

2. Authenticate:
   ```bash
   gcloud auth application-default login
   ```
   Or set `GOOGLE_APPLICATION_CREDENTIALS` to your service account JSON path.

3. Run `/models` in OpenCode to select Vertex models.

---

## User

I cannot /compres with Opus and the current configuration. Here is the error message: litellm.UnsupportedParamsError: Anthropic doesn't support tool calling without `tools=` param specified. Pass `tools=` param OR set `litellm.modify_params = True` // `litellm_settings::modify_params: True` to add dummy tool to the request.. Received Model Group=vertex-ai/claude-opus-4-5
Available Model Group Fallbacks=None 

---

## Assistant

```
Tool: edit
```

---

## Assistant

Updated opencode.json to add `modifyParams: true` for the model. If that doesn't work, update your LiteLLM config (e.g., `config.yaml`) to include `modify_params: true` for this model:

```yaml
model_list:
  - model_name: vertex-ai/claude-opus-4-5
    litellm_params:
      model: vertex_ai/claude-opus-4-5  # adjust if different
      modify_params: true
```

Restart LiteLLM and try `/compress` again. Ensure the model name matches your LiteLLM setup.

---

## User

now i imemediately get following error. Also with normal chat messenges. error: litellm.BadRequestError: Vertex_aiException BadRequestError - b'{"type":"error","error":{"type":"invalid_request_error","message":"modifyParams: Extra inputs are not permitted"},"request_id":"req_vrtx_011CVbRHMjibJgvgZwMQcS5W"}'. Received Model Group=vertex-ai/claude-opus-4-5
Available Model Group Fallbacks=None 

---

## Assistant

```
Tool: edit
```

---

## Assistant

Removed invalid `modifyParams` from opencode.json.

The issue is on the LiteLLM server side. Update your LiteLLM config (e.g., `config.yaml`) to set `modify_params: true` for the model:

```yaml
model_list:
  - model_name: vertex-ai/claude-opus-4-5
    litellm_params:
      model: vertex_ai/claude-3-5-sonnet@20240620  # Use correct Vertex AI model name
      modify_params: true
```

Restart LiteLLM server. Also verify the exact model name - Vertex AI Claude models are like `claude-3-5-sonnet@20240620`, not `claude-opus-4-5`. Check your LiteLLM logs or Vertex AI console for the correct model ID.

---

## User

here is the correct model name: claude-opus-4-5@20251101

---

## Assistant

Update your LiteLLM config with the correct model name and `modify_params: true`:

```yaml
model_list:
  - model_name: vertex-ai/claude-opus-4-5
    litellm_params:
      model: vertex_ai/claude-opus-4-5@20251101
      modify_params: true
```

Restart LiteLLM server and try again. This should resolve the tool calling error.

---

