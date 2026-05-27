"""
api_client.py
e-Gov法令APIとの通信・XML取得を担当するモジュール。
"""

import requests
from urllib.parse import quote

# e-Gov法令API ベースURL
EGOV_API_BASE = "https://elaws.e-gov.go.jp/api/1"

# 法令名 → 法令番号のマッピング（よく使う法令）
LAW_NAME_TO_NUMBER = {
    "建築基準法": "昭和二十五年法律第二百一号",
    "建築士法": "昭和二十五年法律第二百二号",
}


def get_law_xml(law_name_or_number: str) -> str:
    """
    法令名または法令番号を受け取り、e-Gov APIからXML文字列を取得して返す。

    Args:
        law_name_or_number: 法令名（例: "建築基準法"）または法令番号（例: "昭和二十五年法律第二百一号"）

    Returns:
        XML文字列

    Raises:
        ValueError: 法令が見つからない場合
        requests.HTTPError: APIリクエストが失敗した場合
    """
    # 法令名からの変換を試みる
    law_number = LAW_NAME_TO_NUMBER.get(law_name_or_number, law_name_or_number)

    # まず法令番号で直接取得を試みる
    xml_content = _fetch_by_law_number(law_number)
    if xml_content:
        return xml_content

    # 法令番号で取得できなかった場合、法令一覧から検索する
    xml_content = _search_and_fetch(law_name_or_number)
    if xml_content:
        return xml_content

    raise ValueError(f"法令が見つかりませんでした: {law_name_or_number}")


def _fetch_by_law_number(law_number: str) -> str | None:
    """
    法令番号を使ってe-Gov APIから直接XMLを取得する。

    Args:
        law_number: 法令番号

    Returns:
        XML文字列、または取得失敗時はNone
    """
    url = f"{EGOV_API_BASE}/lawdata/{quote(law_number)}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.text
        return None
    except requests.RequestException:
        return None


def _search_and_fetch(law_name: str) -> str | None:
    """
    法令一覧APIで法令名を検索し、最初にヒットした法令のXMLを取得する。

    Args:
        law_name: 法令名（部分一致）

    Returns:
        XML文字列、または取得失敗時はNone
    """
    import xml.etree.ElementTree as ET

    # 法令一覧を取得
    list_url = f"{EGOV_API_BASE}/lawlists/1"
    try:
        response = requests.get(list_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[警告] 法令一覧の取得に失敗しました: {e}")
        return None

    # XMLから法令番号を検索
    try:
        root = ET.fromstring(response.text)
        for law_info in root.iter("LawNameListInfo"):
            name_elem = law_info.find("LawName")
            number_elem = law_info.find("LawNo")
            if name_elem is not None and number_elem is not None:
                if law_name in (name_elem.text or ""):
                    return _fetch_by_law_number(number_elem.text or "")
    except ET.ParseError as e:
        print(f"[警告] 法令一覧のXML解析に失敗しました: {e}")

    return None
