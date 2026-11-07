---
title: Retrying LLM calls without making things worse
date: 2026-10-28
summary: Which errors deserve a retry, why jitter matters, and how a retry budget stops a bad minute from becoming an outage.
tags: llm, reliability, python
draft: true
---

*Sample post from the design, kept as a formatting reference. It's a draft, so it only shows with `make preview`. Delete it or rewrite it in your own words.*

Every LLM API fails sometimes. You get rate limited, the provider is overloaded, or a request just hangs. The instinct is to wrap the call in a loop and try again. That works until it doesn't: a naive retry loop turns a short blip into a thundering herd that keeps the service down.

## Not every error deserves a retry

Start by sorting failures into ones that might succeed on a second try and ones that never will:

- **429 rate limited:** retry, and honor the `retry-after` header if there is one.
- **5xx and overloaded:** retry with backoff.
- **400 bad request:** never retry. The same input will fail the same way.
- **Timeouts:** retry only if the call is safe to repeat.

## Backoff with jitter

Exponential backoff spaces retries out, but if a thousand clients fail at the same moment, they also retry at the same moment. Adding randomness (jitter) spreads them across the window.

```python retry.py
import random, time

RETRYABLE = {429, 500, 502, 503, 529}

def call_with_retries(send, max_attempts=5, base=0.5, cap=20.0):
    for attempt in range(max_attempts):
        try:
            return send()
        except APIError as err:
            if err.status not in RETRYABLE or attempt == max_attempts - 1:
                raise
            # Full jitter: sleep a random amount up to the ceiling
            ceiling = min(cap, base * 2 ** attempt)
            time.sleep(err.retry_after or random.uniform(0, ceiling))
```

## Budget your retries

Backoff limits retries per request. It does nothing about the total. A retry budget caps retries as a fraction of normal traffic.

!!! note "Rule of thumb"
    Retries should add at most about 10% to your request volume. When the budget runs out, fail fast.

## Wrapping up

Classify errors, back off with jitter, and cap the total.
