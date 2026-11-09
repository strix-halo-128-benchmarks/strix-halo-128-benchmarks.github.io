#!/usr/bin/env python3
"""md2html.py — minimal, dependency-free markdown -> standalone HTML renderer.

Handles exactly the subset this document uses: headings, fenced code, pipe tables, ordered and
unordered lists, horizontal rules, bold/italic/inline-code, and paragraphs. ASCII diagrams go into
<pre> with a monospace font and horizontal scroll, so they never wrap into nonsense.

  usage: md2html.py input.md output.html "Title"
"""
import html
import os
import re
import sys

CSS = """
:root { --fg:#e8e6e3; --bg:#14161a; --dim:#9aa4b2; --acc:#7fb0ff; --line:#2a2f38; --code:#0f1115; }
@media (prefers-color-scheme: light) {
  :root { --fg:#1c1f24; --bg:#fbfbfa; --dim:#5b6472; --acc:#1a56b8; --line:#d8dce3; --code:#f3f4f6; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
  font:16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
main { max-width: 980px; margin: 0 auto; padding: 28px 22px 96px; }
h1 { font-size:1.85em; line-height:1.2; margin:.2em 0 .5em; letter-spacing:-.01em; }
h2 { font-size:1.32em; margin:2.1em 0 .6em; padding-top:.55em; border-top:1px solid var(--line); }
h3 { font-size:1.08em; margin:1.7em 0 .45em; color:var(--acc); }
p { margin:.72em 0; }
code { font-family:"SF Mono",ui-monospace,Menlo,Consolas,monospace; font-size:.88em;
  background:var(--code); padding:.12em .35em; border-radius:4px; }
pre { background:var(--code); border:1px solid var(--line); border-radius:8px; padding:14px 16px;
  overflow-x:auto; margin:1.1em 0; }
figure.fig { margin:1.6em 0 0.6em; padding:10px 12px; background:var(--code);
  border:1px solid var(--line); border-radius:8px; }
figure.fig svg { display:block; width:100%; height:auto; max-width:100%; }
pre code { background:none; padding:0; font-size:.8em; line-height:1.5; }
table { border-collapse:collapse; width:100%; margin:1.2em 0; font-size:.9em; display:block; overflow-x:auto; }
th,td { border:1px solid var(--line); padding:.5em .7em; text-align:left; vertical-align:top; }
th { background:var(--code); font-weight:600; }
hr { border:0; border-top:1px solid var(--line); margin:2.2em 0; }
ul,ol { margin:.6em 0 .9em; padding-left:1.45em; }
li { margin:.28em 0; }
strong { color:var(--fg); }
em { color:var(--dim); font-style:italic; }
nav { border:1px solid var(--line); border-radius:8px; padding:14px 18px; margin:1.4em 0 2.2em;
  background:var(--code); font-size:.9em; }
nav a { color:var(--acc); text-decoration:none; }
nav a:hover { text-decoration:underline; }
nav ol { margin:.4em 0 0; padding-left:1.3em; }
a { color:var(--acc); }
.meta { color:var(--dim); font-size:.9em; }
@media print { body{background:#fff;color:#000} nav{display:none} h2{page-break-after:avoid}
  pre,table{page-break-inside:avoid} main{max-width:none} }
"""


def inline(text: str) -> str:
    """Escape, then apply inline code, bold, italic and links."""
    held = []

    def stash(m):
        held.append(m.group(1))
        return f"\x00{len(held)-1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    # [text](url) — without this, markdown links render as literal "[text](url)" in the HTML.
    # Targets are already HTML-escaped above, so an & in a URL arrives as &amp;, which is correct
    # inside an href.
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    for i, code in enumerate(held):
        text = text.replace(f"\x00{i}\x00", f"<code>{html.escape(code, quote=False)}</code>")
    return text


MD_PATH = ""            # set in main(); figures resolve relative to the markdown's directory


