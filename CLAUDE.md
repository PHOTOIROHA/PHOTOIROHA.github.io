# PHOTO IROHA サイト

荒井秀治（PHOTO IROHA・長野）の事業サイト。Adobe Portfolio からの刷新。
デザインの検討経緯やコピーの決定履歴は `~/Desktop/hideji_work/ClaudeCode/写真（プラン／事業）/docs/` にある。
このリポジトリは「実際に公開されるもの」だけを持つ。

## 触り方

```bash
python3 build.py           # docs/ に公開用のHTMLを書き出す
python3 build.py --draft   # 表題欄に DRAFT を出した状態で書き出す（本人確認用）
python3 build.py --preview # preview/ に1枚完結のHTMLを書き出す（Artifact公開用）
```

ビルドに必要なものは Python だけ。npm も外部ライブラリも使わない。
`python3 -m http.server` を `docs/` で立ち上げれば、そのまま表示確認できる。

## 構成

| 場所 | 中身 |
|---|---|
| `src/content/*.json` | **文章と写真の指定。ふだん編集するのはここ。** |
| `src/templates/base.html` | 全ページ共通の外枠（ヘッダー・ナビ・フッター） |
| `src/templates/page_*.html` | ページごとの本体 |
| `src/styles/site.css` | 全ページ共通のCSS。色は `:root` の変数で定義 |
| `photos/<ページ>/` | サイト用に縮小済みの写真。元データは置かない |
| `docs/` | **ビルド結果。手で編集しない。** GitHub Pages がここを公開する |
| `tools/prepare_photos.py` | 元写真をサイト用サイズに書き出す |

`docs/` という名前は GitHub Pages の制約（公開できるのは `/` か `/docs` だけ）。中身は毎回作り直される。

## ページを増やすとき

1. `build.py` 冒頭の `SITE` で、そのページの `ready` を `True` にする
2. `src/content/<ページ名>.json` を作る
3. `src/templates/page_<ページ名>.html` を作る（建築ページを写すのが早い）

`ready` が `False` のページは、ナビに「準備中」と出るだけでリンクにならない。
公開済みのページだけが自動的にリンクになる。

## 写真を差し替えるとき

```bash
python3 tools/prepare_photos.py kenchiku 01-ldk /path/to/元写真.jpg
python3 tools/prepare_photos.py kenchiku hero  /path/to/元写真.jpg --hero
```

そのあと `src/content/kenchiku.json` の `alt`（写真の説明文）も直す。読み上げとSEOで使われる。

**確認を怠らないこと：表札・住所プレート・車のナンバーが写っていないか。**
建売物件はすでに買主が住んでいるので、特定につながる情報は出さない。所在地・分譲地名・区画番号も書かない。

## 決まっていること

- 見出しは明朝（Shippori Mincho）、本文はゴシック（BIZ UDGothic）、ラベル類は M PLUS 1 Code
- 建築ページの冒頭は**大きな写真から始める**（2026-09-10 決定。それ以前は「テキストから」だった）
- 背景は白に寄せる。写真の色を邪魔しない
- 経歴は囲みではなく、本文の下に小さな一行で置く（囲み4つは「大袈裟」と本人判断）
- ライト／ダーク両対応。色は必ず `:root` の変数を通す

## まだ決まっていないこと

- ドメイン（未取得）。当面は `<ユーザー名>.github.io/<リポジトリ名>/` で公開する
- お問い合わせの送信先。いまのボタンは `#contact` を指すだけで動かない。Googleフォームか Formspree を予定
- トップページ、および建築以外の5ページ
- 建築ページの本文は、本人が「AI臭さを減らしたい」として書き直す予定。**こちらから勝手に書き換えない**

## 本人について

プログラマーではない。コマンドは実行できるが、仕組みの説明は必要。
写真の選定は本人の領分なので、こちらが選んだものは必ず「仮」と伝える。
