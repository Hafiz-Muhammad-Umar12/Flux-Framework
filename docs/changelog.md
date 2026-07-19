---
title: Changelog
description: All notable changes to Flux Agents.
---

# Changelog

All notable changes to Flux Agents will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Documentation website with Material for MkDocs
- Comprehensive API reference
- Example documentation pages (Hello World, Weather, Search, E-Commerce, Customer Support)

### Changed

- Version bump to 0.2.0

## [0.2.0] - 2025-01-01

### Added

- **OpenAI provider** (`OpenAIModel`) -- works with OpenAI, OpenRouter, DeepSeek, Groq, and any OpenAI-compatible API
- **Anthropic provider** (`AnthropicModel`) -- Claude model support via the Anthropic SDK
- **Tool registry** (`ToolRegistry`) -- centralized tool management
- **Built-in tools** -- `ShellTool`, `FileReadTool`, `FileWriteTool`
- **Console and file tracing** -- `ConsoleTracer` for stderr, `FileTracer` for JSON lines
- **Cache middleware** (`CacheMiddleware`) -- TTL-based response caching by message hash
- **Rate limit middleware** (`RateLimitMiddleware`) -- token bucket rate limiter
- **Retry middleware** (`RetryMiddleware`) -- exponential backoff retries on `ProviderError`/`ToolError`
- **Profanity guardrail** (`ProfanityGuardrail`) -- configurable word list blocking
- **PII guardrail** (`PIIGuardrail`) -- detects emails, phone numbers, and SSNs in input
- **Vector memory** (`VectorMemory`) -- simple hash-based in-memory vector store with cosine similarity
- **Conversation memory** (`ConversationMemory`) -- wraps a `Session` for substring-based search
- **SQLite session** (`SQLiteSession`) -- persistent conversation storage with WAL mode
- **9 example scripts** -- from basic chat to custom model providers
- **Test suite** -- 60+ tests covering agents, tools, handoffs, guardrails, middleware, and sessions

### Changed

- Improved model registry with prefix matching
- Better streaming support with typed event classes (`TextDeltaEvent`, `ToolCallEvent`, `MessageCompleteEvent`, `UsageEvent`, `ErrorEvent`, `AgentUpdatedEvent`)
- `Agent` is now a frozen dataclass with `clone()` for immutable modifications
- `Agent.instructions` can be a callable receiving `RunContext` for dynamic prompts

### Fixed

- Model inheritance on handoff -- child agents now inherit the parent model when none is set

## [0.1.0] - 2024-12-01

### Added

- **Initial release**
- **Provider-agnostic architecture** -- swap LLM providers without changing application code
- **Agent abstraction** -- immutable dataclass with name, instructions, model, tools, handoffs, guardrails
- **Runner execution engine** -- `Runner.run()` (async), `Runner.run_sync()`, `Runner.run_streamed()`
- **Tool system** -- `@tool` decorator auto-generates JSON schemas from type hints; supports sync and async functions
- **Ollama provider** (`OllamaModel`) -- local LLM inference via Ollama
- **Model registry** (`ModelRegistry`) -- register and resolve models by name
- **Session protocol** and `InMemorySession` -- conversation persistence interface
- **Memory protocol** and `ConversationMemory` -- search over conversation history
- **Middleware protocol** and `LoggingMiddleware` -- request/response interception
- **Event bus** (`EventBus`) -- decoupled observability with `on()`, `on_all()`, `emit()`
- **Streaming support** -- `StreamResult` with async iteration over `StreamEvent` types
- **Guardrail system** -- `InputGuardrail` and `OutputGuardrail` base classes with `GuardrailResult`
- **Handoff system** -- `Handoff` dataclass and agent tuple for multi-agent routing via `transfer_to_{name}` tools
- **CLI entry points** -- `flux` and `flux-agents` commands
- **Global configuration** -- `FluxConfig` with `get_config()` / `set_config()`
- **Basic documentation** -- getting started guide, API reference, architecture overview, troubleshooting
