import os
from dotenv import load_dotenv
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage,SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from typing import Optional, List
from pydantic import BaseModel, Field

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    convert_system_message_to_human=True,
    temperature=0.5,
    max_tokens=400,
    timeout=None,
    max_retries=1,
)

# messages = [
#     ("system", ""),
#     ("human", ""),
# ]
# response = llm.invoke(messages)
# print(response.content)

class Subtopic(BaseModel):
    """Schema for each subtopic."""
    title: str = Field(..., description="The title of the subtopic")

class Subtopics(BaseModel):
    """Schema for a list of subtopics."""
    subtopics: List[Subtopic]



subtopics_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert educational content creator. Given a main topic, 
    identify key subtopics that would form a comprehensive lesson strictly and format them as JSON matching this schema: \n\n"
            "```json\n{schema}\n```. Wrap the JSON output in ```json tags. 
    Focus on the most important aspects that students need to understand."""),
    ("human", "Generate subtopics for: {topic}")
]).partial(schema=Subtopics.schema())

content_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an experienced teacher creating lesson content. 
    For the given subtopic, create:
    1. Natural speech text as if you're explaining it to students
    2. Key points that should appear on presentation slides
    
    Make the explanation engaging and clear, suitable for the target education level.
    Keep the speech conversational but informative."""),
    ("human", "Create lesson content for subtopic: {subtopic} of main topic: {topic}")
])



def extract_json_for_subtopics(message: AIMessage) -> List[dict]:
    """
    Extracts JSON content from a string where JSON is embedded between ```json and ``` tags.
    
    Parameters:
        message (AIMessage): The message object containing the content.
    
    Returns:
        List[dict]: Extracted JSON as Python objects.
    """
    text = message.content
    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    try:
        return [json.loads(match.strip()) for match in matches]
    except Exception:
        raise ValueError(f"Failed to parse: {message}")

subtopics_chain = subtopics_prompt | llm | extract_json_for_subtopics
content_chain = content_prompt | llm | StrOutputParser()

subtopic = subtopics_chain.invoke({"topic": "Introduction to Machine Learning"})
print(subtopic)