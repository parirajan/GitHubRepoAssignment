import os
import re

# Patterns for sensitive data
IP_PATTERN = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
HOSTNAME_PATTERN = r'\b(?:[a-zA-Z0-9-]+\.)+(?:[a-zA-Z]{2,})\b'
EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_PATTERN = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'

# Timestamp patterns to preserve
UNIX_TIMESTAMP_PATTERN = r'\b\d{12,}\b'  # e.g., 165755813888
LOG_TIMESTAMP_PATTERN = r'\b\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}(?:Z)?\b'  # e.g., 2024-05-23T12:00:01Z

# Redaction placeholder
REDACTION = '[REDACTED]'

# Folder to search
folder_path = 'path/to/your/folder'

def redact_file_content(content):
    # Preserve both Unix-style and log-style timestamps
    preserved_items = []

    def preserve_pattern(pattern, label):
        matches = re.findall(pattern, content)
        for i, match in enumerate(matches):
            placeholder = f"__{label}_{i}__"
            preserved_items.append((placeholder, match))
            content_nonlocal[0] = content_nonlocal[0].replace(match, placeholder)

    content_nonlocal = [content]
    preserve_pattern(UNIX_TIMESTAMP_PATTERN, "UNIX_TIMESTAMP")
    preserve_pattern(LOG_TIMESTAMP_PATTERN, "LOG_TIMESTAMP")

    # Redact sensitive info
    content_nonlocal[0] = re.sub(IP_PATTERN, REDACTION, content_nonlocal[0])
    content_nonlocal[0] = re.sub(HOSTNAME_PATTERN, REDACTION, content_nonlocal[0])
    content_nonlocal[0] = re.sub(EMAIL_PATTERN, REDACTION, content_nonlocal[0])
    content_nonlocal[0] = re.sub(PHONE_PATTERN, REDACTION, content_nonlocal[0])

    # Restore preserved timestamps
    for placeholder, original in preserved_items:
        content_nonlocal[0] = content_nonlocal[0].replace(placeholder, original)

    return content_nonlocal[0]

def process_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                redacted_content = redact_file_content(content)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(redacted_content)

                print(f"Processed and redacted: {file_path}")
            except Exception as e:
                print(f"Could not process file {file_path}: {e}")

if __name__ == "__main__":
    process_files(folder_path)
