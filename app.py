import streamlit as st
import pandas as pd

# 页面设置
st.set_page_config(
    page_title="雨刷尺寸查询系统",
    page_icon="🌧️",
    layout="wide"
)

# 应用标题
st.title("🌧️ 汽车雨刷尺寸查询系统")
st.markdown("输入车型名称，查询对应的雨刷尺寸和接头类型")

# 加载Excel数据
@st.cache_data
def load_excel_data():
    try:
        # 读取数据
        wiper_data = pd.read_excel('data/wiper_data.xlsx', sheet_name='wiper_data')
        return wiper_data
    except FileNotFoundError:
        st.error("数据文件未找到，请确保 data/wiper_data.xlsx 文件存在")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"读取数据文件时出错: {e}")
        return pd.DataFrame()

# 加载数据
wiper_data = load_excel_data()

if wiper_data.empty:
    st.stop()

# 侧边栏
st.sidebar.title("🔍 查询选项")

# 品牌选择
brands = ['全部品牌'] + sorted(wiper_data['品牌'].unique().tolist())
selected_brand = st.sidebar.selectbox("选择汽车品牌", brands)

# 根据品牌筛选车型
if selected_brand != '全部品牌':
    filtered_data = wiper_data[wiper_data['品牌'] == selected_brand]
    models = ['全部车型'] + sorted(filtered_data['车型'].unique().tolist())
else:
    models = ['全部车型'] + sorted(wiper_data['车型'].unique().tolist())

selected_model = st.sidebar.selectbox("选择车型", models)

# 接头类型筛选
connector_types = ['全部类型'] + sorted(wiper_data['接头'].unique().tolist())
selected_connector = st.sidebar.selectbox("筛选接头类型", connector_types)

# 主查询区域
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 查询结果")
    
    # 应用筛选条件
    filtered_results = wiper_data.copy()
    
    if selected_brand != '全部品牌':
        filtered_results = filtered_results[filtered_results['品牌'] == selected_brand]
    
    if selected_model != '全部车型':
        filtered_results = filtered_results[filtered_results['车型'] == selected_model]
    
    if selected_connector != '全部类型':
        filtered_results = filtered_results[filtered_results['接头'] == selected_connector]
    
    # 显示结果
    if not filtered_results.empty:
        # 重新排列列的顺序以便更好阅读
        display_columns = ['品牌', '车型', '年份', '主驾', '副驾', '接头', '后雨刷']
        display_data = filtered_results[display_columns]
        
        # 添加样式
        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )
        
        # 显示统计信息
        st.success(f"✅ 找到 {len(filtered_results)} 条匹配记录")
    else:
        st.warning("⚠️ 没有找到匹配的记录，请调整筛选条件")

with col2:
    st.subheader("💡 接头类型说明")
    
    # 显示接头类型说明
    connector_info = {
        "U型": "传统的U型挂钩，安装简单，适用于大多数经济型车型",
        "直插式": "直接插入的接头，常见于日系和部分国产车型",
        "勾型": "钩子式连接，多见于美系和部分欧系车型",
        "侧插式": "从侧面插入的接头，常见于高端车型"
    }
    
    for connector_type, description in connector_info.items():
        with st.expander(f"{connector_type}"):
            st.write(description)
    
    # 品牌统计
    st.subheader("🏢 品牌分布")
    brand_stats = wiper_data['品牌'].value_counts()
    st.bar_chart(brand_stats)

# 搜索功能
st.sidebar.markdown("---")
st.sidebar.subheader("🔎 关键词搜索")
search_term = st.sidebar.text_input("输入车型关键词搜索")

if search_term:
    search_results = wiper_data[
        wiper_data.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
    ]
    if not search_results.empty:
        st.sidebar.success(f"找到 {len(search_results)} 条包含 '{search_term}' 的记录")
        if st.sidebar.button("查看搜索结果"):
            st.subheader(f"🔍 搜索结果: '{search_term}'")
            display_columns = ['品牌', '车型', '年份', '主驾', '副驾', '接头', '后雨刷']
            st.dataframe(search_results[display_columns], use_container_width=True, hide_index=True)
    elif search_term:
        st.sidebar.warning("未找到匹配的记录")

# 数据统计和信息展示
st.markdown("---")
col3, col4, col5 = st.columns(3)

with col3:
    st.metric("总车型数量", len(wiper_data))

with col4:
    unique_brands = len(wiper_data['品牌'].unique())
    st.metric("覆盖品牌数量", unique_brands)

with col5:
    avg_driver_size = wiper_data['主驾'].mean()
    st.metric("平均主驾尺寸", f"{avg_driver_size:.1f}寸")

# 底部信息
st.markdown("---")
st.markdown("### 📝 使用说明")
st.markdown("""
1. **查询雨刷尺寸**: 在左侧边栏选择品牌和车型即可查看对应的雨刷尺寸
2. **筛选接头类型**: 可以按特定接头类型进行筛选
3. **关键词搜索**: 使用搜索功能快速查找特定车型
4. **数据说明**: 
   - 所有数据仅供参考，建议购买前确认实际规格
   - 后雨刷列中"-"表示该车型无后雨刷
""")
