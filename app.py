"""
🏇 有馬記念予想アプリ
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
    page_title="有馬記念予想 2024",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# カスタムCSS
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span, p, li, span, div,
    h1, h2, h3, h4, h5, h6 {
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
    
    /* 結果ボックス - 白背景で視認性確保 */
    .result-box {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 5px solid #ffd700;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .result-box h4, .result-box p, .result-box li, .result-box span,
    .result-box h1, .result-box h2, .result-box h3 {
        color: #333333 !important;
    }
    
    /* 分析ボックス */
    .analysis-box {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        min-height: 280px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .analysis-box h1, .analysis-box h2, .analysis-box h3, .analysis-box h4,
    .analysis-box p, .analysis-box li, .analysis-box span, .analysis-box td, .analysis-box th {
        color: #333333 !important;
    }
    
    .box-horse { border: 3px solid #e74c3c; }
    .box-jockey { border: 3px solid #3498db; }
    .box-course { border: 3px solid #27ae60; }
    .box-total { border: 3px solid #f39c12; background: #fffef5; }
    .box-events { border: 3px solid #9b59b6; }
    .box-numbers { border: 3px solid #e67e22; }
    .box-buy { border: 3px solid #c0392b; background: #fff8f8; }
    
    /* タイトルラベル */
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
    
    /* ボタン */
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
    
    /* タブ */
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.15);
        color: #ffffff !important;
        font-weight: 600;
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
    except:
        return None

def format_data_for_prompt(data):
    formatted = ""
    sheets = ["年齢", "枠順", "騎手", "血統", "前走クラス", "前走レース別", "馬体重増減"]
    titles = ["年齢別期待値", "枠順別期待値", "騎手別期待値（中山2500m）", "血統（種牡馬）別期待値", 
              "前走クラス別期待値", "前走レース別期待値", "馬体重増減別期待値"]
    for sheet, title in zip(sheets, titles):
        if sheet in data:
            formatted += f"【{title}】\n{data[sheet].to_string(index=False)}\n\n"
    return formatted

# ============================================
# 出走馬データ
# ============================================
HORSE_LIST = {
    1: {"馬名": "ダノンデサイル", "性齢": "牡3歳", "騎手": "横山典弘", "血統": "キタサンブラック", "前走": "菊花賞1着", "枠": 1},
    2: {"馬名": "ジャスティンパレス", "性齢": "牡5歳", "騎手": "C.デムーロ", "血統": "ディープインパクト", "前走": "JC8着", "枠": 1},
    3: {"馬名": "シャフリヤール", "性齢": "牡6歳", "騎手": "C.ルメール", "血統": "ディープインパクト", "前走": "JC6着", "枠": 2},
    4: {"馬名": "ベラジオオペラ", "性齢": "牡4歳", "騎手": "横山武史", "血統": "ロードカナロア", "前走": "JC10着", "枠": 2},
    5: {"馬名": "ブローザホーン", "性齢": "牡5歳", "騎手": "菅原明良", "血統": "エピファネイア", "前走": "JC11着", "枠": 3},
    6: {"馬名": "ディープボンド", "性齢": "牡7歳", "騎手": "幸英明", "血統": "キズナ", "前走": "JC12着", "枠": 3},
    7: {"馬名": "プログノーシス", "性齢": "牡6歳", "騎手": "川田将雅", "血統": "ディープインパクト", "前走": "JC4着", "枠": 4},
    8: {"馬名": "アーバンシック", "性齢": "牡3歳", "騎手": "C.ルメール", "血統": "スワーヴリチャード", "前走": "菊花賞2着", "枠": 4},
    9: {"馬名": "ドウデュース", "性齢": "牡5歳", "騎手": "武豊", "血統": "ハーツクライ", "前走": "天皇賞秋1着", "枠": 5},
    10: {"馬名": "ローシャムパーク", "性齢": "牡5歳", "騎手": "戸崎圭太", "血統": "ハービンジャー", "前走": "JC5着", "枠": 5},
    11: {"馬名": "レガレイラ", "性齢": "牝3歳", "騎手": "北村宏司", "血統": "スワーヴリチャード", "前走": "JC9着", "枠": 6},
    12: {"馬名": "スターズオンアース", "性齢": "牝5歳", "騎手": "川田将雅", "血統": "ドゥラメンテ", "前走": "JC7着", "枠": 6},
    13: {"馬名": "スタニングローズ", "性齢": "牝5歳", "騎手": "西村淳也", "血統": "キングカメハメハ", "前走": "エリ女5着", "枠": 7},
    14: {"馬名": "シュトルーヴェ", "性齢": "牡5歳", "騎手": "松山弘平", "血統": "ドゥラメンテ", "前走": "ARC1着", "枠": 7},
    15: {"馬名": "ダノンベルーガ", "性齢": "牡5歳", "騎手": "T.マーカンド", "血統": "ハーツクライ", "前走": "JC3着", "枠": 8},
    16: {"馬名": "ハヤヤッコ", "性齢": "牡8歳", "騎手": "団野大成", "血統": "キングカメハメハ", "前走": "JC13着", "枠": 8},
}

HORSE_INFO_STR = """1枠1番 ダノンデサイル（牡3歳・横山典弘・キタサンブラック産駒・前走菊花賞1着）
1枠2番 ジャスティンパレス（牡5歳・C.デムーロ・ディープインパクト産駒・前走JC8着）
2枠3番 シャフリヤール（牡6歳・C.ルメール・ディープインパクト産駒・前走JC6着）
2枠4番 ベラジオオペラ（牡4歳・横山武史・ロードカナロア産駒・前走JC10着）
3枠5番 ブローザホーン（牡5歳・菅原明良・エピファネイア産駒・前走JC11着）
3枠6番 ディープボンド（牡7歳・幸英明・キズナ産駒・前走JC12着）
4枠7番 プログノーシス（牡6歳・川田将雅・ディープインパクト産駒・前走JC4着）
4枠8番 アーバンシック（牡3歳・C.ルメール・スワーヴリチャード産駒・前走菊花賞2着）
5枠9番 ドウデュース（牡5歳・武豊・ハーツクライ産駒・前走天皇賞秋1着）
5枠10番 ローシャムパーク（牡5歳・戸崎圭太・ハービンジャー産駒・前走JC5着）
6枠11番 レガレイラ（牝3歳・北村宏司・スワーヴリチャード産駒・前走JC9着）
6枠12番 スターズオンアース（牝5歳・川田将雅・ドゥラメンテ産駒・前走JC7着）
7枠13番 スタニングローズ（牝5歳・西村淳也・キングカメハメハ産駒・前走エリ女5着）
7枠14番 シュトルーヴェ（牡5歳・松山弘平・ドゥラメンテ産駒・前走ARC1着）
8枠15番 ダノンベルーガ（牡5歳・T.マーカンド・ハーツクライ産駒・前走JC3着）
8枠16番 ハヤヤッコ（牡8歳・団野大成・キングカメハメハ産駒・前走JC13着）"""
# ============================================
# 機能①: 総合予想（3段階）
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
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"データ分析:\n{format_data_for_prompt(data)}"}],
            temperature=0.5, max_tokens=1000)
        return response.choices[0].message.content
    except Exception as e:
        return f"エラー: {str(e)}"

def predict_horses(client, data, analysis):
    system_prompt = f"""あなたは競馬予想の専門家です。データ分析結果を踏まえ、推奨馬を選定してください。
