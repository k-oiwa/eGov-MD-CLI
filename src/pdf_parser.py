"""
pdf_parser.py
PDFファイルからテキストを抽出し、Markdown形式に整形するモジュール。

告示PDFの典型的な構造:
  - 「第1」「第2」などの見出し → ## 見出し
  - 「一」「二」などの号 → インデント付きリスト
  - 「イ」「ロ」などの下位項目 → さらにインデント
"""

import re
import unicodedata

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


def parse_pdf_to_markdown(pdf_path: str, title: str = "") -> str:
    """
    PDFファイルを読み込み、Markdown文字列に変換する。

    Args:
        pdf_path: PDFファイルのパス
        title: Markdownの最上位見出しに使うタイトル（省略可）

    Returns:
        Markdown形式の文字列

    Raises:
        RuntimeError: PDFパーサーが利用できない場合
        FileNotFoundError: PDFファイルが見つからない場合
    """
    # テキスト抽出
    raw_text = _extract_text(pdf_path)

    if not raw_text.strip():
        return f"# {title}\n\n（テキストを抽出できませんでした）\n"

    # Markdown整形
    md_text = _format_as_markdown(raw_text, title)
    return md_text


def _extract_text(pdf_path: str) -> str:
    """
    PDFからテキストを抽出する。PyMuPDF → pdfplumber の順で試みる。

    Args:
        pdf_path: PDFファイルのパス

    Returns:
        抽出されたテキスト文字列

    Raises:
        RuntimeError: 利用可能なPDFパーサーがない場合
    """
    if PYMUPDF_AVAILABLE:
        return _extract_with_pymupdf(pdf_path)
    elif PDFPLUMBER_AVAILABLE:
        return _extract_with_pdfplumber(pdf_path)
    else:
        raise RuntimeError(
            "PDFパーサーが見つかりません。"
            "'pip install PyMuPDF' または 'pip install pdfplumber' を実行してください。"
        )


def _extract_with_pymupdf(pdf_path: str) -> str:
    """
    PyMuPDF (fitz) を使ってPDFからテキストを抽出する。

    Args:
        pdf_path: PDFファイルのパス

    Returns:
        抽出されたテキスト文字列
    """
    pages_text = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                text = page.get_text("text")
                if text:
                    pages_text.append(text)
            except Exception as e:
                print(f"[警告] ページ {page_num + 1} のテキスト抽出に失敗しました: {e}")
                continue
        doc.close()
    except Exception as e:
        print(f"[警告] PyMuPDFでのPDF読み込みに失敗しました: {e}")

    return "\n".join(pages_text)


def _extract_with_pdfplumber(pdf_path: str) -> str:
    """
    pdfplumber を使ってPDFからテキストを抽出する。

    Args:
        pdf_path: PDFファイルのパス

    Returns:
        抽出されたテキスト文字列
    """
    pages_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                except Exception as e:
                    print(f"[警告] ページ {page_num + 1} のテキスト抽出に失敗しました: {e}")
                    continue
    except Exception as e:
        print(f"[警告] pdfplumberでのPDF読み込みに失敗しました: {e}")

    return "\n".join(pages_text)


def _format_as_markdown(raw_text: str, title: str = "") -> str:
    """
    抽出されたテキストをMarkdown形式に整形する。

    告示の典型的な構造に対応:
    - 「第1」「第2」→ ## 見出し
    - 「一」「二」「三」→ 全角スペースインデント
    - 「イ」「ロ」「ハ」→ 2段インデント

    Args:
        raw_text: PDFから抽出された生テキスト
        title: Markdownの最上位見出し

    Returns:
        Markdown形式の文字列
    """
    lines = raw_text.split("\n")
    md_lines = []

    # タイトル
    if title:
        md_lines.append(f"# {title}")
        md_lines.append("")

    for line in lines:
        line = line.rstrip()
        if not line:
            md_lines.append("")
            continue

        # Unicode正規化（全角数字等を半角に）
        normalized = unicodedata.normalize("NFKC", line)

        # 見出しパターン: 「第1」「第1条」「第一」等
        if re.match(r"^第\s*[0-9一二三四五六七八九十百]+\s*(条|項|号)?[\s　]", normalized):
            # 先頭の空白を除去
            heading_text = line.strip()
            md_lines.append(f"## {heading_text}")
            md_lines.append("")
            continue

        # 号パターン: 行頭が「一　」「二　」等（全角スペース付き）
        if re.match(r"^[一二三四五六七八九十]+[\s　]", line.strip()):
            md_lines.append(f"　{line.strip()}")
            continue

        # 下位項目パターン: 行頭が「イ　」「ロ　」「ハ　」等
        if re.match(r"^[イロハニホヘトチリヌ][\s　]", line.strip()):
            md_lines.append(f"　　{line.strip()}")
            continue

        # 項番号パターン: 行頭が「２　」「３　」等（全角数字）
        if re.match(r"^[２３４５６７８９][\s　]", line.strip()):
            md_lines.append(line.strip())
            continue

        # その他の行はそのまま出力
        md_lines.append(line)

    # 連続する空行を1行に圧縮
    result_lines = []
    prev_empty = False
    for line in md_lines:
        if line == "":
            if not prev_empty:
                result_lines.append("")
            prev_empty = True
        else:
            result_lines.append(line)
            prev_empty = False

    return "\n".join(result_lines)
