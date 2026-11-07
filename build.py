#!/usr/bin/env python3
"""Build the site: posts/*.md + site.toml + projects.toml -> dist/

Usage:
  python build.py            # published content only
  python build.py --drafts   # include posts/projects marked draft
"""
import html
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

ROOT = Path(__file__).parent
OUT = ROOT / "dist"
WORDS_PER_MINUTE = 230

FENCE = re.compile(r"^```(\w[\w+-]*)?(?:[ \t]+(\S+))?[ \t]*\n(.*?)\n```[ \t]*$", re.M | re.S)


@dataclass
class Post:
    slug: str
    title: str
    date: date
    summary: str
    tags: list[str]
    draft: bool
    html: str
    minutes: int
    prev: "Post | None" = field(default=None, repr=False)
    next: "Post | None" = field(default=None, repr=False)

    @property
    def url(self):
        return f"/blog/{self.slug}/"


def parse_front_matter(text):
    """Split '---\\nkey: value\\n---\\nbody' into (dict, body)."""
    if not text.startswith("---\n"):
        return {}, text
    head, _, body = text[4:].partition("\n---\n")
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body


def render_code_block(lang, filename, code):
    try:
        lexer = get_lexer_by_name(lang) if lang else TextLexer()
    except ClassNotFound:
        lexer = TextLexer()
    body = highlight(code, lexer, HtmlFormatter(nowrap=True))
    label = html.escape(filename or lang or "")
    return (
        '<figure class="code">'
        f'<div class="code-bar"><span>{label}</span>'
        '<button type="button" class="copy" aria-label="Copy code">Copy</button></div>'
        f'<pre><code>{body}</code></pre></figure>'
    )


def render_markdown(text):
    """Markdown -> HTML. Fenced blocks (```lang filename) get the design's code figure."""
    blocks = []

    def stash(m):
        blocks.append(render_code_block(m.group(1), m.group(2), m.group(3)))
        return f"\n\nCODEBLOCK{len(blocks) - 1}\n\n"

    text = FENCE.sub(stash, text)
    out = markdown.markdown(text, extensions=["tables", "toc", "attr_list", "admonition"])
    for i, block in enumerate(blocks):
        out = out.replace(f"<p>CODEBLOCK{i}</p>", block)
    return out


def load_posts(drafts):
    posts = []
    for path in sorted((ROOT / "posts").glob("*.md")):
        meta, body = parse_front_matter(path.read_text())
        draft = meta.get("draft", "false").lower() == "true"
        if draft and not drafts:
            continue
        slug = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
        posts.append(Post(
            slug=slug,
            title=meta.get("title", slug),
            date=date.fromisoformat(meta["date"]),
            summary=meta.get("summary", ""),
            tags=[t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            draft=draft,
            html=render_markdown(body),
            minutes=max(1, round(len(body.split()) / WORDS_PER_MINUTE)),
        ))
    posts.sort(key=lambda p: p.date, reverse=True)
    for newer, older in zip(posts, posts[1:]):
        newer.prev, older.next = older, newer
    return posts


def load_projects(drafts):
    projects = tomllib.loads((ROOT / "projects.toml").read_text()).get("project", [])
    return [p for p in projects if drafts or not p.get("draft")]


def group_by_year(posts):
    years = {}
    for p in posts:
        years.setdefault(p.date.year, []).append(p)
    return list(years.items())


def write(path, content):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def main():
    drafts = "--drafts" in sys.argv
    site = tomllib.loads((ROOT / "site.toml").read_text())
    posts = load_posts(drafts)
    projects = load_projects(drafts)
    tags = sorted({t for p in posts for t in p.tags})
    kinds = sorted({p["kind"] for p in projects if p.get("kind")})

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html", "xml"]))
    env.globals.update(site=site, year=date.today().year)

    def page(template, path, **ctx):
        write(path, env.get_template(template).render(**ctx))

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT / "static")

    page("home.html", "index.html", nav="home", posts=posts[:3],
         projects=[p for p in projects if p.get("featured")][:3])
    page("blog.html", "blog/index.html", nav="blog", groups=group_by_year(posts), tags=tags)
    for post in posts:
        page("post.html", f"blog/{post.slug}/index.html", nav="blog", post=post)
    if site.get("show_projects"):
        page("projects.html", "projects/index.html", nav="projects", projects=projects,
             kinds=kinds, posts={p.slug: p for p in posts})
    page("about.html", "about/index.html", nav="about")
    page("contact.html", "contact/index.html", nav="contact")
    if not site.get("contact", {}).get("web3forms_key"):
        print("warning: contact.web3forms_key is empty in site.toml; the contact form won't send")
    page("404.html", "404.html", nav="")

    updated = datetime.now(timezone.utc)
    page("feed.xml", "feed.xml", posts=posts[:20], updated=format_datetime(updated),
         rfc822=lambda d: format_datetime(datetime(d.year, d.month, d.day, tzinfo=timezone.utc)))

    print(f"Built {len(posts)} posts, {len(projects)} projects -> {OUT}"
          + (" (drafts included)" if drafts else ""))


if __name__ == "__main__":
    main()
