"""
🏇 有馬記念予想アプリ 2025
GitHub × Streamlit で動作する競馬予想システム
"""

import streamlit as st
import pandas as pd
from openai import OpenAI
import os

# ============================================
# ページ設定
# ============================================
st.set_page_config(
    page_title="有馬記念予想 2025",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# セッション状態初期化（タブ切替でも結果を保持）
# ============================================
def init_session_state():
    if "comp_results" not in st.session_state:
        st.session_state.comp_results = {"step1": None, "step2": None, "step3": None}
    if "eval_results" not in st.session_state:
        # horse_num -> {"h":..., "j":..., "c":..., "t":...}
        st.session_state.eval_results = {}
    if "sign_results" not in st.session_state:
        st.session_state.sign_results = {"events": None, "numbers": None, "bet": None}

init_session_state()

# ============================================
# カスタムCSS
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');

    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        font-family: 'Noto Sans JP', sans-serif;
    }

    /* ===== 基本テキスト色（表示系は白） ===== */
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* 見出しが灰色になるのを抑止 */
    div[data-testid="stMarkdownContainer"] h1,
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stMarkdownContainer"] h4,
    div[data-testid="stMarkdownContainer"] h5,
    div[data-testid="stMarkdownContainer"] h6,
    div[data-testid="stMarkdownContainer"] a {
        color: #ffffff !important;
    }

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

    .feature-card {
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 215, 0, 0.3);
        margin: 1rem 0;
    }

    .feature-card h3 { color: #ffd700 !important; }
    .feature-card p, .feature-card li { color: #e0e0e0 !important; }

    /* ===== 結果ボックス（白背景→黒文字） ===== */
    .result-box {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 5px solid #ffd700;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        color: #333333 !important;          /* ← テキストノード対策（重要） */
    }
    .result-box * { color: #333333 !important; }

    /* ===== 分析ボックス（白背景→黒文字） ===== */
    .analysis-box {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        min-height: 280px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        color: #333333 !important;          /* ← テキストノード対策（重要） */
    }
    .analysis-box * { color: #333333 !important; }

    .box-horse { border: 3px solid #e74c3c; }
    .box-jockey { border: 3px solid #3498db; }
    .box-course { border: 3px solid #27ae60; }
    .box-total { border: 3px solid #f39c12; background: #fffef5; }
    .box-events { border: 3px solid #9b59b6; }
    .box-numbers { border: 3px solid #e67e22; }
    .box-buy { border: 3px solid #c0392b; background: #fff8f8; }

    /* ===== タイトルラベル ===== */
    .label {
        font-size: 1.1rem;
        font-weight: 700;
        padding: 0.4rem 1rem;
        border-radius: 6px;
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
    .label-events { background: #9b59b6; }
    .label-numbers { background: #e67e22; }
    .label-buy { background: #c0392b; }

    /* ===== ステータス（待機中/分析中） ===== */
    .status-box {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 10px;
        padding: 0.9rem 1rem;
        color: #ffffff !important;
        font-weight: 600;
    }

    /* ===== ボタン ===== */
    .stButton > button {
        background: linear-gradient(135deg, #ffd700, #ff8c00) !important;
        color: #1a1a2e !important;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.7rem 2rem;
        border-radius: 50px;
        border: none;
    }
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.4);
    }

    /* ===== タブ ===== */
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.15);
        color: #ffffff !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ffd700, #ff8c00) !important;
        color: #1a1a2e !important;
    }

    /* ===== サイドバー ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e, #0f3460);
    }
    section[data-testid="stSidebar"] .stMarkdown { color: #ffffff !important; }

    /* ===== Selectbox の選択値が白になる問題：黒に固定 ===== */
    div[data-baseweb="select"] * { color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

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
            xlsx = pd.ExcelFile("data/arima_data.xlsx")
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
    titles = ["年齢別期待値", "枠順別期待値", "騎手別期待値（中山2500m）", "血統（種牡馬）別期待値",
              "前走クラス別期待値", "前走レース別期待値", "馬体重増減別期待値"]
    for sheet, title in zip(sheets, titles):
        if sheet in data:
            formatted += f"【{title}】\n{data[sheet].to_string(index=False)}\n\n"
    return formatted

# ============================================
# 2025年有馬記念 出走予定馬データ（枠順未確定）
# ============================================
HORSE_LIST_2025 = {
    1: {"馬名": "レガレイラ", "性齢": "牝4歳", "騎手": "C.ルメール", "血統": "スワーヴリチャード", "前走": "エリザベス女王杯1着"},
    2: {"馬名": "ミュージアムマイル", "性齢": "牡3歳", "騎手": "C.デムーロ", "血統": "リオンディーズ", "前走": "天皇賞秋2着"},
    3: {"馬名": "ダノンデサイル", "性齢": "牡4歳", "騎手": "戸崎圭太", "血統": "エピファネイア", "前走": "JC3着"},
    4: {"馬名": "メイショウタバル", "性齢": "牡4歳", "騎手": "武豊", "血統": "ゴールドシップ", "前走": "天皇賞秋6着"},
    5: {"馬名": "ビザンチンドリーム", "性齢": "牡4歳", "騎手": "A.プーシャン", "血統": "エピファネイア", "前走": "凱旋門賞5着"},
    6: {"馬名": "ジャスティンパレス", "性齢": "牡6歳", "騎手": "団野大成", "血統": "ディープインパクト", "前走": "JC5着"},
    7: {"馬名": "シンエンペラー", "性齢": "牡4歳", "騎手": "坂井瑠星", "血統": "Siyouni", "前走": "JC8着"},
    8: {"馬名": "タスティエーラ", "性齢": "牡4歳", "騎手": "松山弘平", "血統": "サトノクラウン", "前走": "JC7着"},
    9: {"馬名": "コスモキュランダ", "性齢": "牡3歳", "騎手": "丹内祐次", "血統": "アルアイン", "前走": "JC9着"},
    10: {"馬名": "アドマイヤテラ", "性齢": "牡3歳", "騎手": "川田将雅", "血統": "スワーヴリチャード", "前走": "菊花賞3着"},
    11: {"馬名": "サンライズアース", "性齢": "牡3歳", "騎手": "池添謙一", "血統": "レイデオロ", "前走": "JC15着"},
    12: {"馬名": "エルトンバローズ", "性齢": "牡4歳", "騎手": "西村淳也", "血統": "ディープブリランテ", "前走": "天皇賞秋9着"},
    13: {"馬名": "ミステリーウェイ", "性齢": "牡5歳", "騎手": "松本大輝", "血統": "ハーツクライ", "前走": "ARC1着"},
    14: {"馬名": "サンライズジパング", "性齢": "牡3歳", "騎手": "未定", "血統": "キタサンブラック", "前走": "チャンピオンズC6着"},
    15: {"馬名": "ヘデントール", "性齢": "牡4歳", "騎手": "未定", "血統": "ハービンジャー", "前走": "天皇賞秋10着"},
    16: {"馬名": "シュヴァリエローズ", "性齢": "牡4歳", "騎手": "未定", "血統": "キズナ", "前走": "宝塚記念4着"},
}

HORSE_INFO_STR_2025 = """【2025年有馬記念 出走予定馬】※枠順未確定
レガレイラ（牝4歳・C.ルメール・スワーヴリチャード産駒・前走エリザベス女王杯1着）- ファン投票1位・連覇狙い
ミュージアムマイル（牡3歳・C.デムーロ・リオンディーズ産駒・前走天皇賞秋2着）- 皐月賞馬
ダノンデサイル（牡4歳・戸崎圭太・エピファネイア産駒・前走JC3着）- ダービー馬・昨年3着
メイショウタバル（牡4歳・武豊・ゴールドシップ産駒・前走天皇賞秋6着）- 宝塚記念馬・春秋GP制覇狙い
ビザンチンドリーム（牡4歳・A.プーシャン・エピファネイア産駒・前走凱旋門賞5着）- 海外帰り
ジャスティンパレス（牡6歳・団野大成・ディープインパクト産駒・前走JC5着）- 天皇賞春馬・ラストラン
シンエンペラー（牡4歳・坂井瑠星・Siyouni産駒・前走JC8着）- 皐月賞2着
タスティエーラ（牡4歳・松山弘平・サトノクラウン産駒・前走JC7着）- 昨年ダービー馬
コスモキュランダ（牡3歳・丹内祐次・アルアイン産駒・前走JC9着）- 皐月賞2着
アドマイヤテラ（牡3歳・川田将雅・スワーヴリチャード産駒・前走菊花賞3着）
サンライズアース（牡3歳・池添謙一・レイデオロ産駒・前走JC15着）
エルトンバローズ（牡4歳・西村淳也・ディープブリランテ産駒・前走天皇賞秋9着）
ミステリーウェイ（牡5歳・松本大輝・ハーツクライ産駒・前走ARC1着）- アルゼンチン共和国杯勝ち
サンライズジパング（牡3歳・未定・キタサンブラック産駒・前走チャンピオンズC6着）
ヘデントール（牡4歳・未定・ハービンジャー産駒・前走天皇賞秋10着）
シュヴァリエローズ（牡4歳・未定・キズナ産駒・前走宝塚記念4着）"""

# ============================================
# 機能①: 総合予想
# ============================================
def analyze_data_summary(client, data):
    system_prompt = """あなたは競馬データアナリストです。過去10年のデータから有馬記念で好走しやすい条件を分析してください。
【出力】簡潔に箇条書きで
- 年齢: 好走しやすい年齢
- 枠順: 有利な枠
- 騎手: 期待値の高い騎手TOP3
- 血統: 好走血統TOP3
- 前走: 好走しやすい前走レース
- 馬体重: 好走しやすい増減幅"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"データ分析:\n{format_data_for_prompt(data)}"}],
        temperature=0.5, max_tokens=1000
    )
    return response.choices[0].message.content

def predict_horses(client, data, analysis):
    system_prompt = f"""あなたは競馬予想の専門家です。データ分析結果を踏まえ、2025年有馬記念の推奨馬を選定してください。
{HORSE_INFO_STR_2025}
【出力形式】
◎本命: 馬名 - 選定理由
○対抗: 馬名 - 選定理由
▲単穴: 馬名 - 選定理由
☆穴馬: 馬名 - 選定理由
✕危険馬: 馬名 - 過信禁物な理由"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"【分析結果】\n{analysis}"}],
        temperature=0.7, max_tokens=1500
    )
    return response.choices[0].message.content

def suggest_betting(client, prediction):
    system_prompt = """馬券アドバイザーとして買い目を提案してください。
【出力形式】
■ 本線（堅実）馬連・ワイド
■ 勝負（中配当）三連複・三連単
■ 穴狙い ワイド・三連複
■ 投資配分"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"予想:\n{prediction}"}],
        temperature=0.6, max_tokens=1000
    )
    return response.choices[0].message.content

# ============================================
# 機能②: 単体評価
# ============================================
def analyze_horse(client, horse_info, data):
    system_prompt = """馬の能力を分析。【出力】■ 評価: ★5段階 ■ 血統評価(2-3文) ■ 年齢評価(2-3文) ■ 能力・実績(2-3文)"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"馬名:{horse_info['馬名']} 性齢:{horse_info['性齢']} 血統:{horse_info['血統']} 前走:{horse_info['前走']}\n{format_data_for_prompt(data)}"}],
        temperature=0.6, max_tokens=800
    )
    return response.choices[0].message.content

def analyze_jockey(client, horse_info, data):
    system_prompt = """騎手を分析。【出力】■ 評価: ★5段階 ■ コース成績(2-3文) ■ 騎乗スタイル(2-3文) ■ 馬との相性(2-3文)"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"騎手:{horse_info['騎手']} 騎乗馬:{horse_info['馬名']}\n{format_data_for_prompt(data)}"}],
        temperature=0.6, max_tokens=800
    )
    return response.choices[0].message.content

def analyze_course(client, horse_info, data):
    system_prompt = """コース適性を分析。【出力】■ 評価: ★5段階 ■ 枠順評価(2-3文) ■ コース適性(2-3文) ■ 展開予想(2-3文)"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"馬名:{horse_info['馬名']} 前走:{horse_info['前走']}\n{format_data_for_prompt(data)}"}],
        temperature=0.6, max_tokens=800
    )
    return response.choices[0].message.content

def analyze_total(client, horse_info, h_res, j_res, c_res):
    system_prompt = """3分析を統合して総合評価。【出力】■ 総合評価: ★5段階 ■ 期待度: A-E ■ 総評(4-5文) ■ 馬券的妙味(単勝/連軸/穴馬) ■ 一言"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"【{horse_info['馬名']}】\n馬分析:{h_res}\n騎手分析:{j_res}\nコース分析:{c_res}"}],
        temperature=0.6, max_tokens=800
    )
    return response.choices[0].message.content

# ============================================
# 機能③: サイン理論
# ============================================
def get_events_2025(client):
    system_prompt = """あなたは2025年の日本のニュース・出来事に詳しい専門家です。
2025年に起こった出来事のみを列挙してください。2024年以前は含めないでください。
【カテゴリ】スポーツ/政治/芸能/社会現象 各3-4個
【出力形式】
■ スポーツ（2025年）
1. [出来事] - [日付や数字]
2. ...
■ 政治（2025年）
...
■ 芸能（2025年）
...
■ 社会現象（2025年）
..."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": "2025年1月から12月までの日本での主要な出来事を教えてください。2024年以前は不要です。"}],
        temperature=0.8, max_tokens=1200
    )
    return response.choices[0].message.content

def extract_numbers(client, events):
    system_prompt = """出来事から馬番に使える数字を抽出。【出力】表形式で 出来事|数字|意味 ※16以下優先"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"出来事:\n{events}"}],
        temperature=0.7, max_tokens=1000
    )
    return response.choices[0].message.content

def sign_betting(client, events, numbers):
    system_prompt = f"""サイン理論から2025年有馬記念の買い目を導出してください。
{HORSE_INFO_STR_2025}
【出力】■ 最重要サイン→馬名 ■ 準重要サイン→馬名 ■ 買い目(馬連/三連複/ワイド) ■ 大穴予想
⚠️サイン理論はエンターテイメントです！"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"出来事:\n{events}\n数字:\n{numbers}"}],
        temperature=0.9, max_tokens=1000
    )
    return response.choices[0].message.content

# ============================================
# メインUI
# ============================================
def main():
    st.markdown('<h1 class="main-title">🏇 有馬記念予想 2025</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">第70回 AI × データ分析 × サイン理論</p>', unsafe_allow_html=True)

    client = get_openai_client()

    # サイドバー
    with st.sidebar:
        st.markdown("### ⚙️ 設定")
        uploaded_file = st.file_uploader("📁 予想データ", type=["xlsx", "xls"])

        if uploaded_file:
            data = load_race_data(uploaded_file)
            st.success("✅ データ読み込み完了")
        else:
            data = load_race_data()
            if data:
                st.info("📊 デフォルトデータ使用中")
            else:
                st.warning("⚠️ データなし（分析精度低下）")
                data = {}

        st.markdown("---")
        st.markdown("### 🐴 2025年 出走予定馬")
        for num, info in HORSE_LIST_2025.items():
            st.markdown(f"**{info['馬名']}** ({info['騎手']})")

    tab1, tab2, tab3 = st.tabs(["🎯 総合予想", "🔍 単体評価", "🔮 サイン理論"])

    # -------------------------
    # タブ1: 総合予想（結果保持）
    # -------------------------
    with tab1:
        st.markdown("""<div class="feature-card">
            <h3>🎯 総合予想機能</h3>
            <p>STEP1: データ傾向分析 → STEP2: 馬の選定 → STEP3: 買い目提案</p>
        </div>""", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            start_btn = st.button("🚀 予想スタート", key="comp", use_container_width=True)

        if start_btn:
            if client is None:
                st.error("APIキーを設定してください")
            else:
                with st.spinner("📊 分析中..."):
                    st.session_state.comp_results["step1"] = analyze_data_summary(client, data)
                with st.spinner("🐴 評価中..."):
                    st.session_state.comp_results["step2"] = predict_horses(client, data, st.session_state.comp_results["step1"])
                with st.spinner("💰 検討中..."):
                    st.session_state.comp_results["step3"] = suggest_betting(client, st.session_state.comp_results["step2"])

        # 保存済み結果を常に表示
        cr = st.session_state.comp_results
        if cr["step1"]:
            st.markdown("### STEP1: データ傾向分析")
            st.markdown(f'<div class="result-box"><h4>📊 データ傾向</h4><pre style="margin:0;white-space:pre-wrap;">{cr["step1"]}</pre></div>', unsafe_allow_html=True)
        if cr["step2"]:
            st.markdown("### STEP2: 馬の選定")
            st.markdown(f'<div class="result-box"><h4>🏇 推奨馬</h4><pre style="margin:0;white-space:pre-wrap;">{cr["step2"]}</pre></div>', unsafe_allow_html=True)
        if cr["step3"]:
            st.markdown("### STEP3: 買い目提案")
            st.markdown(f'<div class="result-box"><h4>💰 買い目</h4><pre style="margin:0;white-space:pre-wrap;">{cr["step3"]}</pre></div>', unsafe_allow_html=True)

    # -------------------------
    # タブ2: 単体評価（馬ごとに結果保持）
    # -------------------------
    with tab2:
        st.markdown("""<div class="feature-card">
            <h3>🔍 単体評価機能</h3>
            <p>馬・騎手・コースの3軸で分析 → 統合評価</p>
        </div>""", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            horse_num = st.selectbox(
                "🎰 馬を選択",
                list(HORSE_LIST_2025.keys()),
                format_func=lambda x: f"{HORSE_LIST_2025[x]['馬名']} ({HORSE_LIST_2025[x]['騎手']})",
                key="horse_select"
            )
            eval_btn = st.button("🔍 評価スタート", key="eval", use_container_width=True)

        horse_info = HORSE_LIST_2025[horse_num]
        st.markdown(f"## {horse_info['馬名']} の分析")

        # 3列レイアウト
        col_h, col_j, col_c = st.columns(3)
        ph_h = col_h.empty()
        ph_j = col_j.empty()
        ph_c = col_c.empty()

        st.markdown("---")
        st.markdown('<div class="label label-total">📊 総合評価</div>', unsafe_allow_html=True)
        ph_t = st.empty()

        # 既存結果の取得
        saved = st.session_state.eval_results.get(horse_num)

        # 評価実行
        if eval_btn:
            if client is None:
                st.error("APIキーを設定してください")
            else:
                ph_h.markdown('<div class="label label-horse">🐴 馬分析</div><div class="status-box">分析中...</div>', unsafe_allow_html=True)
                ph_j.markdown('<div class="label label-jockey">🏇 騎手分析</div><div class="status-box">待機中...</div>', unsafe_allow_html=True)
                ph_c.markdown('<div class="label label-course">🏟️ コース分析</div><div class="status-box">待機中...</div>', unsafe_allow_html=True)
                ph_t.markdown('<div class="status-box">待機中...</div>', unsafe_allow_html=True)

                h_res = analyze_horse(client, horse_info, data)
                ph_h.markdown(f'<div class="label label-horse">🐴 馬分析</div><div class="analysis-box box-horse"><pre style="margin:0;white-space:pre-wrap;">{h_res}</pre></div>', unsafe_allow_html=True)

                ph_j.markdown('<div class="label label-jockey">🏇 騎手分析</div><div class="status-box">分析中...</div>', unsafe_allow_html=True)
                j_res = analyze_jockey(client, horse_info, data)
                ph_j.markdown(f'<div class="label label-jockey">🏇 騎手分析</div><div class="analysis-box box-jockey"><pre style="margin:0;white-space:pre-wrap;">{j_res}</pre></div>', unsafe_allow_html=True)

                ph_c.markdown('<div class="label label-course">🏟️ コース分析</div><div class="status-box">分析中...</div>', unsafe_allow_html=True)
                c_res = analyze_course(client, horse_info, data)
                ph_c.markdown(f'<div class="label label-course">🏟️ コース分析</div><div class="analysis-box box-course"><pre style="margin:0;white-space:pre-wrap;">{c_res}</pre></div>', unsafe_allow_html=True)

                ph_t.markdown('<div class="status-box">統合中...</div>', unsafe_allow_html=True)
                t_res = analyze_total(client, horse_info, h_res, j_res, c_res)
                ph_t.markdown(f'<div class="analysis-box box-total"><pre style="margin:0;white-space:pre-wrap;">{t_res}</pre></div>', unsafe_allow_html=True)

                st.session_state.eval_results[horse_num] = {"h": h_res, "j": j_res, "c": c_res, "t": t_res}
                saved = st.session_state.eval_results[horse_num]

        # ボタン押してなくても、保存済みを表示（タブ切替でも消えない）
        if not eval_btn:
            if saved:
                ph_h.markdown(f'<div class="label label-horse">🐴 馬分析</div><div class="analysis-box box-horse"><pre style="margin:0;white-space:pre-wrap;">{saved["h"]}</pre></div>', unsafe_allow_html=True)
                ph_j.markdown(f'<div class="label label-jockey">🏇 騎手分析</div><div class="analysis-box box-jockey"><pre style="margin:0;white-space:pre-wrap;">{saved["j"]}</pre></div>', unsafe_allow_html=True)
                ph_c.markdown(f'<div class="label label-course">🏟️ コース分析</div><div class="analysis-box box-course"><pre style="margin:0;white-space:pre-wrap;">{saved["c"]}</pre></div>', unsafe_allow_html=True)
                ph_t.markdown(f'<div class="analysis-box box-total"><pre style="margin:0;white-space:pre-wrap;">{saved["t"]}</pre></div>', unsafe_allow_html=True)
            else:
                ph_h.markdown('<div class="label label-horse">🐴 馬分析</div><div class="status-box">待機中...</div>', unsafe_allow_html=True)
                ph_j.markdown('<div class="label label-jockey">🏇 騎手分析</div><div class="status-box">待機中...</div>', unsafe_allow_html=True)
                ph_c.markdown('<div class="label label-course">🏟️ コース分析</div><div class="status-box">待機中...</div>', unsafe_allow_html=True)
                ph_t.markdown('<div class="status-box">待機中...</div>', unsafe_allow_html=True)

    # -------------------------
    # タブ3: サイン理論（結果保持）
    # -------------------------
    with tab3:
        st.markdown("""<div class="feature-card">
            <h3>🔮 サイン理論機能</h3>
            <p>2025年の出来事から数字を読み解く ※エンターテイメント</p>
        </div>""", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            sign_btn = st.button("🔮 サイン分析", key="sign", use_container_width=True)

        if sign_btn:
            if client is None:
                st.error("APIキーを設定してください")
            else:
                with st.spinner("📅 収集中..."):
                    st.session_state.sign_results["events"] = get_events_2025(client)
                with st.spinner("🔢 抽出中..."):
                    st.session_state.sign_results["numbers"] = extract_numbers(client, st.session_state.sign_results["events"])
                with st.spinner("💰 導出中..."):
                    st.session_state.sign_results["bet"] = sign_betting(client, st.session_state.sign_results["events"], st.session_state.sign_results["numbers"])

        sr = st.session_state.sign_results
        if sr["events"] or sr["numbers"] or sr["bet"]:
            col_e, col_n = st.columns(2)
            with col_e:
                st.markdown('<div class="label label-events">📅 2025年の出来事</div>', unsafe_allow_html=True)
                if sr["events"]:
                    st.markdown(f'<div class="analysis-box box-events"><pre style="margin:0;white-space:pre-wrap;">{sr["events"]}</pre></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-box">待機中...</div>', unsafe_allow_html=True)
            with col_n:
                st.markdown('<div class="label label-numbers">🔢 抽出数字</div>', unsafe_allow_html=True)
                if sr["numbers"]:
                    st.markdown(f'<div class="analysis-box box-numbers"><pre style="margin:0;white-space:pre-wrap;">{sr["numbers"]}</pre></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-box">待機中...</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown('<div class="label label-buy">💰 サイン理論買い目</div>', unsafe_allow_html=True)
            if sr["bet"]:
                st.markdown(f'<div class="analysis-box box-buy"><pre style="margin:0;white-space:pre-wrap;">{sr["bet"]}</pre></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-box">待機中...</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box">まだ結果がありません。上のボタンから実行してください。</div>', unsafe_allow_html=True)

    # フッター
    st.markdown("---")
    st.markdown("""<div style="text-align:center;color:#999;padding:1rem;">
        ⚠️ 予想は参考情報です。馬券購入は自己責任で。<br>
        🏇 第70回 有馬記念 PREDICTOR 2025 | Powered by GPT-4o
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
