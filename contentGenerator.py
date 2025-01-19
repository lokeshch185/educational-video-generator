import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage,SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
llm = GoogleGenerativeAI(
    model="gemini-pro",
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

subtopics_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert educational content creator. Given a main topic, 
    identify 3-5 key subtopics that would form a comprehensive lesson. 
    Focus on the most important aspects that students need to understand."""),
    ("human", "Generate subtopics for: {topic}")
])

lesson_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an experienced teacher creating lesson content. 
    For the given subtopic, create:
    1. Natural speech text as if you're explaining it to students
    2. Key points that should appear on presentation slides
    
    Make the explanation engaging and clear, suitable for the target education level.
    Keep the speech conversational but informative."""),
    ("human", "Create lesson content for subtopic: {subtopic} of main topic: {topic}")
])

# template = "Write a {tone} email to {company} expressing interest in the {position} position, mentioning {skill} as a key strength. Keep it to 4 lines max"

# prompt_template = ChatPromptTemplate.from_template(template)

# prompt =  prompt_template.invoke({
#     "tone": "energetic", 
#     "company": "samsung", 
#     "position": "AI Engineer", 
#     "skill": "AI"
# })

# slide_titles_prompt = PromptTemplate(
#     input_variables=["topic"],
#     template=(
#         "Create an outline for an educational presentation on '{topic}'. "
#         "Provide only slide titles as a numbered list."
#     ),
# )

# slide_content_prompt = PromptTemplate(
#     input_variables=["slide_title"],
#     template=(
#         "Provide detailed key points for the slide titled '{slide_title}' in an educational presentation. "
#         "Use bullet points for clarity."
#     ),
# )

# def generate_slide_titles(topic):
#     titles_response = llm.invoke(slide_titles_prompt.format(topic=topic))
#     titles = titles_response.split("\n")
#     return [title.strip() for title in titles if title.strip()]

# def generate_slide_content(slide_title):
#     content_response = llm.invoke(slide_content_prompt.format(slide_title=slide_title))
#     return content_response.strip()

# def generate_presentation(topic):
#     slide_titles = generate_slide_titles(topic)
#     if not slide_titles:
#         return "No slide titles generated."
#     presentation = {}
#     for title in slide_titles:
#         content = generate_slide_content(title)
#         presentation[title] = content
#     return presentation

# topic = "Introduction to Machine Learning"
# presentation = generate_presentation(topic)

# for slide, content in presentation.items():
#     print(f"Slide: {slide}")
#     print(content)