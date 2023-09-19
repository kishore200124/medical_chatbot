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

def display_messages():
    st.subheader("Chat")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()

def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        
        # Check if the user's question is relevant to the uploaded PDF
        if st.session_state["agent"].is_trained_on(user_text):
            with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
                agent_text = st.session_state["agent"].ask(user_text)
        else:
            agent_text = "Sorry, I am yet to be trained on this topic. Please try some other question related to the uploaded file."

        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((agent_text, False))
        st.session_state["user_input"] = ""  # Clear the input field after sending a message

def read_and_save_file():
    st.session_state["agent"].forget()
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""

    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {file.name}"):
            st.session_state["agent"].ingest(file_path)
        os.remove(file_path)

def is_openai_api_key_set() -> bool:
    return len(st.session_state["OPENAI_API_KEY"]) > 0

def main():
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
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
        on_change=read_and_save_file,
        label_visibility="collapsed",
        accept_multiple_files=True,
        disabled=not is_openai_api_key_set(),
    )

    st.session_state["ingestion_spinner"] = st.empty()

    display_messages()

    # Use st.form to handle the Enter button
    with st.form(key="message_form"):
        user_input = st.text_input("Ask a medical question", key="user_input", disabled=not is_openai_api_key_set())
        submit_button = st.form_submit_button("Enter", onclick=process_input)

    st.divider()

if __name__ == "__main__":
    main()
