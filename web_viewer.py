import streamlit as st
import json

# Set halaman web
st.set_page_config(page_title="JSONL Dataset Viewer", page_icon="🗺️", layout="wide")
st.title("🗺️ Danau Toba Dataset Viewer")
st.write("Aplikasi web sederhana untuk mengecek dataset JSONL kamu.")

# Load data JSONL
file_path = "dataset_trim_excel_flight_mcp_danau_toba.jsonl"  # Sesuaikan dengan nama file kamu

@st.cache_data
def load_jsonl(path):
    data_list = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data_list.append(json.loads(line))
    except FileNotFoundError:
        st.error(f"File '{path}' tidak ditemukan! Pastikan posisinya satu folder dengan script ini.")
    return data_list

dataset = load_jsonl(file_path)

if dataset:
    # Sidebar untuk navigasi data
    total_data = len(dataset)
    st.sidebar.header("Navigasi Data")
    
    idx_input = st.sidebar.number_input(
        "Pilih Baris Data:", 
        min_value=1, 
        max_value=total_data, 
        value=1, 
        step=1
    )
    
    idx = idx_input - 1
    # idx = st.sidebar.slider("Pilih Baris Data:", 1, total_data, 1) - 1
    
    st.sidebar.metric(label="Total Dataset", value=f"{total_data} Baris")

    # Tampilkan data terpilih
    st.subheader(f"📄 Data ke-{idx + 1}")
    
    current_data = dataset[idx]
    messages = current_data.get("messages", [])

    # Tampilkan isi chat/prompt
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")

        if role == "system":
            with st.expander("⚙️ System Prompt (Klik untuk melihat)", expanded=True):
                st.code(content, language="text")
        elif role == "user":
            with st.chat_message("user"):
                st.write(content)
        elif role == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.write(content)
                
    # Bagian bawah untuk melihat JSON mentahnya (jika butuh)
    with st.expander("🔍 Raw JSON Line"):
        st.json(current_data)