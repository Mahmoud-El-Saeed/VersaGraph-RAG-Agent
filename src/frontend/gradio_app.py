import gradio as gr
import httpx
import uuid
import logging
import os

# System Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
TIMEOUT = 300.0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PERSONA_TEMPLATES = {
    "General Assistant": "You are a highly efficient and professional AI assistant.",
    "Academic Research": "You are a senior academic researcher. Analyze documents critically, cite sources precisely.",
    "Technical Documentation": "You are a senior technical writer. Focus on specifications and API details.",
    "Legal Analysis": "You are a corporate legal consultant. Focus on clauses, obligations, and liability.",
    "Financial Analyst": "You are a senior market analyst. Focus on financial trends and fiscal projections.",
    "Custom Configuration": ""
}

# --- Backend Communication Functions ---

def fetch_sidebar_chats():
    """Fetches list of chat IDs for the sidebar."""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{BACKEND_URL}/chat/history")
            if resp.status_code == 200:
                chats = resp.json().get("chats", [])
                return gr.update(choices=chats, value=None)
    except Exception as e:
        logger.error(f"Failed to fetch chats: {e}")
    return gr.update(choices=[])

def load_chat_history(chat_id):
    """Loads historical messages into the Chatbot UI."""
    if not chat_id:
        return []
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{BACKEND_URL}/chat/history/{chat_id}")
            if resp.status_code == 200:
                messages = resp.json().get("messages", [])
                # Format for gr.Chatbot (Gradio 6): list of {"role": ..., "content": ...} dicts
                history = []
                for msg in messages:
                    role = msg["role"]
                    if role == "agent":
                        role = "assistant"
                    history.append({"role": role, "content": msg["content"]})
                return history
    except Exception as e:
        logger.error(f"Failed to load history for {chat_id}: {e}")
    return []

async def handle_file_workflow(files, chat_id, persona_name, persona_instructions):
    if not chat_id:
        return "System Error: Chat Session ID is mandatory."
    if not files:
        return "System Error: No files selected."

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            upload_files = []
            file_handles = []
            for f in files:
                file_name = os.path.basename(f.name)
                fh = open(f.name, "rb")
                file_handles.append(fh)
                upload_files.append(("files", (file_name, fh))) 

            form_data = {
                "chat_id": chat_id,
                "persona_name": persona_name,
                "persona_instructions": persona_instructions
            }

            upload_resp = await client.post(f"{BACKEND_URL}/data/upload", data=form_data, files=upload_files)
            for fh in file_handles:
                fh.close()

            if upload_resp.status_code != 200:
                return f"Upload Failed: Server returned status {upload_resp.status_code}."
            
            upload_data = upload_resp.json()
            uploaded_count = len(upload_data.get("uploaded", []))
            
            process_payload = {"chat_id": chat_id}
            process_resp = await client.post(f"{BACKEND_URL}/data/process", json=process_payload)
            
            if process_resp.status_code == 200:
                process_data = process_resp.json()
                processed_count = len(process_data.get("processed", []))
                return f"Operation Successful: {uploaded_count} uploaded, {processed_count} indexed."
            
            return f"Processing Incomplete: Server returned status {process_resp.status_code}."
        except Exception as e:
            return f"System Error: {str(e)}"

async def handle_user_message(message, history, chat_id):
    """Processes the message, updates UI immediately, and yields backend response."""
    if not message.strip():
        yield history, ""
        return
        
    if not chat_id:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": "System Warning: A valid Chat Session ID is required."})
        yield history, ""
        return

    # Add user message and a pending bot response to UI immediately
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": "Processing..."})
    yield history, ""

    payload = {"input": {"question": message, "chat_id": chat_id}}

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(f"{BACKEND_URL}/chat/invoke", json=payload)
            if response.status_code == 200:
                result = response.json()
                history[-1]["content"] = result.get("output", "Error: Unrecognized format.")
            else:
                history[-1]["content"] = f"Backend Error ({response.status_code}): {response.text}"
        except Exception as e:
            history[-1]["content"] = f"Network Exception: {str(e)}"
            
    yield history, ""

def generate_new_session():
    return str(uuid.uuid4())[:8]

def update_instructions(choice):
    return PERSONA_TEMPLATES.get(choice, "")

# --- Gradio UI Layout ---

professional_theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="slate",
    neutral_hue="gray",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
)

custom_css = """
/* Vertical radio list in sidebar - one item per row */
.sidebar-chats .gr-radio-group {
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
}
.sidebar-chats .gr-radio-group label {
    width: 100% !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    transition: background 0.2s ease !important;
}
.sidebar-chats .gr-radio-group label:hover {
    background: var(--color-accent-soft) !important;
}
/* Sticky chat input at bottom */
.chat-input-row {
    position: sticky;
    bottom: 0;
    background: var(--background-fill-primary);
    padding-top: 8px;
    z-index: 10;
}
"""

