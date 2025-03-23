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
    model="gemini-1.5-flash",
    convert_system_message_to_human=True,
    temperature=0.5,
    max_tokens=2000,
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

class Slide(BaseModel):
    """Schema for a slide."""
    title: str = Field(..., description="Title of the slide")
    key_points: List[str] = Field(..., description="Key bullet points for the slide")
    teacher_speech: str = Field(..., description="Natural teacher speech explaining this slide's content")

class Content(BaseModel):
    """Schema for content for a subtopic."""
    title: str = Field(..., description="Title of the subtopic")
    introduction: str = Field(..., description="Friendly introduction to the subtopic")
    slides: List[Slide] = Field(..., description="List of slides with content and teacher speech")
    conclusion: str = Field(..., description="Wrap-up message for the subtopic")

subtopics_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert educational content creator. Given a main topic, 
identify 4-6 key subtopics that would make a comprehensive lesson. Each subtopic should be:
- Focused enough to explain in 5-7 minutes
- Build logically on previous subtopics
- Include a mix of concepts, applications, and examples

Format output as JSON matching this schema:
```json
{schema}
```
Wrap the JSON output in ```json tags."""),
    ("human", "Generate subtopics for: {topic}")
]).partial(schema=Subtopics.schema())

def extract_json_for_content(message: Any) -> List[Dict[str, Any]]:
    """Extracts the JSON content from the model's response."""
    text = message.content if hasattr(message, 'content') else message
    print("Raw Text from LLM:\n", text)

    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    extracted_contents = []
    for match in matches:
        try:
            json_data = json.loads(match.strip())
            
            if "title" in json_data and "introduction" in json_data:
                extracted_contents.append(json_data)
            
            elif "Content" in json_data:
                extracted_contents.append(json_data["Content"])
        except Exception as e:
            print(f"Error parsing JSON: {str(e)}")

    return extracted_contents

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

content_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a friendly and engaging college professor teaching students. 
    For the given subtopic, create a natural teaching flow:
    
    1. Start with a warm introduction to get students interested
    2. For each main point:
        - Create a clear slide with bullet points
        - Write out your natural teaching speech as if you're in class
        - Include rhetorical questions and engagement points
        - Use analogies and real-world examples
        - Connect points to previous knowledge
    3. End with a brief conclusion that bridges to the next topic
    
    Be conversational and enthusiastic! Use phrases like:
    - "Now, let's explore..."
    - "You might be wondering..."
    - "Here's an interesting example..."
    - "Can anyone guess..."
    
    Return a single JSON object (not a schema definition) with the following structure:
    {{
        "title": "subtopic title",
        "introduction": "friendly intro text",
        "slides": [
            {{
                "title": "slide title",
                "key_points": ["point 1", "point 2"],
                "teacher_speech": "natural speech for this slide"
            }}
        ],
        "conclusion": "wrap-up message"
    }}
    
    Wrap the JSON output in ```json tags."""),
    ("human", "Create teaching content for subtopic: {subtopic}")
])

subtopics_chain = subtopics_prompt | llm | extract_json_for_subtopics
content_chain = content_prompt | llm | extract_json_for_content

def main():
    main_topic = "Introduction to AI"
    print(f"\nGenerating lesson plan for: {main_topic}\n")
    
    subtopics = subtopics_chain.invoke({"topic": main_topic})
    print("Generated Subtopics:")
    for idx, subtopic in enumerate(subtopics[0], 1):
        print(f"{idx}. {subtopic['title']}")
    
    final_output = {
        "main_topic": main_topic,
        "content": []
    }
    
    print("\nGenerating detailed content for each subtopic...")
    for subtopic in subtopics[0]:
        print(f"\nProcessing: {subtopic['title']}")
        content_response = content_chain.invoke({
            "subtopic": subtopic["title"]
        })
        if content_response:
            final_output["content"].append(content_response[0])
    
    output_file = "lesson_plan.json"
    with open(output_file, "w", encoding='utf-8') as file:
        json.dump(final_output, file, indent=4, ensure_ascii=False)
    
    print(f"\nLesson plan generated and saved to {output_file}")

if __name__ == "__main__":
    main()
    