def render(md: str) -> str:
    lines = md.splitlines()
    out, i = [], 0
    in_list = None
    while i < len(lines):
        line = lines[i]

        # embedded figure: a whole line of the form  {{svg charts/name.svg}}
        m = re.match(r"^\{\{\s*svg\s+(.+?)\s*\}\}$", line.strip())
        if m:
            src = os.path.join(os.path.dirname(os.path.abspath(MD_PATH)), m.group(1))
            try:
                svg = open(src, encoding="utf-8").read()
            except OSError:
                out.append(f"<p><em>[missing figure: {html.escape(m.group(1))}]</em></p>")
                i += 1
                continue
            svg = svg[svg.index("<svg"):] if "<svg" in svg else svg
            out.append("<figure class=\"fig\">" + svg + "</figure>")
            i += 1
            continue

        # fenced code
        if line.strip().startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf), quote=False) + "</code></pre>")
            continue

        # table: a pipe line followed by a separator line
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ["<table><thead><tr>"]
            t += [f"<th>{inline(c)}</th>" for c in header]
            t.append("</tr></thead><tbody>")
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue

        # headings
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        # horizontal rule
        if re.match(r"^-{3,}\s*$", line.strip()):
            out.append("<hr>")
            i += 1
            continue

        # lists
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            kind = "ol" if m.group(2)[0].isdigit() else "ul"
            if in_list != kind:
                if in_list:
                    out.append(f"</{in_list}>")
                out.append(f"<{kind}>")
                in_list = kind
            item = [m.group(3)]
            i += 1
            # wrapped bullet text: indented lines that are not another marker, a table,
            # a fence, a heading, a rule or a figure belong to the item they continue.
            # Without this the continuation is emitted as a paragraph and the list is cut
            # in half — the defect that split §4.1's bullets on every page view.
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip() or not nxt.startswith((" ", "\t")):
                    break
                s = nxt.strip()
                if re.match(r"^([-*]|\d+\.)\s", s) or s.startswith(("|", "```", "#", "{{svg")) \
                        or re.match(r"^-{3,}\s*$", s):
                    break
                item.append(s)
                i += 1
            out.append(f"<li>{inline(' '.join(item))}</li>")
            continue
        elif in_list:
            out.append(f"</{in_list}>")
            in_list = None

        if not line.strip():
            i += 1
            continue

        # paragraph (consume consecutive plain lines)
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|\||```|-{3,}\s*$|(\s*)([-*]|\d+\.)\s)", lines[i]):
            buf.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(b.strip() for b in buf)) + "</p>")

    if in_list:
        out.append(f"</{in_list}>")
    return "\n".join(out)


def main():
    global MD_PATH
    src, dst, title = sys.argv[1], sys.argv[2], sys.argv[3]
    # Optional 4th arg: a description; with PUBLIC_URL set, emit the discovery tags a search engine
    # and a link unfurler read. Omitted (as for the private edition) the page is unchanged.
    desc = sys.argv[4] if len(sys.argv) > 4 else ""
    public = os.environ.get("PUBLIC_URL", "").rstrip("/")
    MD_PATH = src
    md = open(src, encoding="utf-8").read()
    body = render(md)

    head_extra = ""
    if desc and public:
        page_url = f"{public}/" if os.path.basename(dst) == "index.html" else f"{public}/{os.path.basename(dst)}"
        head_extra = f'''<meta name="description" content="{html.escape(desc, quote=True)}">
<link rel="canonical" href="{page_url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(desc, quote=True)}">
<meta property="og:url" content="{page_url}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{html.escape(title, quote=True)}">
<meta name="twitter:description" content="{html.escape(desc, quote=True)}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Dataset",
"name":"{html.escape(title)}","description":"{html.escape(desc)}","url":"{page_url}",
"license":"https://creativecommons.org/licenses/by/4.0/",
"creator":{{"@type":"Organization","name":"strix-halo-128-benchmarks"}},
"isAccessibleForFree":true,
"keywords":["Strix Halo","gfx1151","local LLM","llama.cpp","HumanEval","MMLU-Pro","benchmark"],
"distribution":[{{"@type":"DataDownload","encodingFormat":"application/json",
"contentUrl":"{public}/data/catalogue.json"}}]}}</script>'''

    # build a contents list from the h2 headings
    toc = []
    for m in re.finditer(r"^## (\d+)\. (.+)$", md, re.M):
        anchor = f"s{m.group(1)}"
        toc.append(f'<li><a href="#{anchor}">{html.escape(m.group(2))}</a></li>')
    # inject ids into the rendered h2s
    def add_id(m):
        return f'<h2 id="s{m.group(1)}">{m.group(2)}</h2>'
    body = re.sub(r"<h2>(\d+)\. (.*?)</h2>", add_id, body)

    # title block first, then the contents, then the body
    h1 = re.search(r"<h1>(.*?)</h1>", body, re.S)
    if h1:
        body = body.replace(h1.group(0), "", 1)
        titleblock = f"<h1>{h1.group(1)}</h1>"
    else:
        titleblock = f"<h1>{html.escape(title)}</h1>"

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>{head_extra}<style>{CSS}</style></head>
<body><main>
{titleblock}
<nav><strong>Contents</strong><ol>{"".join(toc)}</ol></nav>
{body}
</main></body></html>"""
    open(dst, "w", encoding="utf-8").write(page)
    print(f"wrote {dst}: {len(page)} bytes, {len(toc)} contents entries")


if __name__ == "__main__":
    main()
