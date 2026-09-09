# 3. Stateful Conversation & NoSQL

To make the machine remember the conversation context, we introduced a **MongoDB (NoSQL) database**.
* **Why NoSQL?** Chat logs are naturally JSON documents. Relational databases are too rigid for this.
* Each session generates a `session_id`, allowing FastAPI to load chat history.
