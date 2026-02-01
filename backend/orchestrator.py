import os
from .database import DatabaseManager
from .parser_engine import CodeParser
from .resolver import Linker

class RepositoryOrchestrator:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.db = DatabaseManager()
        self.parser = CodeParser()
        self.linker = Linker(self.db)

    def scan(self):
        print(f"Scanning Repository: {self.repo_path}")
        IGNORED_DIRS = {'node_modules', '.git', 'dist', 'build', 'coverage', '.next', '__pycache__', 'venv'}
        
        file_paths = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for file in files:
                if file.startswith('.'): continue
                if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.py')):
                    file_paths.append(os.path.join(root, file))

        total = len(file_paths)
        print(f"   Found {total} source files.")

        file_map = {}
        for i, full_path in enumerate(file_paths):
            rel_path = os.path.relpath(full_path, self.repo_path)
            print(f"   [{i+1}/{total}] Parsing: {rel_path}", end='\r')
            
            data = self.parser.parse_file(full_path, self.repo_path)
            if not data: continue
            
            file_map[rel_path] = data
            for func in data['definitions']:
                node_id = f"{rel_path}::{func['name']}"
                self.db.upsert_node({
                    "id": node_id, "name": func['name'], "type": "function",
                    "file_path": rel_path, "start_line": func['start'],
                    "end_line": func['end'], "code": func['code']
                })
                self.db.add_edge(rel_path, node_id, "defines")

        print(f"\nParsing Complete.")
        
        print("Linking Dependencies...")
        global_map = {}
        for row in self.db.get_all_nodes():
            if row['type'] == 'function':
                if row['name'] not in global_map: global_map[row['name']] = []
                global_map[row['name']].append(row['id'])

        for rel_path, data in file_map.items():
            for func_def in data['definitions']:
                caller_id = f"{rel_path}::{func_def['name']}"
                for call in data['calls']:
                    if func_def['start'] <= call['line'] <= func_def['end']:
                        target_id = self.linker.match_call(rel_path, call['name'], global_map)
                        if target_id:
                            self.db.add_edge(caller_id, target_id, "calls")
        print("Graph Built.")
