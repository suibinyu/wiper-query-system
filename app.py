import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import base64

# 设置页面配置
st.set_page_config(
    page_title="雨刷查询系统",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化数据库 - 修复文件路径问题
@st.cache_resource
def init_database():
    """初始化数据库"""
    try:
        # 在 Streamlit Cloud 中，文件路径需要特殊处理
        excel_file_path = "wiper_data.xlsx"
        
        # 检查文件是否存在
        if not os.path.exists(excel_file_path):
            st.error(f"❌ 找不到数据文件: {excel_file_path}")
            st.info("请确保 wiper_data.xlsx 文件已上传到 GitHub 仓库的根目录")
            
            # 显示当前目录的文件列表，帮助调试
            st.write("当前目录文件列表:")
            current_files = []
            for root, dirs, files in os.walk('.'):
                for file in files:
                    current_files.append(os.path.join(root, file))
            st.write(current_files)
            
            return None
        
        # 读取Excel数据
        st.info("正在读取Excel文件...")
        df = pd.read_excel(excel_file_path)
        st.success(f"✅ 成功读取Excel文件，共 {len(df)} 条记录")
        
        # 显示列名确认
        st.write("数据列名:", list(df.columns))
        
        # 创建数据库连接
        conn = sqlite3.connect('wiper_system.db', check_same_thread=False)
        
        # 导入数据到SQLite
        st.info("正在导入数据到数据库...")
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
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model ON wiper_specs(车系)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON query_logs(timestamp)")
        
        conn.commit()
        st.success("✅ 数据库初始化完成!")
        
        # 显示数据预览
        st.subheader("数据预览")
        st.dataframe(df.head(5), use_container_width=True)
        
        return conn
        
    except Exception as e:
        st.error(f"❌ 数据库初始化失败: {str(e)}")
        return None

# 查询函数
def search_wiper_specs(conn, search_term):
    """搜索雨刷规格"""
    try:
        query = """
        SELECT * FROM wiper_specs 
        WHERE 车系 LIKE ? 
        ORDER BY 品牌, 年款 DESC
        """
        search_term = f"%{search_term}%"
        df_result = pd.read_sql_query(query, conn, params=[search_term])
        
        # 记录查询日志
        if search_term != "%%":  # 不记录空查询
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO query_logs (search_term, result_count) VALUES (?, ?)",
                (search_term.replace('%', ''), len(df_result))
            )
            conn.commit()
        
        return df_result
    except Exception as e:
        st.error(f"查询失败: {e}")
        return pd.DataFrame()

# 密码验证函数
def check_admin_password():
    """检查管理员密码"""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    # 从环境变量获取密码，如果没有则使用默认密码
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    if not st.session_state.admin_authenticated:
        st.sidebar.title("🔐 管理员登录")
        password = st.sidebar.text_input("管理员密码:", type="password")
        
        if st.sidebar.button("登录"):
            if password == admin_password:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.sidebar.error("密码错误!")
        return False
    return True

