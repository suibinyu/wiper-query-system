import streamlit as st
import pandas as pd
import os
import glob

# 页面设置
st.set_page_config(
    page_title="雨刷查询",
    page_icon="🌧️",
    layout="centered"
)

# 应用标题
st.title("🌧️ 雨刷尺寸查询")
st.markdown("输入车型名称，查询雨刷尺寸")

# 加载Excel数据
@st.cache_data
def load_excel_data():
    try:
        # 查找数据文件
        possible_files = ['wiper_data.xlsx', 'wiper_data(1).xlsx', 'wiper_data*.xlsx']
        
        found_file = None
        for file_pattern in possible_files:
            matches = glob.glob(file_pattern)
            if matches:
                found_file = matches[0]
                break
        
        if found_file and os.path.exists(found_file):
            # 自动检测工作表
            excel_file = pd.ExcelFile(found_file)
            sheet_names = excel_file.sheet_names
            
            # 使用第一个工作表
            target_sheet = sheet_names[0]
            wiper_data = pd.read_excel(found_file, sheet_name=target_sheet)
            return wiper_data
        else:
            # 创建示例数据
            sample_data = pd.DataFrame({
                '品牌': ['丰田', '本田', '大众', '日产', '丰田', '本田'],
                '车型': ['卡罗拉', '思域', '朗逸', '轩逸', 'RAV4', 'CR-V'],
                '年份': ['2019-2023', '2016-2021', '2018-2023', '2019-2023', '2019-2023', '2017-2023'],
                '主驾': [26, 26, 24, 26, 26, 26],
                '副驾': [16, 16, 18, 16, 18, 18],
                '接头': ['U型', 'U型', '直插式', 'U型', '直插式', '勾型'],
                '后雨刷': [12, 11, '-', 12, 14, 12]
            })
            
            # 保存示例数据
            sample_data.to_excel('wiper_data.xlsx', index=False)
            return sample_data
        
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return pd.DataFrame()

# 加载数据
wiper_data = load_excel_data()

if wiper_data.empty:
    st.stop()

# 搜索栏
search_term = st.text_input(
    "🔍 输入车型名称", 
    placeholder="例如：卡罗拉、思域、朗逸...",
    key="search"
)

# 显示搜索结果
if search_term:
    # 搜索车型名称
    search_results = wiper_data[
        wiper_data['车型'].str.contains(search_term, case=False, na=False)
    ]
    
    if not search_results.empty:
        # 显示每个匹配的结果
        for _, result in search_results.iterrows():
            st.markdown("---")
            
            # 显示基本信息
            st.subheader(f"{result['品牌']} {result['车型']}")
            st.caption(f"年份: {result['年份']}")
            
            # 显示雨刷尺寸
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("主驾", f"{result['主驾']}寸")
            with col2:
                st.metric("副驾", f"{result['副驾']}寸")
            with col3:
                rear_wiper = result['后雨刷']
                if pd.isna(rear_wiper) or rear_wiper == '-':
                    st.metric("后雨刷", "无")
                else:
                    st.metric("后雨刷", f"{rear_wiper}寸")
            
            # 显示接头类型
            st.write(f"**接头类型**: {result['接头']}")
            
        st.success(f"找到 {len(search_results)} 个匹配车型")
    else:
        st.warning("没有找到匹配的车型")
        
        # 显示热门车型建议
        st.info("💡 试试搜索这些热门车型:")
        popular_models = wiper_data['车型'].head(5).tolist()
        cols = st.columns(5)
        for idx, model in enumerate(popular_models):
            with cols[idx]:
                if st.button(model, key=f"suggest_{idx}"):
                    st.session_state.search = model
                    st.experimental_rerun()
else:
    # 没有搜索时显示提示
    st.info("💡 在上方输入框中输入车型名称开始查询")
    
    # 显示热门车型
    st.markdown("### 🚗 热门车型")
    popular_models = wiper_data.head(8)
    
    cols = st.columns(4)
    for idx, (col, (_, model)) in enumerate(zip(cols, popular_models.iterrows())):
        with col:
            if st.button(
                f"{model['车型']}",
                key=f"model_{idx}",
                use_container_width=True
            ):
                st.session_state.search = model['车型']
                st.experimental_rerun()

# 底部信息
st.markdown("---")
st.caption("数据仅供参考，请以实际测量为准")
