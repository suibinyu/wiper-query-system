import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# 设置页面配置
st.set_page_config(
    page_title="雨刷查询系统",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化数据库
@st.cache_resource
def init_database():
    """初始化数据库"""
    try:
        # 检查文件是否存在
        excel_file_path = "wiper_data.xlsx"
        
        if not os.path.exists(excel_file_path):
            st.error(f"❌ 找不到数据文件: {excel_file_path}")
            return None
        
        # 读取Excel数据
        df = pd.read_excel(excel_file_path)
        
        # 创建数据库连接
        conn = sqlite3.connect('wiper_system.db', check_same_thread=False)
        
        # 导入数据到SQLite
        df.to_sql('wiper_specs', conn, if_exists='replace', index=False)
        
        # 创建查询日志表
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_term TEXT,
                result_count INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        return conn
        
    except Exception as e:
        st.error(f"❌ 数据库初始化失败: {str(e)}")
        return None

# 查询函数 - 修复列名问题
def search_wiper_specs(conn, search_term):
    """搜索雨刷规格"""
    try:
        # 首先检查数据库中的实际列名
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(wiper_specs)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 根据实际列名构建查询
        if '车系' in column_names:
            # 使用中文列名
            query = "SELECT * FROM wiper_specs WHERE 车系 LIKE ? ORDER BY 品牌, 年款 DESC"
        elif 'model_series' in column_names:
            # 使用英文列名
            query = "SELECT * FROM wiper_specs WHERE model_series LIKE ? ORDER BY brand, year DESC"
        else:
            # 默认使用第一个文本列
            text_columns = [col[1] for col in columns if col[2] == 'TEXT' and col[1] != 'id']
            if text_columns:
                query = f"SELECT * FROM wiper_specs WHERE {text_columns[0]} LIKE ?"
            else:
                st.error("找不到合适的查询列")
                return pd.DataFrame()
        
        search_term = f"%{search_term}%"
        df_result = pd.read_sql_query(query, conn, params=[search_term])
        
        # 记录查询日志
        if search_term != "%%":
            cursor.execute(
                "INSERT INTO query_logs (search_term, result_count) VALUES (?, ?)",
                (search_term.replace('%', ''), len(df_result))
            )
            conn.commit()
        
        return df_result
        
    except Exception as e:
        st.error(f"查询失败: {e}")
        return pd.DataFrame()

# 数据显示函数 - 适配中英文列名
def display_results(df):
    """显示查询结果"""
    if df.empty:
        st.warning("🚫 未找到匹配记录")
        st.info("💡 提示：尝试输入完整的车系名称，如'高尔夫'、'卡罗拉'等")
        return
    
    st.success(f"✅ 找到 {len(df)} 条匹配记录")
    
    # 显示列名信息（调试用）
    with st.expander("🔧 调试信息（点击查看）"):
        st.write("数据列名:", list(df.columns))
        st.write("前5行数据:", df.head())
    
    for idx, row in df.iterrows():
        with st.container():
            st.markdown("---")
            
            # 适配中英文列名
            brand = row.get('品牌', '') or row.get('brand', '')
            model = row.get('车系', '') or row.get('model_series', '')
            year = row.get('年款', '') or row.get('year', '')
            trim = row.get('车型配置', '') or row.get('trim', '')
            
            # 主标题
            st.subheader(f"🚗 {brand} {model}")
            
            # 基本信息
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**年款**: {year}")
            with col2:
                st.write(f"**配置**: {trim}")
            
            # 雨刷规格信息
            front_driver = row.get('前雨刷主驾尺寸', '') or row.get('front_driver_size', '')
            front_passenger = row.get('前雨刷副驾尺寸', '') or row.get('front_passenger_size', '')
            rear = row.get('后雨刷尺寸', '') or row.get('rear_size', '')
            connector = row.get('接头类型', '') or row.get('connector_type', '')
            
            st.write("### 雨刷规格")
            
            spec_col1, spec_col2, spec_col3, spec_col4 = st.columns(4)
            
            with spec_col1:
                if front_driver and front_passenger:
                    st.metric("前雨刷尺寸", f"{front_driver}+{front_passenger}英寸")
                elif front_driver:
                    st.metric("前雨刷尺寸", f"{front_driver}英寸")
                else:
                    st.metric("前雨刷尺寸", "未知")
            
            with spec_col2:
                if rear:
                    st.metric("后雨刷尺寸", f"{rear}英寸")
                else:
                    st.metric("后雨刷尺寸", "无")
            
            with spec_col3:
                if connector:
                    st.metric("接头类型", connector)
                else:
                    st.metric("接头类型", "未知")
            
            with spec_col4:
                st.metric("记录编号", idx + 1)

# 前台查询页面
def frontend_page(conn):
    """前台查询界面"""
    # 页面标题和介绍
    st.title("🚗 雨刷查询系统")
    st.markdown("---")
    
    # 系统介绍
    st.markdown("""
    <div style="background-color:#f0f2f6;padding:20px;border-radius:10px;margin-bottom:20px">
    <h3 style="color:#1f77b4">欢迎使用雨刷查询系统</h3>
    <p>快速查询车辆雨刷尺寸和接头类型，支持模糊搜索。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 搜索区域
    st.header("🔍 查询雨刷规格")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_term = st.text_input(
            "输入车系名称",
            placeholder="例如：高尔夫、卡罗拉、思域...",
            help="输入车辆系列名称进行查询，支持模糊匹配"
        )
    
    with col2:
        st.markdown("###")  # 垂直间距
        search_clicked = st.button("🔍 搜索", use_container_width=True, type="primary")
    
    with col3:
        st.markdown("###")  # 垂直间距
        if st.button("🔄 重置", use_container_width=True):
            st.rerun()
    
    # 热门搜索提示
    st.info("💡 **热门车系**: 高尔夫 | 卡罗拉 | 思域 | 朗逸 | 轩逸 | 雅阁 | 凯美瑞")
    
    # 执行查询
    if search_clicked:
        if search_term:
            with st.spinner('🔍 正在搜索中，请稍候...'):
                results = search_wiper_specs(conn, search_term)
                display_results(results)
        else:
            st.warning("⚠️ 请输入车系名称")
    
    # 使用说明
    with st.expander("📖 使用说明", expanded=True):
        st.markdown("""
        ### 如何使用本系统
        
        1. **输入车系名称**: 在搜索框中输入您要查询的车辆系列名称
        2. **点击搜索**: 系统会自动匹配相关车型信息
        3. **查看结果**: 系统会显示匹配的车型及其雨刷规格
        
        ### 搜索技巧
        - 支持模糊搜索：输入"高尔夫"可匹配所有高尔夫车型
        - 不需要输入完整名称：输入"卡罗"也能找到卡罗拉
        - 不区分大小写：输入"golf"或"GOLF"效果相同
        
        ### 显示信息说明
        - **前雨刷尺寸**: 主驾驶+副驾驶雨刷长度（英寸）
        - **后雨刷尺寸**: 后窗雨刷长度（英寸）
        - **接头类型**: 雨刷臂连接接口类型
        """)
    
    # 功能特点
    st.markdown("---")
    st.subheader("✨ 系统特点")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align:center;padding:10px">
        <h3>🔍 快速查询</h3>
        <p>输入车系名称，秒级返回结果</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:10px">
        <h3>📊 数据准确</h3>
        <p>基于真实车型数据，结果可靠</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align:center;padding:10px">
        <h3>📱 响应式设计</h3>
        <p>支持电脑、平板、手机访问</p>
        </div>
        """, unsafe_allow_html=True)

# 主应用
def main():
    """主应用"""
    # 初始化会话状态
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    
    # 侧边栏
    with st.sidebar:
        st.title("🚗 雨刷查询系统")
        st.markdown("---")
        
        st.subheader("系统状态")
        if st.session_state.initialized:
            st.success("✅ 系统已就绪")
        else:
            st.warning("🔄 系统初始化中...")
        
        st.markdown("---")
        st.subheader("快捷操作")
        
        if st.button("🔄 重新初始化系统"):
            st.cache_resource.clear()
            st.session_state.initialized = False
            st.rerun()
        
        st.markdown("---")
        st.subheader("关于")
        st.markdown("""
        - **版本**: v1.0
        - **更新**: {}
        - **数据量**: 自动加载
        """.format(datetime.now().strftime('%Y-%m-%d')))
    
    # 主内容区域
    try:
        # 初始化数据库
        if not st.session_state.initialized:
            with st.spinner('🔄 系统初始化中，请稍候...'):
                conn = init_database()
                
                if conn is not None:
                    st.session_state.conn = conn
                    st.session_state.initialized = True
                    st.success("✅ 系统初始化完成！")
                    st.rerun()
                else:
                    st.error("❌ 系统初始化失败")
                    return
        
        # 显示前台查询页面
        frontend_page(st.session_state.conn)
        
    except Exception as e:
        st.error(f"❌ 系统运行出错: {str(e)}")
        st.info("""
        **故障排除建议:**
        1. 检查数据文件是否存在
        2. 确认数据文件格式正确
        3. 点击侧边栏的"重新初始化系统"
        4. 如问题持续，请联系技术支持
        """)

if __name__ == "__main__":
    main()
