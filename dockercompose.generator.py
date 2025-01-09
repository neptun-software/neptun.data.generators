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
OUTPUT_PATH = "jsonl/docker_compose_entries.jsonl"

def generate_docker_compose_entry(line):
    """Generate docker-compose.yml entry for a Docker image."""
    docker_image = line.strip()
    prompt = (
        f"Generate multiple JSONL entries for using `{docker_image}` in a docker-compose.yml file. "
        f"Each entry should focus on a specific use case or service setup, providing clear configurations. "
        f"Use variations in user input but focus solely on generating the docker-compose.yml file content. "
        f"Each JSONL entry should follow this format:\n"
        f'{{"text": "System: You are a generator of docker-compose.yml files.\\n\\nUser: I need a Docker Compose setup for `{docker_image}`.\\n\\nAssistant: version: \'3.9\'\\nservices:\\n  app:\\n    image: {docker_image}\\n    ports:\\n      - \"5000:5000\"\\n    volumes:\\n      - .:/app\\n    command: [example command]"}}\n'
    )

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are a generator of docker-compose.yml files."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=700,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating docker-compose entries for {docker_image}: {e}")
        return None

def main(input_file):
    """Process Docker images and generate docker-compose.yml entries."""
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as output:
        for line in lines:
            print(f"Processing: {line.strip()}")
            entry = generate_docker_compose_entry(line)
            if entry:
                for entry_line in entry.split("\n"):
                    if entry_line.strip():
                        json_output = {
                            "text": f"System: You are a generator of docker-compose.yml files.\n\n{entry_line.strip()}"
                        }
                        output.write(json.dumps(json_output) + "\n")

    print(f"Docker Compose entries saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main(INPUT_DIR) 