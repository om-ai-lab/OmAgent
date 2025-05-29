# ui.py
import gradio as gr
import pandas as pd
import time
import uvicorn
import threading
from connect_server.http_server import task_manager, TaskStatus, app as api_app
from dog_api.map_interact import get_latest_image, handle_image_click
from dog_api.get_video import unitree_stream_video, realsense_stream_video
from fastrtc import WebRTC
from dog_api.move_control import keyboard_control_human_navigation

from dog_api.map_interact import connect_to_server, sio

def get_current_task():
    """Get current task"""
    try:
        res, task = task_manager.get_status()
        if res and task and task.status == TaskStatus.RUNNING:
            return task.task_info
        return ""
    except Exception as e:
        print(f"Error getting current task: {e}")
        return ""

def get_history_tasks():
    """Get history task list"""
    try:
        tasks = task_manager.finished_tasks
        if not tasks:
            return pd.DataFrame(columns=["Task ID", "Task Info", "Status", "Time"])
        
        data = []
        for task in tasks:
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(task.timestamp))
            status_str = "Completed" if task.status == TaskStatus.FINISHED else str(task.status.value)
            data.append({
                "Task ID": task.task_id,
                "Task Info": task.task_info,
                "Status": status_str,
                "Time": time_str
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error getting history tasks: {e}")
        return pd.DataFrame(columns=["Task ID", "Task Info", "Status", "Time"])

def finish_task():
    """Complete current task"""
    try:
        res, task = task_manager.stop_task()
        return get_current_task(), get_history_tasks()
    except Exception as e:
        print(f"Error completing task: {e}")
        return "", get_history_tasks()
    
def fail_task(reason):
    """Fail task"""
    try:
        res, task = task_manager.fail_task(reason)
        return get_current_task(), get_history_tasks()
    except Exception as e:
        print(f"Error failing task: {e}")
        return "", get_history_tasks()

# Create Gradio interface
with gr.Blocks(title="navigation") as demo:
    gr.Markdown("# Navigation Task Management System")
    
    
    
    with gr.Row():
        with gr.Column(scale=1):
            map_view = gr.Image(lambda: get_latest_image(), label="Height Map", height=800, width=480, every=1)
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("X")
                    x_text = gr.Textbox(value="-", label="X", interactive=False)
                with gr.Column(scale=1):
                    gr.Markdown("Y")
                    y_text = gr.Textbox(value="-", label="Y", interactive=False)
            map_view.select(
                fn=handle_image_click,
                inputs=[map_view],
                outputs=[x_text, y_text]
            )
            
            with gr.Row():
                key_input = gr.Textbox(
                    show_label=False,
                    placeholder="Click to start controlling the robot dog",
                    elem_classes="keyboard-input",
                    lines=1,
                    max_lines=1,
                    autofocus=True,  # Auto focus
                    interactive=True,
                    container=False
                )
                            
                # Set text box changes to trigger handler function
                key_input.change(
                    fn=keyboard_control_human_navigation,
                    inputs=[key_input],
                    outputs=[key_input]
                )
        with gr.Column(scale=2):
            
            with gr.Row():
                # with gr.Column(scale=1):
                unitree_video = WebRTC(label="Unitree Video Stream", mode="receive", modality="video")
            with gr.Row():
                unitree_button = gr.Button("Start Unitree Stream", variant="primary")
            unitree_video.stream(
                fn=unitree_stream_video,
                # inputs=[unitree_video],
                outputs=[unitree_video],
                trigger=unitree_button.click,
            )
            with gr.Row():
                # with gr.Column(scale=1):
                realsense_video = WebRTC(label="Realsense Video Stream", mode="receive", modality="video")
            with gr.Row():   
                realsense_button = gr.Button("Start Realsense Stream", variant="primary")
            realsense_video.stream(
                fn=realsense_stream_video,
                # inputs=[realsense_video],
                outputs=[realsense_video],
                trigger=realsense_button.click,
            )
        
    with gr.Row():    
        with gr.Column(scale=1):
            task_info = gr.Textbox(value=lambda: get_current_task(), label="Current Task Info", every=1.0)
            
            # Control buttons
            with gr.Row():
                finish_btn = gr.Button("Task Complete", variant="stop")  
                failed_reason = gr.Textbox(value="", label="Failure Reason", interactive=True)
                failed_btn = gr.Button("Task Failed", variant="stop")

        with gr.Column(scale=2):
            gr.Markdown("## Task History")
            history_table = gr.Dataframe(
                label="Task History List",
                value=lambda: get_history_tasks(),
                interactive=False,
                every=1.0
            )
    
    # Button event binding
    finish_btn.click(
        fn=finish_task,
        inputs=[],
        outputs=[task_info, history_table]
    )
    
    failed_btn.click(
        fn=fail_task,
        inputs=[failed_reason],
        outputs=[task_info, history_table]
    )

# Mount Gradio app to FastAPI application
app = gr.mount_gradio_app(
    app=api_app,
    blocks=demo,
    path="/gradio",
    server_name="127.0.0.1",
    server_port=7869,
    app_kwargs={"docs_url": "/docs"},
)

# Start server
if __name__ == "__main__":
    try:
        server_thread = threading.Thread(target=connect_to_server)
        server_thread.daemon = True
        server_thread.start()
    except Exception as e:
        print(f"Failed to connect to map navigation server: {e}")
    
    try:
        print("API service and UI interface started on the same server")
        print("API documentation URL: http://127.0.0.1:7869/docs")
        print("UI interface URL: http://127.0.0.1:7869/gradio")
        uvicorn.run(app, host="0.0.0.0", port=7869)
    except Exception as e:
        print(f"Failed to start human_navigation_ui service: {e}")
    
    finally:
        if sio.connected:
            sio.disconnect()
