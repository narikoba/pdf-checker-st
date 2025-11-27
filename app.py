import streamlit as st
import google.generativeai as genai
import json

# ページ設定
st.set_page_config(page_title="PDF Bureau Extractor", layout="wide")

# タイトル
st.title("📄 PDF Title & Bureau Extractor")
st.write("PDFをアップロードすると、AIが情報を抽出し、Excelに貼り付けやすい形式で出力します。")

# APIキーの取得
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.warning("⚠️ APIキーが設定されていません。StreamlitのSecrets設定を確認してください。")

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
        
        # モデルの準備（gemini-2.5-flash-lite 固定）
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        
        for i, file in enumerate(uploaded_files):
            try:
                # PDFをバイトデータとして読み込む
                file_bytes = file.getvalue()
                
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
                data["fileName"] = file.name
                results.append(data)
                
            except Exception as e:
                st.error(f"エラー ({file.name}): {e}")
            
            # 進捗バー更新
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        # 結果表示
        if results:
            st.success("完了しました！以下のボックスの右上にあるコピーボタンを押して、Excelに貼り付けてください。")
            
            # Excel貼り付け用データの作成（タブ区切り）
            # 指定順序: 区分 -> 件名 -> 局名
            tsv_lines = []
            for item in results:
                line = f"{item.get('category', '')}\t{item.get('title', '')}\t{item.get('bureau', '')}"
                tsv_lines.append(line)
            
            tsv_output = "\n".join(tsv_lines)
            
            # コピー用ボックスの表示
            st.caption("Excel貼り付け用データ（区分 / 件名 / 局名）")
            st.code(tsv_output, language="text")
            
            # 念のため通常のテーブルも見やすく表示
            st.markdown("---")
            st.caption("抽出結果プレビュー")
            # テーブル表示も見やすい順序に並べ替え
            display_data = [
                {
                    "区分": item.get('category'),
                    "件名": item.get('title'),
                    "局名": item.get('bureau'),
                    "ファイル名": item.get('fileName')
                }
                for item in results
            ]
            st.dataframe(display_data, use_container_width=True)
