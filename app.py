"""
Unit Search Streamlit アプリ

このモジュールは Google スプレッドシート（CSV 出力）からユニット情報を読み込み、
選択したメンバーに対してジャカード係数で類似度の高いユニットを表示します。

使い方:
  $ streamlit run app.py

注意: `SHEET_URL` は公開された CSV 出力の URL を指定してください（公開情報のため埋め込み可）。
"""

from typing import Optional, Set, List, Dict
import logging

import streamlit as st
import pandas as pd

from .i18n import t

logger = logging.getLogger(__name__)

# ページ設定
st.set_page_config(page_title="Unit Search", layout="centered")

# 公開スプレッドシートの CSV 出力 URL
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vStATxaPd8g7Vc9b69UWULyRyvbx4Qqv74MEuNZ4kfnjK6lLNnUosNiPRrSn6R7uawlz3UdD1gRsFaz/pub?output=csv"
)

# available languages (code -> display name)
LANGUAGES = {"en": "English", "ja": "日本語"}


def parse_members(members_raw: str) -> Set[str]:
    """メンバー列の文字列をパースして set を返す。

    - 区切りはカンマ `,` または全角読点 `、` を許可
    - 空の要素は除外
    """
    if members_raw is None:
        return set()
    # 全角読点を半角カンマに統一して分割
    parts = str(members_raw).replace("、", ",").split(",")
    return {p.strip() for p in parts if p.strip()}


def jaccard(a: Set[str], b: Set[str]) -> float:
    """ジャカード係数を計算する。両集合が空なら 0 を返す。"""
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0


@st.cache_data(ttl=600)
def load_data(url: str = SHEET_URL) -> Optional[pd.DataFrame]:
    """CSV を読み込んで `MemberSet` カラムを追加した DataFrame を返す。

    読み込みに失敗した場合は `None` を返す。
    """
    try:
        df = pd.read_csv(url)
    except Exception as exc:  # pragma: no cover - UI-level error handling
        logger.exception("Failed to load CSV from URL")
        # error message will be rendered by caller with localized string
        raise

    # 安全のため必要なカラムがあるか確認
    if 'Members' not in df.columns or 'UnitName' not in df.columns:
        raise ValueError("missing_columns")

    df = df.copy()
    df['MemberSet'] = df['Members'].apply(parse_members)
    return df


def find_matches(df: pd.DataFrame, search_set: Set[str]) -> pd.DataFrame:
    """検索対象の集合に対して一致候補を返す DataFrame。

    戻り値のカラム: `UnitName`, `Members`, `MatchScore`, `Intersection`
    """
    results: List[Dict] = []

    for _, row in df.iterrows():
        target_set: Set[str] = row['MemberSet']
        intersection = len(search_set & target_set)
        if intersection == 0:
            continue
        score = jaccard(search_set, target_set)
        results.append({
            'UnitName': row['UnitName'],
            'Members': row['Members'],
            'MatchScore': score,
            'Intersection': intersection,
        })

    if not results:
        return pd.DataFrame(columns=['UnitName', 'Members', 'MatchScore', 'Intersection'])

    result_df = pd.DataFrame(results).sort_values(
        by=['MatchScore', 'Intersection'], ascending=[False, False]
    )
    return result_df


def main() -> None:
    """Streamlit の UI を構築して検索を実行するメイン関数。"""
    # language selector in the sidebar
    selected_lang = st.sidebar.selectbox(
        "Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda code: LANGUAGES.get(code, code),
        index=0,
    )

    st.title(t("app.title", selected_lang))
    st.markdown(t("app.desc", selected_lang))

    try:
        df = load_data()
    except ValueError as verr:
        st.error(t("error.missing_columns", selected_lang))
        return
    except Exception as exc:  # pragma: no cover - top-level loading failures
        st.error(t("error.loading", selected_lang).format(err=exc))
        return

    # 全メンバー一覧を作る（空集合がある場合は無視）
    try:
        all_members = sorted(list(set().union(*df['MemberSet'])))
    except Exception:
        all_members = []

    selected_members = st.multiselect(
        t("ui.select_members", selected_lang),
        options=all_members,
        placeholder=t("ui.placeholder_select", selected_lang),
    )

    if not selected_members:
        st.info(t("msg.select_prompt", selected_lang))
        return

    search_set = set(selected_members)
    result_df = find_matches(df, search_set)

    if result_df.empty:
        st.warning(t("msg.no_results", selected_lang))
        st.info(t("msg.hint_no_results", selected_lang))
        return

    st.success(t("msg.found_units", selected_lang).format(count=len(result_df)))
    st.dataframe(
        result_df[["UnitName", "Members", "MatchScore"]],
        column_config={
            "UnitName": t("col.unitname", selected_lang),
            "Members": t("col.members", selected_lang),
            "MatchScore": st.column_config.ProgressColumn(
                t("col.matchscore", selected_lang), format="%.2f", min_value=0, max_value=1
            ),
        },
        hide_index=True,
        use_container_width=True,
    )


if __name__ == '__main__':
    main()