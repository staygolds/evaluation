
import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- 設定 ---
st.set_page_config(page_title="ベテラン管理者AI(Gemini版)：職員評価分析", layout="wide")

# Gemini APIキーの設定
# 直接入力するか、環境変数から取得するようにしてください
# genai.configure(api_key="YOUR_GEMINI_API_KEY")

# サイドバーでのAPIキー入力
with st.sidebar:
    api_key_for_app = st.text_input("Gemini API Keyを入力してください", type="password")
    if api_key_for_app:
        genai.configure(api_key=api_key_for_app)

# --- 職務分掌と評価データの入力 --- (動的な入力に変更)
st.title("🛡️ ベテラン管理者AI：Gemini分析システム")
st.caption("職員情報とコンピテンシー評価を直接入力し、経営的視点からアドバイスを生成します。")

# 職員情報の入力
st.sidebar.subheader("職員情報入力")
target_name_for_app = st.sidebar.text_input("職員名", "木暮　光広")
jd_役職 = st.sidebar.text_input("役職", "主任看護師")
jd_重点ミッション = st.sidebar.text_area("重点ミッション", "徹底した健康管理により重度化・欠員を防止し施設入所稼働率を維持。口腔ケアや機能訓練の充実による高い支援品質の提供。短期入所の利用促進（稼働率25.5%からの向上）。", height=100)
jd_具体的職務 = st.sidebar.text_area("具体的職務", "医務日誌整備、服薬管理、口腔ケア、協力医療機関との連携、第1種衛生管理責任者、保健部会担当", height=100)

# 職務分掌データを辞書にまとめる
jd_for_app = {
    "役職": jd_役職,
    "重点ミッション": jd_重点ミッション,
    "具体的職務": jd_具体的職務
}

# 評価項目と評価点の動的入力
st.sidebar.subheader("評価項目と評価点")

# セッションステートで評価項目を管理
if 'eval_items' not in st.session_state:
    st.session_state.eval_items = []

new_item_desc = st.sidebar.text_input("新しい評価項目（具体的行動）")
new_item_score = st.sidebar.number_input("評価点 (1-5)", min_value=1, max_value=5, value=3)

if st.sidebar.button("評価項目を追加"):
    if new_item_desc and new_item_score:
        st.session_state.eval_items.append({"評価項目（具体的行動）": new_item_desc, "評価点 (1-5)": float(new_item_score)})
        st.sidebar.success("評価項目を追加しました。")
    else:
        st.sidebar.error("評価項目と評価点を入力してください。")

# 既存の評価項目を表示・編集
if st.session_state.eval_items:
    st.sidebar.markdown("--- 現在の評価項目 ---")
    eval_df_display = pd.DataFrame(st.session_state.eval_items)
    st.sidebar.dataframe(eval_df_display, use_container_width=True, hide_index=True)

    # 評価項目をクリアするボタン
    if st.sidebar.button("すべての評価項目をクリア"):
        st.session_state.eval_items = []
        st.sidebar.info("すべての評価項目をクリアしました。")


col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"📋 職務分掌の確認: {target_name_for_app}")
    st.info(f"**期待される役割**: {jd_for_app['役職']}")
    st.markdown(f"""**重点目標**:
{jd_for_app['重点ミッション']}""")
    st.markdown(f"""**具体的職務**:
{jd_for_app['具体的職務']}""")

    st.subheader("📊 評価スコア一覧")
    if st.session_state.eval_items:
        st.dataframe(pd.DataFrame(st.session_state.eval_items), use_container_width=True, hide_index=True)
    else:
        st.info("サイドバーから評価項目と評価点を追加してください。")

with col2:
    st.subheader("🧠 Gemini ベテラン管理者分析")

    if st.button("AI分析を開始"):
        if not api_key_for_app:
            st.error("APIキーを入力してください。")
        elif not st.session_state.eval_items:
            st.error("評価項目と評価点を入力してください。")
        else:
            with st.spinner("ベテラン管理者が思考中..."):
                # 分析用のプロンプト構築
                eval_text_for_app = ""
                for item in st.session_state.eval_items:
                    eval_text_for_app += "- {}: {}点\n".format(item['評価項目（具体的行動）'], item['評価点 (1-5)'])

                prompt_for_app = f"""
                あなたは障害者支援施設の「ベテラン施設長（経営歴30年）」です。
                部下の「職務分掌（期待される役割）」と「実際の評価結果」を突き合わせ、深い洞察を行ってください。

                【対象職員】: {target_name_for_app}
                【役職】: {jd_for_app['役職']}
                【この職員に課された経営目標】: {jd_for_app['重点ミッション']}

                【今回のコンピテンシー評価結果】:
                {eval_text_for_app}

                上記を踏まえ、以下の4項目について、プロの経営者として日本語で回答してください。
                1. 【強みの連結】: 評価点が高い項目が、経営目標（稼働率向上やコスト抑制等）にどう貢献しているか。
                2. 【懸念される乖離】: 目標達成のために不可欠なのに、評価点が伸び悩んでいる項目（ボトルネック）の指摘。
                3. 【具体的指導案】: 現場での行動をどう変えさせるべきか、ベテランらしい具体的な助言。
                4. 【面談のキラーフレーズ】: 本人のモチベーションを高めつつ、核心を突くための最初の一言。
                """

                # Geminiモデルの初期化
                model = genai.GenerativeModel('gemini-flash-latest')

                try:
                    response_for_app = model.generate_content(prompt_for_app)
                    st.success("分析完了")
                    st.markdown(response_for_app.text)
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
