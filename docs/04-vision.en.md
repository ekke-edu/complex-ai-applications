# 4. Multimodal Vision

The system can process images (invoices, diagrams) using the Gemini 1.5/3.5 Flash models to generate structured data.

```mermaid
sequenceDiagram
    User->>API: 1. POST /chat_with_image
    API->>Gemini: 3. generate_content
    Gemini-->>API: 4. Analysis
    API->>Mongo: 5. Save History
```
