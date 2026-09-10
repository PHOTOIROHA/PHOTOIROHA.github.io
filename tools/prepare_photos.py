#!/usr/bin/env python3
"""元データの写真を、サイト用のサイズに書き出して photos/ に置く。

  python3 tools/prepare_photos.py kenchiku 01-ldk /path/to/元写真.jpg
  python3 tools/prepare_photos.py kenchiku hero  /path/to/元写真.jpg --hero

macOS標準の sips を使うので、追加のインストールは不要。
元ファイルには一切触らない（読むだけ）。

書き出し設定：
  通常  長辺1600px・JPEG品質70（1枚あたり200〜350KB）
  hero  長辺2000px・JPEG品質72

写真を差し替えたら、忘れずに src/content/<ページ>.json の alt（写真の説明文）も直すこと。
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("page", help="ページ名（例: kenchiku）")
    parser.add_argument("name", help="書き出す名前、拡張子なし（例: 01-ldk）")
    parser.add_argument("source", help="元写真のパス")
    parser.add_argument("--hero", action="store_true", help="冒頭の大きな写真として書き出す")
    args = parser.parse_args()

    source = Path(args.source).expanduser()
    if not source.exists():
        sys.exit(f"元写真が見つかりません: {source}")

    out_dir = ROOT / "photos" / args.page
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.name}.jpg"

    size, quality = (2000, 72) if args.hero else (1600, 70)
    subprocess.run(
        ["sips", "-Z", str(size), "-s", "format", "jpeg",
         "-s", "formatOptions", str(quality), str(source), "--out", str(out)],
        check=True, stdout=subprocess.DEVNULL,
    )

    print(f"{out.relative_to(ROOT)}  {out.stat().st_size / 1024:.0f} KB")
    print("写り込みの確認を忘れずに：表札・住所プレート・車のナンバー")


if __name__ == "__main__":
    main()
