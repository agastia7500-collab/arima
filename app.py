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
# セッション状態（タブ切替でも結果を保持）
# ============================================
if "comp_results" not in st.session_state:
    st.session_state["comp_results"] = {"step1": None, "step2": None, "step3": None}
if "eval_results" not in st.session_state:
    st.session_state["eval_results"] = {}
if "sign_results" not in st.session_state:
    st.session_state["sign_results"] = {"events": None, "numbers": None, "bet": None}

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

EVENTS_2025_STR = """【2025年の主な出来事】
■ 国家プロジェクト・社会（回帰・周期）
- 大阪・関西万博（EXPO 2025）
   - 内容: 1970年の大阪万博から55年ぶり、2005年愛知から20年ぶりの開催
   - 関連数字: 55 (大阪開催55年ぶり), 20 (日本開催20年ぶり), 1970 (前回大阪), 4 (4月開幕)

- 昭和100年
   - 内容: 昭和元年(1926年)から数えて100年目となる節目の年
   - 関連数字: 100 (100年目), 26 (1926年), 1 (100の先頭)

- 戦後80年
   - 内容: 1945年の終戦から80年経過
   - 関連数字: 80 (80年), 45 (1945年), 8 (8月), 15 (15日)

- 乙巳（きのとみ）の年
   - 内容: 干支が「巳」であり、前回の乙巳(1965年)から60年で一巡
   - 関連数字: 6 (十二支の6番目), 60 (60年で還暦), 65 (前回1965年)

- 国勢調査（こくせいちょうさ）
   - 内容: 5年に1度の全数調査（前回2020年から5年ぶり）
   - 関連数字: 5 (5年周期), 20 (前回2020年), 1 (10月1日基準)

- 新紙幣 発行から1年
   - 内容: 2024年7月の発行から1年が経過し定着
   - 関連数字: 1 (1周年), 24 (2024年), 7 (7月)

■ 周年・アニバーサリー（50年・40年）
- 山陽新幹線（岡山～博多）全線開業50周年
   - 内容: 1975年の開業から50年
   - 関連数字: 50 (開業50周年), 75 (1975年), 10 (3月10日開業)

- スーパー戦隊シリーズ 50周年
   - 内容: 1975年のゴレンジャー開始から50年の金字塔
   - 関連数字: 50 (放送50周年), 75 (1975年), 5 (ゴレンジャーの5)

- 沖縄国際海洋博覧会から50周年
   - 内容: 1975年の沖縄返還記念事業から50年
   - 関連数字: 50 (開催50周年), 75 (1975年), 20 (開催日7月20日)

- Microsoft（マイクロソフト）創業50周年
   - 内容: ビル・ゲイツらが創業してから半世紀の節目
   - 関連数字: 50 (創業50周年), 75 (1975年創業), 4 (ロゴの4色)

- ローソン 創業50周年
   - 内容: 日本での1号店オープンから50年
   - 関連数字: 50 (創業50周年), 75 (1975年), 14 (6月14日創業)

- 阪神タイガース 伝説の日本一から40年
   - 内容: バース・掛布・岡田を擁して日本一になった1985年から40年
   - 関連数字: 40 (40年経過), 85 (1985年), 1 (日本一)

- つくば万博（科学万博）から40周年
   - 内容: 1985年開催の科学ブームから40年
   - 関連数字: 40 (開催40周年), 85 (1985年)

■ スポーツ・イベント（回数・記録）
- 第101回 箱根駅伝
   - 内容: 100回記念大会を終え、新たな100年への1歩目
   - 関連数字: 101 (第101回), 2 (1月2日), 3 (1月3日)

- 世界陸上競技選手権大会（東京大会）
   - 内容: 東京で34年ぶり（1991年以来）の開催
   - 関連数字: 34 (34年ぶり), 91 (前回1991年), 20 (第20回大会)

- 夏季デフリンピック（東京大会）
   - 内容: 1924年の第1回パリ大会から約100年で日本初開催
   - 関連数字: 100 (100周年), 25 (第25回大会), 15 (11月15日開幕)

- ドジャース大谷翔平 メジャー8年目
   - 内容: 2018年のエンゼルス入団から数えて8年目のシーズン
   - 関連数字: 8 (8年目), 17 (背番号), 18 (2018年デビュー)

■ ゲーム・テクノロジー（間隔・進化）
- Nintendo Switch 後継機（スイッチ2）の話題
   - 内容: 2017年のSwitch発売から8年ぶりに投入される次世代ハード
   - 関連数字: 8 (8年ぶりの新型機), 2 (2世代目), 17 (前作2017年)

- Windows 10 サポート終了・Windows 11移行
   - 内容: 2015年のリリースから10年を経てサポート終了
   - 関連数字: 10 (発売から10年), 15 (2015年), 11 (Windows 11)

- 「GTA VI（グランド・セフト・オート6）」発売
   - 内容: 世界的ヒット作の前作(V)から12年ぶりの完全新作
   - 関連数字: 12 (前作から12年ぶり), 6 (タイトルナンバーVI), 5 (前作V)

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
   - 関連数字: 40 (公開40周年), 85 (1985年), 1 (パート1)

- NHK連続テレビ小説「あんぱん」
   - 内容: 第112作目の朝ドラ
   - 関連数字: 112 (第112作), 3 (アンパンマンの頬や服の色)

- NHK大河ドラマ「べらぼう」
   - 内容: 第64作目の大河ドラマ
   - 関連数字: 64 (第64作), 1 (1月放送開始)

- 高輪ゲートウェイシティ まちびらき
   - 内容: 2020年の駅開業から5年を経て街全体が完成
   - 関連数字: 5 (駅開業から5年), 30 (3月下旬開業)
"""

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
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"データ分析:\n{format_data_for_prompt(data)}"}],
        temperature=0.5, max_tokens=1000
    )
    return r.choices[0].message.content

