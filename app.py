"""
Unit Search Streamlit app.

Loads published CSV sheets and lets you search unit combinations with filters.
Configure sheet URLs via env vars SHEET_MEMBERS_URL, SHEET_MEMBER_GENERATIONS_URL,
SHEET_UNITS_URL, SHEET_UNIT_MEMBERS_URL (optionally SHEET_MEMBER_ALIASES_URL,
SHEET_UNITS_ALIASES_URL).
"""

import os
import logging
from collections import defaultdict
from typing import Set, List, Dict, Any

import streamlit as st
import pandas as pd

from i18n import t

logger = logging.getLogger(__name__)

# Page settings
st.set_page_config(page_title="Unit Search", layout="centered")

# Required/optional sheet definitions
REQUIRED_SHEETS = ("members", "member_generations", "units", "unit_members")
OPTIONAL_SHEETS = ("member_aliases", "units_aliases")

# available languages (code -> display name)
LANGUAGES = {"en": "English", "ja": "日本語"}


def _detect_or_get_lang() -> str:
    """Determine language from query params or trigger browser detection."""
    params = st.experimental_get_query_params()
    if "lang" in params and params["lang"]:
        code = params["lang"][0]
        if code in LANGUAGES:
            return code

    # inject JS to auto-detect browser language and add `lang` query param
    js = """
    <script>
    (function(){
        try {
            const url = new URL(window.location);
            const params = url.searchParams;
            if (!params.has('lang')) {
                const nav = navigator.language || navigator.userLanguage || 'ja';
                const lang = (nav || 'ja').split('-')[0];
                params.set('lang', lang);
                url.search = params.toString();
                window.location.replace(url.toString());
            }
        } catch (e) {
            /* ignore */
        }
    })();
    </script>
    """
    st.components.v1.html(js, height=0)
    return "ja"


def jaccard(a: Set[str], b: Set[str]) -> float:
    """Calculate Jaccard index; return 0 if both empty."""
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0


def _resolve_sheet_url(key: str) -> str:
    """Resolve sheet URL from env or secrets."""
    env_key = f"SHEET_{key.upper()}_URL"
    secret_key = f"sheet_{key}_url"
    secret_val = st.secrets.get(secret_key) if hasattr(st, "secrets") else None
    return os.environ.get(env_key) or (secret_val or "")


def _validate_required_columns(df: pd.DataFrame, required: List[str], label: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"missing_columns:{label}:{','.join(missing)}")


@st.cache_data(ttl=600)
def load_tables() -> Dict[str, pd.DataFrame]:
    """Load all configured sheets (CSV)."""
    urls: Dict[str, str] = {}
    missing: List[str] = []
    for key in REQUIRED_SHEETS:
        url = _resolve_sheet_url(key)
        if url:
            urls[key] = url
        else:
            missing.append(key)
    if missing:
        raise ValueError(f"missing_sheet_url:{','.join(missing)}")

    for key in OPTIONAL_SHEETS:
        url = _resolve_sheet_url(key)
        if url:
            urls[key] = url

    tables: Dict[str, pd.DataFrame] = {}
    for name, url in urls.items():
        try:
            tables[name] = pd.read_csv(url)
        except Exception:
            logger.exception("Failed to load CSV for %s", name)
            raise
    return tables


