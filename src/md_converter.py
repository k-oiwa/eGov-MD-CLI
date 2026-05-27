"""
md_converter.py
解析済みの法令データ（LawData）を受け取り、Markdown文字列を生成するモジュール。

出力フォーマット例:
  # 建築基準法
  
  ## 第二十条（構造耐力）
  
  建築物は、自重、積載荷重、...
  
  ２　前項の規定は、...
  
  　一　木造の建築物にあっては、...
  
  　　イ　...
"""

from src.xml_parser import LawData, Article, Paragraph, Item, Subitem


def convert_to_markdown(law_data: LawData) -> str:
    """
    LawDataオブジェクトをMarkdown文字列に変換する。

    Args:
        law_data: 解析済みの法令データ

    Returns:
        Markdown形式の文字列
    """
    lines = []

    # 法令名を最上位見出しとして出力
    lines.append(f"# {law_data.law_title}")
    lines.append("")

    for article in law_data.articles:
        lines.extend(_convert_article(article))

    return "\n".join(lines)


def _convert_article(article: Article) -> list[str]:
    """
    Articleオブジェクトを Markdown 行リストに変換する。
    """
    lines = []

    # 条見出し（例: ## 第二十条（構造耐力））
    heading = article.title
    if article.caption:
        heading = f"{heading}{article.caption}"
    lines.append(f"## {heading}")
    lines.append("")

    for i, paragraph in enumerate(article.paragraphs):
        lines.extend(_convert_paragraph(paragraph, para_index=i))

    return lines


def _convert_paragraph(paragraph: Paragraph, para_index: int) -> list[str]:
    """
    Paragraphオブジェクトを Markdown 行リストに変換する。

    Args:
        paragraph: 項データ
        para_index: 条内での項のインデックス（0始まり）
    """
    lines = []

    # 項番号の処理
    # 第一項（para_index == 0）は番号なし、または ParagraphNum が空の場合が多い
    num_text = paragraph.num.strip()
    if num_text and num_text != "1":
        # 第二項以降は番号を先頭に付ける（例: "２　"）
        prefix = f"{num_text}　"
    else:
        prefix = ""

    # 項本文
    if paragraph.sentences:
        sentence_text = "".join(paragraph.sentences)
        lines.append(f"{prefix}{sentence_text}")
    elif prefix:
        lines.append(prefix)

    # 号の出力
    for item in paragraph.items:
        lines.extend(_convert_item(item, indent_level=1))

    lines.append("")
    return lines


def _convert_item(item: Item, indent_level: int) -> list[str]:
    """
    Itemオブジェクトを Markdown 行リストに変換する。

    Args:
        item: 号データ
        indent_level: インデントレベル（1=号, 2=下位項目）
    """
    lines = []
    indent = "　" * indent_level  # 全角スペースでインデント

    # 号番号と本文
    title = item.title
    sentence_text = "".join(item.sentences) if item.sentences else ""

    if title and sentence_text:
        lines.append(f"{indent}{title}　{sentence_text}")
    elif title:
        lines.append(f"{indent}{title}")
    elif sentence_text:
        lines.append(f"{indent}{sentence_text}")

    # 下位項目（イ・ロ・ハ等）
    for subitem in item.subitems:
        lines.extend(_convert_subitem(subitem, indent_level=indent_level + 1))

    return lines


def _convert_subitem(subitem: Subitem, indent_level: int) -> list[str]:
    """
    Subitemオブジェクトを Markdown 行リストに変換する。

    Args:
        subitem: 下位項目データ
        indent_level: インデントレベル
    """
    lines = []
    indent = "　" * indent_level  # 全角スペースでインデント

    title = subitem.title
    sentence_text = "".join(subitem.sentences) if subitem.sentences else ""

    if title and sentence_text:
        lines.append(f"{indent}{title}　{sentence_text}")
    elif title:
        lines.append(f"{indent}{title}")
    elif sentence_text:
        lines.append(f"{indent}{sentence_text}")

    return lines
