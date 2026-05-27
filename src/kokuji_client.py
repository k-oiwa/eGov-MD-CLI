"""
kokuji_client.py
国土交通省ウェブサイトから告示PDFのURLを特定してダウンロードするモジュール。

対応する告示検索先:
  - 国土交通省 建築基準法関係告示一覧
    https://www.mlit.go.jp/jutakukentiku/build/jutakukentiku_house_tk_000044.html
  - e-Gov 法令検索（告示）
    https://elaws.e-gov.go.jp/
"""

import re
import unicodedata
import requests
from bs4 import BeautifulSoup

# 国土交通省 建築基準法関係告示一覧ページ
MLIT_KOKUJI_URL = "https://www.mlit.go.jp/jutakukentiku/build/jutakukentiku_house_tk_000044.html"

# 国土交通省 告示検索ページ（バックアップ）
MLIT_BASE_URL = "https://www.mlit.go.jp"

# e-Gov 告示検索URL
EGOV_KOKUJI_SEARCH = "https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0100/"

# 既知の告示PDFのURLマッピング
# キー: (年号+数字, 番号) の正規化済み文字列
# 値: PDF URL
KNOWN_KOKUJI_URLS: dict[tuple[str, str], str] = {
    # 平成19年国土交通省告示第593号
    # 建築基準法施行令第三十六条の二第五号の国土交通大臣が指定する建築物を定める件
    ("平成19", "593"): "https://www.mlit.go.jp/notice/noticedata/pdf/201703/00006544.pdf",
}

# 年号の変換マッピング（和暦→西暦）
WAREKI_TO_SEIREKI = {
    "令和": 2018,
    "平成": 1988,
    "昭和": 1925,
    "大正": 1911,
    "明治": 1867,
}

# 年号の別表記マッピング
WAREKI_ALIASES = {
    "令和": ["令和", "R", "r"],
    "平成": ["平成", "H", "h"],
    "昭和": ["昭和", "S", "s"],
}


def download_kokuji_pdf(year_str: str, number_str: str, output_path: str) -> str:
    """
    告示の年と番号からPDFをダウンロードして保存する。

    Args:
        year_str: 告示の年（例: "平成19年", "平成19", "H19"）
        number_str: 告示番号（例: "593", "第593号"）
        output_path: 保存先ファイルパス

    Returns:
        保存したファイルパス

    Raises:
        ValueError: PDFが見つからない場合
        requests.RequestException: ダウンロードに失敗した場合
    """
    # 年と番号を正規化
    year_normalized = _normalize_year(year_str)
    number_normalized = _normalize_number(number_str)

    print(f"[情報] 告示を検索中: {year_normalized}年 第{number_normalized}号")

    # 複数の検索先を順番に試みる
    pdf_url = None

    # 0. 既知URLマッピングから検索
    pdf_url = _lookup_known_url(year_normalized, number_normalized)

    # 1. 国土交通省 建築基準法関係告示一覧から検索
    if not pdf_url:
        pdf_url = _search_mlit_kokuji_list(year_normalized, number_normalized)

    # 2. 見つからない場合は国土交通省サイト全体を検索
    if not pdf_url:
        pdf_url = _search_mlit_general(year_normalized, number_normalized)

    if not pdf_url:
        raise ValueError(
            f"告示PDFが見つかりませんでした: {year_str} 第{number_str}号\n"
            f"手動でPDFを取得し、pdf_parser.py を直接使用してください。"
        )

    print(f"[情報] PDF URL: {pdf_url}")
    print(f"[情報] PDFをダウンロード中...")

    # PDFをダウンロード
    response = requests.get(pdf_url, timeout=60, headers=_get_headers())
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"[情報] PDFを保存しました: {output_path}")
    return output_path


def _lookup_known_url(year: str, number: str) -> str | None:
    """
    既知URLマッピングから告示PDFのURLを検索する。

    Args:
        year: 正規化済みの年（例: "平成19"）
        number: 正規化済みの告示番号（例: "593"）

    Returns:
        PDF URL、見つからない場合はNone
    """
    url = KNOWN_KOKUJI_URLS.get((year, number))
    if url:
        print(f"[情報] 既知URLマッピングから取得: {url}")
    return url


