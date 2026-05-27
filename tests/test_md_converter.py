"""
test_md_converter.py
md_converter モジュールの単体テスト。
解析済みデータが正しいMarkdown形式に変換されるかを検証する。
"""

from src.xml_parser import parse_xml
from src.md_converter import convert_to_markdown


SIMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Showa" Num="201" Year="25" LawType="Act" Lang="ja">
  <LawBody>
    <LawTitle>建築基準法</LawTitle>
    <MainProvision>
      <Article Num="20">
        <ArticleTitle>第二十条</ArticleTitle>
        <ArticleCaption>（構造耐力）</ArticleCaption>
        <Paragraph Num="1">
          <ParagraphNum/>
          <ParagraphSentence>
            <Sentence>建築物は安全な構造でなければならない。</Sentence>
          </ParagraphSentence>
          <Item Num="1">
            <ItemTitle>一</ItemTitle>
            <ItemSentence>
              <Sentence>高さが六十メートルを超える建築物。</Sentence>
            </ItemSentence>
            <Subitem1 Num="1">
              <Subitem1Title>イ</Subitem1Title>
              <Subitem1Sentence>
                <Sentence>構造計算による確認。</Sentence>
              </Subitem1Sentence>
            </Subitem1>
          </Item>
        </Paragraph>
        <Paragraph Num="2">
          <ParagraphNum>２</ParagraphNum>
          <ParagraphSentence>
            <Sentence>前項の規定は適用しない。</Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
    </MainProvision>
  </LawBody>
</Law>
"""


class TestConvertToMarkdown:
    def test_law_title_heading(self):
        """法令名がH1見出しとして出力されること"""
        law_data = parse_xml(SIMPLE_XML)
        md = convert_to_markdown(law_data)
        assert "# 建築基準法" in md

    def test_article_heading(self):
        """条見出しがH2見出しとして出力されること"""
        law_data = parse_xml(SIMPLE_XML)
        md = convert_to_markdown(law_data)
        assert "## 第二十条（構造耐力）" in md

    def test_first_paragraph_no_prefix(self):
        """第一項は番号なしで本文が出力されること"""
        law_data = parse_xml(SIMPLE_XML)
        md = convert_to_markdown(law_data)
        assert "建築物は安全な構造でなければならない。" in md
        # 第一項に "１　" のような番号が付かないこと
        assert "１　建築物は" not in md

    def test_second_paragraph_with_prefix(self):
        """第二項は番号付きで出力されること"""
        law_data = parse_xml(SIMPLE_XML)
        md = convert_to_markdown(law_data)
        assert "２　前項の規定は適用しない。" in md

    def test_item_indented(self):
        """号はインデントされて出力されること"""
        law_data = parse_xml(SIMPLE_XML)
        md = convert_to_markdown(law_data)
        # 全角スペース1つのインデント + 号番号
        assert "　一　" in md

    def test_subitem_double_indented(self):
        """下位項目（イ）は2段インデントで出力されること"""
        law_data = parse_xml(SIMPLE_XML)
        md = convert_to_markdown(law_data)
        # 全角スペース2つのインデント + 下位項目番号
        assert "　　イ　" in md
