import streamlit as st
import sqlite3
import pandas as pd
import os
import sys
import base64
import plotly.express as px

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="گنجور",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load local fonts as base64 ───────────────────────────────────────────────
def _font_b64(filename):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "fonts", filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

_regular = _font_b64("Vazirmatn-Regular.woff2")
_bold    = _font_b64("Vazirmatn-Bold.woff2")

# ── Font + layout CSS (no external requests) ─────────────────────────────────
st.markdown(f"""
<style>
@font-face {{
    font-family: 'Vazirmatn';
    font-weight: 400;
    src: url('data:font/woff2;base64,{_regular}') format('woff2');
}}
@font-face {{
    font-family: 'Vazirmatn';
    font-weight: 700;
    src: url('data:font/woff2;base64,{_bold}') format('woff2');
}}

html, body, [class*="css"], .stMarkdown, .stText, button, input, select, textarea {{
    font-family: 'Vazirmatn', sans-serif !important;
}}

.poem-card {{
    border-radius: 12px;
    padding: 1.8rem 2rem;
    margin: 1rem 0;
    line-height: 2.4;
    font-size: 1.1rem;
    border: 1px solid rgba(128,128,128,0.2);
}}

.verse-line {{
    display: flex;
    justify-content: space-between;
    padding: 0.25rem 0;
    border-bottom: 1px solid rgba(128,128,128,0.1);
}}
.verse-line:last-child {{ border-bottom: none; }}

.search-result {{
    border-radius: 8px;
    padding: 0.9rem 1.2rem;
    margin: 0.4rem 0;
    border: 1px solid rgba(128,128,128,0.15);
}}

.result-meta {{
    font-size: 0.82rem;
    opacity: 0.65;
    margin-bottom: 6px;
}}
</style>
""", unsafe_allow_html=True)

# ── DB path (works both normally and inside PyInstaller bundle) ───────────────
def _db_path():
    if "GANJOOR_DB" in os.environ:
        return os.environ["GANJOOR_DB"]
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "ganjoor.db")

@st.cache_resource
def get_connection():
    path = _db_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@st.cache_data(ttl=300)
def query(sql, params=None):
    # SQLite uses ? placeholders; MySQL uses %s — normalise here
    sql = sql.replace("%s", "?").replace("`order`", '"order"').replace("`", "")
    conn = get_connection()
    cur = conn.execute(sql, params or ())
    return [dict(r) for r in cur.fetchall()]

