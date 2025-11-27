# 🟢 Active Session State
**Objective:** Fix "Vertex Claude 4.5" error by routing through LiteLLM.
**Status:** Build

## 🛡️ Applied Constraints
- Logic/IO Separation (Config isolation)
- Zero Trust (Validate config)

## 📝 Current Focus
- **Phase:** Phase 2: Build & Implement
- **Ref:** `opencode.json`

## 🧠 Context & Learnings
- **Configuration Switch:** Switched from direct `vertex` provider (broken) to `litellm` proxy (OpenAI compatible).
- **Model ID:** Using `vertex_ai/claude-opus-4-5` as defined in LiteLLM params.
- **Port:** Assumed default `http://localhost:4000`. User must ensure LiteLLM is running.
