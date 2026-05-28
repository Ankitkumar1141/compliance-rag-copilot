"""
benchmark_dataset.py

Generates and stores a synthetic Q&A evaluation dataset
based on the compliance documents in data/raw_docs/.
"""

import os
import json
from typing import List, Dict

# Hardcoded synthetic benchmark Q&A pairs for testing without an LLM
BENCHMARK_DATASET: List[Dict] = [
    {
        "question": "Can I store customer passwords in plain text?",
        "ground_truth": (
            "No. Storing passwords in plain text is a critical security violation. "
            "According to the OWASP Password Storage Cheat Sheet and company security policy Section 4.3, "
            "passwords must be hashed using strong algorithms such as Argon2id, bcrypt, or PBKDF2 with a unique salt. "
            "Plain text password storage makes systems vulnerable to credential theft."
        ),
        "relevant_docs": ["owasp_passwords.md", "soc2_security_policy.md"],
    },
    {
        "question": "What hashing algorithms are acceptable for storing passwords?",
        "ground_truth": (
            "Acceptable password hashing algorithms include Argon2id (recommended by OWASP), bcrypt, and PBKDF2. "
            "Each password entry must use a unique, cryptographically secure salt of at least 16 bytes. "
            "Weak algorithms such as MD5 or SHA1 are explicitly prohibited."
        ),
        "relevant_docs": ["owasp_passwords.md"],
    },
    {
        "question": "What is the legal basis for processing personal data under GDPR?",
        "ground_truth": (
            "Under GDPR Article 6, processing is lawful only if at least one of the following applies: "
            "the data subject has given consent; processing is necessary for a contract; "
            "it is required by legal obligation; it is needed to protect vital interests; "
            "it serves a public interest or official authority; or there is a legitimate interest "
            "that does not override the data subject's rights."
        ),
        "relevant_docs": ["gdpr_article6.md"],
    },
    {
        "question": "Is multi-factor authentication required for production access?",
        "ground_truth": (
            "Yes. According to company internal security policy Section 4.3, multi-factor authentication (MFA) "
            "must be enforced for all administrative and user access to production infrastructure, "
            "cloud management consoles, and version control repositories."
        ),
        "relevant_docs": ["soc2_security_policy.md"],
    },
    {
        "question": "Can passwords be transmitted over HTTP?",
        "ground_truth": (
            "No. According to OWASP Password Storage Guidelines Section 2, passwords must always be encrypted "
            "in transit using TLS 1.2 or TLS 1.3. Plain text password transmission over insecure protocols "
            "is explicitly prohibited. Passwords must also never be logged in application log files."
        ),
        "relevant_docs": ["owasp_passwords.md"],
    },
]


def get_benchmark_dataset() -> List[Dict]:
    """Returns the built-in synthetic benchmark dataset."""
    return BENCHMARK_DATASET


def save_benchmark_to_file(output_path: str = "data/processed_docs/benchmark_dataset.json"):
    """Saves the benchmark dataset to a JSON file for reference."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(BENCHMARK_DATASET, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Saved benchmark dataset with {len(BENCHMARK_DATASET)} Q&A pairs to: {output_path}")


if __name__ == "__main__":
    save_benchmark_to_file()
    print("[INFO] Benchmark dataset saved successfully.")
