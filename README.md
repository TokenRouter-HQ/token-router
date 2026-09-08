TokenRouter-HQ 🚀
Enterprise LLM Proxy with Prompt Compression, Smart Routing, and Semantic Caching.

TokenRouter-HQ is an open-source, lightweight AI Gateway designed to drastically reduce your LLM API costs (OpenAI, Anthropic) while providing real-time FinOps telemetry.

By acting as a drop-in replacement for the standard OpenAI /v1/chat/completions endpoint, you can integrate it into your existing applications in seconds without rewriting your core logic.

🎯 Key Features (Why use TokenRouter?)
📉 Heuristic Prompt Compression: Automatically strips redundant whitespace, duplicate punctuation, and polite "stop-words" that consume tokens without adding semantic value to the AI.

🧠 Semantic Caching: Identical prompts are served directly from local memory (0ms latency, 100% token savings), avoiding redundant API calls.

🛣️ Smart Routing: Dynamically routes complex prompts to premium models (e.g., gpt-4o) and simple, short tasks to cheaper models (e.g., gpt-4o-mini) based on your strategy.

📊 FinOps Telemetry Engine: Every API response includes a custom header detailing exactly how many tokens were saved, the percentage of cost reduction, and latency.

🔌 Zero Friction (Drop-in Replacement): Fully compatible with OpenAI's API schema. Just change the base URL.

⚙️ Quick Start
1. Install Dependencies
Ensure you have Python 3.8+ installed, then run:bash
pip install fastapi uvicorn tiktoken openai pydantic


### 2. Set your API Key
Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
3. Run the Server
Start the FastAPI server locally:

Bash
uvicorn main:app --reload
The proxy will be available at http://127.0.0.1:8000. You can also access the interactive API documentation at http://127.0.0.1:8000/docs.

💻 How it Works (cURL Example)
Send a standard OpenAI request to your local proxy. Notice the route_strategy parameter!

Bash
curl -X 'POST' \
  '[http://127.0.0.1:8000/v1/chat/completions](http://127.0.0.1:8000/v1/chat/completions)' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "role": "user",
      "content": "Please, could you help me understand how black holes work? I would like to know!"
    }
  ],
  "route_strategy": "auto"
}'
📈 The "FinOps" Response
Your application will receive the standard OpenAI response, but injected with our powerful telemetry data demonstrating your cost savings:

JSON
{
  "id": "chatcmpl-12345",
  "model_used": "gpt-4o-mini",
  "finops_telemetry": {
    "original_tokens": 21,
    "compressed_tokens": 9,
    "tokens_saved": 12,
    "savings_percentage": "57.14%",
    "latency_seconds": "0.4120s"
  },
  "choices": [ ... ]
}
(If you send the exact same request again, you will see a 100% saving due to the Semantic Cache).

🔒 License
This project is licensed under the Apache License 2.0 - allowing for commercial use, modification, and distribution without the toxic "copyleft" clauses. Safe for enterprise deployment.
