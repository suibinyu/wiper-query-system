import streamlit as st
import pandas as pd
import sqlite3
import os

# 设置页面配置
st.set_page_config(
    page_title="雨刷查询",
    page_icon="🚗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 隐藏Streamlit默认元素
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 初始化数据库
@st.cache_resource
def init_database():
    try:
        if not os.path.exists("wiper_data.xlsx"):
            st.error("数据文件未找到")
            return None
        
        df = pd.read_excel("wiper_data.xlsx")
        conn = sqlite3.connect('wiper_system.db', check_same_thread=False)
        df.to_sql('wiper_specs', conn, if_exists='replace', index=False)
        return conn
    except Exception as e:
        st.error(f"初始化失败: {e}")
        return None

# 查询函数
def search_wiper_specs(conn, search_term):
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(wiper_specs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 使用新的列名查询
        if '车型' in columns:
            query = "SELECT * FROM wiper_specs WHERE 车型 LIKE ?"
        else:
            query = "SELECT * FROM wiper_specs WHERE model LIKE ?"
        
        search_term = f"%{search_term}%"
        return pd.read_sql_query(query, conn, params=[search_term])
    except:
        return pd.DataFrame()

# 主页面
def main():
    # 简洁标题
    st.markdown("<h2 style='text-align: center;'>🚗 雨刷查询</h2>", unsafe_allow_html=True)
    
    # 搜索框
    search_term = st.text_input("", placeholder="输入车型名称，如：高尔夫")
    
    # 搜索按钮
    if st.button("查询", use_container_width=True):
        conn = init_database()
        if conn and search_term:
            results = search_wiper_specs(conn, search_term)
            display_results(results, search_term)
        elif not search_term:
            st.warning("请输入车型名称")
        else:
            st.error("系统暂不可用")

# 简洁结果显示
def display_results(df, search_term):
    if df.empty:
        st.info(f"未找到『{search_term}』相关记录")
        return
    
    st.success(f"找到 {len(df)} 条记录")
    
    for idx, row in df.iterrows():
        # 获取数据 - 使用新的列名
        brand = row.get('品牌', '')
        model = row.get('车型', '')
        year = row.get('年份', '')
        
        front_driver = row.get('主驾', '')
        front_passenger = row.get('副驾', '')
        rear = row.get('后雨刷', '')
        connector = row.get('接头', '')
        note = row.get('备注', '')
        
        # 紧凑显示
        st.markdown(f"**{brand} {model}** · {year}款")
        
        specs = []
        if front_driver and front_passenger:
            specs.append(f"主驾: {front_driver}″")
            specs.append(f"副驾: {front_passenger}″")
        elif front_driver:
            specs.append(f"雨刷: {front_driver}″")
        
        if rear and str(rear) != 'nan':
            specs.append(f"后雨刷: {rear}″")
        
        if connector and str(connector) != 'nan':
            specs.append(f"接头: {connector}")
        
        if specs:
            st.markdown(f"<small>{' | '.join(specs)}</small>", unsafe_allow_html=True)
        
        # 显示备注信息
        if note and str(note) != 'nan' and str(note) != '':
            st.markdown(f"<small>📝 {note}</small>", unsafe_allow_html=True)
        
        st.markdown("---")

if __name__ == "__main__":
    main()
