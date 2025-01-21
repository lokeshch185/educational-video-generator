import os
from dotenv import load_dotenv
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage,SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda, RunnableMap, RunnablePassthrough, RunnableParallel
from typing import Optional, List
from pydantic import BaseModel, Field

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    convert_system_message_to_human=True,
    temperature=0.5,
    max_tokens=1000,
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

class Slide(BaseModel):
    """Schema for a slide."""
    title: str = Field(..., description="Title of the slide")
    key_points: List[str] = Field(..., description="Key points for the slide")

class Content(BaseModel):
    """Schema for content for a subtopic."""
    title: str = Field(..., description="Title of the subtopic")
    speech: str = Field(..., description="Natural speech text explaining the subtopic")
    slides: List[Slide] = Field(..., description="List of slides with titles and key points")



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
    # Regular expression to match JSON content
    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    try:
        # Parse JSON and extract the 'subtopics' key
        return [
            json.loads(match.strip())["subtopics"]
            for match in matches
            if "subtopics" in json.loads(match.strip())
        ]
    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {str(e)}")


def extract_json_for_content(message: AIMessage) -> List[Content]:
    """
    Extracts the relevant JSON content from the model's response.

    Parameters:
        message (AIMessage): The message object containing the content.

    Returns:
        List[Content]: A list of Content objects extracted from the response.
    """
    import re
    import json
    from typing import List

    text = message.content
    print("Raw Text from LLM:\n", text)  # Debugging: Print raw text
    
    # Regular expression to match JSON content
    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    print("Extracted Matches:", matches)  # Debugging: Print matched content

    contents = []
    for match in matches:
        try:
            # Parse the JSON string
            json_data = json.loads(match.strip())

            # Validate required keys before processing
            if "title" in json_data and "speech" in json_data and "slides" in json_data:
                slides = [
                    Slide(
                        title=slide.get("title", ""),  # Safely fetch the slide title
                        key_points=slide.get("key_points", [])  # Safely fetch key points
                    )
                    for slide in json_data["slides"]
                ]
                content = Content(
                    title=json_data["title"],
                    speech=json_data["speech"],
                    slides=slides
                )
                contents.append(content)
        except Exception as e:
            print(f"Error parsing JSON: {str(e)}")  # Debugging: Log errors

    return contents

content_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an experienced teacher creating lesson content. 
    For the given subtopic, create:
    1. Natural speech text as if you're explaining it to students.
    2. Key points that should appear on presentation slides while the explanation is given.
    Make the explanation engaging and clear, suitable for the target education level.
    Keep the speech conversational but informative. format them as JSON matching this schema: \n\n
```json\n{schema}\n```. Wrap the JSON output in ```json tags. """),
    ("human", "Create lesson content for subtopic: {subtopic} of main topic: {topic}")
]).partial(schema=Content.schema())

subtopics_chain = subtopics_prompt | llm | extract_json_for_subtopics
content_chain = content_prompt | llm | extract_json_for_content


subtopics = subtopics_chain.invoke({"topic": "Introduction to Machine Learning"})
print(subtopics[0])

for subtopic in subtopics[0]:
    # Pass the subtopic and topic to content_chain
    content = content_chain.invoke({
        "topic": "Introduction to Machine Learning",
        "subtopic": subtopic["title"]
    })
    # Print the generated content
    print(f"Content for {subtopic['title']}:\n")
    print(content)
    print("\n" + "-"*50 + "\n")

