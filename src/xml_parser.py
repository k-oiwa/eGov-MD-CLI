"""
xml_parser.py
e-Gov法令XMLを解析し、扱いやすいPythonデータ構造に変換するモジュール。

e-Gov XMLの主な階層構造:
  Law
  └─ LawBody
     ├─ LawTitle        (法令名)
     └─ MainProvision   (本則)
        └─ Chapter      (章) ※省略される場合あり
           └─ Article   (条)
              ├─ ArticleTitle  (条見出し: 例「第二十条」)
              └─ Paragraph     (項)
                 ├─ ParagraphNum   (項番号: 例「２」、第一項は空の場合あり)
                 ├─ ParagraphSentence (項本文)
                 └─ Item          (号)
                    ├─ ItemTitle       (号番号: 例「一」)
                    ├─ ItemSentence    (号本文)
                    └─ Subitem1        (イ・ロ・ハ等)
                       ├─ Subitem1Title
                       └─ Subitem1Sentence
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class Subitem:
    """号の下位項目（イ・ロ・ハ等）"""
    title: str
    sentences: list[str] = field(default_factory=list)


@dataclass
class Item:
    """号"""
    title: str
    sentences: list[str] = field(default_factory=list)
    subitems: list[Subitem] = field(default_factory=list)


@dataclass
class Paragraph:
    """項"""
    num: str  # 項番号（第一項は空文字列の場合あり）
    sentences: list[str] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)


@dataclass
class Article:
    """条"""
    num: str        # 条番号（例: "20"）
    title: str      # 条見出し（例: "第二十条"）
    caption: str    # 条の表題（例: "（構造耐力）"）
    paragraphs: list[Paragraph] = field(default_factory=list)


@dataclass
class LawData:
    """法令全体"""
    law_title: str
    articles: list[Article] = field(default_factory=list)


def parse_xml(xml_text: str) -> LawData:
    """
    XML文字列を解析してLawDataオブジェクトを返す。

    Args:
        xml_text: e-Gov APIから取得したXML文字列

    Returns:
        LawDataオブジェクト
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"XMLの解析に失敗しました: {e}") from e

    # 法令名の取得
    law_title = _get_text(root, ".//LawTitle") or "（法令名不明）"

    law_data = LawData(law_title=law_title)

    # 全条文を取得
    for article_elem in root.iter("Article"):
        article = _parse_article(article_elem)
        if article:
            law_data.articles.append(article)

    return law_data


def _parse_article(article_elem: ET.Element) -> Article | None:
    """
    <Article>要素を解析してArticleオブジェクトを返す。
    """
    # 条番号（属性 Num から取得）
    num = article_elem.get("Num", "")

    # 条見出し（<ArticleTitle>）
    title_elem = article_elem.find("ArticleTitle")
    title = (title_elem.text or "").strip() if title_elem is not None else ""

    # 条の表題（<ArticleCaption>）
    caption_elem = article_elem.find("ArticleCaption")
    caption = (caption_elem.text or "").strip() if caption_elem is not None else ""

    article = Article(num=num, title=title, caption=caption)

    # 項の解析
    for para_elem in article_elem.iter("Paragraph"):
        paragraph = _parse_paragraph(para_elem)
        if paragraph:
            article.paragraphs.append(paragraph)

    return article


def _parse_paragraph(para_elem: ET.Element) -> Paragraph | None:
    """
    <Paragraph>要素を解析してParagraphオブジェクトを返す。
    """
    # 項番号（<ParagraphNum>）
    num_elem = para_elem.find("ParagraphNum")
    num = (num_elem.text or "").strip() if num_elem is not None else ""

    paragraph = Paragraph(num=num)

    # 項本文（<ParagraphSentence> 内の <Sentence>）
    para_sentence_elem = para_elem.find("ParagraphSentence")
    if para_sentence_elem is not None:
        paragraph.sentences = _extract_sentences(para_sentence_elem)

    # 号の解析（<Item>）
    for item_elem in para_elem.findall("Item"):
        item = _parse_item(item_elem)
        if item:
            paragraph.items.append(item)

    return paragraph


def _parse_item(item_elem: ET.Element) -> Item | None:
    """
    <Item>要素を解析してItemオブジェクトを返す。
    """
    # 号番号（<ItemTitle>）
    title_elem = item_elem.find("ItemTitle")
    title = (title_elem.text or "").strip() if title_elem is not None else ""

    item = Item(title=title)

    # 号本文（<ItemSentence> 内の <Sentence>）
    item_sentence_elem = item_elem.find("ItemSentence")
    if item_sentence_elem is not None:
        item.sentences = _extract_sentences(item_sentence_elem)

    # 下位項目（<Subitem1>）
    for subitem_elem in item_elem.findall("Subitem1"):
        subitem = _parse_subitem(subitem_elem)
        if subitem:
            item.subitems.append(subitem)

    return item


def _parse_subitem(subitem_elem: ET.Element) -> Subitem | None:
    """
    <Subitem1>要素を解析してSubitemオブジェクトを返す。
    """
    # 下位項目番号（<Subitem1Title>）
    title_elem = subitem_elem.find("Subitem1Title")
    title = (title_elem.text or "").strip() if title_elem is not None else ""

    subitem = Subitem(title=title)

    # 下位項目本文（<Subitem1Sentence> 内の <Sentence>）
    sentence_elem = subitem_elem.find("Subitem1Sentence")
    if sentence_elem is not None:
        subitem.sentences = _extract_sentences(sentence_elem)

    return subitem


def _extract_sentences(parent_elem: ET.Element) -> list[str]:
    """
    親要素内の <Sentence> タグからテキストを抽出してリストで返す。
    <Table>や<Fig>は無視し、エラーで停止しない。
    """
    sentences = []
    for sentence_elem in parent_elem.findall("Sentence"):
        try:
            text = _get_all_text(sentence_elem)
            if text:
                sentences.append(text)
        except Exception:
            # 予期しない構造でもスキップして継続
            pass
    # <Sentence>が見つからない場合は親要素のテキストを直接取得
    if not sentences:
        try:
            text = _get_all_text(parent_elem)
            if text:
                sentences.append(text)
        except Exception:
            pass
    return sentences


def _get_all_text(elem: ET.Element) -> str:
    """
    要素内の全テキスト（子要素のテキストを含む）を結合して返す。
    <Table>や<Fig>タグは無視する。
    """
    IGNORE_TAGS = {"Table", "Fig"}
    parts = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag not in IGNORE_TAGS:
            parts.append(_get_all_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts).strip()


def _get_text(root: ET.Element, xpath: str) -> str | None:
    """
    XPathで要素を検索し、テキストを返す。見つからない場合はNone。
    """
    elem = root.find(xpath)
    if elem is not None and elem.text:
        return elem.text.strip()
    return None


def filter_article(law_data: LawData, article_num: str) -> LawData:
    """
    特定の条番号の条文のみを含むLawDataを返す。

    Args:
        law_data: 全条文を含むLawDataオブジェクト
        article_num: 抽出する条番号（例: "20"）

    Returns:
        指定条文のみを含むLawDataオブジェクト
    """
    filtered = LawData(law_title=law_data.law_title)
    for article in law_data.articles:
        if article.num == article_num:
            filtered.articles.append(article)
    if not filtered.articles:
        raise ValueError(f"第{article_num}条が見つかりませんでした。")
    return filtered
