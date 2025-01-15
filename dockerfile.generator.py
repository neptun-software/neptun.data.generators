import datetime
import json
import os
import dotenv
from huggingface_hub import InferenceClient
import logging
import dockerfile

# Logging Configuration
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

dotenv.load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

client = InferenceClient(token=API_TOKEN)
TOP_P = 0.7
TEMPERATURE = 0.6
MAX_TOKENS = 512
MAX_RETRIES = 3  # Define the maximum number of retries for empty responses
MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
FILE_DIR = "/Users/stevanvlajic/Desktop/binnacle-icse2020-1.0.0/datasets/0b-deduplicated-dockerfile-sources/deduplicated-sources" #"dockerfiles/sources-gold"
OUT_FILE = "data/dockerfiles.jsonl"
LOG_DIR = "logs"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)
SUCCESS_LOG_FILE = os.path.join(LOG_DIR, "success.log")
FAILURE_LOG_FILE = os.path.join(LOG_DIR, "failure.log")


def log_to_file(file_path, content):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"{content}\n")


def log_message(message):
    logging.info(message)


class Logger:
    def __init__(self):
        self.current_step = None
        self.success_count = 0
        self.failure_count = 0
        self.total_count = 0
        log_to_file(SUCCESS_LOG_FILE, datetime.datetime.now())
        log_to_file(FAILURE_LOG_FILE, datetime.datetime.now())

    def set_step(self, step_name):
        self.current_step = step_name
        logging.info(f"Current step: {self.current_step}")

    def increment_success(self, filename):
        self.success_count += 1
        self.total_count += 1
        self.log_stats()
        log_to_file(SUCCESS_LOG_FILE, filename)

    def increment_failure(self, filename):
        self.failure_count += 1
        self.total_count += 1
        self.log_stats()
        log_to_file(FAILURE_LOG_FILE, filename)

    def log_stats(self):
        logging.info(
            f"Progress Stats - Total: {self.total_count}, Success: {self.success_count}, Failures: {self.failure_count}"
        )


logger = Logger()


def get_file_paths():
    return [
        os.path.join(FILE_DIR, file)
        for file in os.listdir(FILE_DIR)
        if os.path.isfile(os.path.join(FILE_DIR, file))
    ]


def append_data(jsonl_entry: str):
    with open(OUT_FILE, "a", encoding="utf-8") as f:
        f.write(jsonl_entry + "\n")


def get_dockerfile_content(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def clean_response(response):
    cleaned = "\n".join(line for line in response.splitlines() if line.strip() and not set(line.strip()) == {"-"})
    return cleaned.strip().strip('-')


def parse_and_validate_dockerfile(file_path):
    try:
        parsed_commands = dockerfile.parse_file(file_path)
        logging.info(f"Parsed Dockerfile from {file_path}:")
        for cmd in parsed_commands:
            logging.info(f"Command: {cmd.cmd}, Value: {cmd.value}")
        return parsed_commands
    except dockerfile.GoParseError as e:
        logging.error(f"Failed to parse Dockerfile at {file_path}: {e}")
        return None


def is_valid_response(response):
    if not response:
        return False
    cleaned_response = response.strip()
    if not cleaned_response.startswith("Create a Dockerfile using") or not cleaned_response:
        return False
    return True


def build_jsonl_entry(user_query, dockerfile_content):
    entry = {
        "text": f"System: You are a Dockerfile generator.\n\nUser: {user_query}\n\nAssistant: {dockerfile_content}"
    }
    return json.dumps(entry)


def read_failure_paths():
    with open("logs/failure.log", "r", encoding="utf-8") as f:
        return [data.strip() for data in f.readlines()]


def read_success_paths():
    with open(SUCCESS_LOG_FILE, "r", encoding="utf-8") as f:
        return [data.strip() for data in f.readlines()]


def clean_before_startup():
    with open(SUCCESS_LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")

    with open(FAILURE_LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")


def main():
    prev_success_files = read_success_paths()
    files_to_process = get_file_paths()
    final_file_paths = [x for x in files_to_process if x not in prev_success_files]
    logging.info(f"Fresh startup with...{len(final_file_paths)} Files to process and {len(prev_success_files)} finished entries successfully!")
    clean_before_startup()
    try:
        for file_path in final_file_paths:
            logger.set_step(f"Processing file: {file_path}")

            parsed_commands = parse_and_validate_dockerfile(file_path)
            if not parsed_commands:
                logging.warning(f"Skipping invalid Dockerfile: {file_path}")
                logger.increment_failure(file_path)
                continue

            dockerfile_content = get_dockerfile_content(file_path)

            prompt = f"""
                    You are analyzing a Dockerfile with the following content:

                    {dockerfile_content}

                    Generate a single user question that starts with "Create a Dockerfile using..." and directly references the technologies, tools, or configurations from the Dockerfile. 

                    Ensure the output is:
                    - A single line of plain text.
                    - Starting with "Create a Dockerfile using..."
                    - Relevant to the Dockerfile content.
                    - Free from any additional characters, symbols, or formatting.

                    Output only the question as plain text.
                    """

            retries = 0
            response = None

            while retries < MAX_RETRIES:
                try:
                    response = client.text_generation(
                        model=MODEL,
                        prompt=prompt,
                        temperature=TEMPERATURE,
                        max_new_tokens=MAX_TOKENS,
                        top_p=TOP_P,
                    )

                    if is_valid_response(clean_response(response)):
                        break

                    logging.warning(f"Invalid or empty response. Retrying... ({retries + 1}/{MAX_RETRIES})")
                    retries += 1

                except Exception as api_error:
                    logging.error(f"Error during API call for file: {file_path}. Error: {str(api_error)}")
                    retries += 1
            else:  # while loop ended naturally without a break
                logger.increment_failure(file_path)
                continue

            if not response:
                logging.error(f"Failed to get a valid response for file: {file_path} after {MAX_RETRIES} retries.")
                logger.increment_failure(file_path)
                continue

            try:
                jsonl_entry = build_jsonl_entry(clean_response(response), dockerfile_content)
                append_data(jsonl_entry)
                logger.increment_success(file_path)
            except Exception as processing_error:
                logging.error(f"Error processing response for file: {file_path}. Error: {str(processing_error)}")
                logger.increment_failure(file_path)

    except KeyboardInterrupt:
        logging.info("Process interrupted by user. Exiting gracefully.")


if __name__ == '__main__':
    main()
