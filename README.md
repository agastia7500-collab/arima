# 🏇 有馬記念予想アプリ 2025

第70回有馬記念（2025年12月28日）の予想アプリです。AI（GPT-4o）を活用して、データ分析・単体評価・サイン理論の3つの機能で予想をサポートします。

GitHub × Streamlit Cloud で簡単にデプロイできます。

![Preview](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)

## ✨ 機能

### 🎯 機能①: 総合予想
- 出走馬データを総合的に分析
- **出力:** ◎本命、○対抗、▲単穴、☆穴馬、✕危険馬
- 推奨買い目（馬連・三連複・三連単・ワイド）
- Excelで予想データをアップロード可能

### 🔍 機能②: 単体評価
- 指定した馬番の馬を多角的に分析
- **STEP 1:** 馬分析（能力・血統・実績）
- **STEP 2:** 騎手分析（技量・コース相性）
- **STEP 3:** コース適性分析（中山2500m適性）
- **STEP 4:** 統合評価

### 🔮 機能③: サイン理論
- 2024-2025年の出来事から数字を読み解く
- スポーツ・政治・芸能などの話題を分析
- 数字を馬番・枠番に紐付け
- エンターテイメントとしての予想

## 🚀 セットアップ

### 必要なもの
- GitHubアカウント
- Streamlit Cloudアカウント
- OpenAI APIキー

### 手順

#### 1. リポジトリをフォーク/クローン
```bash
git clone https://github.com/yourusername/arima-predictor.git
cd arima-predictor
```

#### 2. GitHubにプッシュ
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

#### 3. Streamlit Cloud でデプロイ
1. [Streamlit Cloud](https://share.streamlit.io/) にアクセス
2. 「New app」をクリック
3. GitHubリポジトリを選択
4. Main file path: `app.py` を指定
5. 「Advanced settings」→「Secrets」に以下を追加:
   ```toml
   OPENAI_API_KEY = "sk-your-api-key-here"
   ```
6. 「Deploy!」をクリック

## 📁 ファイル構成

```
arima-predictor/
├── app.py                    # メインアプリケーション
├── requirements.txt          # 依存パッケージ
├── .gitignore               # Git除外設定
├── README.md                # このファイル
├── .streamlit/
│   ├── config.toml          # Streamlit設定
│   └── secrets.toml.example # シークレット設定例
└── data/
    └── arima_data.xlsx      # 予想データ（オプション）
```

## 📊 予想データ形式

Excelファイル（`.xlsx`）で以下の列を含めてください：

| 列名 | 説明 | 例 |
|------|------|-----|
| 馬番 | 馬番号 | 1 |
| 馬名 | 馬の名前 | ドウデュース |
| 性齢 | 性別と年齢 | 牡5 |
| 騎手 | 騎手名 | 武豊 |
| 調教師 | 調教師名 | 友道康夫 |
| 前走 | 前走成績 | 天皇賞秋1着 |
| オッズ | 単勝オッズ | 3.5 |

## ⚙️ カスタマイズ

### システムプロンプトの変更
`app.py` 内の以下の関数でシステムプロンプトを変更できます：
- `comprehensive_prediction()` - 総合予想のプロンプト
- `individual_evaluation()` - 単体評価のプロンプト
- `sign_theory_prediction()` - サイン理論のプロンプト

### UIのカスタマイズ
`app.py` 内の `<style>` タグでCSSを変更できます。

## ⚠️ 注意事項

- 本アプリの予想は参考情報です
- 馬券購入は自己責任でお願いします
- サイン理論はエンターテイメントとしてお楽しみください
- APIキーは絶対にGitHubにコミットしないでください

## 📝 ライセンス

MIT License

## 🙏 謝辞

- [Streamlit](https://streamlit.io/)
- [OpenAI](https://openai.com/)
