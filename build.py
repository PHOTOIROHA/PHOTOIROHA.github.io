#!/usr/bin/env python3
"""PHOTO IROHA サイトのビルドスクリプト。

  python3 build.py          … docs/ に公開用のHTMLを書き出す
  python3 build.py --draft  … 表題欄に DRAFT 表示を入れて書き出す
  python3 build.py --preview … preview/ に1枚完結のHTMLを書き出す（Artifact公開用）

外部ライブラリは使わない。Pythonが入っていれば動く。
テンプレートの {{TOKEN}} を文字列で置き換えるだけの、単純な仕組み。
"""

import argparse
import base64
import json
import mimetypes
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
SRC = ROOT / "src"
PHOTOS = ROOT / "photos"
ASSETS = ROOT / "assets"   # ロゴなど、ページに依らない素材

# 公開フォルダ（docs/）に毎回置く目印。開いた人が中身を手で直さないように。
MARKER = """このフォルダは、python3 build.py が毎回まるごと作り直します。

ここのファイルを手で編集しても、次のビルドで消えます。
文章や写真を直すときは、ひとつ上の src/ と photos/ を編集してください。

  src/content/kenchiku.json   文章と、どの写真を使うかの指定
  photos/kenchiku/            サイト用に縮小した写真
  src/styles/site.css         見た目

このフォルダの名前が docs なのは、GitHub Pages が公開できるフォルダ名が
「リポジトリ直下」か「docs」の2つしかないためです。文書置き場ではありません。
"""

# ---------------------------------------------------------------------------
# サイトの構成。ページを増やすときは ready を True にして content/ に JSON を置く。
# ready が False のページは、ナビに「準備中」と表示されるだけでリンクにならない。
# ---------------------------------------------------------------------------
SITE = {
    "top": {"label": "トップ", "slug": "index", "ready": False},
    "sections": [
        {
            "key": "kojin",
            "label": "個人のお客様へ",
            "ready": False,
            "pages": [
                {"key": "kodomo", "label": "子供", "ready": False},
                {"key": "kazoku", "label": "家族写真", "ready": False},
                {"key": "kekkon", "label": "結婚写真", "ready": False},
            ],
        },
        {
            "key": "jigyosha",
            "label": "事業者のお客様へ",
            "ready": True,
            "pages": [
                {"key": "ryori", "label": "料理", "ready": False},
                {"key": "kenchiku", "label": "建築", "ready": True},
                {"key": "jinbutsu", "label": "人物", "ready": False},
            ],
        },
    ],
}


def fill(template: str, values: dict) -> str:
    """{{TOKEN}} を values の中身で置き換える。埋め忘れがあればエラーにする。"""
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    leftover = re.findall(r"\{\{([A-Z_]+)\}\}", template)
    if leftover:
        raise SystemExit(f"テンプレートに未置換のトークンが残っています: {sorted(set(leftover))}")
    return template


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def img_tag(slug: str, filename: str, alt: str, embed: bool) -> str:
    src = data_uri(PHOTOS / slug / filename) if embed else f"photos/{slug}/{filename}"
    return f'<img src="{src}" alt="{alt}">'


def build_nav(current_page: str):
    """ヘッダーの2段のナビを組み立てる。現在地とそれ以外を出し分ける。"""
    current_section = None
    for section in SITE["sections"]:
        if any(p["key"] == current_page for p in section["pages"]):
            current_section = section

    primary = []
    top = SITE["top"]
    if top["ready"]:
        primary.append(f'<a class="nav-item" href="{top["slug"]}.html">{top["label"]}</a>')
    else:
        primary.append(f'<span class="nav-item is-soon">{top["label"]} <span class="soon-tag">準備中</span></span>')

    for section in SITE["sections"]:
        if current_section and section["key"] == current_section["key"]:
            primary.append(f'<span class="nav-item is-current">{section["label"]}</span>')
        elif section["ready"]:
            primary.append(f'<span class="nav-item">{section["label"]}</span>')
        else:
            primary.append(f'<span class="nav-item is-soon">{section["label"]} <span class="soon-tag">準備中</span></span>')

    sub = []
    if current_section:
        sub.append(f'<span class="eyebrow">{current_section["label"]}</span>')
        for page in current_section["pages"]:
            if page["key"] == current_page:
                sub.append(f'<span class="sub-item is-current">{page["label"]}</span>')
            elif page["ready"]:
                sub.append(f'<a class="sub-item" href="{page["key"]}.html">{page["label"]}</a>')
            else:
                sub.append(f'<span class="sub-item is-soon">{page["label"]} <span class="soon-tag">準備中</span></span>')

    breadcrumb_parts = ["トップ"]
    if current_section:
        breadcrumb_parts.append(current_section["label"])
    breadcrumb = " ＞ ".join(breadcrumb_parts)
    page_label = next(
        (p["label"] for s in SITE["sections"] for p in s["pages"] if p["key"] == current_page),
        current_page,
    )
    breadcrumb += f' ＞ <span class="current">{page_label}</span>'

    return "\n      ".join(primary), "\n    ".join(sub), breadcrumb


