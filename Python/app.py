import os
import re

# Define patterns for sensitive information
IP_PATTERN = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
HOSTNAME_PATTERN = r'\b[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+\b'
EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_PATTERN = r'\b(?:\+?(\d{1,3})?[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'

# Placeholder for redaction
REDACTION = '[REDACTED]'

# Define the folder to search through
folder_path = 'path/to/your/folder'

def redact_file_content(content):
    """
    Redact sensitive information from the file content using regular expressions.
    """
    content = re.sub(IP_PATTERN, REDACTION, content)
    content = re.sub(HOSTNAME_PATTERN, REDACTION, content)
    content = re.sub(EMAIL_PATTERN, REDACTION, content)
    content = re.sub(PHONE_PATTERN, REDACTION, content)
    return content

def process_files(folder_path):
    """
    Read through all files in the given folder and redact sensitive information.
    """
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Redact sensitive information
                redacted_content = redact_file_content(content)

                # Save the redacted content back to the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(redacted_content)

                print(f"Processed and redacted: {file_path}")

            except Exception as e:
                print(f"Could not process file {file_path}: {e}")

if __name__ == "__main__":
    process_files(folder_path)
