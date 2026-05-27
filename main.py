"""
main.py
eGov-MD-CLI のエントリーポイント。
CLI引数を解析し、各モジュールを呼び出して法令MarkdownをoutputディレクトリへI保存する。

使用例:
    python main.py get 建築基準法
    python main.py get 建築基準法 --article 20
    python main.py get 建築士法 --article 20
"""

import argparse
import os
import sys

from src.api_client import get_law_xml
from src.xml_parser import parse_xml, filter_article
from src.md_converter import convert_to_markdown

OUTPUT_DIR = "output"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="egov-md-cli",
        description="e-Gov法令APIから法令を取得してMarkdown形式で保存するCLIツール",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get サブコマンド
    get_parser = subparsers.add_parser("get", help="法令を取得してMarkdownに変換する")
    get_parser.add_argument(
        "law_name",
        help="法令名または法令番号（例: 建築基準法、昭和二十五年法律第二百一号）",
    )
    get_parser.add_argument(
        "--article",
        metavar="NUM",
        help="抽出する条番号（例: 20）。省略時は全文を出力する。",
        default=None,
    )
    get_parser.add_argument(
        "--output",
        metavar="DIR",
        help=f"出力先ディレクトリ（デフォルト: {OUTPUT_DIR}）",
        default=OUTPUT_DIR,
    )

    args = parser.parse_args()

    if args.command == "get":
        run_get(args.law_name, args.article, args.output)


def run_get(law_name: str, article_num: str | None, output_dir: str) -> None:
    """
    法令を取得してMarkdownに変換し、ファイルに保存する。

    Args:
        law_name: 法令名または法令番号
        article_num: 抽出する条番号（Noneの場合は全文）
        output_dir: 出力先ディレクトリ
    """
    print(f"[情報] 法令を取得中: {law_name}")
    try:
        xml_text = get_law_xml(law_name)
    except ValueError as e:
        print(f"[エラー] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[エラー] APIの取得に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    print("[情報] XMLを解析中...")
    try:
        law_data = parse_xml(xml_text)
    except ValueError as e:
        print(f"[エラー] {e}", file=sys.stderr)
        sys.exit(1)

    # 特定条文の抽出
    if article_num is not None:
        print(f"[情報] 第{article_num}条を抽出中...")
        try:
            law_data = filter_article(law_data, article_num)
        except ValueError as e:
            print(f"[エラー] {e}", file=sys.stderr)
            sys.exit(1)

    print("[情報] Markdownに変換中...")
    md_text = convert_to_markdown(law_data)

    # 出力ファイル名の決定
    os.makedirs(output_dir, exist_ok=True)
    if article_num is not None:
        filename = f"{law_data.law_title}_第{article_num}条.md"
    else:
        filename = f"{law_data.law_title}.md"

    # ファイル名に使えない文字を除去（Windows対応）
    safe_filename = _sanitize_filename(filename)
    output_path = os.path.join(output_dir, safe_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    print(f"[完了] 保存しました: {output_path}")


def _sanitize_filename(filename: str) -> str:
    """
    ファイル名として使えない文字を除去または置換する。
    """
    invalid_chars = r'\/:*?"<>|'
    for ch in invalid_chars:
        filename = filename.replace(ch, "_")
    return filename


if __name__ == "__main__":
    main()