def predict_horses(client, data, analysis):
    system_prompt = f"""あなたは競馬予想の専門家です。データ分析結果を踏まえ、2025年有馬記念の推奨馬を選定してください。
{HORSE_INFO_STR_2025}
【出力形式】
◎本命: 馬名 - 選定理由
○対抗: 馬名 - 選定理由
▲単穴: 馬名 - 選定理由
☆穴馬: 馬名 - 選定理由
✕危険馬: 馬名 - 過信禁物な理由"""
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"【分析結果】\n{analysis}"}],
        temperature=0.7, max_tokens=1500
    )
    return r.choices[0].message.content

def suggest_betting(client, prediction):
    system_prompt = """馬券アドバイザーとして買い目を提案してください。
【出力形式】
■ 本線（堅実）馬連・ワイド
■ 勝負（中配当）三連複・三連単
■ 穴狙い ワイド・三連複
■ 投資配分"""
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"予想:\n{prediction}"}],
        temperature=0.6, max_tokens=1000
    )
    return r.choices[0].message.content

# ============================================
# 機能②: 単体評価（4段階）
# ============================================
def analyze_horse(client, horse_info, data):
    system_prompt = "馬の能力を分析。【出力】■ 評価: ★5段階 ■ 血統評価(2-3文) ■ 年齢評価(2-3文) ■ 能力・実績(2-3文)"
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"馬名:{horse_info['馬名']} 性齢:{horse_info['性齢']} 血統:{horse_info['血統']} 前走:{horse_info['前走']}\n{format_data_for_prompt(data)}"}],
        temperature=0.6, max_tokens=800
    )
    return r.choices[0].message.content

def analyze_jockey(client, horse_info, data):
    system_prompt = "騎手を分析。【出力】■ 評価: ★5段階 ■ コース成績(2-3文) ■ 騎乗スタイル(2-3文) ■ 馬との相性(2-3文)"
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"騎手:{horse_info['騎手']} 騎乗馬:{horse_info['馬名']}\n{format_data_for_prompt(data)}"}],
        temperature=0.6, max_tokens=800
    )
    return r.choices[0].message.content

def analyze_course(client, horse_info, data):
    system_prompt = "コース適性を分析。【出力】■ 評価: ★5段階 ■ 枠順評価(2-3文) ■ コース適性(2-3文) ■ 展開予想(2-3文)"
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"馬名:{horse_info['馬名']} 前走:{horse_info['前走']}\n{format_data_for_prompt(data)}"}],
        temperature=0.6, max_tokens=800
    )
    return r.choices[0].message.content

def analyze_total(client, horse_info, h_res, j_res, c_res):
    system_prompt = "3分析を統合して総合評価。【出力】■ 総合評価: ★5段階 ■ 期待度: A-E ■ 総評(4-5文) ■ 馬券的妙味(単勝/連軸/穴馬) ■ 一言"
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"【{horse_info['馬名']}】\n馬分析:{h_res}\n騎手分析:{j_res}\nコース分析:{c_res}"}],
        temperature=0.6, max_tokens=800
    )
    return r.choices[0].message.content

# ============================================
# 機能③: サイン理論（3段階）
# ============================================
def get_events_2025(client):
    time.sleep(5)
    return EVENTS_2025_STR

