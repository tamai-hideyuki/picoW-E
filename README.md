# やったこと
- MicroPythonへの書き込み
- OLED文字表示
- 複数行表示
- 枠線表示
- 座標を適切に設定
- 乱数アニメーション
- Wi-Fiスキャン
- Wi-Fi継続監視ループ
- HTTPサーバー起動
- CSS基礎についての学習

## 学んだこと
- CSSにはクラスとidがある。クラスは使いまわせるが、idはその場一回限りで使うもの。
  - idも使いまわせるが、HTML的には仕様違反という扱い
  - 問題はJSでの取得時にidだと最初の１つしか取得できないので問題が生じる

## CSS基礎まとめ

### 1. 色・背景色
- `background-color` : 背景色を指定する
- `color` : 文字色を指定する

### 2. タイポグラフィ
- `font-family` : フォントの種類を指定する
- `text-align` : 文字の位置を指定する（left / center / right）
- `text-decoration` : 下線・打ち消し線などを指定する

### 3. margin・padding
- `margin` : 要素の外側の余白
- `padding` : 要素の内側の余白
- `margin-top / bottom / left / right` : 方向ごとに個別指定できる

### 4. border
- `border` : 枠線を指定する（太さ・種類・色）
- `border-bottom` : 下側だけの枠線
- 種類は `solid`（実線）/ `dashed`（点線）/ `dotted`（丸点線）/ `double`（二重線）

### 5. width・max-width・中央寄せ
- `max-width` : 要素の最大横幅を指定する
- `margin: 0 auto` : 上下0、左右自動で中央寄せになる

### 6. クラスとID
- `.クラス名` : 複数の要素に同じスタイルを使い回せる
- `#ID名` : 1ページに1回だけ使う想定（慣習的）
- 現代では基本的にクラスで統一する方が管理しやすい

### 7. hover
- `:hover` : マウスを乗せた時だけスタイルを適用する
- `cursor: pointer` : マウスカーソルを指マークに変える

### 8. Flexbox
- `display: flex` : Flexboxを有効化する
- `justify-content` : 横方向の並び方を指定する
- `align-items` : 縦方向の揃え方を指定する
- `space-around` : 要素を均等な間隔で並べる
