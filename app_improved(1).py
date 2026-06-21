"""
学生信息管理系统 - Web 应用（优化完善版）
框架: Streamlit + PyMySQL
数据库: MySQL (student_management)
改进点:
  - DB 配置改用 st.secrets，不再硬编码密码
  - 只读查询加 @st.cache_data 缓存，减少数据库压力
  - 仪表盘增加图表（性别饼图、入学年份柱状图、专业分布）
  - 学生列表支持分页
  - 支持 Excel 导出
  - 学生详情弹窗查看
  - 加载动画 & 更好的空状态
"""

import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime
import io
import plotly.express as px
import plotly.graph_objects as go

# ============================================
# 页面配置
# ============================================
st.set_page_config(
    page_title="学生信息管理系统",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# 自定义 CSS 样式（浅色主题美化）
# ============================================
def inject_custom_css():
    """注入全局自定义 CSS 样式"""
    st.markdown("""
    <style>
    /* ----- 全局：所有字体黑色 ----- */
    * {
        color: #000000 !important;
    }
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #e8edf5 100%);
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }

    /* ----- 标题 ----- */
    h1 {
        font-weight: 700 !important;
        font-size: 2rem !important;
        border-bottom: 3px solid #4A90D9;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem !important;
    }
    h2, h3 {
        font-weight: 600 !important;
    }

    /* ----- 卡片容器 ----- */
    .card-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
        transition: box-shadow 0.2s ease;
    }
    .card-container:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }

    /* ----- 筛选卡片 ----- */
    .filter-card {
        background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(74,144,217,0.08);
    }

    /* ----- 侧边栏 ----- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a365d 0%, #2d4a7a 100%) !important;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 1rem !important;
        padding: 0.6rem 1rem !important;
        border-radius: 8px !important;
        margin-bottom: 0.3rem !important;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.12) !important;
    }
    [data-testid="stSidebar"] h1 {
        border-bottom: none !important;
        font-size: 1.4rem !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.2) !important;
    }

    /* ----- 按钮 ----- */
    button[kind="primary"] {
        background: linear-gradient(135deg, #4A90D9 0%, #357ABD 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.2rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(74,144,217,0.3) !important;
    }
    button[kind="primary"] * {
        color: #ffffff !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(74,144,217,0.4) !important;
    }
    button[kind="secondary"] {
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    /* ----- 卡片式 Metric ----- */
    [data-testid="stMetric"] {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.2rem !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    [data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-weight: 700 !important;
        font-size: 2.2rem !important;
    }

    /* ----- 表格 ----- */
    .stDataFrame {
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
        border: 1px solid #e2e8f0 !important;
    }
    .stDataFrame thead th {
        background: linear-gradient(180deg, #4A90D9 0%, #357ABD 100%) !important;
        font-weight: 600 !important;
        padding: 0.7rem 0.8rem !important;
        font-size: 0.9rem !important;
    }
    .stDataFrame thead th * {
        color: #ffffff !important;
    }
    .stDataFrame tbody tr:nth-child(even) {
        background: #f7fafc !important;
    }
    .stDataFrame tbody tr:hover {
        background: #ebf4ff !important;
    }

    /* ----- 展开面板 (expander) ----- */
    .stExpander {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
        margin-bottom: 1rem !important;
    }
    .stExpander > div:first-child {
        background: #f7fafc !important;
    }

    /* ----- 输入框 ----- */
    .stTextInput input, .stSelectbox select {
        border-radius: 8px !important;
        border: 1px solid #cbd5e0 !important;
        padding: 0.5rem 0.8rem !important;
        transition: border-color 0.2s ease !important;
    }
    .stTextInput input:focus {
        border-color: #4A90D9 !important;
        box-shadow: 0 0 0 3px rgba(74,144,217,0.15) !important;
    }

    /* ----- 警告/信息框 ----- */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
    }

    /* ----- 分页器 ----- */
    .stPagination button {
        border-radius: 8px !important;
    }

    /* ----- 页脚 ----- */
    .site-footer {
        text-align: center;
        padding: 1.5rem 1rem;
        margin-top: 3rem;
        border-top: 1px solid #e2e8f0;
        font-size: 0.9rem;
        background: transparent;
    }

    /* ----- 分隔线 ----- */
    hr {
        border-color: #e2e8f0 !important;
        margin: 1.5rem 0 !important;
    }

    /* ----- 覆盖 Streamlit 自带颜色为黑色 ----- */
    label, .stMarkdown, .stText, p, span, div, li, td, th, input, select, textarea {
        color: #000000 !important;
    }
    /* 侧边栏保持白色 */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] .stRadio label {
        color: #ffffff !important;
    }
    /* 表格头保持白色 */
    .stDataFrame thead th,
    .stDataFrame thead th * {
        color: #ffffff !important;
    }
    /* 主按钮文字白色 */
    button[kind="primary"],
    button[kind="primary"] * {
        color: #ffffff !important;
    }

    /* ----- 学生详情弹窗 ----- */
    .student-detail {
        background: #f7fafc;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        margin-top: 1rem;
    }
    .detail-label {
        font-weight: 600;
        color: #4A5568 !important;
        min-width: 80px;
        display: inline-block;
    }
    .detail-value {
        color: #1A202C !important;
    }
    </style>
    """, unsafe_allow_html=True)


def show_footer():
    """在每页底部显示版权信息"""
    st.markdown("""
    <div class="site-footer">
        <p>© 2026 害怕土豆</p>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# 数据库连接函数
# ============================================
@st.cache_resource
def init_connection():
    """初始化数据库连接（带缓存）"""
    return pymysql.connect(
        host=st.secrets["db"]["host"],
        port=int(st.secrets["db"]["port"]),
        user=st.secrets["db"]["user"],
        password=st.secrets["db"]["password"],
        database=st.secrets["db"]["database"],
        charset='utf8mb4',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
        ssl={'ssl': True},
    )


def get_connection():
    """获取数据库连接（优先使用缓存连接，断开则重连）"""
    try:
        conn = init_connection()
        conn.ping(reconnect=True)
        return conn
    except Exception:
        return pymysql.connect(
            host=st.secrets["db"]["host"],
            port=int(st.secrets["db"]["port"]),
            user=st.secrets["db"]["user"],
            password=st.secrets["db"]["password"],
            database=st.secrets["db"]["database"],
            charset='utf8mb4',
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': True},
        )


# ============================================
# 专业管理 - 数据操作函数（带缓存）
# ============================================
@st.cache_data(ttl=60)
def fetch_majors():
    """查询所有专业（带缓存，60秒失效）"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT major_id, major_name FROM major ORDER BY major_id")
            return cur.fetchall()
    finally:
        conn.close()


def add_major(name: str):
    """新增专业"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO major (major_name) VALUES (%s)", (name,))
        st.cache_data.clear()
    finally:
        conn.close()


def delete_major(major_id: int):
    """删除专业"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM major WHERE major_id = %s", (major_id,))
        st.cache_data.clear()
    finally:
        conn.close()


