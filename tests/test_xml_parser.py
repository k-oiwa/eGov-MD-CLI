"""
test_xml_parser.py
xml_parser モジュールの単体テスト。
e-Gov XMLの特殊な構造が正しくパースされるかを検証する。
"""

import pytest
from src.xml_parser import parse_xml, filter_article, LawData, Article, Paragraph, Item


# ---- テスト用XMLサンプル ----

SIMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Showa" Num="201" Year="25" LawType="Act" Lang="ja">
  <LawNum>昭和二十五年法律第二百一号</LawNum>
  <LawBody>
    <LawTitle>建築基準法</LawTitle>
    <MainProvision>
      <Article Num="1">
        <ArticleTitle>第一条</ArticleTitle>
        <ArticleCaption>（目的）</ArticleCaption>
        <Paragraph Num="1">
          <ParagraphNum/>
          <ParagraphSentence>
            <Sentence>この法律は、建築物の敷地、構造、設備及び用途に関する最低の基準を定めて、国民の生命、健康及び財産の保護を図り、もつて公共の福祉の増進に資することを目的とする。</Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
      <Article Num="20">
        <ArticleTitle>第二十条</ArticleTitle>
        <ArticleCaption>（構造耐力）</ArticleCaption>
        <Paragraph Num="1">
          <ParagraphNum/>
          <ParagraphSentence>
            <Sentence>建築物は、自重、積載荷重、積雪荷重、風圧、土圧及び水圧並びに地震その他の震動及び衝撃に対して安全な構造のものとして、次の各号に掲げる建築物の区分に応じ、それぞれ当該各号に定める基準に適合するものでなければならない。</Sentence>
          </ParagraphSentence>
          <Item Num="1">
            <ItemTitle>一</ItemTitle>
            <ItemSentence>
              <Sentence>高さが六十メートルを超える建築物　前項の政令で定める技術的基準（中略）に適合するものであること。</Sentence>
            </ItemSentence>
          </Item>
          <Item Num="2">
            <ItemTitle>二</ItemTitle>
            <ItemSentence>
              <Sentence>高さが六十メートル以下の建築物のうち、（中略）</Sentence>
            </ItemSentence>
            <Subitem1 Num="1">
              <Subitem1Title>イ</Subitem1Title>
              <Subitem1Sentence>
                <Sentence>地震力についての構造計算（中略）</Sentence>
              </Subitem1Sentence>
            </Subitem1>
            <Subitem1 Num="2">
              <Subitem1Title>ロ</Subitem1Title>
              <Subitem1Sentence>
                <Sentence>前号イに規定する構造計算に準ずるものとして（中略）</Sentence>
              </Subitem1Sentence>
            </Subitem1>
          </Item>
        </Paragraph>
        <Paragraph Num="2">
          <ParagraphNum>２</ParagraphNum>
          <ParagraphSentence>
            <Sentence>前項の規定は、その建築物の用途、規模又は構造に応じて（中略）</Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
    </MainProvision>
  </LawBody>
</Law>
"""

XML_WITH_TABLE = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Showa" Num="201" Year="25" LawType="Act" Lang="ja">
  <LawBody>
    <LawTitle>テスト法令</LawTitle>
    <MainProvision>
      <Article Num="5">
        <ArticleTitle>第五条</ArticleTitle>
        <Paragraph Num="1">
          <ParagraphNum/>
          <ParagraphSentence>
            <Sentence>次の表に定めるとおりとする。<Table><TableRow><TableColumn>A</TableColumn></TableRow></Table></Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
    </MainProvision>
  </LawBody>
</Law>
"""

XML_FIRST_PARA_NO_NUM = """<?xml version="1.0" encoding="UTF-8"?>
<Law>
  <LawBody>
    <LawTitle>サンプル法令</LawTitle>
    <MainProvision>
      <Article Num="3">
        <ArticleTitle>第三条</ArticleTitle>
        <Paragraph Num="1">
          <ParagraphNum></ParagraphNum>
          <ParagraphSentence>
            <Sentence>第一項の本文。</Sentence>
          </ParagraphSentence>
        </Paragraph>
        <Paragraph Num="2">
          <ParagraphNum>２</ParagraphNum>
          <ParagraphSentence>
            <Sentence>第二項の本文。</Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
    </MainProvision>
  </LawBody>
</Law>
"""


# ---- テストケース ----