【出走馬】
{HORSE_INFO_STR}
【出力形式】
◎本命: [馬番]馬名 - 選定理由
○対抗: [馬番]馬名 - 選定理由
▲単穴: [馬番]馬名 - 選定理由
☆穴馬: [馬番]馬名 - 選定理由
✕危険馬: [馬番]馬名 - 過信禁物な理由"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"【分析結果】\n{analysis}"}],
            temperature=0.7, max_tokens=1500)
        return response.choices[0].message.content
    except Exception as e:
        return f"エラー: {str(e)}"

def suggest_betting(client, prediction):
    system_prompt = """馬券アドバイザーとして買い目を提案してください。
【出力形式】
■ 本線（堅実）馬連・ワイド
■ 勝負（中配当）三連複・三連単
■ 穴狙い ワイド・三連複
■ 投資配分"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"予想:\n{prediction}"}],
            temperature=0.6, max_tokens=1000)
        return response.choices[0].message.content
    except Exception as e:
        return f"エラー: {str(e)}"

# ============================================
# 機能②: 単体評価（4段階）
# ============================================
def analyze_horse(client, horse_info, data):
    system_prompt = """馬の能力を分析。【出力】■ 評価: ★5段階 ■ 血統評価(2-3文) ■ 年齢評価(2-3文) ■ 能力・実績(2-3文)"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"馬名:{horse_info['馬名']} 性齢:{horse_info['性齢']} 血統:{horse_info['血統']} 前走:{horse_info['前走']}\n{format_data_for_prompt(data)}"}],
            temperature=0.6, max_tokens=800)
        return response.choices[0].message.content
    except Exception as e:
        return f"エラー: {str(e)}"

