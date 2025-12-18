"""
🏇 有馬記念予想アプリ
GitHub × Streamlit で動作する競馬予想システム
"""

import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from datetime import datetime

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
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&family=Zen+Kaku+Gothic+New:wght@400;700&display=swap');
    
    /* 全体のスタイル */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        font-family: 'Noto Sans JP', sans-serif;
    }
    
    /* タイトルスタイル */
    .main-title {
        font-family: 'Noto Sans JP', sans-serif;
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #ffd700, #ff8c00, #ff6347);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        padding: 1rem 0;
        text-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.5)); }
        to { filter: drop-shadow(0 0 20px rgba(255, 140, 0, 0.8)); }
    }
    
    /* サブタイトル */
    .sub-title {
        font-family: 'Zen Kaku Gothic New', sans-serif;
        font-size: 1.2rem;
        color: #e0e0e0;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: 0.3em;
    }
    
    /* 機能カード */
    .feature-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(255, 215, 0, 0.3);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        margin: 1rem 0;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        border-color: rgba(255, 215, 0, 0.6);
        box-shadow: 0 10px 40px rgba(255, 215, 0, 0.2);
    }
    
    /* 予想結果カード */
    .prediction-card {
        background: linear-gradient(145deg, #2d2d44, #1a1a2e);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    
    .honmei { border-left-color: #ff0000; }
    .taikou { border-left-color: #0066ff; }
    .tananaa { border-left-color: #00cc00; }
    .anaba { border-left-color: #ffcc00; }
    .kiken { border-left-color: #666666; }
    
    /* ボタンスタイル */
    .stButton > button {
        background: linear-gradient(135deg, #ffd700, #ff8c00);
        color: #1a1a2e;
        font-weight: 700;
        font-size: 1.2rem;
        padding: 0.8rem 3rem;
        border-radius: 50px;
        border: none;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 30px rgba(255, 215, 0, 0.4);
    }
    
    /* 馬番入力 */
    .stNumberInput > div > div > input {
        background: rgba(255,255,255,0.1);
        border: 2px solid rgba(255, 215, 0, 0.5);
        border-radius: 10px;
        color: white;
        font-size: 1.5rem;
        text-align: center;
    }
    
    /* 結果表示エリア */
    .result-area {
        background: rgba(0,0,0,0.3);
        border-radius: 20px;
        padding: 2rem;
        margin-top: 2rem;
        border: 1px solid rgba(255, 215, 0, 0.2);
    }
    
    /* タブスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.1);
        border-radius: 10px 10px 0 0;
        color: white;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ffd700, #ff8c00);
        color: #1a1a2e;
    }
    
    /* ローディングアニメーション */
    .loading-horse {
        font-size: 3rem;
        animation: run 0.5s infinite;
    }
    
    @keyframes run {
        0%, 100% { transform: translateX(0); }
        50% { transform: translateX(10px); }
    }
    
    /* サイドバー */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a2e, #0f3460);
    }
    
    /* 評価バー */
    .eval-bar {
        height: 20px;
        border-radius: 10px;
        background: linear-gradient(90deg, #ff6347, #ffd700, #00cc00);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# OpenAI クライアント設定
# ============================================
def get_openai_client():
    """OpenAI クライアントを取得"""
    api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))
    if not api_key:
        st.error("⚠️ OpenAI API キーが設定されていません。Streamlit Secrets または環境変数に OPENAI_API_KEY を設定してください。")
        return None
    return OpenAI(api_key=api_key)


# ============================================
# データ読み込み
# ============================================
@st.cache_data
def load_race_data():
    """予想用データの読み込み"""
    try:
        df = pd.read_excel("data/arima_data.xlsx")
        return df
    except FileNotFoundError:
        # サンプルデータを返す
        return pd.DataFrame({
            "馬番": range(1, 17),
            "馬名": ["ドウデュース", "ジャスティンパレス", "スターズオンアース", "タスティエーラ", 
                    "シャフリヤール", "ダノンベルーガ", "ソールオリエンス", "ライラック",
                    "アーバンシック", "プログノーシス", "ベラジオオペラ", "シュトルーヴェ",
                    "レガレイラ", "ローシャムパーク", "ディープボンド", "ハヤヤッコ"],
            "性齢": ["牡5", "牡5", "牝5", "牡4", "牡6", "牡5", "牡4", "牝5",
                    "牡4", "牡6", "牡4", "牡5", "牝4", "牝5", "牡7", "牡8"],
            "騎手": ["武豊", "横山武史", "C.ルメール", "モレイラ", "川田将雅", "戸崎圭太",
                    "横山和生", "M.デムーロ", "C.デムーロ", "吉田隼人", "レーン", "坂井瑠星",
                    "北村宏司", "松山弘平", "幸英明", "団野大成"],
            "調教師": ["友道康夫", "杉山晴紀", "高野友和", "堀宣行", "藤原英昭", "堀宣行",
                      "手塚貴久", "矢作芳人", "池江泰寿", "中内田充正", "上村洋行", "池添学",
                      "木村哲也", "田中博康", "大久保龍志", "清水久詞"],
            "前走": ["天皇賞秋1着", "天皇賞秋3着", "エリザベス女王杯3着", "菊花賞1着",
                    "天皇賞秋5着", "天皇賞秋7着", "天皇賞秋4着", "エリザベス女王杯5着",
                    "菊花賞2着", "天皇賞秋2着", "天皇賞秋6着", "アルゼンチン共和国杯1着",
                    "エリザベス女王杯1着", "天皇賞秋8着", "アルゼンチン共和国杯3着", "札幌記念2着"],
            "オッズ": [3.5, 5.2, 6.8, 8.1, 12.5, 15.3, 18.6, 22.4,
                     25.8, 28.9, 35.2, 42.6, 55.3, 68.9, 85.2, 120.5]
        })


# ============================================
# 機能①: 総合予想
# ============================================
def comprehensive_prediction(client, df):
    """総合予想を実行"""
    
    system_prompt = """あなたは競馬予想の専門家AIです。有馬記念の予想を行います。

【役割】
- 提供されたデータを分析し、科学的かつ論理的な予想を行う
- 各馬の能力、騎手、調教師、前走成績、オッズなどを総合的に評価
- 中山競馬場2500mの特性（小回り、坂、非根幹距離）を考慮

【出力形式】
必ず以下の形式で予想を出力してください：

## 🏆 有馬記念予想

### 📌 本命馬（◎）
**【馬番】馬名**
選出理由：（2-3文で具体的に）

### 📌 対抗馬（○）
**【馬番】馬名**
選出理由：（2-3文で具体的に）

### 📌 単穴（▲）
**【馬番】馬名**
選出理由：（2-3文で具体的に）

### 📌 穴馬（☆）
**【馬番】馬名**
選出理由：（2-3文で具体的に）

### ⚠️ 危険馬（✕）
**【馬番】馬名**
注意点：（なぜ過信禁物か）

### 💰 推奨買い目
- **馬連**: ◎-○ を本線
- **三連複**: ◎○▲ BOX
- **三連単**: ◎→○→▲、◎→▲→○
- **ワイド**: ◎-☆（穴狙い）

### 📊 予想の根拠
（全体的な分析コメント 3-4文）
"""

    user_prompt = f"""以下の出走馬データを分析し、有馬記念の予想を行ってください。

【出走馬データ】
{df.to_string(index=False)}

中山競馬場2500mの特性と各馬の適性を考慮して、総合的に予想してください。
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


# ============================================
# 機能②: 単体評価
# ============================================
def individual_evaluation(client, df, horse_number):
    """指定した馬番の単体評価を実行"""
    
    horse_data = df[df["馬番"] == horse_number]
    if horse_data.empty:
        return "指定された馬番が見つかりません。"
    
    horse_info = horse_data.iloc[0].to_dict()
    
    system_prompt = """あなたは競馬予想の専門家AIです。指定された1頭の馬を多角的に分析します。

【分析手順】
STEP 1: 馬分析 - 馬自身の能力、血統、実績を評価
STEP 2: 騎手分析 - 騎手の能力、コース相性、馬との相性を評価  
STEP 3: コース分析 - 中山2500mへの適性を評価
STEP 4: 統合評価 - 上記3つを統合した総合評価

【出力形式】
必ず以下の形式で出力してください：

## 🐴 馬分析（STEP 1）
### 評価: ⭐⭐⭐⭐☆（5段階）
**分析内容:**
（馬の能力、血統背景、これまでの実績について3-4文で分析）

---

## 🏇 騎手分析（STEP 2）
### 評価: ⭐⭐⭐⭐☆（5段階）
**分析内容:**
（騎手の技量、中山での成績、当該馬との相性について3-4文で分析）

---

## 🏟️ コース適性分析（STEP 3）
### 評価: ⭐⭐⭐⭐☆（5段階）
**分析内容:**
（中山2500mへの適性、コーナリング、坂への対応について3-4文で分析）

---

## 📊 統合評価（STEP 4）
### 総合評価: ⭐⭐⭐⭐☆（5段階）
### 期待度: A / B / C / D / E

**統合コメント:**
（3つの評価を統合した最終的な見解を4-5文で記述）

**推奨:**
- 単勝での購入: おすすめ / 様子見 / 非推奨
- 連系馬券の軸: おすすめ / 様子見 / 非推奨
- 穴馬として: おすすめ / 様子見 / 非推奨
"""

    user_prompt = f"""以下の馬を分析してください。

【対象馬データ】
- 馬番: {horse_info.get('馬番', 'N/A')}
- 馬名: {horse_info.get('馬名', 'N/A')}
- 性齢: {horse_info.get('性齢', 'N/A')}
- 騎手: {horse_info.get('騎手', 'N/A')}
- 調教師: {horse_info.get('調教師', 'N/A')}
- 前走: {horse_info.get('前走', 'N/A')}
- オッズ: {horse_info.get('オッズ', 'N/A')}倍

中山競馬場2500mでの有馬記念に向けた分析をお願いします。
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


# ============================================
# 機能③: サイン理論
# ============================================
def sign_theory_prediction(client):
    """サイン理論に基づく予想を実行"""
    
    system_prompt = """あなたは競馬のサイン理論の専門家AIです。
サイン理論とは、社会的な出来事や数字の偶然の一致から馬券を予想する手法です。

【分析手順】
1. 2024年〜2025年の主要な出来事を列挙
2. それらに関連する数字（日付、順位、記録など）を抽出
3. 有馬記念との関連性を見出す
4. 買い目を導出

【出力形式】
必ず以下の形式で出力してください：

## 🔮 サイン理論分析

### 📅 2024-2025年 注目の出来事

#### 🏆 スポーツ関連
1. **[出来事名]** - 関連数字: X
   - サインの解釈: （どう馬券に結びつくか）

2. **[出来事名]** - 関連数字: X
   - サインの解釈: （どう馬券に結びつくか）

#### 📰 社会・政治関連
1. **[出来事名]** - 関連数字: X
   - サインの解釈: （どう馬券に結びつくか）

#### 🎭 芸能・エンタメ関連
1. **[出来事名]** - 関連数字: X
   - サインの解釈: （どう馬券に結びつくか）

---

### 🔢 抽出された数字の整理
| 出来事 | 数字 | 馬番/枠番への適用 |
|--------|------|-------------------|
| xxx | X | 馬番X |
| xxx | X | 枠番X |

---

### 💫 サイン理論からの導出

**最重要サイン:**
（最も強いサインとその根拠）

**補助サイン:**
（補完的なサインとその根拠）

---

### 💰 サイン理論推奨買い目

**◎ メイン買い目**
- 馬連: X-X
- 三連複: X-X-X

**○ サブ買い目**
- ワイド: X-X
- 馬単: X→X

**注意:** サイン理論はあくまでエンターテイメントです。投資は自己責任で！
"""

    user_prompt = """2024年から2025年にかけての日本での主要な出来事を思い出し、
サイン理論に基づいて有馬記念の買い目を導出してください。

特に以下の観点から数字を抽出してください：
- 大谷翔平の活躍（本塁打数、打点、背番号など）
- パリオリンピックでの日本のメダル
- 政治関連（選挙、首相交代など）
- 芸能ニュース（結婚、引退など）
- 社会現象（流行語、ヒット商品など）

それぞれの数字を馬番や枠番に紐づけて、買い目を提案してください。
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,  # 創造性を高める
            max_tokens=2500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


# ============================================
# メインUI
# ============================================
def main():
    # ヘッダー
    st.markdown('<h1 class="main-title">🏇 有馬記念予想 2024</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">AI × データ分析 × サイン理論</p>', unsafe_allow_html=True)
    
    # クライアント初期化
    client = get_openai_client()
    
    # データ読み込み
    df = load_race_data()
    
    # サイドバー
    with st.sidebar:
        st.markdown("### ⚙️ 設定")
        
        # データアップロード
        uploaded_file = st.file_uploader(
            "📁 予想データをアップロード",
            type=["xlsx", "xls"],
            help="Excelファイル形式でアップロードしてください"
        )
        
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file)
            st.success("✅ データを読み込みました！")
        
        st.markdown("---")
        
        # 出走馬一覧
        st.markdown("### 📋 出走馬一覧")
        for _, row in df.iterrows():
            st.markdown(f"**{row['馬番']}** {row['馬名']} ({row['騎手']})")
    
    # メインコンテンツ - タブ構成
    tab1, tab2, tab3 = st.tabs([
        "🎯 総合予想",
        "🔍 単体評価", 
        "🔮 サイン理論"
    ])
    
    # ============================================
    # タブ1: 総合予想
    # ============================================
    with tab1:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 総合予想機能</h3>
            <p>出走馬のデータを総合的に分析し、本命から穴馬まで予想します。</p>
            <ul>
                <li>◎本命、○対抗、▲単穴、☆穴馬、✕危険馬</li>
                <li>推奨買い目（馬連・三連複・三連単・ワイド）</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 予想スタート", key="comprehensive", use_container_width=True):
                if client:
                    with st.spinner("🏇 AIが分析中..."):
                        result = comprehensive_prediction(client, df)
                    
                    st.markdown("---")
                    st.markdown('<div class="result-area">', unsafe_allow_html=True)
                    st.markdown(result)
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # ============================================
    # タブ2: 単体評価
    # ============================================
    with tab2:
        st.markdown("""
        <div class="feature-card">
            <h3>🔍 単体評価機能</h3>
            <p>指定した馬を多角的に分析します。</p>
            <ul>
                <li>馬分析（能力・血統・実績）</li>
                <li>騎手分析（技量・コース相性）</li>
                <li>コース適性分析（中山2500m適性）</li>
                <li>統合評価（総合的な期待度）</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            horse_number = st.number_input(
                "🎰 馬番を入力",
                min_value=1,
                max_value=len(df),
                value=1,
                step=1
            )
            
            # 選択した馬の情報を表示
            selected_horse = df[df["馬番"] == horse_number]
            if not selected_horse.empty:
                horse = selected_horse.iloc[0]
                st.info(f"**選択中:** {horse['馬番']}番 {horse['馬名']} ({horse['騎手']})")
            
            if st.button("🔍 評価スタート", key="individual", use_container_width=True):
                if client:
                    with st.spinner(f"🏇 {horse_number}番を分析中..."):
                        result = individual_evaluation(client, df, horse_number)
                    
                    st.markdown("---")
                    st.markdown('<div class="result-area">', unsafe_allow_html=True)
                    st.markdown(result)
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # ============================================
    # タブ3: サイン理論
    # ============================================
    with tab3:
        st.markdown("""
        <div class="feature-card">
            <h3>🔮 サイン理論機能</h3>
            <p>2024-2025年の出来事から数字を読み解き、馬券を導出します。</p>
            <ul>
                <li>スポーツ・政治・芸能などの出来事</li>
                <li>関連する数字の抽出</li>
                <li>馬番・枠番との紐付け</li>
                <li>サイン理論に基づく買い目</li>
            </ul>
            <p><small>※サイン理論はエンターテイメントとしてお楽しみください</small></p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔮 サイン分析スタート", key="sign", use_container_width=True):
                if client:
                    with st.spinner("🔮 サインを読み解き中..."):
                        result = sign_theory_prediction(client)
                    
                    st.markdown("---")
                    st.markdown('<div class="result-area">', unsafe_allow_html=True)
                    st.markdown(result)
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # フッター
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 2rem;">
        <p>⚠️ 本アプリの予想は参考情報です。馬券購入は自己責任でお願いします。</p>
        <p>🏇 ARIMA KINEN PREDICTOR 2024 | Powered by OpenAI GPT-4o</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
