import streamlit as st
import graphviz
import os
import random
from streamlit_agraph import agraph, Node, Edge, Config
from backend.graph_service import GraphService
from backend.ai_engine import SeniorEngineerAI

st.set_page_config(page_title="Owlset", layout="wide")

st.markdown("""
<style>
    .block-container {padding-top: 1rem;}
    h3 {margin-bottom: 0px;}
    div[data-testid="stGraphVizChart"] {
        border: 1px solid #f0f2f6; border-radius: 8px; background-color: white;
        padding: 10px; margin-left: auto; margin-right: auto;
        display: block; width: fit-content; overflow: auto;
    }
</style>
""", unsafe_allow_html=True)

if "graph_service" not in st.session_state: 
    st.session_state.graph_service = GraphService()
if "ai_engine" not in st.session_state: 
    st.session_state.ai_engine = SeniorEngineerAI()
if "selected_node" not in st.session_state: 
    st.session_state.selected_node = None
if "current_node_id" not in st.session_state: 
    st.session_state.current_node_id = None

def get_color_for_path(file_path):
    folder = os.path.dirname(file_path)
    random.seed(folder)
    r = random.randint(220, 255) 
    g = random.randint(220, 255)
    b = random.randint(220, 255)
    return f"#{r:02x}{g:02x}{b:02x}"

with st.sidebar:
    st.title("Owlset")
    st.divider()

    if st.button("Reload Database", use_container_width=True):
        st.session_state.graph_service.refresh()
        st.rerun()

    try:
        nodes = st.session_state.graph_service.db.get_all_nodes()
        func_nodes = [n for n in nodes if n['type'] == 'function']
    except Exception as e:
        st.error(f"Error loading nodes: {e}")
        func_nodes = []
    
    options = {}
    for n in func_nodes:
        clean_file = os.path.basename(n['file_path'])
        label = f"{clean_file} :: {n['name']}"
        options[label] = n['id']
    
    search = st.text_input("Search Function", placeholder="e.g. Auth...")
    filtered = [k for k in options.keys() if search.lower() in k.lower()] if search else list(options.keys())
    
    current_index = None
    if st.session_state.selected_node:
        for k, v in options.items():
            if v == st.session_state.selected_node and k in filtered:
                current_index = filtered.index(k)
                break
    
    valid_index = current_index if current_index is not None and 0 <= current_index < len(filtered) else None
    
    try:
        selection = st.selectbox("Select Function:", filtered, index=valid_index)
    except IndexError:
        selection = st.selectbox("Select Function:", filtered, index=None)
    
    if selection and options[selection] != st.session_state.selected_node:
        st.session_state.selected_node = options[selection]
        if "messages" in st.session_state:
            st.session_state.messages = []
        st.rerun()

if st.session_state.selected_node:
    node_id = st.session_state.selected_node
    
    try:
        ctx = st.session_state.graph_service.get_context_for_function(node_id)
    except Exception as e:
        st.error(f"Error loading function context: {e}")
        ctx = None
    
    if ctx is None:
        st.error("Could not load function context. The node may not exist in the database.")
    else:
        target = ctx.get('target')
        if target is None:
            st.error("Function target not found.")
        else:
            if st.session_state.get('current_node_id') != node_id:
                if "messages" in st.session_state:
                    st.session_state.messages = []
                st.session_state.current_node_id = node_id

            st.markdown(f"### `{target.get('name', 'Unknown')}`")
            st.caption(f"File: `{target.get('file_path', 'Unknown')}`")
            if target.get('summary'): 
                st.info(target.get('summary'))

            st.subheader("Source Code")
            with st.expander("View Code", expanded=True):
                ext = target.get('file_path', '').split('.')[-1] if target.get('file_path') else ''
                lang = 'javascript' if ext in ['js', 'jsx', 'ts', 'tsx'] else 'python'
                st.code(target.get('code', ''), language=lang)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Calls**")
                deps = ctx.get('dependencies', [])
                if deps:
                    for d in deps: 
                        st.markdown(f"- `{d.get('name', 'Unknown')}`")
                else: 
                    st.caption("None")
            with c2:
                st.markdown("**Called By**")
                usages = ctx.get('usages', [])
                if usages:
                    for u in usages: 
                        st.markdown(f"- `{u}`")
                else: 
                    st.caption("None")

            st.subheader("Focus Flow")
            g = graphviz.Digraph()
            g.attr(rankdir='LR', bgcolor='transparent', dpi='70')
            g.attr('node', shape='box', style='rounded,filled', fontname='Helvetica', fontsize='12', height='0.5', margin='0.1')
            
            current_name = target.get('name', 'CURRENT')
            g.node('CURRENT', current_name, fillcolor='#FF4B4B', fontcolor='white', penwidth='0')
            
            for d in deps:
                d_name = d.get('name', 'Unknown')
                g.node(d_name, d_name, fillcolor='#f0f2f6', fontcolor='#31333F')
                g.edge('CURRENT', d_name, color='#888888')
            
            for u in usages:
                g.node(u, u, style='dashed,filled', fillcolor='#ffffff', fontcolor='#31333F')
                g.edge(u, 'CURRENT', color='#888888')
            
            try:
                st.graphviz_chart(g, use_container_width=False)
            except Exception as e:
                st.error(f"Error rendering graph: {e}")

            st.subheader("Chat")
            
            if "messages" not in st.session_state: 
                st.session_state.messages = []
            
            for msg in st.session_state.messages:
                with st.chat_message(msg.get("role", "user")): 
                    st.markdown(msg.get("content", ""))

            if q := st.chat_input("Ask about this logic..."):
                st.session_state.messages.append({"role": "user", "content": q})
                st.rerun()

            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            res = st.session_state.ai_engine.ask_with_context(
                                st.session_state.messages[-1]["content"], ctx
                            )
                        except Exception as e:
                            res = f"Error communicating with AI: {str(e)}"
                        
                        st.markdown(res)
                        st.session_state.messages.append({"role": "assistant", "content": res})

else:
    st.info("Select a function from the sidebar to analyze.")

