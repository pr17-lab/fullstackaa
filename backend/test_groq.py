from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)
r = client.chat.completions.create(
    model='llama-3.1-8b-instant',
    messages=[{'role': 'user', 'content': 'Say hello in one word'}],
    max_tokens=10
)
print('Groq works:', r.choices[0].message.content)
