class Linker:
    def __init__(self, db_manager):
        self.db = db_manager

    def match_call(self, caller_file, called_func_name, global_map):
        candidates = global_map.get(called_func_name, [])
        if not candidates: return None
        
        local_id = f"{caller_file}::{called_func_name}"
        if local_id in candidates: return local_id
        if len(candidates) == 1: return candidates[0]
        return candidates[0]