def extract_numbers(client, events):
    system_prompt = f"""
    ## 指示
    あなたは2025年の象徴的な出来事から有馬記念のサインを読み解く専門AIエージェントです。 有馬記念（中山芝2500m）に特化し、2025年の主要なニュースから関連する数字や事象を抽出してください。
    ## 原則
    ・ユーザーの入力形式は自由とする 
    ・結論 → 理由 → 補足 の順で説明する 
    ・専門用語は使ってよいが、必ず一言補足を添える
    
    ## 分析フロー
    ### STEP1 サインの抽出
    2025年の象徴的な出来事から、馬番、枠番、馬名、騎手名、あるいはその他の関連情報に結びつけられる可能性のある具体的な「サイン候補」を複数抽出する。 例：
    ・特定の記念日 → 日付の数字を馬番・枠番に
    ・流行語に入っている数字 →数字を馬番に
    ・スポーツイベントの優勝回数や順位 → 数字を馬番に
    ・特定の有名人のイニシャル → 馬名や騎手名の連想
    ・社会現象の象徴的な色 → 枠色からの連想
    
    ### STEP2 サインの評価
    抽出された複数のサイン候補について、以下の軸で 評価し、2025年有馬記念で見るべきサインを明らかにする。
    A. 話題性・認知度
    その出来事が2025年においてどれだけ多くの人に知られ、話題になったか。
    B. 物語性・意外性
    サインとしての面白さ、偶然性、または逆説的な解釈の余地。
    C. 複数要素との合致
    一つの出来事から複数のサインが導き出される、または複数の出来事が一つのサインを指し示すなど。
    
    ## 出力形式
    【結論】 
    ・2025年の主要サイン候補と、そこから抽出された数字・キーワードのリスト
    ・サイン解釈におけるAIの判断基準（例：直接性重視、話題性重視など）
    
    ## 禁止事項
    ・ユーザーの意見に迎合すること 

    ## 出走馬情報
   {HORSE_INFO_STR_2025}"""
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"出来事:\n{events}"}],
        temperature=0.7, max_tokens=3000
    )
    return r.choices[0].message.content

