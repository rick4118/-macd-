%%writefile app.py
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import re

# 設定網頁標題與排版
st.set_page_config(page_title="日 MACD 翻紅篩選器", layout="wide")
st.title("📈 台灣股票 - 日 MACD 剛翻紅篩選器")
st.markdown("本工具協助篩選出在指定結束日時，日線 MACD 柱狀體（OSC）剛好**由綠翻紅（黃金交叉）**的股票。")

def compute_macd(df, fast=12, slow=26, signal=9):
    df['EMA_fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
    df['EMA_slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
    df['DIF'] = df['EMA_fast'] - df['EMA_slow']
    df['MACD'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    df['OSC'] = df['DIF'] - df['MACD']
    return df

def find_macd_crossover_stocks_daily(ticker_list, start_date, end_date):
    result = []
    download_start = (pd.to_datetime(start_date) - pd.Timedelta(days=90)).strftime('%Y-%m-%d')
    
    # 使用 Streamlit 的進度條與狀態提示
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_tickers = len(ticker_list)

    for i, ticker in enumerate(ticker_list):
        status_text.text(f"正在分析 ({i+1}/{total_tickers}): {ticker} ...")
        progress_bar.progress((i + 1) / total_tickers)
        try:
            df = yf.download(ticker, start=download_start, end=end_date, interval="1d", group_by="column", auto_adjust=True, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if df.empty:
                continue

            df = compute_macd(df)
            df_filtered = df[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]
            if len(df_filtered) < 3:
                continue
            recent = df_filtered.iloc[-3:].copy()

            osc_val = recent['OSC'].values.flatten()

            # 判斷前一日 OSC <= 0 且最新一日 OSC > 0
            if osc_val[-2] <= 0 and osc_val[-1] > 0:
                result.append(ticker)
        except Exception as e:
            pass
            
    status_text.text("分析完成！")
    progress_bar.empty()
    return result

# 側邊欄：參數設定
st.sidebar.header("⚙️ 參數設定")

# 預設股票清單
default_tickers = [
    '1308.TW', '1312A.TW', '1440.TW', '1605.TW', '2030.TW', '2032.TW', '2049.TW', '2069.TW', 
    '2301.TW', '2455.TW', '2461.TW', '2605.TW', '2606.TW', '3003.TW', '3017.TW', '3066.TWO', 
    '3081.TWO', '3141.TWO', '3176.TWO', '3229.TW', '3324.TWO', '3363.TWO', '3416.TW', '3490.TWO', 
    '3504.TW', '3605.TW', '3631.TWO', '3653.TW', '3693.TWO', '4167.TWO', '4771.TW', '4905.TWO', 
    '4912.TW', '5351.TWO', '6108.TW', '6133.TW', '6152.TW', '6187.TWO', '6218.TWO', '6225.TW', 
    '6419.TWO', '6654.TWO', '6716.TWO', '6782.TW', '6840.TWO', '6949.TW', '7714.TWO', '7744.TWO', 
    '8033.TW', '8354.TWO', '8436.TWO', '8942.TWO'
]

tickers_input = st.sidebar.text_area(
    "輸入或貼上股票代號 (以逗號、空格或換行分隔)", 
    value=", ".join(default_tickers),
    height=250
)

# 解析輸入的股票清單（支援多種分隔符號：逗號、空白、換行）
tickers = [t.strip() for t in re.split(r'[\s,\n\r]+', tickers_input) if t.strip()]

# 日期選擇器
start_date = st.sidebar.date_input("開始日期", value=datetime(2025, 11, 1))
end_date = st.sidebar.date_input("結束日期（以該日判斷是否翻紅）", value=datetime(2026, 9, 23))

# 執行按鈕
if st.sidebar.button("🚀 開始篩選", use_container_width=True):
    if not tickers:
        st.warning("請輸入至少一個股票代號。")
    elif start_date >= end_date:
        st.error("開始日期必須早於結束日期。")
    else:
        with st.spinner("正在抓取歷史股價並計算 MACD..."):
            selected_stocks = find_macd_crossover_stocks_daily(
                tickers,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
        
        # 呈現結果
        st.subheader("📊 篩選結果")
        if selected_stocks:
            st.success(f"篩選完成！共找到 {len(selected_stocks)} 檔符合條件的股票。")
            
            # 一鍵複製區塊 1：代碼區塊 (點擊右上角按鈕即可一鍵複製)
            comma_separated_text = ", ".join(selected_stocks)
            st.write("**📋 一鍵複製 (請點選下方框框右上角的複製圖示)：**")
            st.code(comma_separated_text, language="text")

            # 一鍵複製區塊 2：以文字框 (Text Area) 方式顯示
            st.text_area(
                "文字框呈現（可自由手動選取複製）",
                value="\n".join(selected_stocks),
                height=150
            )
        else:
            st.info("在指定的日期區間與最後交易日中，沒有找到剛好日 MACD 翻紅的股票。")