def analyze_jockey(client, horse_info, data):
    system_prompt = """騎手を分析。【出力】■ 評価: ★5段階 ■ コース成績(2-3文) ■ 騎乗スタイル(2-3文) ■ 馬との相性(2-3文)"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"騎手:{horse_info['騎手']} 騎乗馬:{horse_info['馬名']}\n{format_data_for_prompt(data)}"}],
            temperature=0.6, max_tokens=800)
        return response.choices[0].message.content
    except Exception as e:
        return f"エラー: {str(e)}"

def analyze_course(client, horse_info, data):
    system_prompt = """コース適性を分析。【出力】■ 評価: ★5段階 ■ 枠順評価(2-3文) ■ コース適性(2-3文) ■ 展開予想(2-3文)"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"馬名:{horse_info['馬名']} 枠:{horse_info['枠']}枠 前走:{horse_info['前走']}\n{format_data_for_prompt(data)}"}],
            temperature=0.6, max_tokens=800)
        return response.choices[0].message.content
    except Exception as e:
        return f"エラー: {str(e)}"

def analyze_total(client, horse_info, h_res, j_res, c_res):
    system_prompt = """3分析を統合して総合評価。【出力】■ 総合評価: ★5段階 ■ 期待度: A-E ■ 総評(4-5文) ■ 馬券的妙味(単勝/連軸/穴馬) ■ 一言"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"【{horse_info['馬名']}】\n馬分析:{h_res}\n騎手分析:{j_res}\nコース分析:{c_res}"}],
            temperature=0.6, max_tokens=800)
        return response.choices[0].message.content
    except Exception as e:
        return f"エラー: {str(e)}"

# ============================================
# 機能③: サイン理論（3段階）
# ============================================
def get_events_2024(client):
    system_prompt = """2024-2025年の日本の出来事を列挙。【カテゴリ】スポーツ/政治/芸能/社会現象 各3-4個"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": "2024-2025年の主要な出来事を教えてください"}],
            temperature=0.8, max_tokens=1000)
        return response.choices[0].message.content
    except Exception as e:
        return f"エラー: {str(e)}"

def extract_numbers(client, events):
    system_prompt = """出来事から馬番に使える数字を抽出。【出力】表形式で 出来事|数字|意味 ※16以下優先"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"出来事:\n{events}"}],
            temperature=0.7, max_tokens=1000)
        return response.choices[0].message.content
    except Exception as e:
        return f"エラー: {str(e)}"

def sign_betting(client, events, numbers):
    system_prompt = f"""サイン理論から買い目を導出。
【馬番】1ダノンデサイル 2ジャスティンパレス 3シャフリヤール 4ベラジオオペラ 5ブローザホーン 6ディープボンド 7プログノーシス 8アーバンシック 9ドウデュース 10ローシャムパーク 11レガレイラ 12スターズオンアース 13スタニングローズ 14シュトルーヴェ 15ダノンベルーガ 16ハヤヤッコ
【出力】■ 最重要サイン→馬番 ■ 準重要サイン→馬番 ■ 買い目(馬連/三連複/ワイド) ■ 大穴予想
⚠️エンターテイメントです！"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"出来事:\n{events}\n数字:\n{numbers}"}],
            temperature=0.9, max_tokens=1000)
        return response.choices[0].message.content
    except Exception as e:
        return f"エラー: {str(e)}"
