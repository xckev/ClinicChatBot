import ast  # for converting embeddings saved as strings back to arrays/lists
import openai  # for calling the OpenAI API
import pandas as pd  # for storing text and embeddings data
import tiktoken  # for counting tokens
import os
from dotenv import load_dotenv, dotenv_values
import csv
from scipy import spatial  # for calculating vector similarities for search
#absl imports
#from absl import app 
#from absl import flags
import chromadb
from chromadb.utils import embedding_functions
#flask imports
from flask import Flask, jsonify
import requests

app = Flask(__name__)

# models
EMBEDDING_MODEL = "text-embedding-ada-002"
GPT_MODEL = "gpt-3.5-turbo"

#openai key
load_dotenv()
openai_key = os.getenv("openaiKey")

client = chromadb.PersistentClient(path="./data/Ma_Acupuncture/chroma_db")

reviews_file = "./data/Ma_Acupuncture/Ma's_Acupuncture_Clinic_Review_Dataset.csv"
webcontent_file = "./data/Ma_Acupuncture/Ma's_Acupuncture_Clinic_Webcontent_Dataset.csv"

def main():
  print('Reviews file: ', reviews_file)
  print('Webcontent file: ', webcontent_file)
  print('OpenAI Key: ', openai_key)

  print("-----Starting Server-----")
  print("Getting OpenAI API Key...")
  openai.api_key = openai_key

  print("Getting embeddings...")
  openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai_key,
    model_name=EMBEDDING_MODEL
  )
  
  global review_collection
  global webcontent_collection
  try:
    review_collection = client.get_collection(name="review_embeddings", embedding_function=openai_ef)
    webcontent_collection = client.get_collection(name="webcontent_embeddings", embedding_function=openai_ef)
  except ValueError:
    review_collection = client.create_collection(name="review_embeddings", embedding_function=openai_ef)
    webcontent_collection = client.create_collection(name="webcontent_embeddings", embedding_function=openai_ef)
    print("Collections not found. Populating new db...")
    review_df = getNewDf(reviews_file, "Review")
    webcontent_df = getNewDf(webcontent_file, "Text")
    populateDB(review_df, webcontent_df)
  
  print("-----Process Complete-----")
  print("Ready to respond to questions")

#get all reviews and their embeddings in a Dataframe
def getNewDf(csvname, columnName):
  #reading csv into dataframe
  df = pd.read_csv(csvname)
  links = df[["Link"]]
  df = df[[columnName]]
  df["Link"] = links

  df.reset_index(drop=True)

  return df

#Use chromadb !
def populateDB(review_df: pd.DataFrame, webcontent_df: pd.DataFrame):
  idnum = 1
  doclist = []
  metalist = []
  idlist = []
  for i, row in review_df.iterrows():
    doclist.append(str(row["Review"]))
    metalist.append({"Link": str(row["Link"])})
    idlist.append(str(idnum))
    idnum += 1
    
  review_collection.add(
    documents=doclist,
    metadatas=metalist,
    ids=idlist
  )
  
  idnum = 1
  doclist = []
  metalist = []
  idlist = []
  for i, row in webcontent_df.iterrows():
    doclist.append(str(row["Text"]))
    metalist.append({"Link": str(row["Link"])})
    idlist.append(str(idnum))
    idnum += 1

  webcontent_collection.add(
    documents=doclist,
    metadatas=metalist,
    ids=idlist
  )


#search function uses embeddings to return most relevant items
def most_related_reviews(query: str, top_n: int = 3) -> tuple[list[str], list[dict]]:
  result = review_collection.query(
    query_texts=[query],
    n_results=top_n
  )

  return result["documents"][0], result["metadatas"][0]


def most_related_webcontent(query: str, top_n: int = 3) -> tuple[list[str], list[str], list[float]]:
  result = webcontent_collection.query(
    query_texts=[query],
    n_results=top_n
  )

  return result["documents"][0], result["metadatas"][0]

#Return the number of tokens in a string.
def num_tokens(text: str, model: str = GPT_MODEL) -> int:
  encoding = tiktoken.encoding_for_model(model)
  return len(encoding.encode(text))

#creates query message
def query_message(query: str, model: str, token_budget: int) -> str:
  r_strings, r_links = most_related_reviews(query)
  w_strings, w_links = most_related_webcontent(query)

  intro = "Use the below reviews and website articles on Ma's Acupuncture and Traditional Chinese Medicine Clinic to answer the subsequent question. Your response will be a web chatbot response, so keep it concise."
  question = f"\n\nQuestion: {query}"
  message = intro

  for i in range(len(r_strings)):
    string = r_strings[i]
    link = r_links[i]['Link']
    next_review = f'\n\nCustomer Review:\n"""\n{string}\n\nLink: {link}\n"""'
    if(num_tokens(next_review+question, model=model) > (token_budget / 2)):
      break
    else:
      message += next_review

  for i in range(len(w_strings)):
    string = w_strings[i]
    link = w_links[i]['Link']
    next_webcontent = f'\n\nWebsite Article:\n"""\n{string}\n\nLink: {link}\n"""'
    if(num_tokens(message+next_webcontent+question, model=model) > (token_budget / 2)):
      break
    else:
      message += next_webcontent

  #print(message+question)
  return message + question

#asks query message and gets back answer
def ask(query: str, model: str = GPT_MODEL, token_budget: int = 4097, print_message: bool = False) -> str:
  message = query_message(query, model=model, token_budget=token_budget)
  if print_message:
    print(message)

  messages = [{"role": "system", "content": "You answer questions about  Ma's Traditional Chinese Medicine and Acupuncture Clinic"}, {"role": "user", "content": message}]
  response = openai.ChatCompletion.create(model = model, messages = messages, temperature = 0)
  response_message = response["choices"][0]["message"]["content"]
  return response_message

@app.route('/', methods=['GET'])
def get_home():
  toReturn = jsonify({"text": "Welcome to the ClinicChatBot backend server! API requests may be requested from this URL."})
  toReturn.headers.add('Access-Control-Allow-Origin', '*')
  return toReturn

@app.route('/response/<string:question>', methods=['GET'])
def get_response(question):
  toReturn = jsonify({"response": ask(question)})
  toReturn.headers.add('Access-Control-Allow-Origin', '*')
  return toReturn

if __name__ == '__main__':
  main()
  app.run(debug=True)