def sign_betting(client, events, numbers):
    system_prompt = f"""
    ## 指示
    あなたは2025年の象徴的な出来事から有馬記念のサインを読み解き、買い目を導き出す専門AIエージェントです。 有馬記念（中山芝2500m）に特化し、2025年の象徴的な出来事から抽出されたサインをもとに、競馬初心者でも納得しながら意思決定できる形で買い目を提示してください。
    
    ## 出力フロー
    サインの評価と2025年有馬記念の出走馬にもとづいて、以下の軸に基づいて出走馬を評価し、買い目を出力する
    A. 関連性の強さ
    出来事と馬番・馬名などとの結びつきの直接性・明確さ。
    B. 複数要素との合致
    一つのサインから複数の馬番や馬名が導き出される、または複数のサインが一つの馬番を指し示すなど。
    
    ## 原則
    ・ユーザーの入力形式は自由とする 
    ・会話の中でサインの評価・理由・買い方を柔軟に提示してよいが、AIのサイン分析軸・解釈基準は常に一貫させる 
    ・結論 → 理由 → 補足 の順で説明する 
    ・専門用語は使ってよいが、必ず一言補足を添える 
    
    ## 出力形式（初回・まとめ時）
    【結論】 
    ◎本命サイン馬 (理由：2025年のどの出来事とどう関連するか、なぜ本命か)
    ○対抗サイン馬 (理由：同様)
    ▲単穴サイン馬 (理由：同様)
    ☆穴サイン馬 (理由：同様)
    ✕関連薄サイン馬 (理由：なぜ関連が薄いと判断したか)
    
    【買い方の例】 
    ・単勝：最大2点 
    ・馬連：最大3点
    ・三連複：最大6点 
    ・資金配分：安全型 / 攻め型（サインの強度に応じて）
    
    ## 禁止事項
    ・人気順のみでの評価（サイン馬券は人気薄が本命になることも多い） 
    ・内部評価軸（サイン解釈の基準）を会話によって変更すること 
    ・ユーザーの意見に迎合すること 
    ・一般的な競馬のデータ分析や馬の能力評価に偏りすぎること。あくまで「サイン」を主軸とする。"""
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": f"出来事:\n{events}\n考察:\n{numbers}"}],
        temperature=0.5, max_tokens=3000
    )
    return r.choices[0].message.content

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

    # =========================
    # タブ1: 総合予想（再実行時に前回結果を全消し）
    # =========================
    with tab1:
        st.markdown("""<div class="feature-card">
            <h3>🎯 総合予想機能</h3>
            <p>STEP1: データ傾向分析 → STEP2: 馬の選定 → STEP3: 買い目提案</p>
        </div>""", unsafe_allow_html=True)

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
                # 再実行：前回出力を全消し（UIも session_state も）
                comp["step1"] = None
                comp["step2"] = None
                comp["step3"] = None
                ph1.empty()
                ph2.empty()
                ph3.empty()

                ph1.info("📊 分析中...")
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
            eval_btn = st.button("🔍 評価スタート", key="eval_btn", use_container_width=True)

        horse_info = HORSE_LIST_2025[horse_num]
        st.markdown(f"## {horse_info['馬名']} の分析")

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
            ph_h.markdown(render_box("🐴 馬分析", saved["h"], "analysis-box box-horse"), unsafe_allow_html=True)
            ph_j.markdown(render_box("🏇 騎手分析", saved["j"], "analysis-box box-jockey"), unsafe_allow_html=True)
            ph_c.markdown(render_box("🏟️ コース分析", saved["c"], "analysis-box box-course"), unsafe_allow_html=True)
            ph_t.markdown(render_box("📊 総合評価", saved["t"], "analysis-box box-total"), unsafe_allow_html=True)

        if eval_btn:
            if client is None:
                st.error("APIキーを設定してください")
            else:
                # 機能2は押したら前回表示（その馬のUI）を一旦消す
                ph_h.empty()
                ph_j.empty()
                ph_c.empty()
                ph_t.empty()

                ph_h.info("分析中...")
                h_res = analyze_horse(client, horse_info, data)
                ph_h.markdown(render_box("🐴 馬分析", h_res, "analysis-box box-horse"), unsafe_allow_html=True)

                ph_j.info("分析中...")
                j_res = analyze_jockey(client, horse_info, data)
                ph_j.markdown(render_box("🏇 騎手分析", j_res, "analysis-box box-jockey"), unsafe_allow_html=True)

                ph_c.info("分析中...")
                c_res = analyze_course(client, horse_info, data)
                ph_c.markdown(render_box("🏟️ コース分析", c_res, "analysis-box box-course"), unsafe_allow_html=True)

                ph_t.info("統合中...")
                t_res = analyze_total(client, horse_info, h_res, j_res, c_res)
                ph_t.markdown(render_box("📊 総合評価", t_res, "analysis-box box-total"), unsafe_allow_html=True)

                st.session_state["eval_results"][horse_num] = {"h": h_res, "j": j_res, "c": c_res, "t": t_res}

    # =========================
    # タブ3: サイン理論（再実行時に前回結果を全消し）
    # =========================
    with tab3:
        st.markdown("""<div class="feature-card">
            <h3>🔮 サイン理論機能</h3>
            <p>2025年の出来事から数字を読み解く ※エンターテイメント</p>
        </div>""", unsafe_allow_html=True)

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
            ph_e.markdown(render_box("📅 2025年の出来事", sign["events"], "analysis-box box-events"), unsafe_allow_html=True)
        if sign["numbers"]:
            ph_n.markdown(render_box("🔢 サイン抽出", sign["numbers"], "analysis-box box-numbers"), unsafe_allow_html=True)
        if sign["bet"]:
            ph_b.markdown(render_box("💰 サイン理論買い目", sign["bet"], "analysis-box box-buy"), unsafe_allow_html=True)

        if sign_btn:
            if client is None:
                st.error("APIキーを設定してください")
            else:
                # 再実行：前回出力を全消し（UIも session_state も）
                sign["events"] = None
                sign["numbers"] = None
                sign["bet"] = None
                ph_e.empty()
                ph_n.empty()
                ph_b.empty()

                ph_e.info("収集中...")
                e_res = get_events_2025(client)
                sign["events"] = e_res
                ph_e.markdown(render_box("📅 2025年の出来事", e_res, "analysis-box box-events"), unsafe_allow_html=True)

                ph_n.info("抽出中...")
                n_res = extract_numbers(client, e_res)
                sign["numbers"] = n_res
                ph_n.markdown(render_box("🔢 サイン抽出", n_res, "analysis-box box-numbers"), unsafe_allow_html=True)

                ph_b.info("導出中...")
                b_res = sign_betting(client, e_res, n_res)
                sign["bet"] = b_res
                ph_b.markdown(render_box("💰 サイン理論買い目", b_res, "analysis-box box-buy"), unsafe_allow_html=True)

    # フッター
    st.markdown("---")
    st.markdown("""<div style="text-align:center;color:#999;padding:1rem;">
        ⚠️ 予想は参考情報です。馬券購入は自己責任で。<br>
        🏇 第70回 有馬記念 PREDICTOR 2025 | Powered by GPT-4o
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