# ============================================
# 班级管理 - 数据操作函数（带缓存）
# ============================================
@st.cache_data(ttl=60)
def fetch_classes():
    """查询所有班级（含专业名称，带缓存）"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.class_id, c.class_name, c.major_id, m.major_name
                FROM class c
                JOIN major m ON c.major_id = m.major_id
                ORDER BY c.class_id
            """)
            return cur.fetchall()
    finally:
        conn.close()


def add_class(name: str, major_id: int):
    """新增班级"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO class (class_name, major_id) VALUES (%s, %s)",
                (name, major_id),
            )
        st.cache_data.clear()
    finally:
        conn.close()


def update_class(class_id: int, name: str, major_id: int):
    """更新班级信息"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE class SET class_name=%s, major_id=%s WHERE class_id=%s",
                (name, major_id, class_id),
            )
        st.cache_data.clear()
    finally:
        conn.close()


def delete_class(class_id: int):
    """删除班级"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM class WHERE class_id = %s", (class_id,))
        st.cache_data.clear()
    finally:
        conn.close()


# ============================================
# 学生管理 - 数据操作函数
# ============================================
@st.cache_data(ttl=30)
def fetch_students(filter_class=None, filter_gender=None, filter_year=None, filter_keyword=None):
    """
    多条件查询学生列表（带缓存，30秒失效）
    """
    conn = get_connection()
    try:
        sql = """
            SELECT
                s.student_id,
                s.name,
                s.gender,
                s.political_status,
                s.age,
                s.phone,
                s.enrollment_year,
                c.class_name,
                m.major_name,
                s.class_id
            FROM student s
            JOIN class c ON s.class_id = c.class_id
            JOIN major m ON c.major_id = m.major_id
            WHERE 1=1
        """
        params = []

        if filter_class:
            sql += " AND s.class_id = %s"
            params.append(filter_class)
        if filter_gender:
            sql += " AND s.gender = %s"
            params.append(filter_gender)
        if filter_year:
            sql += " AND s.enrollment_year = %s"
            params.append(filter_year)
        if filter_keyword:
            sql += " AND (s.name LIKE %s OR s.student_id LIKE %s)"
            params.extend([f"%{filter_keyword}%", f"%{filter_keyword}%"])

        sql += " ORDER BY s.student_id"

        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def get_student(student_id: str):
    """根据学号查询单个学生"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM student WHERE student_id = %s", (student_id,))
            return cur.fetchone()
    finally:
        conn.close()


def add_student(data: dict):
    """新增学生"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO student
                    (student_id, name, gender, political_status, age, phone, enrollment_year, class_id)
                VALUES
                    (%(student_id)s, %(name)s, %(gender)s, %(political_status)s,
                     %(age)s, %(phone)s, %(enrollment_year)s, %(class_id)s)
                """,
                data,
            )
        st.cache_data.clear()
    finally:
        conn.close()


def update_student(data: dict):
    """更新学生信息"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE student
                SET name=%s, gender=%s, political_status=%s, age=%s,
                    phone=%s, enrollment_year=%s, class_id=%s
                WHERE student_id=%s
                """,
                (
                    data['name'], data['gender'], data['political_status'],
                    data['age'], data['phone'], data['enrollment_year'],
                    data['class_id'], data['student_id'],
                ),
            )
        st.cache_data.clear()
    finally:
        conn.close()


def delete_student(student_id: str):
    """删除学生"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM student WHERE student_id = %s", (student_id,))
        st.cache_data.clear()
    finally:
        conn.close()


def batch_insert_students(records: list):
    """批量导入学生，跳过已存在的学号"""
    conn = get_connection()
    success = 0
    skip = 0
    try:
        with conn.cursor() as cur:
            for rec in records:
                try:
                    cur.execute(
                        """
                        INSERT INTO student
                            (student_id, name, gender, political_status, age, phone, enrollment_year, class_id)
                        VALUES
                            (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            rec['student_id'], rec['name'], rec['gender'],
                            rec.get('political_status', '群众'), rec['age'],
                            rec.get('phone', ''), rec['enrollment_year'], rec['class_id'],
                        ),
                    )
                    success += 1
                except pymysql.err.IntegrityError:
                    skip += 1
    finally:
        conn.close()
    st.cache_data.clear()
    return success, skip


