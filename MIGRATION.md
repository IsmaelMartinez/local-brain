# Migration Guide: From local-brain to LiteLLM

This guide helps you migrate from the deprecated local-brain CLI to LiteLLM for cost optimization and intelligent model routing.

---

## Why Migrate?

LiteLLM provides everything local-brain tried to do, plus:

✅ **Model routing** - Automatic fallback between local/cloud models
✅ **100+ providers** - Ollama, Anthropic, OpenAI, Bedrock, OpenRouter
✅ **Cost tracking** - Built-in dashboards, budgets, per-user limits
✅ **Caching** - Redis, semantic caching for additional savings
✅ **Team features** - SSO, user management, observability
✅ **Production-ready** - 33K+ stars, active development, enterprise support

---

## Prerequisites

- Python 3.8+
- Ollama installed (for local models)
- API keys for cloud providers (Anthropic, OpenAI, etc.)

---

## Installation

### Option 1: Quick Start (Single User)

```bash
# Install LiteLLM
pip install 'litellm[proxy]'

# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull qwen2.5-coder:32b
```

### Option 2: Team Deployment (Docker)

```bash
# Clone LiteLLM
git clone https://github.com/BerriAI/litellm.git
cd litellm

# Use docker-compose
docker-compose up -d
```

---

## Configuration

### Basic Setup (Local Model + Cloud Fallback)

Create `litellm_config.yaml`:

```yaml
model_list:
  # Local model (FREE, replaces local-brain)
  - model_name: local-qwen
    litellm_params:
      model: ollama/qwen2.5-coder:32b
      api_base: http://localhost:11434

  # Cloud fallback for complex tasks
  - model_name: cloud-claude
    litellm_params:
      model: claude-sonnet-4-5-20250929
      api_key: os.environ/ANTHROPIC_API_KEY

# Default to local, fall back to cloud
router_settings:
  routing_strategy: usage-based-routing-v2
  default_model: local-qwen
  fallback_models: ["cloud-claude"]
  timeout: 60s  # Try local for 60s before fallback

# Optional: Enable caching
cache_params:
  type: redis  # Requires Redis server
  host: localhost
  port: 6379
  ttl: 3600  # 1 hour
```

### Advanced Setup (Multi-Provider Routing)

```yaml
model_list:
  # Tier 1: Local (FREE)
  - model_name: ollama-qwen
    litellm_params:
      model: ollama/qwen2.5-coder:32b
      api_base: http://localhost:11434

  # Tier 2: Anthropic Haiku (CHEAP)
  - model_name: claude-haiku
    litellm_params:
      model: claude-haiku-4-5-20251001
      api_key: os.environ/ANTHROPIC_API_KEY

  # Tier 3: Anthropic Sonnet (MODERATE)
  - model_name: claude-sonnet
    litellm_params:
      model: claude-sonnet-4-5-20250929
      api_key: os.environ/ANTHROPIC_API_KEY

  # Tier 4: Anthropic Opus (EXPENSIVE)
  - model_name: claude-opus
    litellm_params:
      model: claude-opus-4-5-20251101
      api_key: os.environ/ANTHROPIC_API_KEY

# Intelligent routing
router_settings:
  routing_strategy: usage-based-routing-v2

  # Model aliases for easy switching
  model_group_alias:
    # Default: Try cheap first, escalate if needed
    auto:
      - ollama-qwen
      - claude-haiku
      - claude-sonnet

    # For explicit quality requests
    premium:
      - claude-sonnet
      - claude-opus

# Cost controls
litellm_settings:
  max_budget: 500  # $500/month limit
  budget_duration: 30d

  # Track usage
  success_callback: ["langfuse"]  # Optional observability

# Security
general_settings:
  master_key: ${LITELLM_MASTER_KEY}  # Set via environment
  allowed_routes: ["/chat/completions", "/v1/chat/completions"]
```

---

## Running LiteLLM

### Development (Local)

```bash
# Start the proxy
litellm --config litellm_config.yaml --port 4000

# In another terminal, configure Claude Code
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY="sk-anything"  # Any value works locally

# Test
claude "write a hello world function in Python"
```

### Production (Background Service)

**Using systemd:**

```bash
# Create service file
sudo nano /etc/systemd/system/litellm.service
```

