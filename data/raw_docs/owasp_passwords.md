# OWASP Password Storage Cheat Sheet Guidelines

## Section 1: Hashing and Salting Passwords

1. Passwords must be hashed using a cryptographically secure, one-way, work-factor adjustable hashing function.
   - Use Argon2id, bcrypt, or PBKDF2. Argon2id is the industry-recommended algorithm.
   - A unique, cryptographically secure salt must be generated for each password entry. The salt should be at least 16 bytes long.
   - Plaintext passwords must never be stored. Storing plaintext passwords makes the system vulnerable to credential theft if a database dump is leaked.

## Section 2: Transmission Security

1. Passwords must always be encrypted in transit using Transport Layer Security (TLS 1.2 or TLS 1.3).
2. Under no circumstances should plain text passwords be passed through insecure protocols or logged in application log files.
