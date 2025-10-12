import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

def phi_llm(query):
    basic_prompt_file = "prompt_templates/basic_p.txt"
    with open(basic_prompt_file, 'r') as file:
        BASIC_PROMPT = file.read()
    
    prompt_template = PromptTemplate.from_template(BASIC_PROMPT)
    # prompt_template.invoke({"question": query})
    
    llm = ChatOpenAI(
            base_url=os.getenv("WB_INFERENCE_BASE_URL"),
            api_key=os.getenv("WANDB_API_KEY"),
            model=os.getenv("WB_INFERENCE_MODEL"),
    )

    chain = prompt_template | llm
    response = chain.invoke({"question": query})
    return response.content