import os
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
        self.current_pdf = None
        self.current_transcription = None  # To keep track of the currently ingested transcription

    def ask(self, question: str) -> str:
        if self.chain is None:
            response = "Please, add a document or provide a YouTube link."
        else:
            response = self.chain({"question": question, "chat_history": self.chat_history})
            response = response["answer"].strip()

            if "I don't know" in response:
                response = "Sorry, I am yet to be trained on this topic. Please try some other question related to the uploaded files."
            else:
                if self.current_pdf:
                    response += f" (Ref: {self.current_pdf})"
                if self.current_transcription:
                    response += f" (YouTube Transcription)"
                
            self.chat_history.append((question, response))
        return response

    def ingest_pdf(self, file_path: os.PathLike, pdf_name: str) -> None:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        splitted_documents = self.text_splitter.split_documents(documents)
        
        self.current_pdf = pdf_name
        
        if self.db is None:
            self.db = FAISS.from_documents(splitted_documents, self.embeddings)
            self.chain = ConversationalRetrievalChain.from_llm(self.llm, self.db.as_retriever())
            self.chat_history = []
        else:
            self.db.add_documents(splitted_documents)

    def ingest_transcription(self, transcription_text: str) -> None:
        # Split the transcription_text into chunks if needed
        # Store the chunks for retrieval
        self.current_transcription = transcription_text

    def forget(self) -> None:
        self.db = None
        self.chain = None
        self.chat_history = None
        self.current_pdf = None
        self.current_transcription = None
