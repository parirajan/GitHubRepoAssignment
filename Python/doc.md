```mermaid
graph TD
    A[REST API Request Input]
    B[Safer Payments Fraud API]
    C[Response: Score & Insights]

    %% Testing layers connected to API
    D[Functional Testing]
    E[Positive Tests:<br>Valid Request, Legit Transaction]
    F[Negative Tests:<br>Missing Field, Invalid Data, Malformed JSON]

    G[API Contract Testing]
    H[Schema Validation & Versioning]

    I[Performance & Load Testing]
    J[Load Testing & Stress Testing]

    K[Security Testing]
    L[Injection, Auth, Malformed Input Tests]

    M[End-to-End & Integration Testing]
    N[Complete Transaction Flow & Mocks]

    O[CI/CD Pipeline & Automation]
    P[Data-Driven Testing,<br>Logging & Monitoring]

    %% Connections
    A --> B
    B --> C

    %% Functional Testing Branch
    A --> D
    D --> E
    D --> F

    %% API Contract Testing Branch
    B --> G
    G --> H

    %% Performance Testing Branch
    B --> I
    I --> J

    %% Security Testing Branch
    B --> K
    K --> L

    %% End-to-End & Integration Testing Branch
    B --> M
    M --> N

    %% CI/CD Integration connecting to all test layers
    O --> D
    O --> G
    O --> I
    O --> K
    O --> M
    O --> P