```ini
[Unit]
Description=LiteLLM Proxy
After=network.target

[Service]
Type=simple
User=litellm
WorkingDirectory=/opt/litellm
Environment="ANTHROPIC_API_KEY=your-key-here"
Environment="LITELLM_MASTER_KEY=your-master-key"
ExecStart=/usr/local/bin/litellm --config /opt/litellm/config.yaml --port 4000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable litellm
sudo systemctl start litellm
sudo systemctl status litellm
```

**Using Docker Compose:**

```yaml
version: '3.8'

services:
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    ports:
      - "4000:4000"
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
    command: ["--config", "/app/config.yaml", "--port", "4000"]
    restart: unless-stopped

  redis:  # Optional, for caching
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

---

## Claude Code Configuration

### For Local Development

```bash
# Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY="sk-anything"

# Optional: Override model selection
export ANTHROPIC_MODEL="local-qwen"  # Use local by default
```

### For Team/Production

```bash
# Point to your team's LiteLLM server
export ANTHROPIC_BASE_URL=https://litellm.yourcompany.com
export ANTHROPIC_API_KEY="sk-user-your-key"  # Get from admin

# Users can select models explicitly
claude --model claude-sonnet "complex question"
claude --model claude-opus "critical decision"
```

---

## Model Selection Guide

### When to Use Each Tier

| Model | Use For | Cost | Quality |
|-------|---------|------|---------|
| **Ollama (local)** | Simple code gen, refactoring, tests | FREE | Good |
| **Claude Haiku** | Quick questions, simple tasks | $ | Good |
| **Claude Sonnet** | Complex debugging, architecture | $$ | Excellent |
| **Claude Opus** | Critical decisions, production code | $$$$ | Best |

### Explicit Model Selection

```bash
# Use local for simple task
claude --model ollama-qwen "add docstrings to this function"

# Use Sonnet for complex task
claude --model claude-sonnet "debug this memory leak"

# Use Opus for critical task
claude --model claude-opus "review this security-sensitive code"
```

---

## Cost Tracking

### View Usage Dashboard

LiteLLM provides a web UI at `http://localhost:4000/ui` showing:
- Total spend
- Cost per model
- Cost per user (if using API keys)
- Request volume
- Success rates

### Set Budget Limits

**Global budget:**
```yaml
litellm_settings:
  max_budget: 1000  # $1000/month org-wide
  budget_duration: 30d
```

**Per-user budget:**
```yaml
# Generate user keys via API or UI
virtual_keys:
  - key: sk-user-alice
    user_id: alice@company.com
    max_budget: 200  # $200/month

  - key: sk-user-bob
    user_id: bob@company.com
    max_budget: 100  # $100/month
    models: ["ollama-qwen", "claude-haiku"]  # No premium access
```

### Export Usage Data

```bash
# Via API
curl http://localhost:4000/spend/logs \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  > usage_data.json

# Analyze with jq
cat usage_data.json | jq '.[] | select(.user_id == "alice@company.com")'
```

---

## Observability Integration

### Langfuse (Recommended)

```yaml
litellm_settings:
  success_callback: ["langfuse"]

env_vars:
  LANGFUSE_PUBLIC_KEY: your-public-key
  LANGFUSE_SECRET_KEY: your-secret-key
  LANGFUSE_HOST: https://cloud.langfuse.com
```

View traces at https://cloud.langfuse.com

### Prometheus + Grafana

```yaml
litellm_settings:
  success_callback: ["prometheus"]

general_settings:
  prometheus_port: 9090
```

Metrics available at `http://localhost:9090/metrics`

---

## Caching for Additional Savings

### Redis Caching (Exact Match)

```yaml
cache_params:
  type: redis
  host: localhost
  port: 6379
  ttl: 3600  # 1 hour
```

Caches identical requests. Saves API costs on repeated queries.

### Semantic Caching (Similarity Match)

```yaml
cache_params:
  type: redis-semantic
  similarity_threshold: 0.8  # 80% similarity = cache hit
  ttl: 3600
```

Caches SIMILAR requests, not just identical. More aggressive savings.

**Example:**
- Request 1: "write a function to check if a number is prime"
- Request 2: "create a function that checks for prime numbers"
- With semantic caching: Request 2 hits cache (90% similar)

