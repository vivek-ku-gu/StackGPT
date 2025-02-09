from langchain_deepseek import ChatDeepSeek
from pymongo import MongoClient
import google.generativeai as genai
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import os
import json
import uuid
load_dotenv()
GENAI_API_KEY = os.environ["GOOGLE_API_KEY"]
MONGO_URI = os.environ["MONGO_URI"]
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
INDEX_NAME = "vector_index"
def get_gemini_embedding(text):
  embedding = genai.embed_content(
        model="models/text-embedding-004",content=text)
  return  embedding['embedding']

try:
      # Establish connection
      client = MongoClient(MONGO_URI)
      # Access database
      db = client["StackGPT"]
      # Access or create collection
      collection = db.get_collection("POC")
except Exception as e:
    print(f"An error occurred: {e}")
    print(f"MONGO_URI: {MONGO_URI}")  # Print the URI for debugging

def find_relevant_documents(query_text, top_k):
        # Get embedding for the query
        indexes = collection.list_indexes()
        for index in indexes:
            print(index)
        query_embedding = get_gemini_embedding(query_text)

        # Perform vector search in MongoDB
        results = collection.aggregate([
            {
                "$vectorSearch": {
                    "index": INDEX_NAME,
                    "path": "embeddings",
                    "queryVector": query_embedding,
                    "numCandidates": 100,
                    "limit": top_k
                }
            }
        ])

        return list(results)

def store_query_embedding_in_mongodb(query, embedding):
  """
  Stores the query and its embedding in the MongoDB database.

  Args:
    query: The query string.
    embedding: The embedding vector for the query.
  """
  try:
      document = {
          "embeddings": str(embedding),
          "query": query,
          "hit": 0
      }
      result = collection.insert_one(document)
  except Exception as e :
      print("insertion failed", e)

  finally:
      # Close the connection
      client.close()
      print(f"Document inserted with ID: {result.inserted_id}")

def store_query_embedding_and_result_in_mongodb(query,res_gemini,res_llama,res_deepseek):
    embedding = get_gemini_embedding(query)
    thread_id = str(uuid.uuid4())
    thread_name = "Results generated during Testing"

    try:
        document = {
            "embeddings": embedding,
            "query": query,
            "result_gemini": res_gemini,
            "result_llama": res_llama,
            "result_deepseek": res_deepseek,
            "thread_name": f"{thread_name} with id {thread_id}",
            "thread_id": thread_id
        }
        result = collection.insert_one(document)
        saved_document = collection.find_one({"_id": result.inserted_id}, {"_id": 0})
        return saved_document

    except Exception as e:
        print("Insertion failed", e)
        return None

    finally:
        client.close()
        print(f"Document inserted with ID: {result.inserted_id}")
async def get_response_from_gemini(prompt):
    response= model.generate_content(prompt)
    result = response.text
    return result
async def generate_response_Llama(prompt_input):
    chat = ChatGroq(temperature=0, groq_api_key=os.environ["GROQ_LLAMA_API"], model_name="llama-3.3-70b-versatile")
    system = "You are a helpful assistant."
    human = "{text}"
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])

    chain = prompt | chat
    AI_message = chain.invoke({"text": prompt_input})
    response = AI_message.content
    return response
async  def generate_response_deepseek(prompt_input):
    chat = ChatGroq(temperature=0, groq_api_key=os.environ["GROQ_LLAMA_API"], model_name="deepseek-r1-distill-llama-70b")
    system = "You are a helpful assistant."
    human = "{text}"
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])

    chain = prompt | chat
    AI_message = chain.invoke({"text": prompt_input})
    response = AI_message.content
    return response
# Update hit count (example)
#update_hit_count("POC", query)
# if query:
#  embedding = get_gemini_embedding(query)
#  # response = store_query_embedding_and_result_in_mongodb(query, embedding)
#  # st.write(embedding)
#  relevent_docs = find_relevant_documents(query,1)
#  st.write(relevent_docs)
#  # st.write(response)
#  print("succesfully executed")