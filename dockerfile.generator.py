import os
import json
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Ensure it is set in the .env file.")

client = OpenAI(api_key=api_key)
INPUT_DIR="data/scraped-images.txt"
GPT_MODEL = "gpt-3.5-turbo-0125"
OUTPUT_PATH = "dockerfile_entries.jsonl"

def generate_dockerfile_entry(line):
    """Generate Dockerfile entry for a Docker image."""
    docker_image = line.strip()
    prompt = (
        f"Generate multiple JSONL entries for using `{docker_image}` in a Dockerfile. "
        f"Each entry should focus on a specific use case, providing clear configurations and explanations. "
        f"Use variations in user input but focus solely on generating Dockerfile content. "
        f"Each JSONL entry should follow this format:\n"
        f'{{"text": "System: You are a generator of Dockerfiles.\\n\\nUser: How do I create a Dockerfile for `{docker_image}`?\\n\\nAssistant: FROM {docker_image}\\nRUN apk add --no-cache [example package]\\nCMD [\"example\", \"command\"]"}}\n'
    )

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are a generator of Dockerfiles."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=700,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating Dockerfile entries for {docker_image}: {e}")
        return None

def main(input_file):
    """Process Docker images and generate Dockerfile entries."""
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as output:
        for line in lines:
            print(f"Processing: {line.strip()}")
            entry = generate_dockerfile_entry(line)
            if entry:
                for entry_line in entry.split("\n"):
                    if entry_line.strip():
                        json_output = {
                            "text": f"System: You are a generator of Dockerfiles.\n\n{entry_line.strip()}"
                        }
                        output.write(json.dumps(json_output) + "\n")

    print(f"Dockerfile entries saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main(INPUT_DIR)  