# eGov-MD-CLI

e-Gov法令APIを利用して法令XMLを取得し、読みやすいMarkdown形式に変換するローカルCLIツールです。

## 概要

2025年の法改正（4号特例の縮小等）を経た建築基準法や建築士法など、最新の関連法令をローカル環境で迅速に確認・管理するために開発されました。

## 対象法令（テスト対象）

- 建築基準法（昭和二十五年法律第二百一号）
- 建築基準法施行令
- 建築士法（昭和二十五年法律第二百二号）

## 環境構築手順

### 前提条件

- Python 3.11 以上

### セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/your-username/eGov-MD-CLI.git
cd eGov-MD-CLI

# 仮想環境の作成と有効化
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 実行コマンド例

```bash
# 建築基準法の全文をMarkdownとして出力
python main.py get 建築基準法

# 建築基準法の第20条のみを抽出して出力
python main.py get 建築基準法 --article 20

# 建築士法の第20条第2項を抽出
python main.py get 建築士法 --article 20
```

## ディレクトリ構成

```
eGov-MD-CLI/
├── README.md           # 本ファイル
├── .gitignore          # Git管理除外設定
├── requirements.txt    # 依存パッケージ一覧
├── main.py             # エントリーポイント・CLI引数処理
├── src/
│   ├── api_client.py   # e-Gov APIとの通信・XML取得
│   ├── xml_parser.py   # XML解析・Pythonデータ構造への変換
│   └── md_converter.py # Markdown文字列の生成
├── tests/              # 単体テスト
└── output/             # 生成されたMarkdownファイルの保存先（Git管理外）
```

## 出力ファイル

変換されたMarkdownファイルは `output/` ディレクトリに保存されます（例: `output/建築基準法.md`）。

## ライセンス

MIT License
