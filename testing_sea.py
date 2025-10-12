from sea.solver import solver
from sea.critic import critic
from utils.evals_utils import extract_boolean

query = "Janet’s ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes muffins for her friends every day with four. She sells the remainder at the farmers' market daily for $2 per fresh duck egg. How much in dollars does she make every day at the farmers' market?"
response = solver(query)
critic = critic(query, response)
bol = extract_boolean(critic['messages'][-1].content)
if bool(bol):
    print("DONT Call Updater")
else:
    print("Call Updater")

print(f"Query: {query}\nResponse: {response}\n Critic:{critic['messages'][-1].content}")


# TODO
# 1. Find a case where the critic says the model fails
# 2. Construct a loop and update the prompt until the critic says True.
#     - Figure out how to update, pass the updaters output to the prompt.
#         - have a variable called updated_prompt and set it to None, when the updater passes a prompt pass it to the solver and use this updated version rather than the old one.

