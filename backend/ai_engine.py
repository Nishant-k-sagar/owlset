import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

class SeniorEngineerAI:
    def __init__(self):
        api_key = os.getenv("MISTRAL_API_KEY")
        self.client = Mistral(api_key=api_key) if api_key else None

    def summarize_function(self, code, name):
        if not self.client: return None
        try:
            res = self.client.chat.complete(
                model="codestral-latest",
                messages=[{"role": "user", "content": f"Summarize this function '{name}' in one sentence. Code: {code[:1500]}..."}]
            )
            return res.choices[0].message.content
        except: return None

    def ask_with_context(self, user_query, context):
        if not self.client: return "AI Not Configured."
        deps = "\n".join([f"- {d['name']}: {d['summary']}" for d in context['dependencies']])
        prompt = f"""TARGET: {context['target']['code']}
DEPS: {deps}
QUESTION: {user_query}"""
        
        res = self.client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": "1. You are a Senior Engineer."
                "2. Strictly stick to the code base related queries."
                "3. Do not respond the Outside questions. If the outside query is asked, respond something like I have no context regarding this query."
                "4. Answer using the code and dependency context provided."},
                {"role": "user", "content": prompt}
            ]
        )
        return res.choices[0].message.content
