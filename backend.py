import uvicorn
from fastapi import FastAPI, Request, Form
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from dotenv import load_dotenv
from langchain_community.document_loaders import CSVLoader
import pandas as pd
import os

load_dotenv()

app = FastAPI()
groq_api_key = os.getenv("GROQ_API_KEY")

# In-memory storage for personal details (use a database for production)
personal_details = {}

def setup_chain():
    base_template = """
    You are a knowledgeable healthcare assistant. Based on the following context, provide a clear, concise, and helpful response to the user's question.
    
    Context: {context}
    
    User's Question: {question}
    
    Your response should include the following sections:
    - **Symptoms**: Describe the symptoms associated with the health condition or query.
    - **Medication Information**: Provide information on relevant medications, including their uses and potential side effects.
    - **Wellness Advice**: Recommend general wellness tips, including diet, exercise, and mental health advice.
    - **Treatment Suggestions**: Suggest potential treatments based on the user's symptoms or conditions.
    
    Always remind the user to consult a healthcare professional for a definitive diagnosis or treatment.
    Reply in a humane format
     
    Response:
    """


    personal_context = (
        f"User's Age: {personal_details.get('age', 'Not provided')}, "
        f"Dietary Restrictions: {personal_details.get('dietary_restrictions', 'Not provided')}, "
        f"Fitness Goals: {personal_details.get('fitness_goals', 'Not provided')}."
    )
    template = f"{personal_context}\n\n{base_template}"
    
    # Set up model and embeddings
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    embeddings = HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    loader = CSVLoader(file_path="dataset.csv", encoding='utf-8')
    docs = loader.load()
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    db = DocArrayInMemorySearch.from_documents(docs, embeddings)
    retriever = db.as_retriever()
    chain_type_kwargs = {"prompt": prompt}

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs=chain_type_kwargs,
        verbose=True
    )
    return chain

agent = setup_chain()

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    question = data.get("prompt")
    response = agent.run(question)
    return {"response": response}

@app.post("/personal")
async def personal_details_endpoint(request: Request):
    data = await request.json()
    personal_details["age"] = data.get("age")
    personal_details["dietary_restrictions"] = data.get("dietary_restrictions")
    personal_details["fitness_goals"] = data.get("fitness_goals")
    return {"message": "Personal details stored successfully."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)