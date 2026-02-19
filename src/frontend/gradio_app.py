import gradio as gr
import httpx
import uuid
import logging

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"
TIMEOUT = 300.0

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Predefined Persona Templates
PERSONA_TEMPLATES = {
    "General Assistant": "You are a helpful and polite AI assistant.",
    "Academic Research": "You are a senior academic researcher. Analyze the documents critically, cite sources precisely, and use formal academic language.",
    "Homework Helper": "You are a friendly tutor. Explain concepts simply, step-by-step, and provide examples to help the student understand.",
    "Technical Documentation": "You are a technical writer. Focus on specifications, API details, and clear architectural explanations.",
    "Legal Analysis": "You are a legal consultant. Focus on clauses, obligations, and potential risks within the provided contracts.",
    "Medical Nursing": "You are a nursing educator. Focus on patient care plans, clinical protocols, and safety measures.",
    "Financial Analyst": "You are a market expert. Focus on trends, numbers, and fiscal projections found in the data.",
    "Custom (Write your own)": ""
}

async def handle_file_workflow(file, chat_id):
    if not chat_id: return "Error: Chat Session ID is required."
    if file is None: return "Error: No file selected."

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            file_name = file.name.split("/")[-1]
            with open(file.name, "rb") as f:
                upload_resp = await client.post(
                    f"{BACKEND_URL}/data/upload",
                    params={"chat_id": chat_id},
                    files={"file": (file_name, f)}
                )
            
            if upload_resp.status_code != 200:
                return f"Upload Failed: {upload_resp.json().get('message')}"
            
            file_id = upload_resp.json().get("file id")
            logger.info(f"File uploaded successfully. ID: {file_id}")

            process_resp = await client.post(
                f"{BACKEND_URL}/data/process",
                json={"chat_id": chat_id, "file_id": file_id}
            )
            
            if process_resp.status_code == 200:
                return f"Success: '{file_name}' is indexed for Chat ID: {chat_id}"
            return f"Processing Failed: {process_resp.json().get('message')}"
        except Exception as e:
            return f"System Error: {str(e)}"

async def chat_response(message, history, chat_id, persona_instructions):
    if not chat_id:
        yield "⚠️ Please provide a Chat Session ID in the sidebar."
        return

    payload = {
        "input": {
            "question": message,
            "chat_id": chat_id,
            "persona": persona_instructions 
        }
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(f"{BACKEND_URL}/chat/invoke", json=payload)
            if response.status_code == 200:
                result = response.json()
                yield result.get("output", "I couldn't process that.")
            else:
                yield f"Backend Error {response.status_code}: {response.text}"
        except Exception as e:
            yield f"Request Error: {str(e)}"

def update_instructions(choice):
    return PERSONA_TEMPLATES.get(choice, "")

# Define Theme
custom_theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="slate",
    neutral_hue="gray",
)

with gr.Blocks(theme=custom_theme) as demo:
    gr.Markdown("# 🤖 VersaGraph RAG System")
    gr.Markdown("Upload documents and chat with customized AI personas.")
    
    with gr.Row():
        # Sidebar: 1/3 of the width
        with gr.Column(scale=1, variant="panel"):
            gr.Markdown("### ⚙️ Session Settings")
            chat_id_box = gr.Textbox(
                value=str(uuid.uuid4())[:8], 
                label="Chat Session ID",
                info="Keep this ID to retrieve history."
            )
            
            gr.Markdown("---")
            gr.Markdown("### 👤 Persona Management")
            persona_dropdown = gr.Dropdown(
                choices=list(PERSONA_TEMPLATES.keys()),
                value="General Assistant",
                label="Select Role Template"
            )
            
            role_instructions = gr.Textbox(
                value=PERSONA_TEMPLATES["General Assistant"],
                label="Role Instructions",
                lines=5,
                interactive=True,
                info="View or edit the prompt instructions here."
            )
            
            gr.Markdown("---")
            gr.Markdown("### 📂 Knowledge Base")
            file_input = gr.File(label="Document Upload", file_types=[".pdf", ".txt", ".docx"])
            upload_btn = gr.Button("📤 Process Document", variant="primary")
            status_msg = gr.Textbox(label="System Status", interactive=False)

        # Main: 2/3 of the width
        with gr.Column(scale=2):
            chatbot = gr.ChatInterface(
                fn=chat_response,
                additional_inputs=[chat_id_box, role_instructions],
                examples=[
                    ["Summarize the main points.", "test-session", "General Assistant"],
                    ["Analyze the risks mentioned.", "test-session", "Legal Analysis"]
                ],
                cache_examples=False
            )

    # Event Handlers
    persona_dropdown.change(
        fn=update_instructions,
        inputs=[persona_dropdown],
        outputs=[role_instructions]
    )

    upload_btn.click(
        fn=handle_file_workflow,
        inputs=[file_input, chat_id_box],
        outputs=[status_msg]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=custom_theme)