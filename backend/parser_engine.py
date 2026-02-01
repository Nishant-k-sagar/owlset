from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript

class CodeParser:
    def __init__(self):
        self.langs = {
            'python': Language(tree_sitter_python.language(), "python"),
            'javascript': Language(tree_sitter_javascript.language(), "javascript"),
            'typescript': Language(tree_sitter_typescript.language_typescript(), "typescript"),
            'tsx': Language(tree_sitter_typescript.language_tsx(), "tsx")
        }
        self.parsers = {}
        for name, lang in self.langs.items():
            p = Parser()
            p.set_language(lang)
            self.parsers[name] = p
    
    def _get_lang_type(self, filepath):
        if filepath.endswith('.py'): return 'python'
        if filepath.endswith(('.js', '.jsx', '.mjs', '.cjs')): return 'javascript'
        if filepath.endswith('.ts'): return 'typescript'
        if filepath.endswith('.tsx'): return 'tsx'
        return None

    def parse_file(self, filepath, root_dir):
        lang_type = self._get_lang_type(filepath)
        if not lang_type: return None

        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        try:
            tree = self.parsers[lang_type].parse(bytes(code, "utf8"))
        except Exception as e:
            return None
        
        definitions = []
        calls = []
        self._traverse(tree.root_node, code, definitions, calls)
        return {"definitions": definitions, "calls": calls, "raw_code": code}

    def _traverse(self, node, code, definitions, calls):
        if node.type in ['function_definition', 'function_declaration', 'method_definition', 'arrow_function']:
            func_name = "anonymous"
            name_node = node.child_by_field_name('name')
            if not name_node and node.parent and node.parent.type == 'variable_declarator':
                name_node = node.parent.child_by_field_name('name')
            if not name_node and node.type == 'method_definition':
                name_node = node.child_by_field_name('name')

            if name_node:
                func_name = code[name_node.start_byte:name_node.end_byte]
                definitions.append({
                    'name': func_name, 'start': node.start_point[0] + 1,
                    'end': node.end_point[0] + 1, 'code': code[node.start_byte:node.end_byte]
                })

        if node.type in ['call_expression', 'call']:
            func_node = node.child_by_field_name('function')
            if func_node:
                if func_node.type == 'attribute' or func_node.type == 'member_expression':
                    prop = func_node.child_by_field_name('attribute') or func_node.child_by_field_name('property')
                    if prop:
                        calls.append({'name': code[prop.start_byte:prop.end_byte], 'line': node.start_point[0]+1})
                elif func_node.type == 'identifier':
                    calls.append({'name': code[func_node.start_byte:func_node.end_byte], 'line': node.start_point[0]+1})

        for child in node.children:
            self._traverse(child, code, definitions, calls)
