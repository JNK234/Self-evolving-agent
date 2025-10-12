# ABOUTME: Utility to generate structured JSON rubrics from human descriptions
# ABOUTME: Uses LLM to transform vague criteria into machine-readable evaluation rubrics

import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def generate_rubric(description: str, output_file: str = "rubric.json") -> dict:
    """
    Generate a structured rubric from a human description.

    Args:
        description: Human-provided description of ideal output characteristics
        output_file: Path to save the generated rubric JSON

    Returns:
        Generated rubric as dictionary
    """
    meta_prompt = """You are a rubric designer. Given a description of an ideal output,
generate a detailed, structured JSON rubric.

The rubric MUST follow this exact structure:
{
  "name": "Descriptive rubric name",
  "version": "1.0",
  "description": "Brief description of what this rubric evaluates",
  "criteria": [
    {
      "id": "criterion_id_snake_case",
      "description": "Clear description of what this criterion evaluates",
      "weight": 0.X,  // Must sum to 1.0 across all criteria
      "expected_pattern": "What patterns or characteristics to look for"
    }
  ]
}

Make the rubric comprehensive, machine-parseable, and actionable.
Output ONLY valid JSON, no additional text."""

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
    )

    messages = [
        SystemMessage(content=meta_prompt),
        HumanMessage(content=f"Create a rubric for: {description}")
    ]

    response = llm.invoke(messages)

    # Parse JSON from response
    rubric_text = response.content.strip()
    # Remove markdown code blocks if present
    if rubric_text.startswith("```"):
        rubric_text = rubric_text.split("```")[1]
        if rubric_text.startswith("json"):
            rubric_text = rubric_text[4:]
        rubric_text = rubric_text.strip()

    rubric = json.loads(rubric_text)

    # Validate weights sum to 1.0
    total_weight = sum(c["weight"] for c in rubric["criteria"])
    if abs(total_weight - 1.0) > 0.01:
        print(f"Warning: Criterion weights sum to {total_weight}, not 1.0. Normalizing...")
        for criterion in rubric["criteria"]:
            criterion["weight"] = criterion["weight"] / total_weight

    # Save to file
    with open(output_file, 'w') as f:
        json.dump(rubric, f, indent=2)

    print(f"✓ Rubric generated and saved to {output_file}")
    return rubric


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python rubric_generator.py '<description>'")
        print("Example: python rubric_generator.py 'A good math solution shows work, uses tools, and formats the answer clearly'")
        sys.exit(1)

    description = sys.argv[1]
    rubric = generate_rubric(description)

    print("\nGenerated Rubric:")
    print(json.dumps(rubric, indent=2))
