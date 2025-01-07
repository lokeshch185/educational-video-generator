import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-pro")
response = llm.invoke("hello")
print(response)

# # Prompt Template for Slide Content
# prompt = PromptTemplate(
#     input_variables=["topic"],
#     template=(
#         "Create an educational presentation on '{topic}'. "
#         "Provide slide titles and key points for each slide. Use the following format:\n\n"
#         "Slide 1: Title\n- Point 1\n- Point 2\n\n"
#         "Slide 2: Title\n- Point 1\n- Point 2\n\n"
#     )
# )

# def generate_presentation_content(topic):
#     content = llm(prompt.format(topic=topic))
#     return content

# topic = "Introduction to Machine Learning"
# presentation_content = generate_presentation_content(topic)
# print(presentation_content)
