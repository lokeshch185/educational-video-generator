import os
from dotenv import load_dotenv
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage,SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda, RunnableMap, RunnablePassthrough, RunnableParallel
from typing import Optional, List ,Dict, Any
from pydantic import BaseModel, Field

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    convert_system_message_to_human=True,
    temperature=0.5,
    max_tokens=500,
    timeout=None,
    generation_config={"response_mime_type": "application/json"},
    max_retries=2,
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
identify 2 key subtopics that would form a comprehensive lesson strictly and format them as JSON matching this schema: \n\n
```json\n{schema}\n```. Wrap the JSON output in ```json tags. 
Focus on the most important aspects that students need to understand."""),
    ("human", "Generate subtopics for: {topic}")
]).partial(schema=Subtopics.schema())

def extract_json_for_subtopics(message: AIMessage) -> List[dict]:
    """
    Extracts the relevant JSON content from the model's response.
    
    Parameters:
        message (AIMessage): The message object containing the content.
    
    Returns:
        List[dict]: A list of subtopics extracted from the response.
    """
    text = message.content
    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    try:
        return [
            json.loads(match.strip())["subtopics"]
            for match in matches
            if "subtopics" in json.loads(match.strip())
        ]
    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {str(e)}")



class Slide(BaseModel):
    """Schema for a slide."""
    title: str = Field(..., description="Title of the slide")
    key_points: List[str] = Field(..., description="Key points for the slide")

class Content(BaseModel):
    """Schema for content for a subtopic."""
    title: str = Field(..., description="Title of the subtopic")
    speech: str = Field(..., description="Natural speech text explaining the subtopic")
    slides: List[Slide] = Field(..., description="List of slides with titles and key points")

def extract_json_for_content(message: Any) -> List[Dict[str, Any]]:
    """
    Extracts the relevant JSON content from the model's response.

    Parameters:
        message (Any): The message object or string containing the content.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing the JSON content extracted from the response.
    """
    text = message.content if hasattr(message, 'content') else message
    # print("Raw Text from LLM:\n", text)

    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    # print("Extracted Matches:", matches)

    extracted_contents = []
    for match in matches:
        try:
            json_data = json.loads(match.strip())
            if "Content" in json_data and all(k in json_data["Content"] for k in ["title", "speech", "slides"]):
                extracted_contents.append(json_data["Content"])
        except Exception as e:
            print(f"Error parsing JSON: {str(e)}")

    return extracted_contents

content_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an experienced teacher creating lesson content. 
    For the given subtopic,1) generate Natural speech text as if you're explaining it to students.
    2. Create content for slides with titles and key points to be played during the lesson.
    Strictly format them as JSON matching this schema: \n
```json\n{schema}\n```. Wrap the JSON output in json tags.
    Make the explanation engaging and clear, suitable for the target education level.
    Keep the speech conversational but informative."""),
    ("human", "Create lesson content for subtopic: {subtopic}")
]).partial(schema=Content.schema())

subtopics_chain = subtopics_prompt | llm | extract_json_for_subtopics
content_chain = content_prompt | llm | extract_json_for_content


# response = content_chain.invoke({"topic": "Introduction to langchain", "subtopic": "features of langchain"})
# print(response)


main_topic = "Introduction to Machine Learning"
subtopics = subtopics_chain.invoke({"topic": main_topic})
print(subtopics[0])
final_output = {
    "main_topic": main_topic,
    "content": []
}
for subtopic in subtopics[0]:
    content_response = content_chain.invoke({
        "subtopic": subtopic["title"]
    })
    if content_response:
            print(content_response[0])
            final_output["content"].append(content_response[0])

output_file = "lesson_plan.json"
with open(output_file, "w") as file:
    json.dump(final_output, file, indent=4)

print(json.dumps(final_output, indent=4))
    