---

## Team Features

### SSO Integration (Enterprise)

LiteLLM Enterprise includes built-in SSO for 5+ users.

**Without Enterprise**, use OAuth2-Proxy:

```yaml
# docker-compose.yml
services:
  oauth2-proxy:
    image: quay.io/oauth2-proxy/oauth2-proxy
    environment:
      - OAUTH2_PROXY_PROVIDER=oidc
      - OAUTH2_PROXY_OIDC_ISSUER_URL=https://your-okta.com
      - OAUTH2_PROXY_CLIENT_ID=xxx
      - OAUTH2_PROXY_CLIENT_SECRET=xxx
      - OAUTH2_PROXY_UPSTREAMS=http://litellm:4000
    ports:
      - "443:443"
```

### User Management

```bash
# Create user key via API
curl -X POST http://localhost:4000/key/generate \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -d '{
    "user_id": "alice@company.com",
    "max_budget": 200,
    "models": ["ollama-qwen", "claude-haiku", "claude-sonnet"]
  }'

# Response
{
  "key": "sk-user-abc123...",
  "user_id": "alice@company.com"
}
```

---

## Migration Checklist

- [ ] Install LiteLLM and Ollama
- [ ] Create `litellm_config.yaml` with your models
- [ ] Start LiteLLM proxy
- [ ] Update Claude Code environment variables
- [ ] Test with simple query
- [ ] Verify model routing works (local → cloud fallback)
- [ ] Set up cost tracking dashboard
- [ ] Configure budget limits (optional)
- [ ] Add caching for additional savings (optional)
- [ ] Uninstall local-brain CLI

---

## Troubleshooting

### "Connection refused" when connecting to LiteLLM

```bash
# Check if LiteLLM is running
curl http://localhost:4000/health

# Check logs
docker logs litellm  # If using Docker
journalctl -u litellm -f  # If using systemd
```

### "Model not found" error

```bash
# Verify model name in config
cat litellm_config.yaml | grep model_name

# Test model directly
litellm --model ollama/qwen2.5-coder:32b --test
```

### Slow response times

```bash
# Check if local Ollama is running
ollama list

# Increase timeout in config
router_settings:
  timeout: 120s  # 2 minutes
```

### Cache not working

```bash
# Verify Redis is running
redis-cli ping  # Should return PONG

# Check LiteLLM logs for cache hits
# Look for "Cache Hit: True" in logs
```

---

## Getting Help

- **LiteLLM Docs:** https://docs.litellm.ai/
- **GitHub Issues:** https://github.com/BerriAI/litellm/issues
- **Discord:** https://discord.com/invite/wuPM9dRgDw
- **Enterprise Support:** sales@berri.ai

---

## Cost Savings Examples

### Example 1: Solo Developer

**Before (direct Anthropic):**
- 1000 requests/month
- All to Claude Sonnet: 1000 × $13.80 = **$13,800/month**

**After (LiteLLM routing):**
- 800 requests to Ollama (local): $0
- 150 requests to Haiku: 150 × $1.68 = $252
- 50 requests to Sonnet: 50 × $13.80 = $690
- **Total: $942/month (93% savings)**

### Example 2: 10-Person Team

**Before:**
- 10 users × $350/month = **$3,500/month**

**After:**
- 7 users on local Ollama: 7 × $0 = $0
- 3 users on routed cloud: 3 × $100/month = $300
- **Total: $300/month (91% savings)**

### Example 3: Enterprise (50 users)

**Before:**
- 50 users × $350/month = **$17,500/month ($210K/year)**

**After:**
- LiteLLM infrastructure: $100/month
- 80% Ollama/cheap models, 15% Sonnet, 5% Opus
- Average: $75/user/month × 50 = $3,750/month
- **Total: $3,850/month ($46K/year) - 78% savings ($164K/year saved)**

---

## Next Steps

1. Follow the [Quick Start](#option-1-quick-start-single-user)
2. Configure your [model routing](#configuration)
3. Set up [cost tracking](#cost-tracking)
4. Add [caching](#caching-for-additional-savings) for extra savings
5. Share with your team!

---

*For questions about this migration, open an issue on the [local-brain GitHub](https://github.com/IsmaelMartinez/local-brain) or reach out to the LiteLLM community.*
