import streamlit as st
import google.generativeai as genai
import json
import os

# ページ設定
st.set_page_config(page_title="PDF Bureau Extractor", layout="wide")

# タイトル
st.title("📄 PDF Title & Bureau Extractor")
st.write("PDFをアップロードすると、AIが「局名」と「分類」を自動抽出します。")

# APIキーの取得（StreamlitのSecretsから読み込む）
# ※まだ設定していないので、エラーが出ても気にしないでください
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.warning("⚠️ APIキーが設定されていません。後でStreamlitの管理画面で設定します。")

# 定数リスト
VALID_BUREAUS = [
  "政策企画局", "子供政策連携室", "総務局", "財務局", "デジタルサービス局", "主税局", "生活文化局", 
  "都民安全総合対策本部", "スポーツ推進本部", "都市整備局", "住宅政策本部", "環境局", "福祉局", 
  "保健医療局", "産業労働局", "中央卸売市場", "スタートアップ戦略推進本部", "建設局", "港湾局", 
  "会計管理局", "交通局", "水道局", "下水道局", "教育庁", "選挙管理委員会事務局", "人事委員会事務局", 
  "監査事務局", "労働委員会事務局", "収用委員会事務局", "警視庁", "東京消防庁"
]

VALID_CATEGORIES = [
  "答申･報告･調査結果", "事業、計画", "会議等", "募集", "ｲﾍﾞﾝﾄ･講演", "事件･事故･処分",
  "動物", "人事･訃報･表彰", "資料", "ｺﾒﾝﾄ･声明･談話", "選挙関係", "入試関係",
  "広報紙・ﾊﾟﾝﾌﾚｯﾄ・定期刊行物", "統計", "議会", "報道官", "取材案内",
  "デフリンピック・世界陸上", "その他", "災害関係"
]

# AIへの指示プロンプト
PROMPT = f"""
添付された文書画像から、以下の情報をJSON形式で抽出してください。
1. bureau: 文書を発行した局名（通常右上に記載）。リストから選択: {', '.join(VALID_BUREAUS)}
2. category: 件名から推測される分類。リストから選択: {', '.join(VALID_CATEGORIES)}
3. title: 文書の件名（「件名：」などのプレフィックスは除く）

出力は以下のJSON形式のみにしてください：
{{ "bureau": "...", "category": "...", "title": "..." }}
"""

# ファイルアップロード
uploaded_files = st.file_uploader("PDFファイルをここにドラッグ＆ドロップ", type="pdf", accept_multiple_files=True)

if uploaded_files:
    if st.button("抽出開始"):
        results = []
        progress_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            try:
                # PDFをバイトデータとして読み込む
                file_bytes = file.getvalue()
                
                # Geminiモデルの準備（FlashモデルはPDFを直接読めます）
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                # AIに送信
                response = model.generate_content([
                    PROMPT,
                    {"mime_type": "application/pdf", "data": file_bytes}
                ])
                
                # JSON部分を探して抽出
                text = response.text
                json_str = text.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                
                data = json.loads(json_str)
                data["fileName"] = file.name # ファイル名も追加
                results.append(data)
                
            except Exception as e:
                st.error(f"エラー ({file.name}): {e}")
            
            # 進捗バー更新
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        # 結果表示
        if results:
            st.success("完了しました！")
            st.dataframe(results, use_container_width=True)