with gr.Blocks(title="VersaGraph Enterprise RAG") as demo:
    
    # State variable to keep track of the active session
    current_chat_id = gr.State(value=generate_new_session())

    # --- Left Sidebar: Chat Sessions ---
    with gr.Sidebar(open=True, position="left", width=260):
        gr.Markdown("### 💬 VersaGraph")
        new_chat_btn = gr.Button("➕ New Chat", variant="primary", size="lg")
        gr.Markdown("---")
        gr.Markdown("##### Recent Sessions")
        chat_history_radio = gr.Radio(
            choices=[],
            label=None,
            interactive=True,
            elem_classes=["sidebar-chats"]
        )
        refresh_sidebar_btn = gr.Button("🔄 Refresh", variant="secondary", size="sm")

    # --- Right Sidebar: Knowledge Base & Agent Configuration ---
    with gr.Sidebar(open=False, position="right", width=340):
        gr.Markdown("### ⚙️ Agent Configuration")
        active_session_display = gr.Textbox(
            label="Active Session ID",
            interactive=False
        )
        persona_dropdown = gr.Dropdown(
            choices=list(PERSONA_TEMPLATES.keys()),
            value="General Assistant",
            label="Assigned Role"
        )
        role_instructions = gr.Textbox(
            value=PERSONA_TEMPLATES["General Assistant"],
            label="System Instructions",
            lines=3,
            interactive=True
        )
        gr.Markdown("---")
        gr.Markdown("### 📁 Knowledge Base")
        file_input = gr.File(
            label="Upload Documents",
            file_types=[".pdf", ".txt", ".docx"],
            file_count="multiple"
        )
        upload_btn = gr.Button("🚀 Upload & Process", variant="primary")
        status_msg = gr.Textbox(label="System Output", interactive=False, lines=1)

    # --- Center: Main Chat Area ---
    chatbot = gr.Chatbot(label="VersaGraph Intelligence", height=650)
    with gr.Row(elem_classes=["chat-input-row"]):
        msg_input = gr.Textbox(
            placeholder="Ask anything about your documents…",
            container=False,
            scale=9,
            show_label=False
        )
        submit_btn = gr.Button("Send ➤", variant="primary", scale=1)

    # --- Event Listeners ---

    # Sync state to display
    demo.load(fn=lambda x: x, inputs=[current_chat_id], outputs=[active_session_display])
    demo.load(fn=fetch_sidebar_chats, inputs=None, outputs=[chat_history_radio])

    persona_dropdown.change(fn=update_instructions, inputs=[persona_dropdown], outputs=[role_instructions])

    upload_btn.click(
        fn=handle_file_workflow,
        inputs=[file_input, current_chat_id, persona_dropdown, role_instructions],
        outputs=[status_msg]
    )

    # Chat submission events (Enter key or button click)
    msg_input.submit(
        fn=handle_user_message,
        inputs=[msg_input, chatbot, current_chat_id],
        outputs=[chatbot, msg_input]
    )
    submit_btn.click(
        fn=handle_user_message,
        inputs=[msg_input, chatbot, current_chat_id],
        outputs=[chatbot, msg_input]
    )

    # When a chat is selected from the sidebar: update state and load history
    chat_history_radio.change(
        fn=lambda x: x, # Update the current state to the selected chat ID
        inputs=[chat_history_radio],
        outputs=[current_chat_id]
    ).then(
        fn=lambda x: x, # Sync display
        inputs=[current_chat_id],
        outputs=[active_session_display]
    ).then(
        fn=load_chat_history, # Load history from Backend
        inputs=[current_chat_id],
        outputs=[chatbot]
    )

    # New Chat logic: Generate ID, clear UI, unselect radio
    new_chat_btn.click(
        fn=generate_new_session,
        outputs=[current_chat_id]
    ).then(
        fn=lambda x: x, # Sync display
        inputs=[current_chat_id],
        outputs=[active_session_display]
    ).then(
        fn=lambda: ([], gr.update(value=None)), # Clear chat and unselect history radio
        outputs=[chatbot, chat_history_radio]
    ).then(
        fn=fetch_sidebar_chats, # Refresh sidebar to show new state
        outputs=[chat_history_radio]
    )
    
    refresh_sidebar_btn.click(fn=fetch_sidebar_chats, inputs=None, outputs=[chat_history_radio])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=professional_theme, css=custom_css)