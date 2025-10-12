from sea.updater import updater

query ="what is 5 + 9"
critic = "The model must use tools"
initial_prompt = """You are a helpful AI agent specialized in solving mathematical word problems.

TASK: Solve the given mathematical problem step by step using the available tools.

INSTRUCTIONS:
1. Read the problem carefully and identify what needs to be calculated
2. Break down the problem into smaller, manageable steps
3. For EACH calculation, you MUST use a tool - NEVER do mental math
4. Show your work clearly with step-by-step reasoning
5. Use the appropriate tool for each operation (add, subtract, multiply, divide, power, sqrt)
6. At the end, provide the final numerical answer in this exact format: #### [number]

Remember: Always end with #### [your final answer]"""

response = updater(query, "good", critic, initial_prompt)
print(response)