def build_page(slug: str, draft: bool, embed: bool) -> str:
    content = json.loads((SRC / "content" / f"{slug}.json").read_text(encoding="utf-8"))
    page_tpl = (SRC / "templates" / f"page_{slug}.html").read_text(encoding="utf-8")
    base_tpl = (SRC / "templates" / "base.html").read_text(encoding="utf-8")
    css = (SRC / "styles" / "site.css").read_text(encoding="utf-8")

    gallery_items = "\n".join(
        "        " + img_tag(slug, p["file"], p["alt"], embed) for p in content["gallery"]["photos"]
    )
    cta_lines = "\n".join(f"        <p>{line}</p>" for line in content["cta"]["lines"])

    # メールの宛先と件名。件名は日本語なので URL エンコードして渡す。
    mailto = f'mailto:{content["cta"]["email"]}?subject={quote(content["cta"]["subject"])}'

    main = fill(page_tpl, {
        "HERO_IMG": img_tag(slug, content["hero"]["file"], content["hero"]["alt"], embed),
        "EYEBROW": content["eyebrow"],
        "HEADING": content["heading"],
        "BODY": content["body"],
        "CAREER": content["career"],
        "FEATURE_TITLE": content["feature"]["title"],
        "FEATURE_NOTE": f'        <span class="eyebrow">{content["feature"]["note"]}</span>' if content["feature"]["note"] else "",
        "FEATURE_IMG": img_tag(slug, content["feature"]["file"], content["feature"]["alt"], embed),
        "FEATURE_CAPTION": f'        <figcaption>{content["feature"]["caption"]}</figcaption>' if content["feature"]["caption"] else "",
        "GALLERY_TITLE": content["gallery"]["title"],
        "GALLERY_NOTE": content["gallery"]["note"],
        "GALLERY_ITEMS": gallery_items,
        "CTA_LINES": cta_lines,
        "CTA_HREF": mailto,
        "CTA_EMAIL": content["cta"]["email"],
        "CTA_NOTE": f'        <p class="cta-note">{content["cta"]["note"]}</p>' if content["cta"].get("note") else "",
        "CTA_LABEL": content["cta"]["label"],
    })

    nav_primary, nav_sub, breadcrumb = build_nav(slug)

    if draft:
        today = date.today().strftime("%Y.%m.%d")
        sheet_meta = (
            '<div class="sheet-meta mono">'
            f'<span>SHEET <b>{content["nav_label"]}</b></span>'
            '<span>STATUS <b>DRAFT</b></span>'
            f'<span>{today}</span></div>'
        )
        foot_note = "デザイン確認用ドラフト"
    else:
        sheet_meta = ""
        foot_note = "&copy; PHOTO IROHA"

    style = f"<style>\n{css}\n</style>" if embed else '<link rel="stylesheet" href="styles/site.css">'

    return fill(base_tpl, {
        "PAGE_TITLE": content["page_title"],
        "DESCRIPTION": content["description"],
        "STYLE": style,
        "LOGO": data_uri(ASSETS / "logo.png") if embed else "assets/logo.png",
        "ROOT": "",
        "NAV_PRIMARY": nav_primary,
        "NAV_SUB": nav_sub,
        "BREADCRUMB": breadcrumb,
        "SHEET_META": sheet_meta,
        "MAIN": main,
        "FOOT_NOTE": foot_note,
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", action="store_true", help="表題欄に DRAFT を表示する")
    parser.add_argument("--preview", action="store_true", help="1枚完結のHTMLを preview/ に書き出す")
    args = parser.parse_args()

    slugs = [p["key"] for s in SITE["sections"] for p in s["pages"] if p["ready"]]

    if args.preview:
        out_dir = ROOT / "preview"
        out_dir.mkdir(exist_ok=True)
        for slug in slugs:
            path = out_dir / f"{slug}.html"
            path.write_text(build_page(slug, draft=True, embed=True), encoding="utf-8")
            print(f"preview/{slug}.html  {path.stat().st_size / 1024 / 1024:.2f} MB")
        return

    out_dir = ROOT / "docs"   # GitHub Pages が公開できるフォルダ名は / か /docs のみ
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir()
    (out_dir / "styles").mkdir()
    shutil.copy2(SRC / "styles" / "site.css", out_dir / "styles" / "site.css")
    shutil.copytree(PHOTOS, out_dir / "photos")
    shutil.copytree(ASSETS, out_dir / "assets")
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    (out_dir / "これはビルド結果です.txt").write_text(MARKER, encoding="utf-8")

    for slug in slugs:
        (out_dir / f"{slug}.html").write_text(build_page(slug, draft=args.draft, embed=False), encoding="utf-8")
        print(f"docs/{slug}.html")

    total = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
    print(f"合計 {total / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
