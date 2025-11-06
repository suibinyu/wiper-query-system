import streamlit as st
import pandas as pd

# 页面设置
st.set_page_config(
    page_title="雨刷尺寸查询系统",
    page_icon="🌧️",
    layout="centered"
)

# 应用标题
st.title("🌧️ 汽车雨刷尺寸查询系统")
st.markdown("输入您的车型名称，查询对应的雨刷尺寸和接头类型")

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

# 搜索框
st.markdown("### 🔍 输入车型名称搜索")
search_term = st.text_input(
    "请输入车型名称（例如：卡罗拉、CR-V、3系等）", 
    placeholder="输入车型名称...",
    key="search_input"
)

# 显示搜索结果
if search_term:
    # 搜索逻辑：在车型列中查找包含搜索词的行（不区分大小写）
    search_results = wiper_data[
        wiper_data['车型'].str.contains(search_term, case=False, na=False)
    ]
    
    if not search_results.empty:
        st.success(f"✅ 找到 {len(search_results)} 个匹配车型")
        
        # 显示每个匹配的结果
        for idx, result in search_results.iterrows():
            with st.container():
                st.markdown("---")
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader(f"{result['品牌']} {result['车型']}")
                    st.caption(f"年份: {result['年份']}")
                
                with col2:
                    col2_1, col2_2, col2_3 = st.columns(3)
                    
                    with col2_1:
                        st.metric("主驾尺寸", f"{result['主驾雨刷尺寸(寸)']}寸")
                    
                    with col2_2:
                        st.metric("副驾尺寸", f"{result['副驾雨刷尺寸(寸)']}寸")
                    
                    with col2_3:
                        st.metric("接头类型", result['主驾接头类型'])
                
                # 显示备注（如果有）
                if pd.notna(result['备注']) and result['备注'] != '':
                    st.info(f"备注: {result['备注']}")
        
        # 显示数据表格（可选）
        with st.expander("📋 查看详细数据表格"):
            display_columns = ['品牌', '车型', '年份', '主驾雨刷尺寸(寸)', '副驾雨刷尺寸(寸)', '主驾接头类型', '副驾接头类型']
            st.dataframe(
                search_results[display_columns],
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("⚠️ 没有找到匹配的车型，请尝试以下建议：")
        st.markdown("""
        - 检查拼写是否正确
        - 尝试使用更通用的车型名称（如只输入'卡罗'而不是'卡罗拉'）
        - 或浏览下面的热门车型
        """)

# 热门车型推荐（当没有搜索或搜索无结果时显示）
if not search_term or (search_term and search_results.empty):
    st.markdown("### 🚗 热门车型参考")
    
    # 显示一些热门车型作为参考
    popular_models = wiper_data.head(8)  # 显示前8个车型作为热门参考
    
    cols = st.columns(4)
    for idx, (col, model) in enumerate(zip(cols, popular_models.iterrows())):
        _, model_data = model
        with col:
            st.button(
                f"{model_data['品牌']} {model_data['车型']}",
                key=f"model_{idx}",
                use_container_width=True,
                on_click=lambda x=model_data['车型']: st.session_state.update({"search_input": x})
            )

# 接头类型说明
st.markdown("---")
st.markdown("### 💡 接头类型说明")

connector_info = {
    "U型": "传统的U型挂钩，安装简单，适用于大多数经济型车型",
    "直插式": "直接插入的接头，常见于日系和部分国产车型",
    "勾型": "钩子式连接，多见于美系和部分欧系车型",
    "侧插式": "从侧面插入的接头，常见于高端车型"
}

cols = st.columns(4)
for idx, (connector_type, description) in enumerate(connector_info.items()):
    with cols[idx]:
        st.metric(connector_type, description)

# 底部信息
st.markdown("---")
st.markdown("""
**使用说明:**
1. 在搜索框中输入您的车型名称
2. 系统将显示匹配的车型及其雨刷规格
3. 点击热门车型按钮可以快速搜索

**注意事项:**
- 不同年份的同款车型可能有不同的雨刷规格
- 本数据仅供参考，请以实际测量为准
- 如有疑问，建议咨询专业汽车配件店
""")