def _search_mlit_kokuji_list(year: str, number: str) -> str | None:
    """
    国土交通省 建築基準法関係告示一覧ページからPDF URLを検索する。

    Args:
        year: 西暦年（例: "2007"）または和暦年（例: "平成19"）
        number: 告示番号（例: "593"）

    Returns:
        PDF URL、見つからない場合はNone
    """
    try:
        response = requests.get(MLIT_KOKUJI_URL, timeout=30, headers=_get_headers())
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except requests.RequestException as e:
        print(f"[警告] 国土交通省告示一覧の取得に失敗しました: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    return _find_pdf_link(soup, year, number, MLIT_BASE_URL)


def _search_mlit_general(year: str, number: str) -> str | None:
    """
    国土交通省サイトの複数ページから告示PDFを検索する。

    Args:
        year: 西暦年または和暦年
        number: 告示番号

    Returns:
        PDF URL、見つからない場合はNone
    """
    # 国土交通省の建築関連告示ページ一覧
    search_urls = [
        "https://www.mlit.go.jp/jutakukentiku/build/jutakukentiku_house_tk_000045.html",
        "https://www.mlit.go.jp/jutakukentiku/build/jutakukentiku_house_tk_000046.html",
        "https://www.mlit.go.jp/jutakukentiku/build/index.html",
    ]

    for url in search_urls:
        try:
            response = requests.get(url, timeout=30, headers=_get_headers())
            if response.status_code != 200:
                continue
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            result = _find_pdf_link(soup, year, number, MLIT_BASE_URL)
            if result:
                return result
        except requests.RequestException:
            continue

    return None


def _find_pdf_link(
    soup: BeautifulSoup, year: str, number: str, base_url: str
) -> str | None:
    """
    BeautifulSoupオブジェクトから告示番号に一致するPDFリンクを探す。

    Args:
        soup: 解析済みHTMLオブジェクト
        year: 西暦年または和暦年
        number: 告示番号
        base_url: 相対URLを絶対URLに変換するためのベースURL

    Returns:
        PDF URL、見つからない場合はNone
    """
    # 検索パターンを生成（表記揺れに対応）
    patterns = _build_search_patterns(year, number)

    for a_tag in soup.find_all("a", href=True):
        href = str(a_tag.get("href", ""))
        link_text = _normalize_text(a_tag.get_text())

        # PDFリンクかどうか確認
        is_pdf = href.lower().endswith(".pdf")

        # テキストまたはhrefに告示番号が含まれるか確認
        for pattern in patterns:
            if re.search(pattern, link_text, re.IGNORECASE) or re.search(
                pattern, _normalize_text(href), re.IGNORECASE
            ):
                if is_pdf:
                    # 絶対URLに変換
                    if href.startswith("http"):
                        return href
                    elif href.startswith("/"):
                        return f"{base_url}{href}"
                    else:
                        return f"{base_url}/{href}"

    return None


def _build_search_patterns(year: str, number: str) -> list[str]:
    """
    告示番号の検索パターンを生成する（表記揺れ対応）。

    Args:
        year: 西暦年または和暦年
        number: 告示番号

    Returns:
        正規表現パターンのリスト
    """
    patterns = []

    # 番号の数字部分を抽出
    num_digits = re.sub(r"[^\d]", "", number)

    # 年の数字部分を抽出
    year_digits = re.sub(r"[^\d]", "", year)

    # パターン1: 「第593号」「第593号」（全角・半角）
    patterns.append(rf"第\s*{num_digits}\s*号")

    # パターン2: 「593号」
    patterns.append(rf"{num_digits}\s*号")

    # パターン3: 年+番号の組み合わせ（例: 19年593号、H19_593）
    if year_digits:
        patterns.append(rf"{year_digits}[年_\-]{num_digits}")

    return patterns


def _normalize_year(year_str: str) -> str:
    """
    年の表記を正規化する（例: "平成19年" → "平成19"）。

    Args:
        year_str: 年の文字列

    Returns:
        正規化された年文字列
    """
    # 末尾の「年」を除去
    year_str = year_str.strip().rstrip("年")
    return year_str


def _normalize_number(number_str: str) -> str:
    """
    告示番号を正規化する（例: "第593号" → "593"）。

    Args:
        number_str: 告示番号の文字列

    Returns:
        数字のみの告示番号
    """
    # 「第」「号」を除去し、数字のみ抽出
    number_str = number_str.strip()
    number_str = re.sub(r"[第号\s]", "", number_str)
    # 全角数字を半角に変換
    number_str = unicodedata.normalize("NFKC", number_str)
    return number_str


def _normalize_text(text: str) -> str:
    """
    テキストを正規化する（全角→半角、スペース除去等）。

    Args:
        text: 正規化するテキスト

    Returns:
        正規化されたテキスト
    """
    # Unicode正規化（全角→半角）
    text = unicodedata.normalize("NFKC", text)
    # 連続するスペースを1つに
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _get_headers() -> dict:
    """
    HTTPリクエスト用のヘッダーを返す。
    """
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
    }
