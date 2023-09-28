import os
import tempfile
import streamlit as st
from streamlit_chat import message
from agent import Agent
import pytube
from pytube import YouTube

# Set Streamlit page configuration
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

# Helper function to display chat messages
def display_messages():
    st.subheader("Chat")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()

# Helper function to process user input
def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
            agent_text = st.session_state["agent"].ask(user_text)

        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((agent_text, False))
        
def read_and_save_file():
    st.session_state["agent"].forget()
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""
    st.session_state["youtube_link"] = ""  # Reset the YouTube link

    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        # Pass the PDF file name to the ingest method
        pdf_name = file.name
        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {pdf_name}"):
            st.session_state["agent"].ingest_pdf(file_path, pdf_name)
        os.remove(file_path)
        
# Helper function to retrieve YouTube video transcription
def retrieve_youtube_transcription(youtube_link):
    try:
        # Extract video ID from the YouTube link
        video_id = pytube.extract.video_id(youtube_link)

        # Initialize YouTube object and fetch video
        yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
        yt_captions = yt.captions

        # Search for English (auto-generated) caption track if available
        caption = None
        for track in yt_captions:
            if 'en' in track.code:
                caption = track
                break

        if caption:
            transcription_text = caption.generate_srt_captions()
            return transcription_text
        else:
            return None

    except Exception as e:
        st.error(f"Error retrieving YouTube transcription: {str(e)}")
        return None

# Main function
def main():
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
        st.session_state["youtube_link"] = ""  # Initialize the YouTube link
        if st.session_state["OPENAI_API_KEY"]:
            st.session_state["agent"] = Agent(st.session_state["OPENAI_API_KEY"])
        else:
            st.session_state["agent"] = None

    st.header("Medical ChatBot")

    if st.text_input("OpenAI API Key", value=st.session_state.get("OPENAI_API_KEY", ""), key="input_OPENAI_API_KEY", type="password"):
        if (
            len(st.session_state["input_OPENAI_API_KEY"]) > 0
            and st.session_state["input_OPENAI_API_KEY"] != st.session_state.get("OPENAI_API_KEY", "")
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
        disabled=not st.session_state.get("OPENAI_API_KEY"),
    )

    st.session_state["ingestion_spinner"] = st.empty()

    display_messages()
    st.text_input("Ask a medical question", key="user_input", disabled=not st.session_state.get("OPENAI_API_KEY"), on_change=process_input)

    # YouTube Video Transcription Support
    st.subheader("Retrieve YouTube Video Transcription")
    st.text_input("Paste YouTube Link", key="youtube_link")
    if st.button("Retrieve Transcription"):
        process_youtube_link()

    st.divider()

if __name__ == "__main__":
    main()
