import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5",
    temperature=0.5,
    max_tokens=100,
    timeout=None,
    max_retries=1,
)
response = llm.invoke("hello")
print(response)

slide_titles_prompt = PromptTemplate(
    input_variables=["topic"],
    template=(
        "Create an outline for an educational presentation on '{topic}'. "
        "Provide only slide titles as a numbered list."
    ),
)

slide_content_prompt = PromptTemplate(
    input_variables=["slide_title"],
    template=(
        "Provide detailed key points for the slide titled '{slide_title}' in an educational presentation. "
        "Use bullet points for clarity."
    ),
)

def generate_slide_titles(topic):
    titles_response = llm.invoke(slide_titles_prompt.format(topic=topic))
    titles = titles_response.split("\n")
    return [title.strip() for title in titles if title.strip()]

def generate_slide_content(slide_title):
    content_response = llm.invoke(slide_content_prompt.format(slide_title=slide_title))
    return content_response.strip()

def generate_presentation(topic):
    slide_titles = generate_slide_titles(topic)
    if not slide_titles:
        return "No slide titles generated."
    presentation = {}
    for title in slide_titles:
        content = generate_slide_content(title)
        presentation[title] = content
    return presentation

topic = "Introduction to Machine Learning"
presentation = generate_presentation(topic)

for slide, content in presentation.items():
    print(f"Slide: {slide}")
    print(content)