def prepare_data(tables: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Normalize loaded tables into convenient structures."""
    _validate_required_columns(tables["members"], ["member_id", "display_name", "alias", "branch", "status"], "members")
    _validate_required_columns(tables["member_generations"], ["member_id", "generation", "is_primary"], "member_generations")
    _validate_required_columns(tables["units"], ["unit_id", "canonical_name", "note"], "units")
    _validate_required_columns(tables["unit_members"], ["unit_id", "member_id", "weight"], "unit_members")

    members_df = tables["members"].fillna("")
    gen_df = tables["member_generations"].fillna("")
    unit_df = tables["units"].fillna("")
    unit_members_df = tables["unit_members"]

    member_alias_df = tables.get("member_aliases", pd.DataFrame(columns=["member_id", "alias"]).fillna(""))
    unit_alias_df = tables.get("units_aliases", pd.DataFrame(columns=["unit_id", "alias", "alias_note"]).fillna(""))

    member_meta: Dict[str, Dict[str, Any]] = {}
    member_alias_map: Dict[str, str] = {}
    branches: Set[str] = set()
    statuses: Set[str] = set()

    def add_member_alias(alias_raw: Any, member_id: str) -> None:
        alias = str(alias_raw).strip()
        if alias:
            member_alias_map[alias.lower()] = member_id

    for _, row in members_df.iterrows():
        mid = str(row["member_id"]).strip()
        if not mid:
            continue
        alias = str(row.get("alias", "")).strip()
        branch = str(row.get("branch", "")).strip()
        status = str(row.get("status", "")).strip()
        member_meta[mid] = {
            "member_id": mid,
            "display_name": str(row.get("display_name", mid)).strip() or mid,
            "alias": alias,
            "branch": branch,
            "status": status,
            "generations": set(),
        }
        add_member_alias(alias, mid)
        if branch:
            branches.add(branch)
        if status:
            statuses.add(status)

    for _, row in member_alias_df.iterrows():
        add_member_alias(row.get("alias", ""), str(row.get("member_id", "")).strip())

    generations: Set[str] = set()
    for _, row in gen_df.iterrows():
        mid = str(row.get("member_id", "")).strip()
        gen = str(row.get("generation", "")).strip()
        if not mid or not gen or mid not in member_meta:
            continue
        member_meta[mid]["generations"].add(gen)
        generations.add(gen)

    unit_alias_map: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: {"aliases": [], "notes": []})
    for _, row in unit_alias_df.iterrows():
        uid = str(row.get("unit_id", "")).strip()
        alias = str(row.get("alias", "")).strip()
        note = str(row.get("alias_note", "")).strip()
        if not uid or not alias:
            continue
        unit_alias_map[uid]["aliases"].append(alias)
        if note:
            unit_alias_map[uid]["notes"].append(f"{alias}: {note}")

    unit_members_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for _, row in unit_members_df.iterrows():
        uid = str(row.get("unit_id", "")).strip()
        mid = str(row.get("member_id", "")).strip()
        if not uid or not mid or mid not in member_meta:
            continue
        weight_val = row.get("weight", 9999)
        try:
            weight = float(weight_val)
        except Exception:
            weight = 9999
        unit_members_map[uid].append({"member_id": mid, "weight": weight})

    units_prepared: List[Dict[str, Any]] = []
    for _, row in unit_df.iterrows():
        uid = str(row.get("unit_id", "")).strip()
        if not uid:
            continue
        members = sorted(unit_members_map.get(uid, []), key=lambda m: m["weight"])
        member_ids = [m["member_id"] for m in members]
        member_set = set(member_ids)

        branches_set = {member_meta[mid]["branch"] for mid in member_set if member_meta.get(mid, {}).get("branch")}
        statuses_set = {member_meta[mid]["status"] for mid in member_set if member_meta.get(mid, {}).get("status")}
        gen_set: Set[str] = set()
        for mid in member_set:
            gen_set.update(member_meta[mid]["generations"])

        display_members = [member_meta[mid]["display_name"] for mid in member_ids if mid in member_meta]
        member_display = ", ".join(display_members)

        aliases = unit_alias_map[uid]["aliases"]
        alias_notes = unit_alias_map[uid]["notes"]
        canonical_name = str(row.get("canonical_name", "")).strip()
        note = str(row.get("note", "")).strip()

        units_prepared.append({
            "UnitId": uid,
            "UnitName": canonical_name or (aliases[0] if aliases else uid),
            "Aliases": aliases,
            "AliasNotes": alias_notes,
            "Note": note,
            "MemberSet": member_set,
            "MemberDisplay": member_display,
            "Branches": branches_set,
            "Generations": gen_set,
            "Statuses": statuses_set,
        })

    units_df = pd.DataFrame(units_prepared)
    return {
        "units_df": units_df,
        "member_meta": member_meta,
        "member_alias_map": member_alias_map,
        "branch_options": sorted([b for b in branches if b]),
        "status_options": sorted([s for s in statuses if s]),
        "generation_options": sorted([g for g in generations if g]),
    }


def find_matches(units_df: pd.DataFrame, search_set: Set[str]) -> pd.DataFrame:
    """Calculate match scores for selected members against units."""
    results: List[Dict[str, Any]] = []
    for _, row in units_df.iterrows():
        target_set: Set[str] = row.get("MemberSet", set())
        intersection = len(search_set & target_set)
        if intersection == 0:
            continue
        score = jaccard(search_set, target_set)
        results.append({
            "UnitName": row.get("UnitName", ""),
            "UnitId": row.get("UnitId", ""),
            "Members": row.get("MemberDisplay", ""),
            "Note": row.get("Note", ""),
            "Aliases": row.get("Aliases", []),
            "AliasNotes": row.get("AliasNotes", []),
            "Branches": row.get("Branches", set()),
            "Generations": row.get("Generations", set()),
            "Statuses": row.get("Statuses", set()),
            "MatchScore": score,
            "Intersection": intersection,
        })

    if not results:
        return pd.DataFrame(columns=["UnitName", "UnitId", "Members", "Note", "MatchScore", "Aliases", "AliasNotes", "Branches", "Generations", "Statuses", "Intersection"])

    result_df = pd.DataFrame(results).sort_values(by=["MatchScore", "Intersection"], ascending=[False, False])
    return result_df


def apply_filters(df: pd.DataFrame, branches: Set[str], statuses: Set[str], generations: Set[str]) -> pd.DataFrame:
    """Filter result DataFrame by selected facets."""
    if df.empty:
        return df

    def _passes(row: pd.Series) -> bool:
        if branches and not (row.get("Branches", set()) & branches):
            return False
        if statuses and not (row.get("Statuses", set()) & statuses):
            return False
        if generations and not (row.get("Generations", set()) & generations):
            return False
        return True

    return df[df.apply(_passes, axis=1)]


def main() -> None:
    selected_lang = _detect_or_get_lang()

    options = list(LANGUAGES.keys())
    try:
        index = options.index(selected_lang)
    except ValueError:
        index = options.index("ja") if "ja" in options else 0

    chosen = st.sidebar.selectbox(
        t("ui.language", selected_lang) if selected_lang in LANGUAGES else "Language",
        options=options,
        format_func=lambda code: LANGUAGES.get(code, code),
        index=index,
    )
    if chosen != selected_lang:
        st.experimental_set_query_params(lang=chosen)
        return
    selected_lang = chosen

    st.title(t("app.title", selected_lang))
    st.markdown(t("app.desc", selected_lang))

    try:
        tables = load_tables()
        data = prepare_data(tables)
    except ValueError as verr:
        err_txt = str(verr)
        if err_txt.startswith("missing_sheet_url"):
            st.error(f"Sheet URL is missing: {err_txt}")
        elif err_txt.startswith("missing_columns"):
            st.error(t("error.missing_columns", selected_lang))
        else:
            st.error(err_txt)
        return
    except Exception as exc:
        st.error(t("error.loading", selected_lang).format(err=exc))
        return

    units_df = data["units_df"]
    member_meta = data["member_meta"]
    branch_options: List[str] = data["branch_options"]
    status_options: List[str] = data["status_options"]
    generation_options: List[str] = data["generation_options"]

    member_ids = sorted(member_meta.keys(), key=lambda m: member_meta[m]["display_name"])
    selected_members = st.multiselect(
        t("ui.select_members", selected_lang),
        options=member_ids,
        format_func=lambda mid: f"{member_meta[mid]['display_name']} ({member_meta[mid]['alias']})" if member_meta[mid].get("alias") else member_meta[mid]["display_name"],
        placeholder=t("ui.placeholder_select", selected_lang),
    )

    if not selected_members:
        st.info(t("msg.select_prompt", selected_lang))
        return

    st.sidebar.divider()
    branch_filter = set(st.sidebar.multiselect("Branch", options=branch_options, placeholder="JP / EN / ID ..."))
    status_filter = set(st.sidebar.multiselect("Status", options=status_options, placeholder="active / graduated ..."))
    generation_filter = set(st.sidebar.multiselect("Generation", options=generation_options, placeholder="1st gen / Myth ..."))

    search_set = set(selected_members)
    result_df = find_matches(units_df, search_set)
    result_df = apply_filters(result_df, branch_filter, status_filter, generation_filter)

    if result_df.empty:
        st.warning(t("msg.no_results", selected_lang))
        st.info(t("msg.hint_no_results", selected_lang))
        return

    st.success(t("msg.found_units", selected_lang).format(count=len(result_df)))

    def _set_to_label(values: Any) -> str:
        return ", ".join(sorted(values)) if values else "-"

    result_df["BranchesLabel"] = result_df["Branches"].apply(_set_to_label)
    result_df["GenerationsLabel"] = result_df["Generations"].apply(_set_to_label)

    display_df = result_df[["UnitName", "Members", "BranchesLabel", "GenerationsLabel", "Note", "MatchScore"]]
    st.dataframe(
        display_df,
        column_config={
            "UnitName": t("col.unitname", selected_lang),
            "Members": t("col.members", selected_lang),
            "Note": t("col.note", selected_lang),
            "BranchesLabel": "Branch",
            "GenerationsLabel": "Generation",
            "MatchScore": st.column_config.ProgressColumn(
                t("col.matchscore", selected_lang), format="%.2f", min_value=0, max_value=1
            ),
        },
        hide_index=True,
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
