import gradio as gr
from gradio import update  # Add this line to import the update function
import websockets
import json
import asyncio
import time
import copy

# Configure WebSocket server address
WS_SERVER = "ws://0.0.0.0:9000/ws/woz_tools"

# Save current active sessions
active_conversations = {}

async def receive_messages(chatbot, session_info, session_dropdown):
    """Receive messages from the robot"""
    uri = WS_SERVER
    reconnect_delay = 1
    max_delay = 30
    
    # Return initial state first
    # yield chatbot, session_info, session_dropdown, "Connected"
    yield chatbot, session_info, session_dropdown
    # while True:
    #     try:
    async with websockets.connect(uri)as websocket:
        reconnect_delay = 1
        print("WebSocket connection established")
        
        while True:
            try:
                message = await websocket.recv()
                # message = await asyncio.wait_for(websocket.recv(), timeout=15)
                data = json.loads(message)
                
                # Handle conversation_task type messages
                if data.get("type") == "conversation_task":
                    # Generate conversation ID (if not provided)
                    conversation_id = f"conv_{int(time.time())}"
                    
                    # Save conversation data
                    active_conversations[conversation_id] = data
                    
                    # Get task information and chat history
                    task_info = data.get("task_info", "No task information")
                    chat_history = data.get("chat_history", [])
                    
                    # Update session information display
                    session_info = f"Task Information:\n{task_info}"
                    
                    # Update chat interface
                    new_chatbot = []
                    for msg in chat_history:
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        
                        if role == "user":
                            new_chatbot.append((content, None))
                        elif role == "assistant":
                            new_chatbot.append((None, content))
                    
                    # Update session dropdown - use gr.update() instead of gr.Dropdown.update()
                    sessions = list(active_conversations.keys())
                    
                    # yield new_chatbot, session_info, update(choices=sessions, value=conversation_id if sessions else None), "Message received"
                    yield new_chatbot, session_info, update(choices=sessions, value=conversation_id if sessions else None)
            # except asyncio.TimeoutError:
            #     print(f"WebSocket connection timeout, retrying in {reconnect_delay} seconds...")
            #     yield chatbot, session_info, session_dropdown, "Disconnected"
            #     break
            except json.JSONDecodeError:
                print(f"Received non-JSON format message: {message}")
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                break

async def send_message(chatbot, message, session_dropdown):
    """Send human operator reply"""
    if not message.strip() or not session_dropdown:
        return chatbot, ""
    
    conversation_id = session_dropdown
    
    if conversation_id not in active_conversations:
        return chatbot, ""
    
    # Add to chat interface
    chatbot.append((None, message))
    
    # Get current session data
    conversation_data = active_conversations[conversation_id]
    
    # Make a copy for modification
    new_data = copy.deepcopy(conversation_data)
    
    # Add assistant message to chat history
    new_data["chat_history"].append({
        "role": "assistant",
        "content": message
    })
    
    # Set incomplete status
    new_data["is_done"] = False
    
    # Save updated session data
    active_conversations[conversation_id] = new_data
    
    # Send updated session data
    await send_to_robot(json.dumps(new_data))
    
    return chatbot, ""

async def mark_conversation_complete(chatbot, result_input, session_dropdown):
    """Mark conversation as complete"""
    if not session_dropdown:
        return chatbot, result_input
    
    conversation_id = session_dropdown
    
    if conversation_id not in active_conversations:
        return chatbot, result_input
    
    # Get current session data
    conversation_data = active_conversations[conversation_id]
    
    # Make a copy for modification
    new_data = copy.deepcopy(conversation_data)
    
    # Set completion status and result
    new_data["is_done"] = True
    new_data["result"] = result_input
    
    # Save updated session data
    active_conversations[conversation_id] = new_data
    
    # Send updated session data
    await send_to_robot(json.dumps(new_data))
    
    # Add prompt to chat interface
    chatbot.append((None, f"[System] Conversation marked as complete, result: {result_input}"))
    
    chatbot = []
    return chatbot, ""

async def send_to_robot(message):
    """Send message to robot"""
    uri = WS_SERVER
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(message)
            return True
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return False

# Custom CSS
custom_css = """
.operator-ui {
    height: 100vh !important;
    max-height: calc(100vh - 200px) !important;
    overflow-y: auto;
}

.session-info {
    background-color: #f0f0f0;
    padding: 10px;
    border-radius: 5px;
    white-space: pre-wrap;
}
"""

# Create Gradio interface
with gr.Blocks(css=custom_css) as demo:
    with gr.Row():
        with gr.Column(scale=7):
            chatbot = gr.Chatbot([], elem_id="operator-ui", height=600)
            with gr.Row():
                with gr.Column(scale=8):
                    msg_input = gr.Textbox(
                        placeholder="Enter message...",
                        show_label=False,
                        lines=2
                    )
                with gr.Column(scale=1):
                    send_btn = gr.Button("Send")
        
        with gr.Column(scale=3):
            textbox = gr.Textbox(
                "",
                interactive=False,
                container=False,
            )
            connect_btn = gr.Button("Connect")
            session_info = gr.Textbox(
                label="Task Information",
                placeholder="Waiting for robot connection...",
                lines=10,
                elem_classes=["session-info"]
            )
            session_dropdown = gr.Dropdown(
                label="Active Sessions",
                choices=[],
                interactive=True,
                allow_custom_value=False
            )
            result_input = gr.Textbox(
                label="Conversation Result Summary",
                placeholder="Please enter conversation result summary here to mark conversation as complete...",
                lines=2
            )
            complete_btn = gr.Button("Mark Conversation Complete", variant="primary")
    
    # connect_btn.click(
    #     receive_messages,
    #     inputs=[chatbot, session_info, session_dropdown],
    #     outputs=[chatbot, session_info, session_dropdown, textbox]
    # )
    
    # Set up event handlers
    send_btn.click(
        send_message,
        inputs=[chatbot, msg_input, session_dropdown],
        outputs=[chatbot, msg_input]
    )
    
    msg_input.submit(
        send_message,
        inputs=[chatbot, msg_input, session_dropdown],
        outputs=[chatbot, msg_input]
    )
    
    complete_btn.click(
        mark_conversation_complete,
        inputs=[chatbot, result_input, session_dropdown],
        outputs=[chatbot, result_input]
    )
    
    
    
    # Receive messages
    demo.load(
        receive_messages,
        inputs=[chatbot, session_info, session_dropdown],
        outputs=[chatbot, session_info, session_dropdown]
    )

# Launch interface
if __name__ == "__main__":
    try:
        print(f"Starting human operator interface, connecting to WebSocket server: {WS_SERVER}")
        demo.launch(server_port=7871)
    except Exception as e:
        print(f"Launch failed: {str(e)}") 
