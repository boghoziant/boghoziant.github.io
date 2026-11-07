# Personal site

A small static-site generator in Python: Markdown posts in, HTML out. Design from the Claude Design canvas "Personal website design".

## Use

```
make setup     # first time only
make preview   # build with drafts, serve at http://localhost:8000
make build     # build published content into dist/
```

## Where things live

| What | Where |
|---|---|
| Your name, bio, links, About page | `site.toml` |
| Projects | `projects.toml` |
| Posts | `posts/YYYY-MM-DD-slug.md` |
| Layout and pages | `templates/` (Jinja2) |
| Styles, theme toggle, filters | `static/style.css`, `static/site.js` |
| The generator | `build.py` |

## Writing a post

```
---
title: My post
date: 2026-11-07
summary: One sentence for the list and the RSS feed.
tags: llm, python
draft: true
---

Markdown here. Code blocks take a language and an optional filename:

```python retry.py
print("hi")
```
```

Remove `draft: true` (or set it to false) to publish.

## Deploy

`dist/` is plain HTML, so any static host works. GitHub Pages: push this repo, then use a Pages workflow that runs `make setup build` and publishes `dist/`.
