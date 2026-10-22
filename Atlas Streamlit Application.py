import streamlit as st
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
DB_NAME = "atlas.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General'
            )
        ''')
        try:
            conn.execute("ALTER TABLE logs ADD COLUMN category TEXT NOT NULL DEFAULT 'General'")
        except sqlite3.OperationalError:
            pass 

        conn.execute('''
            CREATE TABLE IF NOT EXISTS system_memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

# --- APP CONFIG & STYLING ---
st.set_page_config(page_title="Atlas System", page_icon="🧭", layout="wide")

st.title("🧭 Atlas Core Intelligence System")
st.markdown("Your interactive, persistent memory and logging dashboard.")

# --- SIDEBAR NAVIGATION ---
st.sidebar.header("Atlas Controls")
menu_option = st.sidebar.radio(
    "Navigation", 
    ["📊 System Overview", "📝 Add Log", "📂 View & Filter Logs", "🔍 Search Logs", "🧠 Persistent Memory"]
)

# ==========================================
# 1. SYSTEM OVERVIEW
# ==========================================
if menu_option == "📊 System Overview":
    st.subheader("System Overview Dashboard")
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs")
        total_logs = cursor.fetchone()[0]
        
        if total_logs == 0:
            st.info("No logs found in Atlas memory yet. Use the sidebar to add some!")
        else:
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM logs")
            first_log, latest_log = cursor.fetchone()
            
            cursor.execute("SELECT category, COUNT(*) FROM logs GROUP BY category")
            category_counts = cursor.fetchall()
            
            cursor.execute("SELECT key, value FROM system_memory")
            sys_memory = cursor.fetchall()

            # Metric Cards
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Logs", total_logs)
            col2.metric("First Logged", first_log)
            col3.metric("Latest Logged", latest_log)

            if sys_memory:
                st.markdown("### 🧠 Active System Memory Keys")
                mem_cols = st.columns(len(sys_memory) if len(sys_memory) <= 3 else 3)
                for idx, (k, v) in enumerate(sys_memory):
                    mem_cols[idx % 3].metric(label=k, value=v)

            st.markdown("### 🏷️ Category Breakdown")
            cat_data = {cat: count for cat, count in category_counts}
            st.bar_chart(cat_data)

            # Export Button
            if st.button("📥 Export Overview Report to File"):
                filename = "atlas_overview_report.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"=== Atlas Overview ===\nTotal Logs: {total_logs}\nFirst: {first_log}\nLatest: {latest_log}\n")
                st.success(f"Report successfully saved to {filename}!")

# ==========================================
# 2. ADD LOG
# ==========================================
elif menu_option == "📝 Add Log":
    st.subheader("Record a New Log")
    
    with st.form("log_form"):
        content = st.text_area("Log Content", placeholder="What do you want Atlas to remember?")
        category = st.text_input("Category", value="General", placeholder="e.g., Work, Personal, Code")
        submit_button = st.form_submit_button(label="Record Log")
        
        if submit_button:
            if content.strip():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with sqlite3.connect(DB_NAME) as conn:
                    conn.execute("INSERT INTO logs (timestamp, content, category) VALUES (?, ?, ?)", (timestamp, content, category))
                    conn.commit()
                st.success(f"Successfully recorded under category **[{category}]**!")
            else:
                st.error("Log content cannot be empty.")

# ==========================================
# 3. VIEW & FILTER LOGS
# ==========================================
elif menu_option == "📂 View & Filter Logs":
    st.subheader("Persistent Memory Logs")
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM logs")
        categories = ["All"] + [r[0] for r in cursor.fetchall()]
        
    selected_cat = st.selectbox("Filter by Category", categories)
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        if selected_cat == "All":
            cursor.execute("SELECT id, timestamp, category, content FROM logs ORDER BY timestamp DESC")
        else:
            cursor.execute("SELECT id, timestamp, category, content FROM logs WHERE category = ? ORDER BY timestamp DESC", (selected_cat,))
        rows = cursor.fetchall()
        
    if not rows:
        st.warning("No logs found.")
    else:
        st.markdown(f"Showing **{len(rows)}** log(s):")
        for row in rows:
            with st.expander(f"[{row[0]}] {row[1]} — **{row[2]}**"):
                st.write(row[3])
                if st.button(f"Delete Log ID {row[0]}", key=f"del_{row[0]}"):
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.execute("DELETE FROM logs WHERE id = ?", (row[0],))
                        conn.commit()
                    st.rerun()

# ==========================================
# 4. SEARCH LOGS
# ==========================================
elif menu_option == "🔍 Search Logs":
    st.subheader("Keyword Search")
    query = st.text_input("Search query", placeholder="Type keywords...")
    
    if query:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, timestamp, category, content FROM logs WHERE content LIKE ? ORDER BY timestamp DESC", (f"%{query}%",))
            rows = cursor.fetchall()
            
        if not rows:
            st.info(f"No results found for '{query}'.")
        else:
            st.success(f"Found {len(rows)} match(es):")
            for row in rows:
                st.markdown(f"> **[{row[0]}] {row[1]}** *[{row[2]}]*  \n> {row[3]}")

# ==========================================
# 5. PERSISTENT MEMORY (KEY-VALUE)
# ==========================================
elif menu_option == "🧠 Persistent Memory":
    st.subheader("Key-Value System Memory")
    
    tab1, tab2 = st.tabs(["View / Delete Memory", "Set / Update Memory"])
    
    with tab1:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value, updated_at FROM system_memory ORDER BY key ASC")
            mem_rows = cursor.fetchall()
            
        if not mem_rows:
            st.info("System memory is empty.")
        else:
            for k, v, updated in mem_rows:
                col1, col2, col3 = st.columns([2, 3, 1])
                col1.text(f"Key: {k}")
                col2.text(f"Value: {v}")
                if col3.button("Delete", key=f"mem_del_{k}"):
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.execute("DELETE FROM system_memory WHERE key = ?", (k,))
                        conn.commit()
                    st.rerun()
                    
    with tab2:
        with st.form("mem_form"):
            key_input = st.text_input("Key Name", placeholder="e.g. current_project")
            val_input = st.text_input("Value", placeholder="e.g. Atlas UI upgrade")
            submitted = st.form_submit_button("Save to Memory")
            
            if submitted:
                if key_input.strip() and val_input.strip():
                    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.execute('''
                            INSERT INTO system_memory (key, value, updated_at) 
                            VALUES (?, ?, ?)
                            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                        ''', (key_input, val_input, updated_at))
                        conn.commit()
                    st.success(f"System memory updated: '{key_input}' = '{val_input}'")
                else:
                    st.error("Both key and value are required.")