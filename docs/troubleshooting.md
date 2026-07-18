# Troubleshooting

## Common Issues

### 1. "No module named 'flux'"

**Solution**: Install the package first.

```bash
cd C:\Users\FC\swarm
pip install -e .
```

### 2. "No module named 'aiohttp'"

**Solution**: Install aiohttp for Ollama provider.

```bash
pip install aiohttp
```

### 3. "Provider 'ollama' error (400): does not support tools"

**Cause**: Your model doesn't support tool calling.

**Solution**: Use a bigger model.

```bash
ollama pull qwen2:1.5b    # Supports tools
ollama pull llama3.2       # Best quality
```

### 4. "Model returned empty response"

**Cause**: Model is too small or not responding properly.

**Solution**:
- Use a bigger model
- Check if Ollama is running: `ollama list`
- Test directly: `ollama run qwen2:0.5b "Hello"`

### 5. "Connection refused" / "Cannot connect to Ollama"

**Solution**: Start Ollama first.

```bash
# Windows: Ollama should start automatically
# If not, run:
ollama serve

# Check if running:
ollama list
```

### 6. "MaxTurnsExceeded"

**Cause**: Agent is stuck in a loop (tool calling repeatedly).

**Solution**: Increase max_turns or check agent instructions.

```python
from flux.agent import AgentSettings
agent = Agent(
    settings=AgentSettings(max_turns=20),  # Increase from default 10
    ...
)
```

### 7. "GuardrailTripwireTriggered"

**Cause**: Input or output was blocked by a guardrail.

**Solution**: Check guardrail configuration or remove guardrails for testing.

### 8. Slow responses

**Solutions**:
- Use smaller model: `qwen2:0.5b` (352MB)
- Reduce `max_tokens` in ModelSettings
- Check Ollama is using GPU: `ollama ps`

## Model Recommendations

| Model | Size | Tools | Quality | Speed |
|-------|------|-------|---------|-------|
| qwen2:0.5b | 352MB | No | Basic | Fast |
| qwen2:1.5b | 1GB | Yes | Good | Medium |
| llama3.2 | 2GB | Yes | Best | Slow |

## Getting Help

1. Check Ollama status: `ollama list`
2. Run tests: `cd C:\Users\FC\swarm && python -m pytest tests/ -v`
3. Check examples: `C:\Users\FC\swarm\examples\`