class TestParseXml:
    def test_law_title(self):
        """法令名が正しく取得できること"""
        law_data = parse_xml(SIMPLE_XML)
        assert law_data.law_title == "建築基準法"

    def test_article_count(self):
        """条の数が正しいこと"""
        law_data = parse_xml(SIMPLE_XML)
        assert len(law_data.articles) == 2

    def test_article_num_and_title(self):
        """条番号と条見出しが正しく取得できること"""
        law_data = parse_xml(SIMPLE_XML)
        article20 = law_data.articles[1]
        assert article20.num == "20"
        assert article20.title == "第二十条"
        assert article20.caption == "（構造耐力）"

    def test_paragraph_count(self):
        """第20条の項数が正しいこと"""
        law_data = parse_xml(SIMPLE_XML)
        article20 = law_data.articles[1]
        assert len(article20.paragraphs) == 2

    def test_first_paragraph_num_empty(self):
        """第一項の ParagraphNum が空文字列であること"""
        law_data = parse_xml(SIMPLE_XML)
        article20 = law_data.articles[1]
        first_para = article20.paragraphs[0]
        assert first_para.num == ""

    def test_second_paragraph_num(self):
        """第二項の ParagraphNum が '２' であること"""
        law_data = parse_xml(SIMPLE_XML)
        article20 = law_data.articles[1]
        second_para = article20.paragraphs[1]
        assert second_para.num == "２"

    def test_item_count(self):
        """第20条第1項の号数が正しいこと"""
        law_data = parse_xml(SIMPLE_XML)
        article20 = law_data.articles[1]
        first_para = article20.paragraphs[0]
        assert len(first_para.items) == 2

    def test_item_title(self):
        """号番号が正しく取得できること"""
        law_data = parse_xml(SIMPLE_XML)
        article20 = law_data.articles[1]
        first_para = article20.paragraphs[0]
        assert first_para.items[0].title == "一"
        assert first_para.items[1].title == "二"

    def test_subitem_count(self):
        """第20条第1項第2号の下位項目数が正しいこと"""
        law_data = parse_xml(SIMPLE_XML)
        article20 = law_data.articles[1]
        first_para = article20.paragraphs[0]
        item2 = first_para.items[1]
        assert len(item2.subitems) == 2

    def test_subitem_title(self):
        """下位項目番号（イ・ロ）が正しく取得できること"""
        law_data = parse_xml(SIMPLE_XML)
        article20 = law_data.articles[1]
        first_para = article20.paragraphs[0]
        item2 = first_para.items[1]
        assert item2.subitems[0].title == "イ"
        assert item2.subitems[1].title == "ロ"

    def test_paragraph_sentence(self):
        """項本文が取得できること"""
        law_data = parse_xml(SIMPLE_XML)
        article20 = law_data.articles[1]
        first_para = article20.paragraphs[0]
        assert len(first_para.sentences) > 0
        assert "建築物は" in first_para.sentences[0]

    def test_table_ignored(self):
        """<Table>タグが含まれていてもエラーにならないこと"""
        law_data = parse_xml(XML_WITH_TABLE)
        assert len(law_data.articles) == 1
        para = law_data.articles[0].paragraphs[0]
        assert len(para.sentences) > 0

    def test_invalid_xml_raises(self):
        """不正なXMLはValueErrorを送出すること"""
        with pytest.raises(ValueError):
            parse_xml("これはXMLではありません")

    def test_first_para_empty_num(self):
        """第一項のParagraphNumが空タグの場合も空文字列として扱われること"""
        law_data = parse_xml(XML_FIRST_PARA_NO_NUM)
        article = law_data.articles[0]
        assert article.paragraphs[0].num == ""
        assert article.paragraphs[1].num == "２"


class TestFilterArticle:
    def test_filter_existing_article(self):
        """存在する条番号でフィルタリングできること"""
        law_data = parse_xml(SIMPLE_XML)
        filtered = filter_article(law_data, "20")
        assert len(filtered.articles) == 1
        assert filtered.articles[0].num == "20"

    def test_filter_preserves_law_title(self):
        """フィルタリング後も法令名が保持されること"""
        law_data = parse_xml(SIMPLE_XML)
        filtered = filter_article(law_data, "20")
        assert filtered.law_title == "建築基準法"

    def test_filter_nonexistent_article_raises(self):
        """存在しない条番号はValueErrorを送出すること"""
        law_data = parse_xml(SIMPLE_XML)
        with pytest.raises(ValueError):
            filter_article(law_data, "999")
