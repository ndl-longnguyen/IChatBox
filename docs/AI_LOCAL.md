# Local AI Auto Reply

IChatBox supports local AI auto-replies with an Ollama-compatible HTTP API.

## Runtime

The web app reads these environment variables:

- `AI_LOCAL_BASE_URL`: Ollama API URL, default `http://localhost:11434`
- `AI_LOCAL_MODEL`: model name, default `qwen2.5:1.5b`
- `AI_LOCAL_TIMEOUT_SECONDS`: HTTP timeout for one reply, default `30`
- `AI_LOCAL_MAX_TOKENS`: maximum generated tokens for one reply, default `160`
- `AI_LOCAL_NUM_CTX`: local model context window, default `1024`
- `AI_KNOWLEDGE_CHUNK_SIZE`: character chunk size for training data
- `AI_KNOWLEDGE_CHUNK_OVERLAP`: overlap between chunks
- `AI_KNOWLEDGE_UPLOAD_MAX_BYTES`: maximum upload size for one knowledge file

With Docker Compose, the `ollama` service is behind the optional `ai` profile:

```bash
docker compose --profile ai up -d
docker compose exec ollama ollama pull qwen2.5:1.5b
```

If auto-reply logs `timed out`, the model is reachable but did not finish within
`AI_LOCAL_TIMEOUT_SECONDS`. Increase the timeout, reduce `AI_LOCAL_MAX_TOKENS`,
or use a smaller/faster model for CPU-only machines.

## Admin Workflow

1. Open `AI` in the tenant admin navigation (`/admin/ai/`).
2. Add training data by pasting text or uploading a `.txt`, `.md`, `.markdown`, `.csv`, or `.json` file.
3. The system stores the original document and splits it into searchable chunks.
4. Enable `AI auto-reply`.
5. Visitor messages are answered only when AI is enabled and relevant trained chunks exist.
6. Delete a trained document from the AI page when it is outdated; its chunks are removed automatically.

## Storage Model

- `AISettings`: per-admin auto-reply switch, model name, language, prompt, and retrieval limits.
- `KnowledgeBase`: per-admin knowledge container.
- `KnowledgeDocument`: original manual/file content.
- `KnowledgeChunk`: optimized searchable chunks used as local AI context.
- `TrainingJob`: records chunking/training attempts.

This keeps uploaded knowledge separated per admin and avoids sending one large document to the model for every message.
