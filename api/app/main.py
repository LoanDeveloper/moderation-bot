from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

banned_topics = set()

class Topic(BaseModel):
    topic: str

@app.post("/ban_topics")
def add_topic(topic: Topic):
    banned_topics.add(topic.topic.lower())
    return {"message": "Sujet ajouté"}

@app.delete("/ban_topics")
def remove_topic(topic: Topic):
    banned_topics.discard(topic.topic.lower())
    return {"message": "Sujet supprimé"}

@app.get("/rules")
def get_rules():
    return {"banned_topics": list(banned_topics)}