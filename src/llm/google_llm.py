import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def basic_google_llm(query, google_model = "gemini-2.5-flash"):
    basic_prompt_file = "prompt_templates/basic_p.txt"
    with open(basic_prompt_file, 'r') as file:
        BASIC_PROMPT = file.read()
    
    prompt_template = PromptTemplate.from_template(BASIC_PROMPT)
    # prompt_template.invoke({"question": query})

    llm = ChatGoogleGenerativeAI(
        model = google_model,
        temperature = 0,
        timeout = None,
        max_retries=1,
    )
    chain = prompt_template | llm
    response = chain.invoke({"question": query})
    return response.content