# Company Internal Security Policy & SOC2 Compliance

## Section 4.3: Access Control and Password Security

1. Access control mechanisms must be implemented to restrict access to personal data, customer systems, and intellectual property. Only authorized personnel with business justification may access production databases containing customer information.

2. All authentication credentials, including passwords, API keys, and private SSH keys, must be stored securely. 
   - Under no circumstances shall passwords or access keys be stored or transmitted in plaintext.
   - All passwords stored in database systems must be hashed using a strong cryptographic hashing algorithm. Permitted algorithms include bcrypt, Argon2, or PBKDF2 with appropriate salt and iteration settings.
   - Storing passwords in plaintext, reversibly encrypted, or hashed with weak algorithms (such as MD5 or SHA1) is a critical security policy violation.

3. Multi-factor authentication (MFA) must be enforced for all administrative and user access to production infrastructure, cloud management consoles, and version control repositories.
