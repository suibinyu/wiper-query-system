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

# 简化的查询函数 - 只搜索车型字段
def search_wiper_specs(conn, search_term):
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(wiper_specs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 只搜索车型字段
        if '车型' in columns:
            query = "SELECT * FROM wiper_specs WHERE 车型 LIKE ? ORDER BY 品牌, 年份 DESC"
        else:
            query = "SELECT * FROM wiper_specs WHERE model LIKE ? ORDER BY brand, year DESC"
        
        search_pattern = f"%{search_term}%"
        df_result = pd.read_sql_query(query, conn, params=[search_pattern])
        return df_result
        
    except Exception as e:
        st.error(f"查询失败: {e}")
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
            # 提取纯车型关键词（移除品牌信息）
            clean_search_term = extract_model_keyword(search_term)
            results = search_wiper_specs(conn, clean_search_term)
            display_results(results, clean_search_term)
        elif not search_term:
            st.warning("请输入车型名称")
        else:
            st.error("系统暂不可用")

# 提取纯车型关键词的函数
def extract_model_keyword(search_term):
    """从搜索词中提取纯车型关键词"""
    # 常见的汽车品牌列表
    common_brands = [
        '大众', '丰田', '本田', '日产', '宝马', '奔驰', '奥迪', '现代', 
        '起亚', '福特', '雪佛兰', '别克', '标致', '雪铁龙', '马自达',
        '斯巴鲁', '三菱', '铃木', '沃尔沃', '雷克萨斯', '英菲尼迪',
        '讴歌', '凯迪拉克', '林肯', '捷豹', '路虎', '保时捷', '法拉利',
        '兰博基尼', '玛莎拉蒂', '特斯拉', '蔚来', '理想', '小鹏', '比亚迪'
    ]
    
    # 移除品牌信息
    clean_term = search_term
    for brand in common_brands:
        if brand in clean_term:
            clean_term = clean_term.replace(brand, '')
    
    # 移除可能的多余空格和符号
    clean_term = clean_term.strip().replace(' ', '').replace('·', '')
    
    # 如果移除品牌后为空，则使用原词
    if not clean_term:
        return search_term
    
    return clean_term

# 简洁结果显示
def display_results(df, search_term):
    if df.empty:
        st.info(f"未找到『{search_term}』相关记录")
        st.markdown("""
        💡 **搜索提示**：
        - 请输入车型名称，如："高尔夫"
        - 支持模糊搜索，输入"高尔"也能找到高尔夫
        """)
        return
    
    st.success(f"找到 {len(df)} 条记录")
    
    for idx, row in df.iterrows():
        # 获取数据 - 使用新的列名
        brand = row.get('品牌', '')
        model = row.get('车型', '')
        year = row.get('年份', '')
        
        front_driver = row.get('主驾', '')
        front_passenger = row.get('副驾', '')
        connector = row.get('接头', '')
        rear = row.get('后雨刷', '')
        note = row.get('备注', '')
        
        # 紧凑显示
        st.markdown(f"**{brand} {model}** · {year}款")
        
        specs = []
        if front_driver and front_passenger:
            specs.append(f"主驾: {front_driver}″")
            specs.append(f"副驾: {front_passenger}″")
        elif front_driver:
            specs.append(f"雨刷: {front_driver}″")
        
        # 接头信息排在前面
        if connector and str(connector) != 'nan':
            specs.append(f"接头: {connector}")
        
        # 后雨刷信息排在后面
        if rear and str(rear) != 'nan':
            specs.append(f"后雨刷: {rear}″")
        
        if specs:
            st.markdown(f"<small>{' | '.join(specs)}</small>", unsafe_allow_html=True)
        
        # 显示备注信息
        if note and str(note) != 'nan' and str(note) != '':
            st.markdown(f"<small>📝 {note}</small>", unsafe_allow_html=True)
        
        st.markdown("---")

if __name__ == "__main__":
    main()

