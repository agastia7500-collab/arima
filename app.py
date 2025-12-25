"""
🏇 有馬記念予想アプリ 2025
GitHub × Streamlit で動作する競馬予想システム
"""

import streamlit as st
import pandas as pd
from openai import OpenAI
import os
import html
import time
from typing import Any, Dict, List
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

# ============================================
# ページ設定
# ============================================
st.set_page_config(
    page_title="有馬記念予想 2025",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================
# セッション状態（タブ切替でも結果を保持）
# ============================================
if "comp_results" not in st.session_state:
    st.session_state["comp_results"] = {"step1": None, "step2": None, "step3": None}
if "eval_results" not in st.session_state:
    st.session_state["eval_results"] = {}
if "sign_results" not in st.session_state:
    st.session_state["sign_results"] = {"events": None, "numbers": None, "bet": None}
if "search_results" not in st.session_state:
    st.session_state["search_results"] = None
if "search_date_jst" not in st.session_state:
    st.session_state["search_date_jst"] = None
if "search_error" not in st.session_state:
    st.session_state["search_error"] = None

# ============================================
# 表示ヘルパー（白文字問題の根本対策）
# - LLM出力をMarkdownとして解釈させず、HTMLエスケープして箱の中に固定
# ============================================
def text_to_safe_html(text: str) -> str:
    if text is None:
        return ""
    s = html.escape(str(text))
    s = s.replace("\n", "<br>")
    s = s.replace("<br>- ", "<br>• ")
    if s.startswith("- "):
        s = "• " + s[2:]
    return s


def render_box(title: str, body_text: str, box_class: str = "result-box") -> str:
    body = text_to_safe_html(body_text)
    return f"""
    <div class="{box_class}">
      <div class="box-title">{html.escape(title)}</div>
      <div class="box-body">{body}</div>
    </div>
    """


def render_sidebar_search(sb_debug, sb_body):
    sb_debug.caption(f"date={st.session_state.get('search_date_jst')}")
    sb_debug.caption(f"has_results={bool(st.session_state.get('search_results'))}")
    sb_debug.caption(f"error={st.session_state.get('search_error')}")

    if st.session_state.get("search_results"):
        sb_body.markdown(
            render_box("Web検索結果", st.session_state["search_results"], "analysis-box"),
            unsafe_allow_html=True,
        )
    else:
        sb_body.info("まだWeb検索は実行されていません")


# ============================================
# カスタムCSS
# ============================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');

    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        font-family: 'Noto Sans JP', sans-serif;
    }

    /* 基本テキストは白 */
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* タイトル */
    .main-title {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #ffd700, #ff8c00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #e0e0e0 !important;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: 0.2em;
    }

    /* 機能説明カード */
    .feature-card {
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 215, 0, 0.3);
        margin: 1rem 0;
    }
    .feature-card h3 { color: #ffd700 !important; }
    .feature-card p, .feature-card li { color: #e0e0e0 !important; }

    /* 結果ボックス：黒文字を100%保証 */
    .result-box {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.2rem 1.3rem;
        margin: 0.6rem 0;
        border-left: 5px solid #ffd700;
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        color: #111111 !important;
    }
    .analysis-box {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        min-height: 280px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.20);
        color: #111111 !important;
    }
    .box-title{
        font-weight: 800;
        font-size: 1.05rem;
        margin-bottom: 0.6rem;
        color: #111111 !important;
    }
    .box-body{
        font-size: 0.98rem;
        line-height: 1.7;
        color: #111111 !important;
        white-space: normal;
        word-break: break-word;
    }

    .box-horse { border: 3px solid #e74c3c; }
    .box-jockey { border: 3px solid #3498db; }
    .box-course { border: 3px solid #27ae60; }
    .box-total { border: 3px solid #f39c12; background: #fffef5; }
    .box-events { border: 3px solid #9b59b6; }
    .box-numbers { border: 3px solid #e67e22; }
    .box-buy { border: 3px solid #c0392b; background: #fff8f8; }

    /* ラベル */
    .label {
        font-size: 1.05rem;
        font-weight: 800;
        padding: 0.45rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
        text-align: center;
        color: #ffffff !important;
        display: inline-block;
        width: 100%;
    }
    .label-horse { background: #e74c3c; }
    .label-jockey { background: #3498db; }
    .label-course { background: #27ae60; }
    .label-total { background: #f39c12; }
    .label-step1 { background: #2c3e50; }
    .label-step2 { background: #34495e; }
    .label-step3 { background: #7f8c8d; }
    .label-events { background: #9b59b6; }
    .label-numbers { background: #e67e22; }
    .label-buy { background: #c0392b; }

    /* ボタン */
    .stButton > button {
        background: linear-gradient(135deg, #ffd700, #ff8c00) !important;
        color: #1a1a2e !important;
        font-weight: 800;
        font-size: 1.1rem;
        padding: 0.7rem 2rem;
        border-radius: 50px;
        border: none;
    }
    .stButton > button:hover {
        transform: scale(1.03);
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.35);
    }

    /* タブ */
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.15);
        color: #ffffff !important;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ffd700, #ff8c00) !important;
        color: #1a1a2e !important;
    }

    /* サイドバー */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e, #0f3460);
    }
    section[data-testid="stSidebar"] .stMarkdown { color: #ffffff !important; }

    /* Selectbox 文字を黒 */
    div[data-baseweb="select"] * { color: #000000 !important; }

    /* info/success/warning の文字を白（暗い背景で見えるように） */
    div[data-testid="stAlert"] * { color: #ffffff !important; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
/* selectbox のラベル文字を白くする */
label[data-testid="stWidgetLabel"] {
    color: #ffffff !important;
    font-weight: 700;
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================
# OpenAI クライアント
# ============================================
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))
    if not api_key:
        st.error("⚠️ OpenAI API キーが設定されていません")
        return None
    return OpenAI(api_key=api_key)

# ============================================
# データ読み込み
# ============================================
@st.cache_data
def load_race_data(uploaded_file=None):
    try:
        if uploaded_file is not None:
            xlsx = pd.ExcelFile(uploaded_file)
        else:
            xlsx = pd.ExcelFile("arima_data.xlsx")
        data = {}
        for sheet in xlsx.sheet_names:
            data[sheet] = pd.read_excel(xlsx, sheet_name=sheet)
        return data
    except Exception:
        return None


def format_data_for_prompt(data):
    if data is None:
        return "データなし"
    formatted = ""
    sheets = ["年齢", "枠順", "騎手", "血統", "前走クラス", "前走レース別", "馬体重増減"]
    titles = [
        "年齢別期待値",
        "枠順別期待値",
        "騎手別期待値（中山2500m）",
        "血統（種牡馬）別期待値",
        "前走クラス別期待値",
        "前走レース別期待値",
        "馬体重増減別期待値",
    ]
    for sheet, title in zip(sheets, titles):
        if sheet in data:
            formatted += f"\n{data[sheet].to_string(index=False)}\n\n"
    return formatted

# ============================================
# 2025年有馬記念 出走予定馬データ（枠順未確定）
# ============================================
HORSE_LIST_2025 = {
    1: {"枠番": 0, "馬番": 0, "馬名": "レガレイラ", "性齢": "牝4歳", "騎手": "C.ルメール", "血統": "スワーヴリチャード", "前走": "エリザベス女王杯1着"},
    2: {"枠番": 0, "馬番": 0, "馬名": "ミュージアムマイル", "性齢": "牡3歳", "騎手": "C.デムーロ", "血統": "リオンディーズ", "前走": "天皇賞秋2着"},
    3: {"枠番": 0, "馬番": 0, "馬名": "ダノンデサイル", "性齢": "牡4歳", "騎手": "戸崎圭太", "血統": "エピファネイア", "前走": "JC3着"},
    4: {"枠番": 0, "馬番": 0, "馬名": "メイショウタバル", "性齢": "牡4歳", "騎手": "武豊", "血統": "ゴールドシップ", "前走": "天皇賞秋6着"},
    5: {"枠番": 0, "馬番": 0, "馬名": "ビザンチンドリーム", "性齢": "牡4歳", "騎手": "A.プーシャン", "血統": "エピファネイア", "前走": "凱旋門賞5着"},
    6: {"枠番": 0, "馬番": 0, "馬名": "ジャスティンパレス", "性齢": "牡6歳", "騎手": "団野大成", "血統": "ディープインパクト", "前走": "JC5着"},
    7: {"枠番": 0, "馬番": 0, "馬名": "シンエンペラー", "性齢": "牡4歳", "騎手": "坂井瑠星", "血統": "Siyouni", "前走": "JC8着"},
    8: {"枠番": 0, "馬番": 0, "馬名": "タスティエーラ", "性齢": "牡4歳", "騎手": "松山弘平", "血統": "サトノクラウン", "前走": "JC7着"},
    9: {"枠番": 0, "馬番": 0, "馬名": "コスモキュランダ", "性齢": "牡3歳", "騎手": "丹内祐次", "血統": "アルアイン", "前走": "JC9着"},
    10: {"枠番": 0, "馬番": 0, "馬名": "アドマイヤテラ", "性齢": "牡3歳", "騎手": "川田将雅", "血統": "スワーヴリチャード", "前走": "菊花賞3着"},
    11: {"枠番": 0, "馬番": 0, "馬名": "サンライズアース", "性齢": "牡3歳", "騎手": "池添謙一", "血統": "レイデオロ", "前走": "JC15着"},
    12: {"枠番": 0, "馬番": 0, "馬名": "エルトンバローズ", "性齢": "牡4歳", "騎手": "西村淳也", "血統": "ディープブリランテ", "前走": "天皇賞秋9着"},
    13: {"枠番": 0, "馬番": 0, "馬名": "ミステリーウェイ", "性齢": "牡5歳", "騎手": "松本大輝", "血統": "ハーツクライ", "前走": "ARC1着"},
    14: {"枠番": 0, "馬番": 0, "馬名": "サンライズジパング", "性齢": "牡3歳", "騎手": "未定", "血統": "キタサンブラック", "前走": "チャンピオンズC6着"},
    15: {"枠番": 0, "馬番": 0, "馬名": "ヘデントール", "性齢": "牡4歳", "騎手": "未定", "血統": "ハービンジャー", "前走": "天皇賞秋10着"},
    16: {"枠番": 0, "馬番": 0, "馬名": "シュヴァリエローズ", "性齢": "牡4歳", "騎手": "未定", "血統": "キズナ", "前走": "宝塚記念4着"},
}

HORSE_INFO_STR_2025 = """【2025年有馬記念 出走予定馬】※枠順・馬番未確定
枠0・馬0｜レガレイラ（牝4歳・C.ルメール・スワーヴリチャード産駒・前走エリザベス女王杯1着）- ファン投票1位・連覇狙い
枠0・馬0｜ミュージアムマイル（牡3歳・C.デムーロ・リオンディーズ産駒・前走天皇賞秋2着）- 皐月賞馬
枠0・馬0｜ダノンデサイル（牡4歳・戸崎圭太・エピファネイア産駒・前走JC3着）- ダービー馬・昨年3着
枠0・馬0｜メイショウタバル（牡4歳・武豊・ゴールドシップ産駒・前走天皇賞秋6着）- 宝塚記念馬・春秋GP制覇狙い
枠0・馬0｜ビザンチンドリーム（牡4歳・A.プーシャン・エピファネイア産駒・前走凱旋門賞5着）- 海外帰り
枠0・馬0｜ジャスティンパレス（牡6歳・団野大成・ディープインパクト産駒・前走JC5着）- 天皇賞春馬・ラストラン
枠0・馬0｜シンエンペラー（牡4歳・坂井瑠星・Siyouni産駒・前走JC8着）- 皐月賞2着
枠0・馬0｜タスティエーラ（牡4歳・松山弘平・サトノクラウン産駒・前走JC7着）- 昨年ダービー馬
枠0・馬0｜コスモキュランダ（牡3歳・丹内祐次・アルアイン産駒・前走JC9着）- 皐月賞2着
枠0・馬0｜アドマイヤテラ（牡3歳・川田将雅・スワーヴリチャード産駒・前走菊花賞3着）
枠0・馬0｜サンライズアース（牡3歳・池添謙一・レイデオロ産駒・前走JC15着）
枠0・馬0｜エルトンバローズ（牡4歳・西村淳也・ディープブリランテ産駒・前走天皇賞秋9着）
枠0・馬0｜ミステリーウェイ（牡5歳・松本大輝・ハーツクライ産駒・前走ARC1着）- アルゼンチン共和国杯勝ち
枠0・馬0｜サンライズジパング（牡3歳・未定・キタサンブラック産駒・前走チャンピオンズC6着）
枠0・馬0｜ヘデントール（牡4歳・未定・ハービンジャー産駒・前走天皇賞秋10着）
枠0・馬0｜シュヴァリエローズ（牡4歳・未定・キズナ産駒・前走宝塚記念4着）
"""

EVENTS_2025_STR = """【2025年の主な出来事】
■ 国家プロジェクト・社会（回帰・周期）
- 大阪・関西万博（EXPO 2025）
   - 内容: 1970年の大阪万博から55年ぶり、2005年愛知から20年ぶりの開催
   - 関連数字: 55 (大阪開催55年ぶり), 1970 (前回大阪), 4 (4月開幕), 10（10月閉幕）, 13(開幕日/閉幕日)

- 新紙幣 発行から1年
   - 内容: 2024年7月の発行から1年が経過し定着
   - 関連数字: 1 (1周年), 24 (2024年), 7 (7月)

■ スポーツ・イベント（回数・記録）
- 第101回 箱根駅伝
   - 内容: 101回大会
   - 関連数字: 101 (第101回), 2 (1月2日), 3 (1月3日)

- 世界陸上競技選手権大会（東京大会）
   - 内容: 東京で34年ぶり（1991年以来）の開催
   - 関連数字: 34 (34年ぶり), 91 (前回1991年), 20 (第20回大会)

- ドジャース大谷翔平 メジャー8年目
   - 内容: 2018年のエンゼルス入団から数えて8年目のシーズン
   - 関連数字: 8 (8年目), 17 (背番号), 18 (2018年デビュー)

■ ゲーム・テクノロジー（間隔・進化）
- Nintendo Switch 後継機（スイッチ2）の話題
   - 内容: 2017年のSwitch発売から8年ぶりに投入される次世代ハード
   - 関連数字: 8 (8年ぶりの新型機), 2 (2世代目), 17 (前作2017年)

- スーパーマリオブラザーズ 40周年
   - 内容: 1985年のファミコン版発売から40年
   - 関連数字: 40 (発売40周年), 85 (1985年), 13 (9月13日発売)

- iPhone 17 シリーズ発売
   - 内容: 毎年恒例の新型iPhone発売
   - 関連数字: 17 (シリーズ番号), 9 (例年の9月発売)

■ エンタメ・施設（新作・開業）
- 映画「ミッション：インポッシブル」第8作公開
   - 内容: シリーズ第8作目にして最終章とされる作品
   - 関連数字: 8 (第8作), 23 (2025年5月23日公開予定)

- 映画「バック・トゥ・ザ・フューチャー」公開40周年
   - 内容: 1985年公開の名作から40年
   - 関連数字: 40 (公開40周年), 85 (1985年)

- NHK連続テレビ小説「あんぱん」
   - 内容: 第112作目の朝ドラ
   - 関連数字: 112 (第112作), 3 (アンパンマンの頬や服の色)

- NHK大河ドラマ「べらぼう」
   - 内容: 第64作目の大河ドラマ
   - 関連数字: 64 (第64作), 1 (1月放送開始)
"""

search_query = """
あなたは第70回有馬記念2025の予想に資する情報を調査する専門家です。
以下の調査対象について、WEB検索を行い、事実ベースで整理してください。
必ず整理した内容を出力してください。

【調査対象】
1. 有馬記念の出走馬一覧・枠順・騎手・斤量
2. 各馬の直近レース内容（最低1走）
　- 距離 / 馬場 / 通過順 / 上がり / 着差
3. 当日の馬体重増減・馬場状態・天候
4. 逃げ・先行馬の想定（ペース判断用）

【出力要件】
- JRA/主催者、公式出走表・公式結果、信頼できる出走データベース（事実情報）を最優先
- 推測・予想・主観は含まない
- 予想記事の印、回顧記事の主観評価、SNSの推測は使用禁止
- 調査対象の項目ごとに箇条書きの文章で20個以上出力する(各項目5個以上)
- 調査結果において、予想に影響しそうな内容は可能な限り全て具体的に記述する
- 出典の出力は不要
- 上記調査にかかわる内容以外の出力は不要(はい等の応答文やネクストアクションの提案等は不要)
"""

# ============================================
# GPT-5-mini 共通コール（Responses API）
# - temperature等は使わない（GPT-5系でエラー要因になりやすい）
# - max_output_tokens は必要に応じて指定
# ============================================
def _call_gpt5mini_text(client: OpenAI, system_prompt: str, user_prompt: str, max_output_tokens: int) -> str:
    r = client.responses.create(
        model="gpt-5-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_output_tokens=max_output_tokens,
    )
    return (r.output_text or "").strip()

# ============================================
# Web検索機能（Responses API + web_search）
# - gpt-5-mini で web_search を実行
# - output_text が空でも sources を拾って最低限返す（RuntimeError対策）
# ============================================
def gpt_web_search(client, prompt: str) -> str: 
    response = client.responses.create( 
        model="gpt-4.1", 
        tools=[{"type": "web_search"}], 
        input=prompt, # ← search_query をそのまま入れる 
        max_output_tokens=3000, # 出力量制御 
    ) 
    return response.output_text

# from typing import List, Dict, Any, Optional

# def _get(obj: Any, key: str, default=None):
#     """dict/obj 両対応でプロパティ取得"""
#     if obj is None:
#         return default
#     if isinstance(obj, dict):
#         return obj.get(key, default)
#     return getattr(obj, key, default)

# def _extract_sources_from_response(r: Any) -> List[Any]:
#     """
#     Responses API の web_search_call から sources を抽出。
#     SDKの返却が dict / typed object のどちらでも動くようにする。
#     """
#     out = _get(r, "output", []) or []
#     for item in out:
#         if _get(item, "type", None) == "web_search_call":
#             action = _get(item, "action", None)
#             sources = _get(action, "sources", None)
#             if sources:
#                 return list(sources)
#     return []

# def gpt_web_search(client: OpenAI, prompt: str) -> str:
#     r = client.responses.create(
#         model="gpt-5-mini",
#         tools=[{"type": "web_search"}],
#         tool_choice="auto",
#         include=["web_search_call.action.sources"],
#         input=prompt,
#         max_output_tokens=3000,
#     )

#     text = (getattr(r, "output_text", "") or "").strip()
#     if text:
#         return text

#     # 文章が空でも、sources/snippet を「検索結果テキスト」として返す
#     sources = []
#     for item in getattr(r, "output", []) or []:
#         if getattr(item, "type", None) == "web_search_call":
#             action = getattr(item, "action", None)
#             sources = list(getattr(action, "sources", None) or [])
#             break

#     if sources:
#         lines = ["（検索本文が空だったため、検索結果スニペットを返します）"]
#         for s in sources[:20]:
#             title = (getattr(s, "title", "") or "").strip()
#             url = (getattr(s, "url", "") or "").strip()
#             snippet = (getattr(s, "snippet", "") or "").strip()
#             if title or snippet or url:
#                 lines.append(f"- {title}\n  {url}\n  {snippet}".strip())
#         return "\n".join(lines).strip()

#     return "（WEB検索結果なし）"

def ensure_daily_gpt_search(client: OpenAI, query: str) -> str:
    if client is None:
        st.session_state["search_error"] = "client is None"
        return None

    today = datetime.now(JST).date().isoformat()

    # すでに今日の分があれば再利用
    if st.session_state.get("search_date_jst") == today and st.session_state.get("search_results"):
        return st.session_state["search_results"]

    try:
        text = gpt_web_search(client, query)  # str想定
        if not text or not str(text).strip():
            raise RuntimeError("web_search returned empty text")
        st.session_state["search_results"] = str(text)
        st.session_state["search_date_jst"] = today
        st.session_state["search_error"] = None
        return st.session_state["search_results"]
    except Exception as e:
        st.session_state["search_error"] = repr(e)
        st.session_state["search_results"] = None
        st.session_state["search_date_jst"] = None
        return None

# ============================================
# 機能①: 総合予想（3段階）
# ============================================
def analyze_data_summary(client, data):
    search_results = st.session_state.get("search_results") or "（WEB検索結果なし）"
    system_prompt = f"""
## 指示
あなたは有馬記念（中山芝2500m）を専門とする競馬予想AIエージェントです。
過去の有馬記念データとWEB一次情報をもとに傾向を分析してください。
出力に「*」や「#」を含まないでください。

## 使用すべき情報源
- JRA/主催者、公式出走表・公式結果、信頼できる出走データベース（事実情報）
- 参照データ

## 参照データ
ファイル名：有馬記念過去データ
　- 年齢：年齢×着順割合
　- 枠順：枠番×着順割合
　- 騎手：騎手別着順割合
　- 血統：種牡馬別の有馬記念着順割合
　- 前走レース別：前走レース別の着順割合
　- 馬体重増減：増減幅区分×着順割合

## 傾向分析フロー
### STEP1 レースの見立て整理
逃げ・先行馬の頭数と脚質分布から、
レース全体のペースを以下3段階で判定する。
ここで構築した内容は、会話中にブレさせないようにすること。

- S（スロー）
- M（ミドル）
- H（ハイ）
※ペース判定の根拠を1行で示す。

### STEP2 過去データ傾向
以下を個別評価し傾向を出力する  
　・年齢  
　・枠順  
　・前走レース  
　・血統  
　・騎手  
　・馬体重
　・コース形態（小回り・コーナー数・坂）
・求められる能力（スタミナ・器用さ・持続力）
・不利になりやすいタイプ

## 出力形式
【レース全体のペース傾向】
(内容を簡潔に記載)
【年齢】
(○○歳の馬が好走しやすい傾向といった内容を簡潔に記載)
【枠順】  
(～～という傾向といった形式で内容を簡潔に記載)
【前走レース】
(～～という傾向といった形式で内容を簡潔に記載)
【血統】
(～～という傾向といった形式で内容を簡潔に記載)
【騎手】
(～～という傾向といった形式で内容を簡潔に記載)
【馬体重】
(～～という傾向といった形式で内容を簡潔に記載)
【コース形態】
(内容を簡潔に記載)
【求められる能力】
(内容を簡潔に記載)
【不利になりやすいタイプ】
(内容を簡潔に記載)

## 出走馬情報
{HORSE_INFO_STR_2025}

## WEB検索結果
{search_results}
"""
    return _call_gpt5mini_text(
        client=client,
        system_prompt=system_prompt,
        user_prompt=f"データ分析:\n{format_data_for_prompt(data)}",
        max_output_tokens=8000,
    )


def predict_horses(client, data, analysis):
    search_results = st.session_state.get("search_results") or "（WEB検索結果なし）"
    system_prompt = f"""
## 指示
あなたは有馬記念（中山芝2500m）を専門とする競馬予想AIエージェントです。
コース傾向・過去の有馬記念データ・当日のWEB一次情報・展開分析を統合して、競馬初心者でも「なぜこの馬が本命／対抗／穴なのか」を納得しながら理解できる形で推奨馬を提示してください。
出力に「*」や「#」を含まないでください。
「出力形式」に従って出力してください。STEPの出力は不要です。

### 使用すべき情報源
- JRA/主催者、公式出走表・公式結果、信頼できる出走データベース（事実情報）
- 有馬記念のコース傾向

### 避けるべき情報/予想方法
- 予想記事の印、回顧記事の主観評価、SNSの推測、オッズだけでの結論

## 分析フロー
### STEP1 出走馬評価
全出走馬を以下6指標で **0〜5点** で採点し、合計点を算出する。

A. コース適性  
　中山実績・小回り・坂への対応力

B. 距離適性  
　2200〜2600mでの内容（着順よりレース内容重視）

C. 展開適性  
　想定ペース × 脚質の相性

D. 近走内容  
　位置取り・上がり・持続力・不利の有無を評価

E. 過去データ適合（統合評価）  
　以下を内部で個別評価し、統合して点数化する  
　・年齢  
　・枠順  
　・前走レース  
　・血統  
　・騎手  
※出力時は「どの要素が一致したか」を必ず明示する

F. 当日要素  
　馬体重増減・パドック・馬場状態  
※不明な項目は0点扱い

### STEP2  リスク評価
合計点に加え、以下のようなリスク要因を考慮して最終評価を確定する。
- 距離不安
- 折り合い不安
- 当日状態の悪化
- 展開不利

## 印付けルール（重要）
- 印は「点数順」ではなく、総合評価＋リスク＋他馬との比較決定する
- 各印には必ず以下を含めること
  1. なぜこの印なのか（決定打）
  2. 他の有力馬と比べて優れている点
  3. 不安点がある場合は正直に明示

## 出力形式
◎本命
（最上位評価とした決定的理由や舞台・展開・当日条件との噛み合いを記載）
（不安点があれば記載）
○対抗（理由）
（本命より評価を下げた理由や逆転があるとすればどの条件かを記載）
▲単穴（理由）
（能力は足りるが評価を抑えた理由や好走する場合の具体的シナリオを記載）
☆穴馬（理由）
（点数が低くても評価対象とした理由を記載）
（好走条件が限定される場合は必ず明記）
✕危険馬（理由）
（評価を下げた理由や過信してはいけないポイントを記載）

## 禁止事項
・人気順のみでの評価

## 出走馬情報
{HORSE_INFO_STR_2025}

## WEB検索結果
{search_results}
"""
    return _call_gpt5mini_text(
        client=client,
        system_prompt=system_prompt,
        user_prompt=f"【分析結果】\n{analysis}",
        max_output_tokens=8000,
    )


def suggest_betting(client, prediction):
    search_results = st.session_state.get("search_results") or "（WEB検索結果なし）"
    system_prompt = f"""
## 指示
あなたは有馬記念（中山芝2500m）を専門とする競馬予想AIエージェントです。
推奨馬の印をもとに、馬券の買い目を【リスク別】に整理して提示してください。
出力に「*」や「#」を含まないでください。

### 使用してよい情報源
- 推奨馬印

## 出力ルール
- 「買い目の提案」は必ず【タイプ別】に分類して出力すること
- 分類名は以下を基本とする
  - 安全型（的中重視・堅実）
  - バランス型（期待値重視）
  - 攻め型（高配当狙い）
- タイプごとに、なぜその構成にしたかを一言で補足すること

## 出力形式
◆ 安全型（的中重視）
（買い方（馬連・三連複等どの買い方でもOK）および狙いの考え方を記載）

◆ バランス型（期待値重視）
（買い方（馬連・三連複等どの買い方でもOK）および狙いの考え方を記載）

◆ 攻め型／冒険型（高配当狙い）
（買い方（馬連・三連複等どの買い方でもOK）および狙いの考え方を記載）

【資金配分の目安】
（上記のパターンそれぞれの資金配分を記載）

## 出走馬情報
{HORSE_INFO_STR_2025}

## WEB検索結果
{search_results}
"""
    return _call_gpt5mini_text(
        client=client,
        system_prompt=system_prompt,
        user_prompt=f"予想:\n{prediction}",
        max_output_tokens=8000,
    )

# ============================================
# 機能②: 単体評価（4段階）
# ============================================
def analyze_horse(client, horse_info, data):
    search_results = st.session_state.get("search_results") or "（WEB検索結果なし）"
    system_prompt = f"""
## 指示
あなたは有馬記念（中山芝2500m）を専門とする競馬予想AIエージェントです。
ユーザーが指定した「出走馬1頭」について、馬単体の能力を評価してください。
出力に「*」や「#」を含まないでください。

## 評価項目
・ 血統評価  
　- 種牡馬の有馬記念着順割合を参照
　- 好走傾向の強弱を評価
　- 有馬記念向き血統かどうかを判断

・ 年齢評価  
　- 年齢別の有馬記念着順割合を参照
　- 好走ゾーン・不振ゾーンとの一致度を評価

・ 前走結果評価
　- 前走レース別の有馬記念着順割合を参照
　- 有馬記念に繋がりやすいローテ・成績かを評価

## WEB検索結果
{search_results}

## ★評価の内部目安（非出力）
★★★★★：有馬記念の負荷条件でも能力低下がほぼ見られない
★★★★☆：高負荷下でも一定水準を維持できる
★★★☆☆：能力はあるが、消耗や展開でブレが出る
★★☆☆☆：地力は高いが、有馬条件では割引が必要
★☆☆☆☆：能力評価以前に条件的に厳しい 
※この基準は内部判断用であり、説明文には直接書かないこと。

## 出力形式
【評価】
(「★☆☆☆☆」の形式で記載）
【コメント】
(2-3文で記載)
・血統評価：(1文で記載)
・年齢評価：(1文で記載)
・前走結果評価：(1文で記載)
"""
    user_prompt = (
        f"馬名:{horse_info['馬名']} "
        f"枠番:{horse_info['枠番']} 馬番:{horse_info['馬番']} "
        f"性齢:{horse_info['性齢']} 血統:{horse_info['血統']} 前走:{horse_info['前走']}\n"
        f"{format_data_for_prompt(data)}"
    )
    return _call_gpt5mini_text(client, system_prompt, user_prompt, max_output_tokens=8000)


def analyze_jockey(client, horse_info, data):
    search_results = st.session_state.get("search_results") or "（WEB検索結果なし）"
    system_prompt = f"""
## 指示
あなたは有馬記念（中山芝2500m）を専門とする競馬予想AIエージェントです。
ユーザーが指定した「出走馬1頭」について、騎乗する騎手単体の評価を行ってください。
出力に「*」や「#」を含まないでください。
※本評価は、実施済の「馬単体評価」後続の「コース適性評価」と
　統合される前提のため、評価基準・結論をブレさせないこと。

## 評価項目
騎手別の有馬記念着順割合を参照し、以下3区分で内部判定する 
・好走傾向  
・平均的  
・不振傾向  

## WEB検索結果
{search_results}

## ★評価の内部目安（非出力）
★★★★★：好走傾向が非常に強く、凡走が少ない  
★★★★☆：好走傾向があり、安定感のある水準  
★★★☆☆：平均的水準  
★★☆☆☆：好走例はあるが、安定感に欠ける  
★☆☆☆☆：明確に不振傾向  
※この基準は内部判断用であり、説明文には直接書かないこと。

## 出力形式
【評価】
(「★☆☆☆☆」の形式で記載）
【コメント】
(2-3文で記載)
"""
    user_prompt = (
        f"騎手:{horse_info['騎手']} "
        f"騎乗馬:{horse_info['馬名']} "
        f"枠番:{horse_info['枠番']} 馬番:{horse_info['馬番']}\n"
        f"{format_data_for_prompt(data)}"
    )
    return _call_gpt5mini_text(client, system_prompt, user_prompt, max_output_tokens=8000)


def analyze_course(client, horse_info, data):
    search_results = st.session_state.get("search_results") or "（WEB検索結果なし）"
    system_prompt = f"""
## 指示
あなたは有馬記念（中山芝2500m）を専門とする競馬予想AIエージェントです。
ユーザーが指定した「出走馬1頭」について、有馬記念のコース適性を評価してください。
出力に「*」や「#」を含まないでください。

※本評価は、これまでに実施した  
- 馬単体評価
- 騎手評価  
の後続に位置づく評価であり、最終的な「総評」と統合される前提です。  
評価基準や結論をブレさせず、整合性を重視してください。

## 前提ルール
- 傾向分析プロンプトで確定させた
　・想定ペース（S/M/H）
　・有馬記念のコース特性
　・不利になりやすいタイプ
　を前提条件として評価すること

## 評価項目
・枠順
　- 枠番別の有馬記念着順割合を参照
　- 当該枠が有利・不利どちらの傾向かを評価

・距離適性  
　- 前走レース別の有馬記念好走傾向を参照
　- 前走ローテーションが中山芝2500mに繋がりやすい距離帯かを評価

・展開予想
　- 想定ペース（S/M/H）を前提とし当該馬の脚質タイプが有馬記念で有利・不利になりやすいかを評価

## WEB検索結果
{search_results}

## ★評価の内部目安（非出力）
★★★★★：コース形態・距離・馬場傾向に非常に噛み合う  
★★★★☆：有馬記念の舞台条件に適性が高い  
★★★☆☆：適性面で可もなく不可もない  
★★☆☆☆：舞台条件とややズレがあり、割引が必要  
★☆☆☆☆：舞台条件との不適合が大きい  
※この基準は内部判断用であり、説明文には直接書かないこと。

## 出力形式
【評価】
(「★☆☆☆☆」の形式で記載）
【コメント】
(2-3文で総評を記載)
・枠順：(1文で記載)
・距離適性：(1文で記載)
・展開予想：(1文で記載)
"""
    user_prompt = (
        f"馬名:{horse_info['馬名']} "
        f"枠番:{horse_info['枠番']} 馬番:{horse_info['馬番']} "
        f"前走:{horse_info['前走']}\n"
        f"{format_data_for_prompt(data)}"
    )
    return _call_gpt5mini_text(client, system_prompt, user_prompt, max_output_tokens=8000)


def analyze_total(client, horse_info, h_res, j_res, c_res):
    search_results = st.session_state.get("search_results") or "（WEB検索結果なし）"
    system_prompt = f"""
## 指示
あなたは有馬記念（中山芝2500m）を専門とする競馬予想AIエージェントです。
以下の3つの評価結果のみを入力情報として使用し、
「この馬を有馬記念でどのように扱うべきか」を最終的に総評してください。
出力に「*」や「#」を含まないでください。

- 馬単体評価（傾向適合度）
- 騎手単体評価（傾向適合度）
- コース適性評価（当年条件への適合度）

## 総評ロジック
 -評価は「掛け合わせ」で行う。
-いずれか1項目が低評価の場合、他が高評価でもリスクとして必ず反映すること。
- 特に以下の役割を明確にする：
　・馬単体評価＝素材としての有馬記念適性  
　・コース適性評価＝今年の条件との噛み合い  
　・騎手評価＝取りこぼしリスク（減点要素）

## WEB検索結果
{search_results}

## ★評価の内部目安（非出力）
★★★★★：3評価すべてが高水準で、致命的リスクなし  
★★★★☆：高水準だが一部に明確な注意点あり  
★★★☆☆：評価は揃うが、強調材料に欠ける  
★★☆☆☆：明確な不安要素が優勢  
★☆☆☆☆：複数評価で不利が重なる  
※この基準は内部判断用であり、説明文には直接書かないこと。

## 出力形式（厳守）
以下の形式でのみ出力すること。

【評価】
(「★☆☆☆☆」の形式で記載）  
【コメント】  
(馬、騎手、コースの3評価を掛け合わせた結論を3〜4文で簡潔に記述) 

【馬券的妙味】  
(軸向き／相手向き／ヒモ向き／見送り のいずれかを明示し理由を補足。軸向き等の用語についても解説を入れてください。)  

【一言】  
(判断を象徴する短いフレーズを記載)
"""
    user_prompt = (
        f"【枠{horse_info['枠番']}・馬{horse_info['馬番']} {horse_info['馬名']}】\n"
        f"馬分析:{h_res}\n"
        f"騎手分析:{j_res}\n"
        f"コース分析:{c_res}"
    )
    return _call_gpt5mini_text(client, system_prompt, user_prompt, max_output_tokens=8000)

# ============================================
# 機能③: サイン理論（3段階）
# ============================================
def get_events_2025(client):
    time.sleep(5)
    return EVENTS_2025_STR


def extract_numbers(client, events):
    system_prompt = f"""
## 指示
あなたは2025年の象徴的な出来事から有馬記念のサインを読み解く専門家です。 
有馬記念（中山芝2500m）に特化し、2025年の主要なニュースから関連する数字や事象を抽出してください。
出力に「*」や「#」を含まないでください。

## 原則
・ユーザーの入力形式は自由とする 
・結論 → 理由 → 補足 の順で説明する 
・補足では結論や理由に対する信ぴょう性を増すような具体的かつ意味深な小話を語ってください。
・専門用語は使ってよいが、必ず一言補足を添える
・陰謀論的な考え方が面白いかもしれません。
・一定の納得感を醸成するような巧みな語り口でお願いします。
・STEPの出力は不要です。

## 分析フロー
### STEP1 サインの抽出
2025年の象徴的な出来事から、馬番、枠番、馬名、騎手名、あるいはその他の関連情報に結びつけられる可能性のある具体的な「サイン候補」を複数抽出する。 例：
・特定の記念日 → 日付の数字を馬番・枠番に
・流行語に入っている数字 →数字を馬番に
・スポーツイベントの優勝回数や順位 → 数字を馬番に
・特定の有名人のイニシャル → 馬名や騎手名の連想
・社会現象の象徴的な色 → 枠色からの連想

### STEP2 サインの評価
抽出された複数のサイン候補について、以下の軸で評価し、2025年有馬記念で見るべきサインを明らかにする。
A. 話題性・認知度
その出来事が2025年においてどれだけ多くの人に知られ、話題になったか。
B. 物語性・意外性
サインとしての面白さ、偶然性、または逆説的な解釈の余地。
C. 複数要素との合致
一つの出来事から複数のサインが導き出される、または複数の出来事が一つのサインを指し示すなど。

## 出力形式
【結論】 
（2025年の主要サイン候補と、そこから抽出された数字・キーワードのリストを記載）
（サイン解釈における判断基準（例：直接性重視、話題性重視など）を記載）

【理由】
（上記結論に至った理由を記載）

【補足】
(陰謀論的なこじつけの小話で良いです。さも、常識かのように語ってください。)

## 禁止事項
・ユーザーの意見に迎合すること 
・キリのいい数字ばかり選ばないでください。複雑な数字こそ奥深い考察ができるはずです。

## 出走馬情報
{HORSE_INFO_STR_2025}
"""
    return _call_gpt5mini_text(
        client=client,
        system_prompt=system_prompt,
        user_prompt=f"出来事:\n{events}",
        max_output_tokens=8000,
    )


def sign_betting(client, events, numbers):
    system_prompt = f"""
## 指示
あなたは2025年の象徴的な出来事から有馬記念のサインを読み解き、買い目を導き出す専門AIエージェントです。 
有馬記念（中山芝2500m）に特化し、2025年の象徴的な出来事から抽出されたサインをもとに、競馬初心者でも納得しながら意思決定できる形で買い目を提示してください。
出力に「*」や「#」を含まないでください。
「出力形式」に従って出力してください。

## 出力フロー
サインの評価と2025年有馬記念の出走馬にもとづいて、以下の軸に基づいて出走馬を評価し、買い目を出力する
A. 関連性の強さ
出来事と馬番・馬名などとの結びつきの直接性・明確さ。
B. 複数要素との合致
一つのサインから複数の馬番や馬名が導き出される、または複数のサインが一つの馬番を指し示すなど。

## 原則
・ユーザーの入力形式は自由とする 
・会話の中でサインの評価・理由・買い方を柔軟に提示してよいが、AIのサイン分析軸・解釈基準は常に一貫させる 
・専門用語は使ってよいが、必ず一言補足を添える 

## 出力形式（初回・まとめ時）
◎本命サイン馬 (理由：2025年のどの出来事とどう関連するか、なぜ本命か)
○対抗サイン馬 (理由：同様)
▲単穴サイン馬 (理由：同様)
☆穴サイン馬 (理由：同様)
✕関連薄サイン馬 (理由：なぜ関連が薄いと判断したか)

◆ 安全型（的中重視）
（買い方（馬連・三連複等どの買い方でもOK）および狙いの考え方を記載）

◆ バランス型（期待値重視）
（買い方（馬連・三連複等どの買い方でもOK）および狙いの考え方を記載）

◆ 攻め型／冒険型（高配当狙い）
（買い方（馬連・三連複等どの買い方でもOK）および狙いの考え方を記載）

【資金配分の目安】
（上記のパターンそれぞれの資金配分を記載）

## 禁止事項
・人気順のみでの評価（サイン馬券は人気薄が本命になることも多い） 
・内部評価軸（サイン解釈の基準）を会話によって変更すること 
・ユーザーの意見に迎合すること 
・一般的な競馬のデータ分析や馬の能力評価に偏りすぎること。あくまで「サイン」を主軸とする。

## 出走馬情報
{HORSE_INFO_STR_2025}
"""
    return _call_gpt5mini_text(
        client=client,
        system_prompt=system_prompt,
        user_prompt=f"出来事:\n{events}\n考察:\n{numbers}",
        max_output_tokens=8000,
    )

# ============================================
# メインUI
# ============================================
def main():
    st.markdown('<h1 class="main-title">🏇 有馬記念予想 2025</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">第70回 AI × データ分析 × サイン理論</p>', unsafe_allow_html=True)

    client = get_openai_client()
    data = load_race_data()

    if data is None:
        st.error("❌ arima_data.xlsx の読み込みに失敗しました")
        st.stop()

    # サイドバー
    with st.sidebar:
        st.markdown("### ⚙️ 設定")

        if st.button("🔄 今日の検索をリセット", use_container_width=True):
            st.session_state["search_date_jst"] = None
            st.session_state["search_results"] = None
            st.session_state["search_error"] = None
            st.success("検索キャッシュをリセットしました（次回は再検索します）")

        st.markdown("---")
        st.markdown("### 🔎 Web検索結果（当日キャッシュ）")

        sb_debug = st.empty()
        sb_body = st.empty()

    tab1, tab2, tab3 = st.tabs(["🎯 総合予想", "🔍 単体評価", "🔮 サイン理論"])
    render_sidebar_search(sb_debug, sb_body)

    # =========================
    # タブ1: 総合予想（再実行時に前回結果を全消し）
    # =========================
    with tab1:
        st.markdown(
            """<div class="feature-card">
            <h3>🎯 総合予想機能</h3>
            <p>STEP1: データ傾向分析 → STEP2: 馬の選定 → STEP3: 買い目提案</p>
        </div>""",
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            start_btn = st.button("🚀 予想スタート", key="comp_btn", use_container_width=True)

        comp = st.session_state["comp_results"]

        st.markdown('<div class="label label-step1">STEP1: データ傾向分析</div>', unsafe_allow_html=True)
        ph1 = st.empty()
        st.markdown('<div class="label label-step2">STEP2: 馬の選定</div>', unsafe_allow_html=True)
        ph2 = st.empty()
        st.markdown('<div class="label label-step3">STEP3: 買い目提案</div>', unsafe_allow_html=True)
        ph3 = st.empty()

        # 既存結果（再実行していないときは保持表示）
        if comp["step1"]:
            ph1.markdown(render_box("📊 データ傾向", comp["step1"], "result-box"), unsafe_allow_html=True)
        if comp["step2"]:
            ph2.markdown(render_box("🏇 推奨馬", comp["step2"], "result-box"), unsafe_allow_html=True)
        if comp["step3"]:
            ph3.markdown(render_box("💰 買い目", comp["step3"], "result-box"), unsafe_allow_html=True)

        if start_btn:
            if client is None:
                st.error("APIキーを設定してください")
            else:
                comp["step1"] = None
                comp["step2"] = None
                comp["step3"] = None
                ph1.empty()
                ph2.empty()
                ph3.empty()

                ph1.info("📊 分析中...")
                ensure_daily_gpt_search(client, search_query)
                render_sidebar_search(sb_debug, sb_body)
                comp["step1"] = analyze_data_summary(client, data)
                ph1.markdown(render_box("📊 データ傾向", comp["step1"], "result-box"), unsafe_allow_html=True)

                ph2.info("🐴 評価中...")
                comp["step2"] = predict_horses(client, data, comp["step1"])
                ph2.markdown(render_box("🏇 推奨馬", comp["step2"], "result-box"), unsafe_allow_html=True)

                ph3.info("💰 検討中...")
                comp["step3"] = suggest_betting(client, comp["step2"])
                ph3.markdown(render_box("💰 買い目", comp["step3"], "result-box"), unsafe_allow_html=True)

    # =========================
    # タブ2: 単体評価（馬ごとに結果を保持）
    # =========================
    with tab2:
        st.markdown(
            """<div class="feature-card">
            <h3>🔍 単体評価機能</h3>
            <p>馬・騎手・コースの3軸で分析 → 統合評価</p>
        </div>""",
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            horse_num = st.selectbox(
                "🎰 馬を選択",
                list(HORSE_LIST_2025.keys()),
                format_func=lambda x: (
                    f"[{HORSE_LIST_2025[x]['枠番']}]"
                    f" {HORSE_LIST_2025[x]['馬番']}｜"
                    f"{HORSE_LIST_2025[x]['馬名']}（{HORSE_LIST_2025[x]['騎手']}）"
                ),
                key="horse_select",
            )
            eval_btn = st.button("🔍 評価スタート", key="eval_btn", use_container_width=True)

        horse_info = HORSE_LIST_2025[horse_num]
        st.markdown(f"## [{horse_info['枠番']}] {horse_info['馬番']} {horse_info['馬名']}（{horse_info['騎手']}）")

        col_h, col_j, col_c = st.columns(3)
        with col_h:
            st.markdown('<div class="label label-horse">🐴 馬分析</div>', unsafe_allow_html=True)
            ph_h = st.empty()
        with col_j:
            st.markdown('<div class="label label-jockey">🏇 騎手分析</div>', unsafe_allow_html=True)
            ph_j = st.empty()
        with col_c:
            st.markdown('<div class="label label-course">🏟️ コース分析</div>', unsafe_allow_html=True)
            ph_c = st.empty()

        st.markdown("---")
        st.markdown('<div class="label label-total">📊 総合評価</div>', unsafe_allow_html=True)
        ph_t = st.empty()

        saved = st.session_state["eval_results"].get(horse_num)

        # 保存済みがあれば表示（押していない時だけ）
        if saved and not eval_btn:
            ph_h.markdown(render_box("", saved["h"], "analysis-box box-horse"), unsafe_allow_html=True)
            ph_j.markdown(render_box("", saved["j"], "analysis-box box-jockey"), unsafe_allow_html=True)
            ph_c.markdown(render_box("", saved["c"], "analysis-box box-course"), unsafe_allow_html=True)
            ph_t.markdown(render_box("", saved["t"], "analysis-box box-total"), unsafe_allow_html=True)

        if eval_btn:
            if client is None:
                st.error("APIキーを設定してください")
            else:
                ph_h.empty()
                ph_j.empty()
                ph_c.empty()
                ph_t.empty()

                ph_h.info("分析中...")
                ensure_daily_gpt_search(client, search_query)
                render_sidebar_search(sb_debug, sb_body)
                h_res = analyze_horse(client, horse_info, data)
                ph_h.markdown(render_box("", h_res, "analysis-box box-horse"), unsafe_allow_html=True)

                ph_j.info("分析中...")
                j_res = analyze_jockey(client, horse_info, data)
                ph_j.markdown(render_box("", j_res, "analysis-box box-jockey"), unsafe_allow_html=True)

                ph_c.info("分析中...")
                c_res = analyze_course(client, horse_info, data)
                ph_c.markdown(render_box("", c_res, "analysis-box box-course"), unsafe_allow_html=True)

                ph_t.info("統合中...")
                t_res = analyze_total(client, horse_info, h_res, j_res, c_res)
                ph_t.markdown(render_box("", t_res, "analysis-box box-total"), unsafe_allow_html=True)

                st.session_state["eval_results"][horse_num] = {"h": h_res, "j": j_res, "c": c_res, "t": t_res}

    # =========================
    # タブ3: サイン理論（再実行時に前回結果を全消し）
    # =========================
    with tab3:
        st.markdown(
            """<div class="feature-card">
            <h3>🔮 サイン理論機能</h3>
            <p>2025年の出来事から数字を読み解く ※エンターテイメント</p>
        </div>""",
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            sign_btn = st.button("🔮 サイン分析", key="sign_btn", use_container_width=True)

        col_e, col_n = st.columns(2)
        with col_e:
            st.markdown('<div class="label label-events">📅 2025年の出来事</div>', unsafe_allow_html=True)
            ph_e = st.empty()
        with col_n:
            st.markdown('<div class="label label-numbers">🔢 サイン抽出</div>', unsafe_allow_html=True)
            ph_n = st.empty()

        st.markdown("---")
        st.markdown('<div class="label label-buy">💰 サイン理論買い目</div>', unsafe_allow_html=True)
        ph_b = st.empty()

        sign = st.session_state["sign_results"]

        # 既存結果（再実行していないときは保持表示）
        if sign["events"]:
            ph_e.markdown(render_box("", sign["events"], "analysis-box box-events"), unsafe_allow_html=True)
        if sign["numbers"]:
            ph_n.markdown(render_box("", sign["numbers"], "analysis-box box-numbers"), unsafe_allow_html=True)
        if sign["bet"]:
            ph_b.markdown(render_box("", sign["bet"], "analysis-box box-buy"), unsafe_allow_html=True)

        if sign_btn:
            if client is None:
                st.error("APIキーを設定してください")
            else:
                sign["events"] = None
                sign["numbers"] = None
                sign["bet"] = None
                ph_e.empty()
                ph_n.empty()
                ph_b.empty()

                ph_e.info("収集中...")
                ensure_daily_gpt_search(client, search_query)
                render_sidebar_search(sb_debug, sb_body)
                e_res = get_events_2025(client)
                sign["events"] = e_res
                ph_e.markdown(render_box("", e_res, "analysis-box box-events"), unsafe_allow_html=True)

                ph_n.info("抽出中...")
                n_res = extract_numbers(client, e_res)
                sign["numbers"] = n_res
                ph_n.markdown(render_box("", n_res, "analysis-box box-numbers"), unsafe_allow_html=True)

                ph_b.info("導出中...")
                b_res = sign_betting(client, e_res, n_res)
                sign["bet"] = b_res
                ph_b.markdown(render_box("", b_res, "analysis-box box-buy"), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        """<div style="text-align:center;color:#999;padding:1rem;">
        🏇 第70回 有馬記念 PREDICTOR 2025
    </div>""",
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()
