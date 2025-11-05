import streamlit as st
import pandas as pd
import sqlite3
import os

# 设置页面配置
st.set_page_config(
    page_title="雨刷查询系统",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"  # 侧边栏默认收起
)

# 初始化数据库
@st.cache_resource
def init_database():
    """初始化数据库"""
    try:
        excel_file_path = "wiper_data.xlsx"
        
        if not os.path.exists(excel_file_path):
            st.error("❌ 找不到数据文件")
            return None
        
        # 读取Excel数据
        df = pd.read_excel(excel_file_path)
        
        # 创建数据库连接
        conn = sqlite3.connect('wiper_system.db', check_same_thread=False)
        
        # 导入数据到SQLite
        df.to_sql('wiper_specs', conn, if_exists='replace', index=False)
        
        return conn
        
    except Exception as e:
        st.error("❌ 系统初始化失败")
        return None

# 查询函数
def search_wiper_specs(conn, search_term):
    """搜索雨刷规格"""
    try:
        # 检测列名
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(wiper_specs)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 构建查询
        if '车系' in column_names:
            query = "SELECT * FROM wiper_specs WHERE 车系 LIKE ? ORDER BY 品牌, 年款 DESC"
        elif 'model_series' in column_names:
            query = "SELECT * FROM wiper_specs WHERE model_series LIKE ? ORDER BY brand, year DESC"
        else:
            return pd.DataFrame()
        
        search_term = f"%{search_term}%"
        df_result = pd.read_sql_query(query, conn, params=[search_term])
        
        return df_result
        
    except Exception as e:
        return pd.DataFrame()

# 主页面
def main():
    """主应用"""
    
    # 页面标题
    st.title("🚗 雨刷查询系统")
    st.markdown("---")
    
    # 系统介绍
    st.markdown("""
    <div style="text-align:center;padding:20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:10px;color:white;margin-bottom:30px">
    <h2>快速查询雨刷尺寸</h2>
    <p>输入车系名称，立即获取准确的雨刷规格信息</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 搜索区域
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input(
            " ",
            placeholder="请输入车系名称，例如：高尔夫、卡罗拉...",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        search_clicked = st.button("🔍 搜索", use_container_width=True, type="primary")
    
    # 热门搜索提示
    st.caption("💡 热门搜索：高尔夫 | 卡罗拉 | 思域 | 朗逸 | 轩逸 | 雅阁 | 凯美瑞")
    
    st.markdown("---")
    
    # 初始化数据库
    conn = init_database()
    
    # 执行查询
    if search_clicked and search_term:
        if conn is None:
            st.error("系统暂不可用，请稍后重试")
        else:
            with st.spinner('搜索中...'):
                results = search_wiper_specs(conn, search_term)
                display_results(results, search_term)
    elif search_clicked and not search_term:
        st.warning("请输入车系名称")
    
    # 使用说明
    with st.expander("使用说明", expanded=False):
        st.markdown("""
        - **输入车系名称**：在搜索框中输入车辆系列名称
        - **点击搜索**：系统自动匹配相关车型
        - **查看结果**：显示雨刷尺寸和接头类型信息
        - **模糊搜索**：支持不完整名称搜索
        """)

# 结果显示函数
def display_results(df, search_term):
    """显示查询结果"""
    if df.empty:
        st.warning(f"未找到与『{search_term}』相关的记录")
        st.info("""
        💡 **建议**：
        - 检查车系名称是否正确
        - 尝试使用更简短的关键词
        - 确认车系名称的完整性
        """)
        return
    
    st.success(f"找到 {len(df)} 条与『{search_term}』相关的记录")
    
    # 显示结果
    for idx, row in df.iterrows():
        with st.container():
            # 适配中英文列名
            brand = row.get('品牌', '') or row.get('brand', '')
            model = row.get('车系', '') or row.get('model_series', '')
            year = row.get('年款', '') or row.get('year', '')
            trim = row.get('车型配置', '') or row.get('trim', '')
            
            front_driver = row.get('前雨刷主驾尺寸', '') or row.get('front_driver_size', '')
            front_passenger = row.get('前雨刷副驾尺寸', '') or row.get('front_passenger_size', '')
            rear = row.get('后雨刷尺寸', '') or row.get('rear_size', '')
            connector = row.get('接头类型', '') or row.get('connector_type', '')
            
            # 创建卡片式布局
            st.markdown(f"""
            <div style="background-color:#f8f9fa;padding:20px;border-radius:10px;border-left:4px solid #007bff;margin:10px 0">
                <h3 style="margin:0;color:#333">{brand} {model}</h3>
                <p style="margin:5px 0;color:#666">{year} | {trim}</p>
                <div style="display:flex;gap:20px;margin-top:10px">
            """, unsafe_allow_html=True)
            
            # 规格信息
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if front_driver and front_passenger:
                    st.metric("前雨刷", f"{front_driver}+{front_passenger}″")
                elif front_driver:
                    st.metric("前雨刷", f"{front_driver}″")
            
            with col2:
                if rear:
                    st.metric("后雨刷", f"{rear}″")
                else:
                    st.metric("后雨刷", "无")
            
            with col3:
                if connector:
                    st.metric("接头类型", connector)
            
            with col4:
                st.metric("序号", idx + 1)
            
            st.markdown("</div></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
