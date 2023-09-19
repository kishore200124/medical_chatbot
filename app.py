import os
import tempfile
import streamlit as st
from streamlit_chat import message
from agent import Agent

st.set_page_config(
    page_title="Medical ChatBot",
    page_icon="💉",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for design
st.markdown(
    """
    <style>
    body {
        background-color: #f7f7f7;
        font-family: Arial, sans-serif;
    }
    .stTextInput {
        font-size: 16px;
    }
    .stButton {
        background-color: #007BFF;
        color: white;
    }
    .stButton:hover {
        background-color: #0056b3;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def display_messages(pdf_chat_history):
    st.subheader("Chat")
    for i, (msg, is_user) in enumerate(pdf_chat_history):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()

def process_input(pdf_chat_histories):
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        selected_pdf = st.selectbox("Select PDF", list(pdf_chat_histories.keys()))
        with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
            agent_text = st.session_state["agent"].ask(user_text)

        # Append messages to the selected PDF's chat history
        pdf_chat_histories[selected_pdf].append((user_text, True))
        pdf_chat_histories[selected_pdf].append((agent_text, False))

def read_and_save_file(pdf_chat_history):
    st.session_state["user_input"] = ""

    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        # Pass the PDF file name to the ingest method
        pdf_name = file.name
        if pdf_name not in st.session_state["pdf_chat_histories"]:
            st.session_state["pdf_chat_histories"][pdf_name] = []  # Initialize chat history for the PDF
        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {pdf_name}"):
            st.session_state["agent"].ingest(file_path, pdf_name)
        os.remove(file_path)

def is_openai_api_key_set() -> bool:
    return len(st.session_state["OPENAI_API_KEY"]) > 0

def main():
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["pdf_chat_histories"] = {}  # Dictionary to store chat histories for each PDF
        st.session_state["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
        if is_openai_api_key_set():
            st.session_state["agent"] = Agent(st.session_state["OPENAI_API_KEY"])
        else:
            st.session_state["agent"] = None

    st.header("Medical ChatBot")

    if st.text_input("OpenAI API Key", value=st.session_state["OPENAI_API_KEY"], key="input_OPENAI_API_KEY", type="password"):
        if (
            len(st.session_state["input_OPENAI_API_KEY"]) > 0
            and st.session_state["input_OPENAI_API_KEY"] != st.session_state["OPENAI_API_KEY"]
        ):
            st.session_state["OPENAI_API_KEY"] = st.session_state["input_OPENAI_API_KEY"]
            if st.session_state["agent"] is not None:
                st.warning("Please, upload the files again.")
            st.session_state["messages"] = []
            st.session_state["user_input"] = ""
            st.session_state["agent"] = Agent(st.session_state["OPENAI_API_KEY"])

    st.subheader("Sample Medical Questions")
    st.write("- What are the common symptoms of COVID-19?")
    st.write("- How is diabetes diagnosed?")
    st.write("- Tell me about the treatment options for asthma.")

    st.subheader("Upload a Medical Document")
    st.file_uploader(
        "Upload medical document (PDF)",
        type=["pdf"],
        key="file_uploader",
        on_change=lambda: read_and_save_file(st.session_state["pdf_chat_histories"]),
        label_visibility="collapsed",
        accept_multiple_files=True,
        disabled=not is_openai_api_key_set(),
    )

    st.session_state["ingestion_spinner"] = st.empty()

    selected_pdf = st.selectbox("Select PDF", list(st.session_state["pdf_chat_histories"].keys()))

    pdf_chat_history = st.session_state["pdf_chat_histories"].get(selected_pdf, [])
    display_messages(pdf_chat_history)
    
    st.text_input("Ask a medical question", key="user_input", disabled=not is_openai_api_key_set(), on_change=lambda: process_input(pdf_chat_history))

    st.divider()

if __name__ == "__main__":
    main()