# ── Sidebar Nav ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📜 گنجور")
    st.divider()
    page = st.radio(
        "بخش",
        ["🏠 خانه", "👤 شاعران و اشعار", "🔍 جستجو", "🎲 شعر تصادفی", "📊 آمار"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("پایگاه داده گنجور")

# ── Poem renderer (shared) ────────────────────────────────────────────────────
def render_poem(verses):
    lines_html = ""
    hemistich = []
    for v in verses:
        hemistich.append(v["text"])
        if v["position"] in (1, None) or len(hemistich) == 2:
            if len(hemistich) == 2:
                lines_html += f'<div class="verse-line"><span>{hemistich[0]}</span><span>{hemistich[1]}</span></div>'
            else:
                lines_html += f'<div class="verse-line"><span>{hemistich[0]}</span></div>'
            hemistich = []
    if hemistich:
        lines_html += f'<div class="verse-line"><span>{hemistich[0]}</span></div>'
    st.markdown(f'<div class="poem-card">{lines_html}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 خانه":
    st.markdown("# 📜 گنجور — پایگاه شعر فارسی")
    st.divider()

    try:
        poets  = query("SELECT COUNT(*) AS c FROM poets")[0]["c"]
        cats   = query("SELECT COUNT(*) AS c FROM categories")[0]["c"]
        poems  = query("SELECT COUNT(*) AS c FROM poems")[0]["c"]
        verses = query("SELECT COUNT(*) AS c FROM verses")[0]["c"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("شاعر", f"{poets:,}")
        c2.metric("مجموعه", f"{cats:,}")
        c3.metric("شعر", f"{poems:,}")
        c4.metric("بیت", f"{verses:,}")
    except Exception as e:
        st.error(f"خطا در اتصال به پایگاه داده: {e}")

    st.divider()
    st.markdown("### شاعران برتر (بر اساس تعداد بیت)")
    try:
        top = query("""
            SELECT p.name, COUNT(v.id) AS verse_count
            FROM poets p
            JOIN categories c ON c.poetId = p.id
            JOIN poems po ON po.categoryId = c.id
            JOIN verses v ON v.poemId = po.id
            GROUP BY p.id
            ORDER BY verse_count DESC
            LIMIT 10
        """)
        df = pd.DataFrame(top)
        fig = px.bar(
            df, x="verse_count", y="name", orientation="h",
            labels={"verse_count": "تعداد بیت", "name": "شاعر"},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_family="Vazirmatn", yaxis_title="", xaxis_title="تعداد بیت",
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"خطا: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# BROWSE POETS & POEMS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👤 شاعران و اشعار":
    st.markdown("# 👤 شاعران و اشعار")

    try:
        poets_list = query("SELECT id, name, description FROM poets ORDER BY name")
        poet_names = [p["name"] for p in poets_list]
        poet_ids   = {p["name"]: p["id"] for p in poets_list}
        poet_descs = {p["name"]: p.get("description", "") for p in poets_list}

        selected_poet = st.selectbox("انتخاب شاعر", poet_names)

        if selected_poet:
            pid = poet_ids[selected_poet]
            desc = poet_descs[selected_poet]
            if desc:
                st.info(desc)

            cats = query(
                "SELECT id, name FROM categories WHERE poetId=%s AND parentId IS NULL ORDER BY id",
                (pid,)
            )
            if cats:
                cat_names = [c["name"] for c in cats]
                cat_ids   = {c["name"]: c["id"] for c in cats}
                selected_cat = st.selectbox("انتخاب کتاب / مجموعه", cat_names)

                if selected_cat:
                    cid = cat_ids[selected_cat]

                    subcats = query(
                        "SELECT id, name FROM categories WHERE parentId=%s ORDER BY id",
                        (cid,)
                    )

                    if subcats:
                        subcat_names = [s["name"] for s in subcats]
                        subcat_ids   = {s["name"]: s["id"] for s in subcats}
                        selected_sub = st.selectbox("انتخاب بخش", subcat_names)
                        search_cat_id = subcat_ids[selected_sub]
                    else:
                        search_cat_id = cid

                    poems = query(
                        "SELECT id, title FROM poems WHERE categoryId=%s ORDER BY id LIMIT 200",
                        (search_cat_id,)
                    )
                    if poems:
                        poem_titles = [po["title"] for po in poems]
                        poem_ids    = {po["title"]: po["id"] for po in poems}
                        selected_poem = st.selectbox("انتخاب شعر", poem_titles)

                        if selected_poem:
                            poem_id = poem_ids[selected_poem]
                            verses = query(
                                "SELECT `order`, text, position FROM verses WHERE poemId=%s ORDER BY `order`",
                                (poem_id,)
                            )
                            st.markdown(f"### {selected_poem}")
                            if verses:
                                render_poem(verses)
                    else:
                        st.info("شعری یافت نشد.")
    except Exception as e:
        st.error(f"خطا: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# SEARCH
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 جستجو":
    st.markdown("# 🔍 جستجو در اشعار")

    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input("کلمه یا عبارت مورد نظر را وارد کنید", placeholder="مثلاً: عشق، می، باده...")
    with col2:
        try:
            poets_list = query("SELECT id, name FROM poets ORDER BY name")
            poet_options = ["همه شاعران"] + [p["name"] for p in poets_list]
            poet_filter  = st.selectbox("فیلتر شاعر", poet_options)
        except:
            poet_filter = "همه شاعران"

    if keyword:
        try:
            if poet_filter == "همه شاعران":
                results = query("""
                    SELECT v.text, po.title AS poem_title, p.name AS poet_name
                    FROM verses v
                    JOIN poems po ON po.id = v.poemId
                    JOIN categories c ON c.id = po.categoryId
                    JOIN poets p ON p.id = c.poetId
                    WHERE v.text LIKE %s
                    LIMIT 50
                """, (f"%{keyword}%",))
            else:
                pid = next(p["id"] for p in poets_list if p["name"] == poet_filter)
                results = query("""
                    SELECT v.text, po.title AS poem_title, p.name AS poet_name
                    FROM verses v
                    JOIN poems po ON po.id = v.poemId
                    JOIN categories c ON c.id = po.categoryId
                    JOIN poets p ON p.id = c.poetId
                    WHERE v.text LIKE %s AND p.id = %s
                    LIMIT 50
                """, (f"%{keyword}%", pid))

            st.caption(f"{len(results)} نتیجه یافت شد")
            for r in results:
                highlighted = r["text"].replace(keyword, f"**{keyword}**")
                st.markdown(f"""
<div class="search-result">
    <div class="result-meta">{r['poet_name']} — {r['poem_title']}</div>
    {r['text']}
</div>""", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"خطا در جستجو: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# RANDOM POEM
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎲 شعر تصادفی":
    st.markdown("# 🎲 شعر تصادفی")

    try:
        poets_list   = query("SELECT id, name FROM poets ORDER BY name")
        poet_options = ["هر شاعری"] + [p["name"] for p in poets_list]

        col1, col2 = st.columns([2, 1])
        with col1:
            poet_pick = st.selectbox("شاعر", poet_options)
        with col2:
            st.write("")
            st.write("")
            refresh = st.button("🎲 شعر جدید", use_container_width=True)

        if refresh:
            st.cache_data.clear()

        if poet_pick == "هر شاعری":
            poem = query("SELECT id, title, categoryId FROM poems ORDER BY RANDOM() LIMIT 1")
        else:
            pid  = next(p["id"] for p in poets_list if p["name"] == poet_pick)
            poem = query("""
                SELECT po.id, po.title, po.categoryId
                FROM poems po
                JOIN categories c ON c.id = po.categoryId
                WHERE c.poetId = %s
                ORDER BY RANDOM() LIMIT 1
            """, (pid,))

        if poem:
            p      = poem[0]
            poet   = query("""
                SELECT pt.name FROM poets pt
                JOIN categories c ON c.poetId = pt.id
                WHERE c.id = %s LIMIT 1
            """, (p["categoryId"],))
            verses = query(
                "SELECT text, position, `order` FROM verses WHERE poemId=%s ORDER BY `order`",
                (p["id"],)
            )

            poet_name = poet[0]["name"] if poet else ""
            st.markdown(f"### {p['title']}")
            st.caption(poet_name)
            st.divider()

            if verses:
                render_poem(verses)
    except Exception as e:
        st.error(f"خطا: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 آمار":
    st.markdown("# 📊 آمار پایگاه داده")

    try:
        st.markdown("### تعداد اشعار هر شاعر")
        data = query("""
            SELECT p.name, COUNT(po.id) AS poem_count
            FROM poets p
            JOIN categories c ON c.poetId = p.id
            JOIN poems po ON po.categoryId = c.id
            GROUP BY p.id ORDER BY poem_count DESC LIMIT 20
        """)
        df = pd.DataFrame(data)
        fig = px.pie(
            df, names="name", values="poem_count",
            hole=0.4,
        )
        fig.update_layout(font_family="Vazirmatn", paper_bgcolor="rgba(0,0,0,0)", height=420)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### تعداد بیت هر شاعر")
        data2 = query("""
            SELECT p.name, COUNT(v.id) AS verse_count
            FROM poets p
            JOIN categories c ON c.poetId = p.id
            JOIN poems po ON po.categoryId = c.id
            JOIN verses v ON v.poemId = po.id
            GROUP BY p.id ORDER BY verse_count DESC LIMIT 15
        """)
        df2 = pd.DataFrame(data2)
        fig2 = px.bar(
            df2, x="name", y="verse_count",
            labels={"verse_count": "تعداد بیت", "name": "شاعر"},
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_family="Vazirmatn", xaxis_title="", height=380,
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("### جدول کامل شاعران")
        all_poets = query("""
            SELECT p.name AS شاعر,
                   COUNT(DISTINCT po.id) AS تعداد_شعر,
                   COUNT(v.id)           AS تعداد_بیت
            FROM poets p
            LEFT JOIN categories c ON c.poetId = p.id
            LEFT JOIN poems po ON po.categoryId = c.id
            LEFT JOIN verses v ON v.poemId = po.id
            GROUP BY p.id ORDER BY تعداد_بیت DESC
        """)
        st.dataframe(pd.DataFrame(all_poets), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"خطا: {e}")
