import streamlit as st
import pandas as pd
import sqlite3
import os

# 隐藏Streamlit的默认菜单和按钮
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 设置页面配置
st.set_page_config(
    page_title="雨刷查询",
    page_icon="🔧",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# 初始化数据库
@st.cache_resource
def init_database():
    try:
        if not os.path.exists("wiper_data.xlsx"):
            return None
        df = pd.read_excel("wiper_data.xlsx")
        conn = sqlite3.connect('wiper_system.db', check_same_thread=False)
        df.to_sql('wiper_specs', conn, if_exists='replace', index=False)
        return conn
    except:
        return None

# 查询函数
def search_wiper_specs(conn, search_term):
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(wiper_specs)")
        columns = [col[1] for col in cursor.fetchall()]
        if '车系' in columns:
            query = "SELECT * FROM wiper_specs WHERE 车系 LIKE ?"
        else:
            query = "SELECT * FROM wiper_specs WHERE model_series LIKE ?"
        search_term = f"%{search_term}%"
        return pd.read_sql_query(query, conn, params=[search_term])
    except:
        return pd.DataFrame()

# 主页面
def main():
    # 布局
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.image(
            "https://5b0988e595225.cdn.sohucs.com/images/20190628/c3887e7c8841462bb0e6e27bf3c84062.jpeg",
            width=40
        )
    
    with col2:
        st.markdown("<h2 style='margin-top: 8px;'>雨刷查询</h2>", unsafe_allow_html=True)
    
    # 搜索功能
    search_term = st.text_input("", placeholder="输入车系名称，如：高尔夫")
    
    if st.button("查询", use_container_width=True):
        conn = init_database()
        if conn and search_term:
            results = search_wiper_specs(conn, search_term)
            display_results(results, search_term)
        elif not search_term:
            st.warning("请输入车系名称")
        else:
            st.error("系统暂不可用")

def display_results(df, search_term):
    if df.empty:
        st.info(f"未找到『{search_term}』相关记录")
        return
    st.success(f"找到 {len(df)} 条记录")
    
    for idx, row in df.iterrows():
        brand = row.get('品牌', '') or row.get('brand', '')
        model = row.get('车系', '') or row.get('model_series', '')
        year = row.get('年款', '') or row.get('year', '')
        
        front_driver = row.get('前雨刷主驾尺寸', '') or row.get('front_driver_size', '')
        front_passenger = row.get('前雨刷副驾尺寸', '') or row.get('front_passenger_size', '')
        rear = row.get('后雨刷尺寸', '') or row.get('rear_size', '')
        connector = row.get('接头类型', '') or row.get('connector_type', '')
        
        st.markdown(f"**{brand} {model}** · {year}")
        
        specs = []
        if front_driver and front_passenger:
            specs.append(f"前: {front_driver}+{front_passenger}″")
        elif front_driver:
            specs.append(f"前: {front_driver}″")
        if rear:
            specs.append(f"后: {rear}″")
        if connector:
            specs.append(f"接头: {connector}")
        
        if specs:
            st.markdown(f"<small>{' | '.join(specs)}</small>", unsafe_allow_html=True)
        st.markdown("---")

if __name__ == "__main__":
    main()
