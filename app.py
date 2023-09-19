import os
import tempfile
import streamlit as st
from streamlit_chat import message
from utils import Utils  # Import the Utils class from utils module

st.set_page_config(
    page_title="Medical ChatBot",
    page_icon="💉",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ... (Rest of your code)

def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
            # Update the following line to use Utils class instead of Agent
            agent_text = st.session_state["agent"].ask(user_text)

        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((agent_text, False))

def read_and_save_file():
    st.session_state["agent"].forget()
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""

    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {file.name}"):
            # Update the following line to use Utils class instead of Agent
            st.session_state["agent"].ingest(file_path)
        os.remove(file_path)

def main():
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
        if is_openai_api_key_set():
            # Update the following line to create an instance of Utils class instead of Agent
            st.session_state["agent"] = Utils(st.session_state["OPENAI_API_KEY"])
        else:
            st.session_state["agent"] = None

    st.header("Medical ChatBot")

    # ... (Rest of your code)

if __name__ == "__main__":
    main()
