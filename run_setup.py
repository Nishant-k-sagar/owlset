import os
from backend.orchestrator import RepositoryOrchestrator
from backend.ai_engine import SeniorEngineerAI
from backend.database import DatabaseManager

REPO_PATH = "./data/repo"

def main():
    if not os.path.exists(REPO_PATH) or not os.listdir(REPO_PATH):
        print(f"WARNING: Paste code into '{REPO_PATH}'!")
        return

    print("1. Parsing...")
    RepositoryOrchestrator(REPO_PATH).scan()

    print("2. Summarizing...")
    db = DatabaseManager()
    ai = SeniorEngineerAI()
    nodes = [n for n in db.get_all_nodes() if n['type'] == 'function' and not n['summary']]
    
    print(f"   {len(nodes)} functions to process.")
    for i, n in enumerate(nodes):
        print(f"   [{i+1}/{len(nodes)}] {n['name']}...")
        s = ai.summarize_function(n['code'], n['name'])
        if s: db.update_summary(n['id'], s)
    
    print("Done! Run: streamlit run main_app.py")

if __name__ == "__main__":
    main()
