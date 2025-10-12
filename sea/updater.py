import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate


load_dotenv()

def updater(query: str, response: str, critic: str, initial_prompt: str):
    with open("prompt_templates/sea_updater_p.txt", "r") as f:
        system_prompt = f.read()


    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        timeout=None,
        max_retries=1,
    )

    # llm = ChatOpenAI(
    #     base_url=os.getenv("WB_INFERENCE_BASE_URL"),
    #     api_key=os.getenv("WANDB_API_KEY"),
    #     model=os.getenv("WB_INFERENCE_MODEL"),
    # )
    
    prompt_template = PromptTemplate.from_template(system_prompt)
    chain = prompt_template | llm
    response = chain.invoke({
        "query": query,
        "response": response, 
        "critic": critic, 
        "initial_prompt": initial_prompt
    })
    return response.content