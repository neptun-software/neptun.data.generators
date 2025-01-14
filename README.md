# Dockerfile Processor

## Overview
This repository contains a Python-based tool for analyzing and processing Dockerfiles. It is designed to generate user-friendly questions and outputs in JSONL format for training or other applications. The tool uses the Hugging Face Inference API to interact with a language model, providing meaningful outputs based on the content of the Dockerfiles.

---

## Features
- **Automated Dockerfile Analysis:** Parses and validates Dockerfiles for processing.
- **Hugging Face Integration:** Uses `mistralai/Mistral-7B-Instruct-v0.3` for generating prompts and responses.
- **Error Handling & Retry Mechanism:** Handles API failures with retry logic and logs failures for later review.
- **Logging:** Tracks success and failure statistics in both console output and log files.
- **JSONL Output:** Generates well-structured JSONL files with system-user interactions for each Dockerfile.

---

## File Structure

```
.
├── dockerfiles
│   └── sources-gold       # Directory containing input Dockerfiles
├── data
│   └── dockerfiles.jsonl  # Output file storing processed data in JSONL format
├── logs
│   ├── success.log        # Logs filenames successfully processed
│   └── failure.log        # Logs filenames that failed processing
├── .env                   # Environment variables (e.g., API_TOKEN)
├── main.py                # Main Python script for processing Dockerfiles
├── README.md              # Repository documentation (this file)
└── requirements.txt       # Python dependencies
```

---

## How It Works
1. **Dockerfile Parsing:**
   - The tool reads Dockerfiles from the `dockerfiles/sources-gold` directory.
   - Validates each file using the `dockerfile` library to ensure compatibility.

2. **Prompt Generation:**
   - Constructs a prompt based on the content of the Dockerfile.
   - Sends the prompt to the Hugging Face Inference API for processing.

3. **Response Handling:**
   - Validates and cleans the model's response.
   - Retries up to a defined limit if the response is invalid or empty.

4. **Output Generation:**
   - Creates a JSONL entry with the Dockerfile content and the generated user question.
   - Logs each file's success or failure into separate log files.

---

## Usage

### Prerequisites
1. Python 3.8+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the `.env` file with your Hugging Face API token:
   ```
   API_TOKEN=your_hugging_face_api_token
   ```

### Running the Script
Execute the main script to process Dockerfiles:
```bash
python main.py
```

### Outputs
- **Processed Data:**
  - Saved in `data/dockerfiles.jsonl` as structured JSONL.
- **Logs:**
  - Successful files: `logs/success.log`
  - Failed files: `logs/failure.log`

---

## Example JSONL Entry
```json
{
  "text": "System: You are a Dockerfile generator.\n\nUser: Create a Dockerfile using...\n\nAssistant: FROM alpine:3.10\nRUN ..."
}
```

---

## Contributing
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-branch
   ```
3. Make your changes and commit them:
   ```bash
   git commit -m "Add new feature"
   ```
4. Push to your branch:
   ```bash
   git push origin feature-branch
   ```
5. Open a pull request.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact
For questions or feedback, please create an issue in this repository.

