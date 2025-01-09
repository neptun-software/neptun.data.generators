import os
import json
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Ensure it is set in the .env file.")

client = OpenAI(api_key=api_key)
GPT_MODEL = "gpt-3.5-turbo-0125"
INPUT_DIR="data/scraped-images.txt"
OUTPUT_PATH = "jsonl/docker_info_entries.jsonl"

def generate_general_info_entry(line):
    """Generate general information entry for a Docker image."""
    docker_image = line.strip()
    prompt = (
        f"Generate multiple JSONL entries for `{docker_image}`. "
        f"Each entry should describe use cases, version details, and best practices for this image. "
        f"Use variations in user input but focus solely on generating these details. "
        f"Each JSONL entry should follow this format:\n"
        f'{{"text": "System: Provide detailed information about Docker images.\\n\\nUser: What is `{docker_image}` used for?\\n\\nAssistant: [Detailed answer including use cases, examples, and best practices]"}}\n'
    )

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are a generator of Docker image information."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=700,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating general info entries for {docker_image}: {e}")
        return None

def main(input_file):
    """Process Docker images and generate general information entries."""
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as output:
        for line in lines:
            print(f"Processing: {line.strip()}")
            entry = generate_general_info_entry(line)
            if entry:
                for entry_line in entry.split("\n"):
                    if entry_line.strip():
                        json_output = {
                            "text": f"System: Provide detailed information about Docker images.\n\n{entry_line.strip()}"
                        }
                        output.write(json.dumps(json_output) + "\n")

    print(f"General information entries saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main(INPUT_DIR)