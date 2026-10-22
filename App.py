import streamlit as st
from atlas import Atlas
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Atlas App", page_icon="🛡️", layout="centered")

st.title("🛡️ Atlas Core System")
db = Atlas()

# Sidebar Navigation
menu = st.sidebar.radio("Navigation", ["View Logs", "Add Log", "System Overview", "Search", "Manage Memory"])

if menu == "View Logs":
    st.header("📜 All Logs")
    rows = db.db_exec("SELECT id, time, category, content FROM logs ORDER BY time DESC", fetch="all")
    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Time", "Category", "Content"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("Delete a Log")
        del_id = st.number_input("Enter Log ID to delete", min_value=1, step=1)
        if st.button("Delete"):
            db.db_exec("DELETE FROM logs WHERE id = ?", (int(del_id),))
            st.success(f"Deleted log ID {del_id}!")
            st.rerun()
    else:
        st.info("No logs found yet.")

elif menu == "Add Log":
    st.header("➕ Add New Log")
    with st.form("log_form"):
        content = st.text_area("Log Content")
        category = st.text_input("Category", value="General")
        submitted = st.form_submit_button("Save Log")
        if submitted:
            if content:
                db.db_exec("INSERT INTO logs (time, content, category) VALUES (?, ?, ?)", 
                             (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), content, category))
                st.success("✅ Log saved successfully!")
            else:
                st.error("⚠️ Log content cannot be empty.")

elif menu == "System Overview":
    st.header("📊 System Overview")
    total = db.db_exec("SELECT COUNT(*) FROM logs", fetch="one")[0]
    st.metric("Total Logs Recorded", total)
    
    st.subheader("🔑 Active Memory Keys")
    mem = db.db_exec("SELECT key, value, updated FROM memory", fetch="all")
    if mem:
        mem_df = pd.DataFrame(mem, columns=["Key", "Value", "Last Updated"])
        st.dataframe(mem_df, use_container_width=True, hide_index=True)
    else:
        st.info("No memory keys stored.")

elif menu == "Search":
    st.header("🔍 Search Logs")
    kw = st.text_input("Enter keyword or phrase")
    if kw:
        rows = db.db_exec("SELECT id, time, category, content FROM logs WHERE content LIKE ?", (f"%{kw}%",), fetch="all")
        if rows:
            df = pd.DataFrame(rows, columns=["ID", "Time", "Category", "Content"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("No matches found.")

elif menu == "Manage Memory":
    st.header("🧠 Persistent Memory")
    with st.form("mem_form"):
        k = st.text_input("Key Name")
        v = st.text_input("Value")
        submitted = st.form_submit_button("Save / Update Key")
        if submitted:
            if k and v:
                db.db_exec("INSERT OR REPLACE INTO memory (key, value, updated) VALUES (?, ?, ?)", 
                             (k, v, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                st.success(f"✨ Memory key '{k}' updated!")
            else:
                st.error("⚠️ Both Key and Value are required.")
              