# ============================================
# 统计查询函数（带缓存）
# ============================================
@st.cache_data(ttl=60)
def fetch_stats():
    """获取系统统计数据"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM student")
            student_count = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM class")
            class_count = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM major")
            major_count = cur.fetchone()['cnt']
            cur.execute("SELECT gender, COUNT(*) AS cnt FROM student GROUP BY gender")
            gender_stats = {row['gender']: row['cnt'] for row in cur.fetchall()}
            cur.execute(
                "SELECT enrollment_year, COUNT(*) AS cnt "
                "FROM student GROUP BY enrollment_year ORDER BY enrollment_year"
            )
            year_stats = cur.fetchall()
            cur.execute(
                "SELECT m.major_name, COUNT(s.student_id) AS cnt "
                "FROM major m LEFT JOIN class c ON m.major_id = c.major_id "
                "LEFT JOIN student s ON c.class_id = s.class_id "
                "GROUP BY m.major_id, m.major_name ORDER BY cnt DESC"
            )
            major_stats = cur.fetchall()
        return {
            'student_count': student_count,
            'class_count': class_count,
            'major_count': major_count,
            'gender_stats': gender_stats,
            'year_stats': year_stats,
            'major_stats': major_stats,
        }
    finally:
        conn.close()


# ============================================
# 页面：学生信息管理（增删改查 + 筛选 + 分页 + 导出）
# ============================================
def page_student_management():
    st.title("📋 学生信息管理")

    # 初始化状态
    for key in ['show_add_form', 'show_edit_form', 'edit_data', 'show_delete_confirm', 'pending_delete', 'filter_class', 'filter_gender', 'filter_year', 'filter_keyword']:
        if key not in st.session_state:
            if key == 'filter_class':
                st.session_state[key] = 0
            elif key in ['filter_gender', 'filter_year', 'filter_keyword']:
                st.session_state[key] = '全部' if 'gender' in key or 'year' in key else ''
            else:
                st.session_state[key] = False if key != 'edit_data' else None

    # ----- 筛选区域（卡片样式）-----
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown("### 🔍 筛选条件")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        classes = fetch_classes()
        class_options = {c['class_id']: f"{c['class_name']}（{c['major_name']}）" for c in classes}
        class_options[0] = "全部班级"
        selected_class = st.selectbox(
            "按班级筛选",
            options=list(class_options.keys()),
            format_func=lambda x: class_options[x],
            key="filter_class_select",
        )

    with col2:
        gender = st.selectbox("按性别筛选", options=["全部", "男", "女"], key="filter_gender_select")

    with col3:
        enrollment_year = st.selectbox(
            "按入学年份筛选",
            options=["全部"] + [str(y) for y in range(2018, 2027)],
            key="filter_year_select",
        )

    with col4:
        keyword = st.text_input("🔎 搜索（姓名/学号）", placeholder="输入姓名或学号...", key="filter_keyword_input")

    if st.button("🔍 查询", type="primary"):
        st.session_state.filter_class = selected_class if selected_class != 0 else None
        st.session_state.filter_gender = gender if gender != "全部" else None
        st.session_state.filter_year = int(enrollment_year) if enrollment_year != "全部" else None
        st.session_state.filter_keyword = keyword if keyword.strip() else None
        st.session_state.student_page = 1  # 重置分页
    st.markdown('</div>', unsafe_allow_html=True)

    # 获取查询参数
    fc = st.session_state.get('filter_class')
    fg = st.session_state.get('filter_gender')
    fy = st.session_state.get('filter_year')
    fk = st.session_state.get('filter_keyword')

    # 执行查询
    with st.spinner("正在查询学生数据..."):
        students = fetch_students(
            filter_class=fc,
            filter_gender=fg,
            filter_year=fy,
            filter_keyword=fk,
        )

    # ----- 操作按钮 -----
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 1, 1, 5])
    with col_btn1:
        if st.button("➕ 新增学生", use_container_width=True):
            st.session_state.show_add_form = True
    with col_btn2:
        if st.button("📥 刷新列表", use_container_width=True):
            for key in ['filter_class', 'filter_gender', 'filter_year', 'filter_keyword']:
                if key in st.session_state:
                    del st.session_state[key]
            st.cache_data.clear()
            st.rerun()
    with col_btn3:
        # Excel 导出按钮
        if students:
            df_export = pd.DataFrame(students)
            df_export = df_export.rename(columns={
                'student_id': '学号', 'name': '姓名', 'gender': '性别',
                'political_status': '政治面貌', 'age': '年龄', 'phone': '联系电话',
                'enrollment_year': '入学年份', 'class_name': '班级', 'major_name': '专业',
            })
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, sheet_name='学生信息', index=False)
            excel_buffer.seek(0)
            st.download_button(
                label="📊 导出 Excel",
                data=excel_buffer,
                file_name=f"学生信息_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    # ----- 新增学生表单 -----
    if st.session_state.get('show_add_form', False):
        with st.expander("✏️ 新增学生", expanded=True):
            _render_student_form(mode="add")

    # ----- 数据表格（分页）-----
    st.markdown(f"### 📊 学生列表（共 {len(students)} 条）")
    if students:
        PAGE_SIZE = 10
        total_pages = max(1, (len(students) + PAGE_SIZE - 1) // PAGE_SIZE)
        if 'student_page' not in st.session_state:
            st.session_state.student_page = 1
        page = st.session_state.student_page

        # 分页控制器
        col_p1, col_p2, col_p3 = st.columns([2, 3, 2])
        with col_p1:
            if st.button("⬅️ 上一页", disabled=(page <= 1), use_container_width=True):
                st.session_state.student_page -= 1
                st.rerun()
        with col_p2:
            st.markdown(f"<div style='text-align:center; padding:0.5rem;'>第 {page} / {total_pages} 页</div>", unsafe_allow_html=True)
        with col_p3:
            if st.button("➡️ 下一页", disabled=(page >= total_pages), use_container_width=True):
                st.session_state.student_page += 1
                st.rerun()

        start = (page - 1) * PAGE_SIZE
        end = min(start + PAGE_SIZE, len(students))
        page_students = students[start:end]

        df = pd.DataFrame(page_students)
        df_display = df.rename(columns={
            'student_id': '学号', 'name': '姓名', 'gender': '性别',
            'political_status': '政治面貌', 'age': '年龄', 'phone': '联系电话',
            'enrollment_year': '入学年份', 'class_name': '班级', 'major_name': '专业',
        })
        display_cols = ['学号', '姓名', '性别', '政治面貌', '年龄', '联系电话', '入学年份', '班级', '专业']
        df_display = df_display[display_cols]

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                '学号': st.column_config.TextColumn(width='medium'),
                '姓名': st.column_config.TextColumn(width='small'),
                '性别': st.column_config.TextColumn(width='small'),
                '联系电话': st.column_config.TextColumn(width='medium'),
            },
            height=400,
        )

        # ----- 学生详情查看（选择学号查看详情）-----
        st.markdown("---")
        st.markdown("### 🔎 查看学生详情")
        detail_sid = st.selectbox(
            "选择学生查看详情",
            options=[""] + [f"{s['student_id']} - {s['name']}" for s in students],
            format_func=lambda x: "请选择..." if x == "" else x,
        )
        if detail_sid:
            sid = detail_sid.split(" - ")[0]
            stu = get_student(sid)
            if stu:
                class_info = next((c for c in classes if c['class_id'] == stu['class_id']), None)
                major_name = class_info['major_name'] if class_info else "未知"
                class_name = class_info['class_name'] if class_info else "未知"
                st.markdown(f"""
                <div class="student-detail">
                    <h3 style="margin-top:0;">👤 学生详细信息</h3>
                    <p><span class="detail-label">学号：</span><span class="detail-value">{stu['student_id']}</span></p>
                    <p><span class="detail-label">姓名：</span><span class="detail-value">{stu['name']}</span></p>
                    <p><span class="detail-label">性别：</span><span class="detail-value">{stu['gender']}</span></p>
                    <p><span class="detail-label">政治面貌：</span><span class="detail-value">{stu.get('political_status', '群众')}</span></p>
                    <p><span class="detail-label">年龄：</span><span class="detail-value">{stu['age']}</span></p>
                    <p><span class="detail-label">联系电话：</span><span class="detail-value">{stu.get('phone', '未填写')}</span></p>
                    <p><span class="detail-label">入学年份：</span><span class="detail-value">{stu['enrollment_year']}</span></p>
                    <p><span class="detail-label">班级：</span><span class="detail-value">{class_name}</span></p>
                    <p><span class="detail-label">专业：</span><span class="detail-value">{major_name}</span></p>
                </div>
                """, unsafe_allow_html=True)

        # ----- 操作区域（编辑 + 删除）-----
        st.markdown("---")
        st.markdown("### ⚙️ 操作")

        op_col1, op_col2 = st.columns(2)

        with op_col1:
            st.markdown("#### ✏️ 编辑学生")
            edit_id = st.selectbox(
                "选择要编辑的学生（学号 - 姓名）",
                options=[f"{s['student_id']} - {s['name']}" for s in students],
                key="edit_select",
            )
            if st.button("🔧 加载编辑表单", type="primary"):
                sid = edit_id.split(" - ")[0]
                stu = get_student(sid)
                if stu:
                    st.session_state.edit_data = stu
                    st.session_state.show_edit_form = True
                    st.rerun()

            if st.session_state.get('show_edit_form', False) and st.session_state.get('edit_data'):
                with st.expander("✏️ 编辑学生信息", expanded=True):
                    _render_student_form(mode="edit", data=st.session_state.edit_data)

        with op_col2:
            st.markdown("#### 🗑️ 删除学生")
            delete_id = st.selectbox(
                "选择要删除的学生（学号 - 姓名）",
                options=[f"{s['student_id']} - {s['name']}" for s in students],
                key="delete_select",
            )

            if st.button("🗑️ 确认删除", type="secondary"):
                st.session_state.pending_delete = delete_id.split(" - ")[0]
                st.session_state.show_delete_confirm = True
                st.rerun()

            if st.session_state.get('show_delete_confirm', False):
                sid = st.session_state.get('pending_delete', '')
                stu = get_student(sid)
                if stu:
                    st.warning(
                        f"⚠️ 确定要删除学生【{stu['student_id']} - {stu['name']}】吗？此操作不可恢复！"
                    )
                    confirm_col1, confirm_col2 = st.columns(2)
                    with confirm_col1:
                        if st.button("✅ 确定删除", type="primary"):
                            delete_student(sid)
                            st.success(f"✅ 学生【{stu['name']}】已成功删除！")
                            _clear_form_state()
                            st.rerun()
                    with confirm_col2:
                        if st.button("❌ 取消"):
                            st.session_state.show_delete_confirm = False
                            st.session_state.pending_delete = ''
                            st.rerun()
    else:
        st.info("📭 暂无学生数据，请先添加学生，或修改筛选条件。")

    st.markdown("---")
    show_footer()


def _render_student_form(mode="add", data=None):
    """渲染学生表单（新增/编辑共用）"""
    classes = fetch_classes()
    class_map = {c['class_id']: f"{c['class_name']}（{c['major_name']}）" for c in classes}

    if not classes:
        st.warning("⚠️ 系统中暂无班级数据，请先在【班级管理】中添加班级后再添加学生。")
        return

    with st.form(key=f"student_form_{mode}"):
        col1, col2, col3 = st.columns(3)

        with col1:
            student_id = st.text_input(
                "学号 *",
                value=data['student_id'] if data else "",
                max_chars=20,
                disabled=(mode == "edit"),
                placeholder="如：20210101001",
            )
            name = st.text_input(
                "姓名 *",
                value=data['name'] if data else "",
                placeholder="请输入姓名",
            )
            gender = st.selectbox(
                "性别 *",
                options=["男", "女"],
                index=0 if not data else (0 if data['gender'] == '男' else 1),
            )
            political_status = st.text_input(
                "政治面貌",
                value=data['political_status'] if data else "群众",
                placeholder="如：中共党员、共青团员、群众",
            )

        with col2:
            age = st.number_input(
                "年龄 *",
                min_value=10,
                max_value=99,
                value=data['age'] if data else 18,
            )
            phone = st.text_input(
                "联系电话",
                value=data['phone'] if data and data.get('phone') else "",
                placeholder="如：13800001111",
            )
            enroll_year_val = int(data.get('enrollment_year', 2021) or 2021)
            enroll_year_options = list(range(2018, 2027))
            enroll_idx = enroll_year_options.index(enroll_year_val) if enroll_year_val in enroll_year_options else 3
            enrollment_year = st.selectbox(
                "入学年份 *",
                options=enroll_year_options,
                index=enroll_idx,
            )

        with col3:
            class_ids = list(class_map.keys())
            default_class_index = 0
            if data and data.get('class_id') in class_ids:
                default_class_index = class_ids.index(data['class_id'])

            selected_class_id = st.selectbox(
                "班级 *",
                options=class_ids,
                format_func=lambda x: class_map[x],
                index=default_class_index,
            )

        submitted = st.form_submit_button(
            "✅ 提交新增" if mode == "add" else "💾 保存修改",
            type="primary",
        )

        if submitted:
            if not student_id or not name:
                st.error("❌ 学号和姓名不能为空！")
                return
            if not student_id.strip() or not name.strip():
                st.error("❌ 学号和姓名不能只包含空格！")
                return

            form_data = {
                'student_id': student_id.strip(),
                'name': name.strip(),
                'gender': gender,
                'political_status': political_status.strip() or '群众',
                'age': age,
                'phone': phone.strip() if phone else '',
                'enrollment_year': enrollment_year,
                'class_id': selected_class_id,
            }

            try:
                if mode == "add":
                    add_student(form_data)
                    st.success(f"✅ 学生【{name}】添加成功！")
                else:
                    update_student(form_data)
                    st.success(f"✅ 学生【{name}】信息已更新！")

                _clear_form_state()
                st.rerun()
            except pymysql.err.IntegrityError as e:
                if "Duplicate" in str(e):
                    st.error(f"❌ 学号【{student_id}】已存在，请使用其他学号！")
                else:
                    st.error(f"❌ 数据库错误：{e}")
            except Exception as e:
                st.error(f"❌ 操作失败：{e}")


def _clear_form_state():
    """清除表单相关状态"""
    for key in ['show_add_form', 'show_edit_form', 'edit_data', 'show_delete_confirm', 'pending_delete']:
        if key in st.session_state:
            del st.session_state[key]


# ============================================
# 页面：批量导入（优化版）
# ============================================
def page_batch_import():
    st.title("📥 批量导入学生")

    st.markdown("""
    ### 使用说明
    1. 下载 CSV 模板或准备符合格式的 CSV 文件
    2. 上传文件后系统会自动预览数据
    3. 确认无误后点击【开始导入】
    """)
    st.info("💡 支持 UTF-8 / GBK 编码，系统会自动识别。")

    # 下载模板
    template_cols = ['student_id', 'name', 'gender', 'political_status', 'age', 'phone', 'enrollment_year', 'class_id']
    template_df = pd.DataFrame(columns=template_cols, dtype=str)
    csv_buffer = io.StringIO()
    template_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')

    col_tmp1, col_tmp2 = st.columns([1, 3])
    with col_tmp1:
        st.download_button(
            label="📄 下载 CSV 模板",
            data=csv_buffer.getvalue().encode('utf-8-sig'),
            file_name="student_import_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")

    # 文件上传
    uploaded_file = st.file_uploader(
        "选择 CSV 文件上传",
        type=["csv"],
        help="请确保 CSV 文件列名与模板一致，编码为 UTF-8 或 GBK",
    )

    if uploaded_file is not None:
        try:
            for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']:
                try:
                    uploaded_file.seek(0)
                    raw_df = pd.read_csv(uploaded_file, dtype=str, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                st.error("❌ 无法识别文件编码，请使用 UTF-8 编码保存 CSV 文件")
                return

            raw_df.columns = raw_df.columns.str.strip()

            required_cols = {'student_id', 'name', 'gender', 'age', 'enrollment_year', 'class_id'}
            missing = required_cols - set(raw_df.columns)
            if missing:
                st.error(f"❌ CSV 文件缺少必需列：{', '.join(missing)}")
                return

            # 数据预览
            st.markdown("### 📊 数据预览")
            st.dataframe(raw_df, use_container_width=True, hide_index=True)

            classes = fetch_classes()
            valid_class_ids = {c['class_id'] for c in classes}

            st.markdown("### 🔍 数据校验结果")
            errors = []
            valid_records = []

            for idx, row in raw_df.iterrows():
                row_num = idx + 2
                row_errors = []

                sid = str(row.get('student_id', '')).strip()
                name_val = str(row.get('name', '')).strip()
                gender_val = str(row.get('gender', '')).strip()
                age_val = str(row.get('age', '')).strip()
                year_val = str(row.get('enrollment_year', '')).strip()
                class_val = str(row.get('class_id', '')).strip()
                political_val = str(row.get('political_status', '')).strip()
                phone_val = str(row.get('phone', '')).strip()

                if not sid:
                    row_errors.append("学号为空")
                if not name_val:
                    row_errors.append("姓名为空")
                if gender_val not in ('男', '女'):
                    row_errors.append(f"性别无效：{gender_val}")
                if not age_val.isdigit() or not (10 <= int(age_val) <= 99):
                    row_errors.append(f"年龄无效：{age_val}")
                if not year_val.isdigit():
                    row_errors.append(f"入学年份无效：{year_val}")
                try:
                    if int(class_val) not in valid_class_ids:
                        row_errors.append(f"班级编号不存在：{class_val}")
                except ValueError:
                    row_errors.append(f"班级编号格式错误：{class_val}")
                # 手机号格式简单校验
                if phone_val and (not phone_val.isdigit() or len(phone_val) not in (11,)):
                    row_errors.append(f"手机号格式可能不正确：{phone_val}")

                if row_errors:
                    errors.append(f"第 {row_num} 行: {'; '.join(row_errors)}")
                else:
                    valid_records.append({
                        'student_id': sid,
                        'name': name_val,
                        'gender': gender_val,
                        'political_status': political_val if political_val else '群众',
                        'age': int(age_val),
                        'phone': phone_val if phone_val else '',
                        'enrollment_year': int(year_val),
                        'class_id': int(class_val),
                    })

            if errors:
                st.error(f"❌ 发现 {len(errors)} 条错误：")
                for e in errors[:20]:  # 最多显示20条
                    st.write(f"  - {e}")
                if len(errors) > 20:
                    st.write(f"  ... 还有 {len(errors) - 20} 条错误未显示")

            col_valid, col_err = st.columns(2)
            with col_valid:
                st.success(f"✅ 有效数据：{len(valid_records)} 条")
            with col_err:
                st.error(f"❌ 错误数据：{len(errors)} 条")

            if valid_records and st.button("🚀 开始导入", type="primary", use_container_width=True):
                with st.spinner(f"正在导入 {len(valid_records)} 条数据..."):
                    progress_bar = st.progress(0.0)
                    # 分批导入，每批100条
                    batch_size = 100
                    total_success = 0
                    total_skip = 0
                    for i in range(0, len(valid_records), batch_size):
                        batch = valid_records[i:i+batch_size]
                        s, sk = batch_insert_students(batch)
                        total_success += s
                        total_skip += sk
                        progress_bar.progress(min(1.0, (i + batch_size) / len(valid_records)))
                st.success(f"✅ 导入完成！成功 {total_success} 条，跳过（学号重复）{total_skip} 条")

        except Exception as e:
            st.error(f"❌ 文件处理失败：{e}")

    show_footer()


# ============================================
# 页面：班级管理（优化版）
# ============================================
def page_class_management():
    st.title("🏫 班级管理")

    classes = fetch_classes()
    majors = fetch_majors()

    # 数据表格
    if classes:
        df = pd.DataFrame(classes)
        df_display = df.rename(columns={
            'class_id': '班级编号',
            'class_name': '班级名称',
            'major_name': '所属专业',
        })
        st.dataframe(
            df_display[['班级编号', '班级名称', '所属专业']],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("📭 暂无班级数据")

    st.markdown("---")

    # 新增班级
    st.markdown("### ➕ 新增班级")
    with st.form("add_class_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_class_name = st.text_input("班级名称", placeholder="如：计科2201班")
        with col2:
            major_options = {m['major_id']: m['major_name'] for m in majors}
            if major_options:
                new_major_id = st.selectbox(
                    "所属专业",
                    options=list(major_options.keys()),
                    format_func=lambda x: major_options[x],
                )
            else:
                st.warning("请先在专业管理中添加专业")
                new_major_id = None

        if st.form_submit_button("✅ 添加班级", type="primary"):
            if new_class_name and new_class_name.strip() and new_major_id:
                try:
                    add_class(new_class_name.strip(), new_major_id)
                    st.success(f"✅ 班级【{new_class_name}】添加成功！")
                    st.rerun()
                except pymysql.err.IntegrityError as e:
                    st.error(f"❌ 该班级名称在当前专业下已存在！")
            else:
                st.error("❌ 请填写班级名称并选择专业")

    if classes:
        st.markdown("---")
        st.markdown("### ⚙️ 班级操作")

        edit_col, delete_col = st.columns(2)

        with edit_col:
            st.markdown("#### ✏️ 编辑班级")
            edit_class_id = st.selectbox(
                "选择班级",
                options=[f"{c['class_id']} - {c['class_name']}" for c in classes],
                key="edit_class_select",
            )
            if st.button("🔧 加载编辑", type="primary", key="load_edit_class"):
                cid = int(edit_class_id.split(" - ")[0])
                target = next((c for c in classes if c['class_id'] == cid), None)
                if target:
                    st.session_state.edit_class = target
                    st.rerun()

            if st.session_state.get('edit_class'):
                target = st.session_state.edit_class
                with st.form("edit_class_form"):
                    edit_name = st.text_input("班级名称", value=target['class_name'])
                    major_map = {m['major_id']: m['major_name'] for m in fetch_majors()}
                    default_idx = list(major_map.keys()).index(target['major_id']) if target['major_id'] in major_map else 0
                    edit_major = st.selectbox(
                        "所属专业",
                        options=list(major_map.keys()),
                        format_func=lambda x: major_map[x],
                        index=default_idx,
                    )
                    save_col, cancel_col = st.columns(2)
                    with save_col:
                        if st.form_submit_button("💾 保存修改", type="primary"):
                            update_class(target['class_id'], edit_name.strip(), edit_major)
                            st.success(f"✅ 班级信息已更新！")
                            del st.session_state.edit_class
                            st.rerun()
                    with cancel_col:
                        if st.form_submit_button("❌ 取消"):
                            del st.session_state.edit_class
                            st.rerun()

        with delete_col:
            st.markdown("#### 🗑️ 删除班级")
            del_class_id = st.selectbox(
                "选择班级",
                options=[f"{c['class_id']} - {c['class_name']}" for c in classes],
                key="delete_class_select",
            )
            if st.button("🗑️ 删除班级", type="secondary"):
                st.warning("⚠️ 确定删除此班级吗？如果该班级下还有学生，删除将失败。")
                if st.button("✅ 确定删除", type="primary", key="confirm_del_class"):
                    cid = int(del_class_id.split(" - ")[0])
                    try:
                        delete_class(cid)
                        st.success("✅ 班级已删除！")
                        st.rerun()
                    except pymysql.err.IntegrityError:
                        st.error("❌ 删除失败：该班级下仍有学生，请先清空学生！")
                    except Exception as e:
                        st.error(f"❌ 删除失败：{e}")

    show_footer()


# ============================================
# 页面：专业管理（优化版）
# ============================================
def page_major_management():
    st.title("📚 专业管理")

    majors = fetch_majors()

    if majors:
        df = pd.DataFrame(majors)
        df_display = df.rename(columns={
            'major_id': '专业编号',
            'major_name': '专业名称',
        })
        st.dataframe(
            df_display[['专业编号', '专业名称']],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("📭 暂无专业数据")

    st.markdown("---")

    col_add, col_del = st.columns(2)

    with col_add:
        st.markdown("### ➕ 新增专业")
        with st.form("add_major_form"):
            new_major_name = st.text_input("专业名称", placeholder="如：人工智能")
            if st.form_submit_button("✅ 添加专业", type="primary"):
                if new_major_name and new_major_name.strip():
                    try:
                        add_major(new_major_name.strip())
                        st.success(f"✅ 专业【{new_major_name}】添加成功！")
                        st.rerun()
                    except pymysql.err.IntegrityError:
                        st.error(f"❌ 专业【{new_major_name}】已存在！")
                else:
                    st.error("❌ 专业名称不能为空")

    with col_del:
        st.markdown("### 🗑️ 删除专业")
        if majors:
            del_major = st.selectbox(
                "选择要删除的专业",
                options=[f"{m['major_id']} - {m['major_name']}" for m in majors],
            )
            if st.button("🗑️ 删除专业", type="secondary"):
                st.warning("⚠️ 确定删除此专业吗？如果该专业下还有班级，删除将失败。")
                if st.button("✅ 确定删除", type="primary", key="confirm_del_major"):
                    mid = int(del_major.split(" - ")[0])
                    try:
                        delete_major(mid)
                        st.success("✅ 专业已删除！")
                        st.rerun()
                    except pymysql.err.IntegrityError:
                        st.error("❌ 删除失败：该专业下仍有班级，请先清空班级！")
                    except Exception as e:
                        st.error(f"❌ 删除失败：{e}")
        else:
            st.info("暂无专业可删除")

    show_footer()


# ============================================
# 页面：系统概览（首页，含图表）
# ============================================
def page_dashboard():
    st.title("🎓 学生信息管理系统")

    # 获取统计数据（带缓存）
    with st.spinner("正在加载统计数据..."):
        stats = fetch_stats()

    student_count = stats['student_count']
    class_count = stats['class_count']
    major_count = stats['major_count']
    gender_stats = stats['gender_stats']
    year_stats = stats['year_stats']
    major_stats = stats['major_stats']

    # ----- 统计卡片 -----
    st.markdown(f"""
    <div style="display:flex; gap:1.2rem; margin-bottom:2rem; flex-wrap:wrap;">
        <div class="card-container" style="flex:1; min-width:180px; text-align:center; border-top:4px solid #4A90D9;">
            <div style="font-size:2.5rem; margin-bottom:0.3rem;">📋</div>
            <div style="font-size:2.4rem; font-weight:700;">{student_count}</div>
            <div style="font-weight:600; font-size:1rem;">学生总数</div>
        </div>
        <div class="card-container" style="flex:1; min-width:180px; text-align:center; border-top:4px solid #48BB78;">
            <div style="font-size:2.5rem; margin-bottom:0.3rem;">🏫</div>
            <div style="font-size:2.4rem; font-weight:700;">{class_count}</div>
            <div style="font-weight:600; font-size:1rem;">班级总数</div>
        </div>
        <div class="card-container" style="flex:1; min-width:180px; text-align:center; border-top:4px solid #ED8936;">
            <div style="font-size:2.5rem; margin-bottom:0.3rem;">📚</div>
            <div style="font-size:2.4rem; font-weight:700;">{major_count}</div>
            <div style="font-weight:600; font-size:1rem;">专业总数</div>
        </div>
        <div class="card-container" style="flex:1; min-width:180px; text-align:center; border-top:4px solid #9F7AEA;">
            <div style="font-size:2.5rem; margin-bottom:0.3rem;">👦</div>
            <div style="font-size:2.4rem; font-weight:700;">{gender_stats.get('男', 0)}</div>
            <div style="font-weight:600; font-size:1rem;">男生人数</div>
        </div>
        <div class="card-container" style="flex:1; min-width:180px; text-align:center; border-top:4px solid #ED64A6;">
            <div style="font-size:2.5rem; margin-bottom:0.3rem;">👧</div>
            <div style="font-size:2.4rem; font-weight:700;">{gender_stats.get('女', 0)}</div>
            <div style="font-weight:600; font-size:1rem;">女生人数</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ----- 图表区域 -----
    if student_count > 0:
        st.markdown("---")
        st.markdown("### 📊 数据可视化")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # 性别分布饼图
            gender_labels = list(gender_stats.keys())
            gender_values = list(gender_stats.values())
            if gender_labels:
                fig_gender = px.pie(
                    values=gender_values,
                    names=gender_labels,
                    title="性别分布",
                    color_discrete_map={'男': '#4A90D9', '女': '#ED64A6'},
                    hole=0.4,
                )
                fig_gender.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#000000'),
                    title_font=dict(size=16, color='#000000'),
                    legend=dict(font=dict(color='#000000')),
                )
                st.plotly_chart(fig_gender, use_container_width=True)
            else:
                st.info("暂无性别统计数据")

        with chart_col2:
            # 入学年份分布柱状图
            if year_stats:
                year_df = pd.DataFrame(year_stats)
                fig_year = px.bar(
                    year_df,
                    x='enrollment_year',
                    y='cnt',
                    title="入学年份分布",
                    labels={'enrollment_year': '入学年份', 'cnt': '人数'},
                    color_discrete_sequence=['#4A90D9'],
                    text='cnt',
                )
                fig_year.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#000000'),
                    title_font=dict(size=16, color='#000000'),
                    xaxis=dict(title_font=dict(color='#000000'), tickfont=dict(color='#000000')),
                    yaxis=dict(title_font=dict(color='#000000'), tickfont=dict(color='#000000')),
                )
                fig_year.update_traces(textposition='outside')
                st.plotly_chart(fig_year, use_container_width=True)
            else:
                st.info("暂无入学年份统计数据")

        # 专业人数分布图
        if major_stats:
            st.markdown("#### 各专业学生人数")
            major_df = pd.DataFrame(major_stats)
            fig_major = px.bar(
                major_df,
                x='major_name',
                y='cnt',
                title="各专业学生人数",
                labels={'major_name': '专业', 'cnt': '学生人数'},
                color='cnt',
                color_continuous_scale='Blues',
                text='cnt',
            )
            fig_major.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#000000'),
                title_font=dict(size=16, color='#000000'),
                xaxis=dict(title_font=dict(color='#000000'), tickfont=dict(color='#000000')),
                yaxis=dict(title_font=dict(color='#000000'), tickfont=dict(color='#000000')),
            )
            fig_major.update_traces(textposition='outside')
            st.plotly_chart(fig_major, use_container_width=True)
    else:
        st.info("📭 系统中暂无学生数据，请先添加学生后在仪表盘中查看统计图表。")

    st.markdown("---")

    # 功能导航卡片
    st.markdown("### 🎯 功能导航")
    nav_items = [
        ("📋", "学生信息管理", "学生增删改查，按班级/性别/入学年份筛选，支持分页和导出", "#4A90D9"),
        ("📥", "批量导入", "通过 CSV 文件批量导入学生信息", "#48BB78"),
        ("🏫", "班级管理", "班级及所属专业的增删改操作", "#ED8936"),
        ("📚", "专业管理", "专业的添加与删除", "#9F7AEA"),
    ]

    cols = st.columns(4)
    for i, (icon, title, desc, color) in enumerate(nav_items):
        with cols[i]:
            st.markdown(f"""
            <div class="card-container" style="text-align:center; border-top:4px solid {color}; cursor:pointer; height:180px;">
                <div style="font-size:2.2rem; margin-bottom:0.5rem;">{icon}</div>
                <div style="font-weight:700; font-size:1.1rem; margin-bottom:0.4rem;">{title}</div>
                <div style="font-size:0.85rem; line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.info("💡 请使用左侧边栏导航到各功能页面。")

    show_footer()


# ============================================
# 主程序入口
# ============================================
def main():
    """主程序：侧边栏导航 + 页面路由"""

    # 注入自定义样式
    inject_custom_css()

    # ----- 侧边栏 -----
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
            <div style="font-size:3rem; margin-bottom:0.3rem;">🎓</div>
            <div style="font-size:1.3rem; font-weight:700; color:#ffffff; margin-bottom:0.2rem;">学生管理系统</div>
            <div style="font-size:0.8rem; color:rgba(255,255,255,0.55);">Student Management System</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        page = st.radio(
            "功能导航",
            options=[
                "🏠 系统概览",
                "📋 学生信息管理",
                "📥 批量导入",
                "🏫 班级管理",
                "📚 专业管理",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.caption(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption("Powered by Streamlit + MySQL")

    # ----- 页面路由 -----
    if "系统概览" in page:
        page_dashboard()
    elif "学生信息管理" in page:
        page_student_management()
    elif "批量导入" in page:
        page_batch_import()
    elif "班级管理" in page:
        page_class_management()
    elif "专业管理" in page:
        page_major_management()


# ============================================
# 启动入口
# ============================================
if __name__ == "__main__":
    main()
