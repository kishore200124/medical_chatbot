import os
import tempfile
import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi
import streamlit as st
from streamlit_chat import message
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import OpenAI

class Agent:
    def __init__(self, openai_api_key: str = None) -> None:
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.llm = OpenAI(temperature=0, openai_api_key=openai_api_key)
        self.chat_history = None
        self.chain = None
        self.db = None
        self.current_pdf = None  # To keep track of the currently ingested PDF
        self.youtube_transcripts = {}  # To store YouTube transcripts and summaries

    def ask(self, question: str) -> str:
        if self.chain is None:
            response = "Please, add a document or YouTube transcript."
        else:
            response = self.chain({"question": question, "chat_history": self.chat_history})
            response = response["answer"].strip()

            # Check if the response contains "I don't know" and replace it with the desired message
            if "I don't know." in response:
                response = "Sorry, I am yet to be trained on this topic. Please try some other question related to the uploaded file or YouTube video."
            else:
                # Include the reference to the PDF file or YouTube video if available
                if self.current_pdf:
                    response += f" (Ref: {self.current_pdf})"
                elif self.current_video:
                    response += f" (Ref: {self.current_video})"
                
            self.chat_history.append((question, response))
        return response

    def ingest(self, file_path: os.PathLike, pdf_name: str) -> None:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        splitted_documents = self.text_splitter.split_documents(documents)
        
        self.current_pdf = pdf_name  # Store the PDF file name
        
        if self.db is None:
            self.db = FAISS.from_documents(splitted_documents, self.embeddings)
            self.chain = ConversationalRetrievalChain.from_llm(self.llm, self.db.as_retriever())
            self.chat_history = []
        else:
            self.db.add_documents(splitted_documents)

    def ingest_youtube_transcript(self, youtube_link: str) -> None:
        # Extract video ID from the YouTube link
        video_id = youtube_link.split("?v=")[-1]

        # Fetch the video transcript
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
        except youtube_transcript_api.exceptions.TranscriptUnavailable:
            return "Transcript not available for this video."

        # Summarize the transcript into chapters (adjust this as needed)
        chapters = []  # Each chapter is a list of transcript lines
        current_chapter = []
        chapter_length = 0  # Approximate number of characters per chapter
        max_chapter_length = 2000  # Adjust this value as needed

        for line in transcript:
            current_chapter.append(line["text"])
            chapter_length += len(line["text"])

            if chapter_length >= max_chapter_length:
                chapters.append("\n".join(current_chapter))
                current_chapter = []
                chapter_length = 0

        if current_chapter:
            chapters.append("\n".join(current_chapter))

        # Store the transcript and chapters
        self.youtube_transcripts[youtube_link] = chapters

        # Ingest the chapters into the agent's knowledge base
        for i, chapter in enumerate(chapters):
            self.ingest_text(chapter, f"Chapter {i + 1}")

    def ingest_text(self, text: str, text_name: str) -> None:
        documents = [text]
        splitted_documents = self.text_splitter.split_documents(documents)

        if self.db is None:
            self.db = FAISS.from_documents(splitted_documents, self.embeddings)
            self.chain = ConversationalRetrievalChain.from_llm(self.llm, self.db.as_retriever())
            self.chat_history = []
        else:
            self.db.add_documents(splitted_documents)
            self.chain = ConversationalRetrievalChain.from_llm(self.llm, self.db.as_retriever())

    def forget(self) -> None:
        self.db = None
        self.chain = None
        self.chat_history = None
        self.current_pdf = None
        self.youtube_transcripts = {}  # Reset YouTube transcripts

# ... (rest of the Agent class)