# ============================================
# メインUI
# ============================================
def main():
    st.markdown('<h1 class="main-title">🏇 有馬記念予想 2024</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">AI × データ分析 × サイン理論</p>', unsafe_allow_html=True)
    
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
                data = {}
        
        st.markdown("---")
        st.markdown("### 🐴 出走馬")
        for num, info in HORSE_LIST.items():
            st.markdown(f"**{num}** {info['馬名']}")
    
    # タブ
    tab1, tab2, tab3 = st.tabs(["🎯 総合予想", "🔍 単体評価", "🔮 サイン理論"])
    
    # タブ1: 総合予想
    with tab1:
        st.markdown("""<div class="feature-card">
            <h3>🎯 総合予想機能</h3>
            <p>STEP1: データ傾向分析 → STEP2: 馬の選定 → STEP3: 買い目提案</p>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            start_btn = st.button("🚀 予想スタート", key="comp", use_container_width=True)
        
        if start_btn and client and data:
            st.markdown("### STEP1: データ傾向分析")
            with st.spinner("📊 分析中..."):
                step1 = analyze_data_summary(client, data)
            st.markdown(f'<div class="result-box"><h4>📊 データ傾向</h4>{step1}</div>', unsafe_allow_html=True)
            
            st.markdown("### STEP2: 馬の選定")
            with st.spinner("🐴 評価中..."):
                step2 = predict_horses(client, data, step1)
            st.markdown(f'<div class="result-box"><h4>🏇 推奨馬</h4>{step2}</div>', unsafe_allow_html=True)
            
            st.markdown("### STEP3: 買い目提案")
            with st.spinner("💰 検討中..."):
                step3 = suggest_betting(client, step2)
            st.markdown(f'<div class="result-box"><h4>💰 買い目</h4>{step3}</div>', unsafe_allow_html=True)
    
    # タブ2: 単体評価
    with tab2:
        st.markdown("""<div class="feature-card">
            <h3>🔍 単体評価機能</h3>
            <p>馬・騎手・コースの3軸で分析 → 統合評価</p>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            horse_num = st.selectbox("🎰 馬番を選択", list(HORSE_LIST.keys()),
                                     format_func=lambda x: f"{x}番 {HORSE_LIST[x]['馬名']} ({HORSE_LIST[x]['騎手']})")
            eval_btn = st.button("🔍 評価スタート", key="eval", use_container_width=True)
        
        if eval_btn and client and data:
            horse_info = HORSE_LIST[horse_num]
            st.markdown(f"## {horse_num}番 {horse_info['馬名']} の分析")
            
            # 3列レイアウト
            col_h, col_j, col_c = st.columns(3)
            
            with col_h:
                st.markdown('<div class="label label-horse">🐴 馬分析</div>', unsafe_allow_html=True)
                ph_h = st.empty()
                ph_h.info("分析中...")
            with col_j:
                st.markdown('<div class="label label-jockey">🏇 騎手分析</div>', unsafe_allow_html=True)
                ph_j = st.empty()
                ph_j.info("待機中...")
            with col_c:
                st.markdown('<div class="label label-course">🏟️ コース分析</div>', unsafe_allow_html=True)
                ph_c = st.empty()
                ph_c.info("待機中...")
            
            st.markdown("---")
            st.markdown('<div class="label label-total">📊 総合評価</div>', unsafe_allow_html=True)
            ph_t = st.empty()
            ph_t.info("待機中...")
            
            # 馬分析
            h_res = analyze_horse(client, horse_info, data)
            ph_h.markdown(f'<div class="analysis-box box-horse">{h_res}</div>', unsafe_allow_html=True)
            
            # 騎手分析
            ph_j.info("分析中...")
            j_res = analyze_jockey(client, horse_info, data)
            ph_j.markdown(f'<div class="analysis-box box-jockey">{j_res}</div>', unsafe_allow_html=True)
            
            # コース分析
            ph_c.info("分析中...")
            c_res = analyze_course(client, horse_info, data)
            ph_c.markdown(f'<div class="analysis-box box-course">{c_res}</div>', unsafe_allow_html=True)
            
            # 総合評価
            ph_t.info("統合中...")
            t_res = analyze_total(client, horse_info, h_res, j_res, c_res)
            ph_t.markdown(f'<div class="analysis-box box-total">{t_res}</div>', unsafe_allow_html=True)
    
    # タブ3: サイン理論
    with tab3:
        st.markdown("""<div class="feature-card">
            <h3>🔮 サイン理論機能</h3>
            <p>2024-2025年の出来事から数字を読み解く ※エンターテイメント</p>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            sign_btn = st.button("🔮 サイン分析", key="sign", use_container_width=True)
        
        if sign_btn and client:
            # 2列レイアウト
            col_e, col_n = st.columns(2)
            
            with col_e:
                st.markdown('<div class="label label-events">📅 出来事一覧</div>', unsafe_allow_html=True)
                ph_e = st.empty()
                ph_e.info("収集中...")
            with col_n:
                st.markdown('<div class="label label-numbers">🔢 抽出数字</div>', unsafe_allow_html=True)
                ph_n = st.empty()
                ph_n.info("待機中...")
            
            st.markdown("---")
            st.markdown('<div class="label label-buy">💰 サイン理論買い目</div>', unsafe_allow_html=True)
            ph_b = st.empty()
            ph_b.info("待機中...")
            
            # 出来事
            e_res = get_events_2024(client)
            ph_e.markdown(f'<div class="analysis-box box-events">{e_res}</div>', unsafe_allow_html=True)
            
            # 数字抽出
            ph_n.info("抽出中...")
            n_res = extract_numbers(client, e_res)
            ph_n.markdown(f'<div class="analysis-box box-numbers">{n_res}</div>', unsafe_allow_html=True)
            
            # 買い目
            ph_b.info("導出中...")
            b_res = sign_betting(client, e_res, n_res)
            ph_b.markdown(f'<div class="analysis-box box-buy">{b_res}</div>', unsafe_allow_html=True)
    
    # フッター
    st.markdown("---")
    st.markdown("""<div style="text-align:center;color:#999;padding:1rem;">
        ⚠️ 予想は参考情報です。馬券購入は自己責任で。<br>
        🏇 ARIMA PREDICTOR 2024 | Powered by GPT-4o
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
