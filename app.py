import streamlit as st
import requests

# --- 1. CONFIGURATION ---
API_URL = "http://localhost:8000"
BASE_URL = f"{API_URL}/LLM"

st.set_page_config(page_title="Private RAG", layout="wide", page_icon="🦾")

# --- 2. SESSION STATE INITIALIZATION ---
def init_state():
    defaults = {
        "token": None,
        "chat_id": None,
        "username": "User",
        "messages": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# --- 3. API WRAPPERS (Logic Layer) ---
def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def create_chat_callback():
    try:
        r = requests.post(f"{BASE_URL}/chats", json={"title": "New Session"}, headers=get_headers())
        if r.status_code in [200, 201]:
            new_chat = r.json()
            st.session_state.chat_id = str(new_chat["id"])
            st.session_state.messages = [] 
            if "chat_selector" in st.session_state:
                del st.session_state["chat_selector"]
            st.toast("Chat Created!", icon="🚀")
        else:
            st.error(f"Failed: {r.text}")
    except Exception as e:
        st.error(f"Error: {e}")

def get_streaming_response(prompt):
    payload = {
        "prompt": prompt,
        "chat_id": st.session_state.chat_id
    }
    try:
        with requests.post(
            f"{BASE_URL}/chat/stream", 
            json=payload, 
            headers=get_headers(), 
            stream=True
        ) as r:
            if r.status_code == 200:
                for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        yield chunk
            else:
                yield f"❌ Error {r.status_code}: {r.text}"
    except Exception as e:
        yield f"🚨 Connection Lost: {e}"

# --- 4. SIDEBAR (Auth, Nav & RAG) ---
with st.sidebar:
    st.title("🔐 Access Control")
    
    if st.session_state.token:
        st.success(f"Logged in as: **{st.session_state.username}**")
        if st.button("🚪 Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.divider()
        st.subheader("💬 Conversations")
        st.button("➕ New Chat", on_click=create_chat_callback, use_container_width=True)
        
        # --- БЕЗПЕЧНЕ ЗАВАНТАЖЕННЯ ЧАТІВ ---
        try:
            resp = requests.get(f"{BASE_URL}/chats/10/0", headers=get_headers())
            if resp.status_code == 200:
                chats = resp.json()
                chat_options = {c["title"]: str(c["id"]) for c in chats}
                titles = list(chat_options.keys())
                ids = list(chat_options.values())
                current_id = str(st.session_state.chat_id)
                
                if current_id and current_id not in ids:
                    titles.insert(0, "🆕 New Session...")
                    chat_options["🆕 New Session..."] = current_id
                    ids.insert(0, current_id)

                if titles:
                    current_idx = ids.index(current_id) if current_id in ids else 0
                    
                    def on_chat_change():
                        new_id = chat_options[st.session_state.chat_selector]
                        if st.session_state.chat_id != new_id:
                            st.session_state.chat_id = new_id
                            st.session_state.messages = []

                    st.radio("Select Session:", titles, index=current_idx, key="chat_selector", on_change=on_chat_change)
        except:
            st.error("Loading...")
        # --- RAG TOGGLE ---
        st.divider()
        use_rag = st.toggle("🧠 Enable RAG (Document Search)", value=False)
        # --- ЗАВАНТАЖЕННЯ ДОКУМЕНТІВ (RAG) ---
        st.divider()
        st.subheader("📁 Knowledge Base")
        uploaded_file = st.file_uploader("Upload PDF/TXT", type=['pdf', 'txt'])
        
        import time # Додай на початку файлу

        # ... (в блоці Knowledge Base) ...
        if uploaded_file:
            if st.button("🔌 Index Document", use_container_width=True):
                with st.spinner("Uploading to Worker..."):
                    files_payload = {
                        "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                    }
                    r = requests.post(f"{BASE_URL}/file", files=files_payload, headers=get_headers())
                    
                    if r.status_code == 200:
                        task_id = r.json().get('task_id')
                        status_placeholder = st.empty() # Створюємо порожнє місце для статусу
                        
                        # Робимо "пінг" воркера кожні 2 секунди
                        for _ in range(15): # Чекаємо максимум 30 секунд
                            status_res = requests.get(f"{BASE_URL}/status/{task_id}")
                            if status_res.status_code == 200:
                                state = status_res.json().get("status")
                                if state == "SUCCESS":
                                    status_placeholder.success("✅ Document Indexed Successfully!")
                                    break
                                elif state == "FAILURE":
                                    status_placeholder.error("❌ Worker failed to process document.")
                                    break
                                else:
                                    status_placeholder.info(f"⏳ Processing in background... ({state})")
                            time.sleep(2)
                    else:
                        st.error(f"Upload failed: {r.status_code}")
            
    else:
        # --- LOGIN / REGISTER UI ---
        mode = st.radio("Action", ["Login", "Register"])
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        e = st.text_input("Email") if mode == "Register" else None
        
        if st.button("Submit", use_container_width=True):
            try:
                if mode == "Login":
                    r = requests.post(f"{API_URL}/v1/auth/token", data={"username": u, "password": p})
                    if r.status_code == 200:
                        st.session_state.token = r.json()["access_token"]
                        st.session_state.username = u
                        st.rerun()
                    else: st.error("Invalid Credentials")
                else:
                    r = requests.post(f"{API_URL}/v1/auth/register", json={"username": u, "password": p, "email": e})
                    if r.status_code in [200, 201]: st.success("Registered! Please Login.")
            except Exception as ex: st.error(f"Error: {ex}")

# --- 5. MAIN CHAT INTERFACE ---
if st.session_state.token:
    if not st.session_state.chat_id:
        st.info("👈 Create or select a chat in the sidebar to begin.")
    else:
        # Визначаємо, чи увімкнено RAG (змінна use_rag має бути оголошена в сайдбарі)
        # Якщо ти ще не додав тумблер у сайдбар, додай: use_rag = st.sidebar.toggle("🧠 RAG Mode")
        
        st.title(f"🤖 {'RAG' if use_rag else 'Private'} Assistant")
        
        # Відображення історії повідомлень
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Поле вводу
        if prompt := st.chat_input("How can I help you?"):
            # Додаємо запит юзера
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Відповідь асистента
            with st.chat_message("assistant"):
                if use_rag:
                    # --- RAG MODE (Пошук по базі Qdrant) ---
                    with st.spinner("🔍 Searching documents and thinking..."):
                        rag_payload = {
                            "query": prompt,
                            "system_prompt": "You are a professional assistant. Use the provided context to answer exactly."
                        }
                        try:
                            # Твій ендпоінт /LLM/rag_chat
                            r = requests.post(f"{BASE_URL}/rag_chat", json=rag_payload, headers=get_headers())
                            if r.status_code == 200:
                                # Отримуємо відповідь (зазвичай вона не стрімиться в RAG)
                                answer = r.json().get("answer", "I couldn't find relevant info.")
                                st.markdown(answer)
                                st.session_state.messages.append({"role": "assistant", "content": answer})
                            else:
                                st.error(f"RAG Error: {r.status_code}")
                        except Exception as e:
                            st.error(f"Connection Error: {e}")
                else:
                    # --- NORMAL MODE (Стрімінг Llama 3) ---
                    # Використовуємо наш генератор для ефекту друку
                    response_text = st.write_stream(get_streaming_response(prompt))
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
else:
    st.info("Please login to access the system.")