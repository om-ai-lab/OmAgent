import cv2
from PIL import Image
import base64
from io import BytesIO

def process_video(video_path: str, desired_fps: float):
    """
    Process an MP4 video and extract frames at a specified frame rate.
    
    Parameters:
        video_path (str): Path to the input MP4 file.
        desired_fps (float): The frame rate at which to extract frames.
                             For example, if the video is 30 fps and desired_fps is 5,
                             the function will extract one frame every 6 frames.
                             
    Returns:
        List[Tuple[float, np.ndarray]]:
            A list where each element is a tuple (timestamp, frame_image).
            - timestamp: Time in seconds when the frame was captured.
            - frame_image: The image (as a numpy array) of the extracted frame.
    """
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Error opening video file: {video_path}")
    
    # Get the original frames per second of the video
    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    if orig_fps <= 0:
        raise ValueError("Cannot determine the video's FPS.")
    
    # Calculate the interval (in number of frames) to achieve the desired processing fps
    frame_interval = int(round(orig_fps / desired_fps))
    # If the desired fps is higher than the original fps, process every frame
    if frame_interval < 1:
        frame_interval = 1

    frames = []
    frame_count = 0
    success, frame = cap.read()
    
    while success:
        # Only process frames that match the interval
        if frame_count % frame_interval == 0:
            # Calculate timestamp in seconds for this frame
            timestamp = frame_count / orig_fps
            frames.append((timestamp, frame))
        frame_count += 1
        success, frame = cap.read()
    
    cap.release()
    return frames

def process_video_yield(video_path: str, desired_fps: float, output_format: str = "numpy"):
    """
    Process an MP4 video and yield frames at a specified frame rate.
    
    Parameters:
        video_path (str): Path to the input MP4 file.
        desired_fps (float): The frame rate at which to extract frames.
        output_format (str): Format of the returned frame.
                             "numpy" (default): return as a NumPy array.
                             "PIL": return as a PIL Image.
                             "base64": return as a base64 encoded JPEG string.
    
    Yields:
        Tuple[float, Any]: A tuple (timestamp, frame) where:
            - timestamp: Time in seconds when the frame was captured.
            - frame: The frame in the desired format.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Error opening video file: {video_path}")
    
    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    if orig_fps <= 0:
        raise ValueError("Cannot determine the video's FPS.")
    
    frame_interval = int(round(orig_fps / desired_fps))
    if frame_interval < 1:
        frame_interval = 1

    frame_count = 0
    success, frame = cap.read()
    
    while success:
        if frame_count % frame_interval == 0:
            timestamp = frame_count / orig_fps
            if output_format == "PIL" or output_format == "base64":
                # Convert frame from BGR to RGB format
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                if output_format == "base64":
                    buffer = BytesIO()
                    pil_image.save(buffer, format="JPEG")
                    buffer.seek(0)
                    frame_output = base64.b64encode(buffer.read()).decode("utf-8")
                else:
                    frame_output = pil_image
            else:
                frame_output = frame
            yield (timestamp, frame_output)
        frame_count += 1
        success, frame = cap.read()
    
    cap.release()

def process_video_stream(stream_source, desired_fps: float):
    """
    Process a video stream and yield frames at a specified frame rate.
    
    Parameters:
        stream_source (str or int): The source for the video stream.
                                    This can be a URL (e.g., for an RTSP stream)
                                    or an integer for a webcam device (e.g., 0).
        desired_fps (float): The rate (in frames per second) at which to process frames.
    
    Yields:
        Tuple[float, np.ndarray]: A tuple (timestamp, frame_image) where:
            - timestamp: Time in seconds when the frame was captured.
            - frame_image: The captured frame as a NumPy array.
    """
    cap = cv2.VideoCapture(stream_source)
    if not cap.isOpened():
        raise ValueError(f"Error opening video stream: {stream_source}")
    
    # Try to get the original FPS; if not available, default to 30
    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    if orig_fps <= 0:
        orig_fps = 30.0

    # Calculate the frame interval to yield frames at the desired FPS
    frame_interval = int(round(orig_fps / desired_fps))
    if frame_interval < 1:
        frame_interval = 1

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            # If the frame is not read successfully, break or implement reconnect logic
            print("Failed to retrieve frame; exiting stream loop.")
            break
        if frame_count % frame_interval == 0:
            timestamp = frame_count / orig_fps
            yield (timestamp, frame)
        frame_count += 1

    cap.release()

# Example usage:
if __name__ == "__main__":
    video_file = "/Users/kyusonglee/Downloads/VID_20241127_143638.mp4"  # Replace with your MP4 file path
    target_fps = 2  # Process 2 frames per second
    
    # Change output_format to "numpy", "PIL", or "base64" as needed
    output_format = "numpy"
    
    try:
        for timestamp, frame in process_video(video_file, target_fps, output_format):
            print(f"Frame at {timestamp:.2f} seconds")
            if output_format == "numpy":
                print("Frame shape:", frame.shape)
            elif output_format == "PIL":
                frame.show()  # This will open the image using the default image viewer
            elif output_format == "base64":
                print("Base64 string length:", len(frame))
    except Exception as e:
        print("Error:", e)
