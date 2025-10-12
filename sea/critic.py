import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from typing import List, Dict
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate


load_dotenv()

def critic(problems_data: List[Dict]):
    with open("prompt_templates/sea_critic_p.txt", "r") as f:
        system_prompt = f.read()

    llm = ChatOpenAI(
        base_url=os.getenv("WB_INFERENCE_BASE_URL"),
        api_key=os.getenv("WANDB_API_KEY"),
        model=os.getenv("WB_INFERENCE_MODEL"),
    )
    
    # Format the problems data for the critic
    problems_text = ""
    for i, problem in enumerate(problems_data):
        problems_text += f"\nProblem {i+1}:\n"
        problems_text += f"Query: {problem['question']}\n"
        problems_text += f"Expected Answer: {problem['expected_answer']}\n"
        problems_text += f"Model Response: {problem['response']}\n"
        problems_text += f"Correct: {problem['is_correct']}\n"
        problems_text += "-" * 50 + "\n"
    
    prompt_template = PromptTemplate.from_template(system_prompt)
    chain = prompt_template | llm
    
    response = chain.invoke({
        "problems_data": problems_text
    })
    
    return response.content