# 前台查询页面
def frontend_page(conn):
    """前台查询界面"""
    st.title("🚗 雨刷查询系统")
    st.markdown("---")
    
    # 搜索框
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input(
            "输入车系名称查询",
            placeholder="例如：高尔夫、卡罗拉...",
            help="输入车辆系列名称进行查询"
        )
    
    with col2:
        st.markdown("###")
        search_clicked = st.button("🔍 搜索", use_container_width=True)
    
    # 执行查询
    if search_clicked and search_term:
        with st.spinner('搜索中...'):
            results = search_wiper_specs(conn, search_term)
            display_results(results, False)
    elif search_clicked and not search_term:
        st.warning("请输入车系名称")
    
    # 使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        - 在搜索框中输入车系名称（如：高尔夫、卡罗拉）
        - 系统会自动匹配相关车型
        - 查看显示的雨刷规格信息
        - 支持模糊搜索，输入部分名称即可
        """)

# 数据显示函数
def display_results(df, is_admin=False):
    """显示查询结果"""
    if df.empty:
        st.warning("未找到匹配记录")
        return
    
    st.success(f"找到 {len(df)} 条匹配记录")
    
    for idx, row in df.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"{row.get('品牌', '')} {row.get('车系', '')}")
                st.write(f"**年款**: {row.get('年款', '')} | **配置**: {row.get('车型配置', '')}")
                
                # 显示雨刷规格
                front_driver = row.get('前雨刷主驾尺寸', '')
                front_passenger = row.get('前雨刷副驾尺寸', '')
                rear = row.get('后雨刷尺寸', '')
                connector = row.get('接头类型', '')
                
                specs_text = ""
                if front_driver and front_passenger:
                    specs_text += f"**前雨刷**: {front_driver}+{front_passenger}英寸  "
                elif front_driver:
                    specs_text += f"**前雨刷**: {front_driver}英寸  "
                    
                if rear:
                    specs_text += f"**后雨刷**: {rear}英寸  "
                    
                if connector:
                    specs_text += f"**接头类型**: {connector}"
                
                if specs_text:
                    st.markdown(specs_text)
            
            st.markdown("---")

# 后台管理功能函数
def show_data_overview(conn, df):
    """显示数据概览"""
    st.header("📊 数据概览")
    
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总记录数", len(df))
        
        with col2:
            brand_count = df['品牌'].nunique()
            st.metric("品牌数量", brand_count)
        
        with col3:
            model_count = df['车系'].nunique()
            st.metric("车系数量", model_count)
        
        with col4:
            complete_records = len(df[df['前雨刷主驾尺寸'].notna()])
            st.metric("完整记录", f"{complete_records}/{len(df)}")
        
        # 显示数据表格预览
        st.subheader("数据预览")
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.warning("数据库中没有数据")

def show_usage_stats(conn):
    """显示使用统计"""
    st.header("📈 使用统计")
    
    try:
        logs_df = pd.read_sql_query("SELECT * FROM query_logs ORDER BY timestamp DESC LIMIT 1000", conn)
        
        if not logs_df.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("总查询次数", len(logs_df))
            
            with col2:
                unique_searches = logs_df['search_term'].nunique()
                st.metric("唯一查询词", unique_searches)
            
            with col3:
                no_result_queries = len(logs_df[logs_df['result_count'] == 0])
                st.metric("无结果查询", no_result_queries)
            
            # 显示最近查询
            st.subheader("最近查询记录")
            st.dataframe(logs_df.head(20), use_container_width=True)
        else:
            st.info("暂无查询日志")
    
    except Exception as e:
        st.error(f"读取日志失败: {e}")

def show_data_management(conn, df):
    """数据管理"""
    st.header("✏️ 数据管理")
    
    if not df.empty:
        st.subheader("当前数据")
        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 保存更改", use_container_width=True):
                try:
                    edited_df.to_sql('wiper_specs', conn, if_exists='replace', index=False)
                    st.success("数据保存成功!")
                except Exception as e:
                    st.error(f"保存失败: {e}")
        
        with col2:
            if st.button("🔄 重新加载数据", use_container_width=True):
                st.rerun()
    else:
        st.warning("数据库中没有数据")

def show_query_logs(conn):
    """查询日志"""
    st.header("🔍 查询日志")
    
    try:
        logs_df = pd.read_sql_query("SELECT * FROM query_logs ORDER BY timestamp DESC", conn)
        
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True)
            
            if st.button("🗑️ 清除所有日志"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM query_logs")
                conn.commit()
                st.success("日志已清除")
                st.rerun()
        else:
            st.info("暂无查询日志")
    
    except Exception as e:
        st.error(f"读取日志失败: {e}")

# 后台管理页面
def admin_page(conn):
    """后台管理界面"""
    if not check_admin_password():
        return
    
    st.title("⚙️ 管理后台")
    st.markdown("---")
    
    # 管理菜单
    menu_option = st.sidebar.radio(
        "管理功能",
        ["📊 数据概览", "📈 使用统计", "✏️ 数据管理", "🔍 查询日志"]
    )
    
    # 获取数据
    try:
        df = pd.read_sql_query("SELECT * FROM wiper_specs", conn)
    except:
        st.error("无法读取数据")
        return
    
    if menu_option == "📊 数据概览":
        show_data_overview(conn, df)
    elif menu_option == "📈 使用统计":
        show_usage_stats(conn)
    elif menu_option == "✏️ 数据管理":
        show_data_management(conn, df)
    elif menu_option == "🔍 查询日志":
        show_query_logs(conn)

# 主应用
def main():
    """主应用"""
    # 显示初始化状态
    st.sidebar.title("系统状态")
    
    # 初始化数据库
    with st.spinner('系统初始化中...'):
        conn = init_database()
    
    if conn is None:
        st.error("⚠️ 系统初始化失败，请检查数据文件")
        
        # 提供调试信息
        st.info("""
        **故障排除步骤:**
        1. 确保 `wiper_data.xlsx` 文件已上传到 GitHub 仓库
        2. 检查文件名是否正确（包括扩展名）
        3. 确认文件在仓库根目录
        4. 等待几分钟让 Streamlit Cloud 同步文件
        """)
        return
    
    # 侧边栏导航
    st.sidebar.title("导航菜单")
    app_mode = st.sidebar.radio(
        "选择模式",
        ["🔍 前台查询", "⚙️ 后台管理"]
    )
    
    # 根据选择显示不同页面
    if app_mode == "🔍 前台查询":
        frontend_page(conn)
    else:
        admin_page(conn)
    
    # 页脚
    st.sidebar.markdown("---")
    st.sidebar.markdown("**系统信息**")
    st.sidebar.markdown(f"版本: v1.0")
    st.sidebar.markdown(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()
