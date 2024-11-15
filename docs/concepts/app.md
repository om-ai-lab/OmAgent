# App

OmAgent App is an app for developers to visualize and edit business scenario content for large model capabilities. It supports interaction with multimodal large models by obtaining data from mobile phone cameras, audio streams, etc., and combining memory, tool invocation, and other capabilities. Based on the business scenarios developed by users, it outputs corresponding content through interaction with the Agent service, providing a demonstration app for intelligent agent scenario development with multimodal content input and output. Next, we will introduce the relevant functions of OmAgent App step by step to start the user's experience journey.

## App Installation
The QR code for downloading the app is as follows:

<p align="center">
  <img src="../images/app_qrcode.png" width="300"/>
</p>

- Currently, only Android phones are supported for download and use, but iOS support is coming soon.

## App Usage

### 1. APP Home Page
After opening the APP, the guide page will be displayed as shown in the figure below:

<p align="center">
  <img src="../images/app_boot_page.png" width="300"/>
</p>

The APP home page includes Mobile, Glasses, and Connection Settings as shown below:
<p align="center">
  <img src="../images/app_home.png" width="300"/>
</p>

#### 1.1 Connection Settings
The app automatically searches for and connects to the environment IP running on the local network. If the connection is successful, a toast message will display: "Connection Successful". If the connection fails, a toast message will display: "Service connection failure".
- Click the "Connection Settings" button at the bottom of the homepage to enter the app configuration page, as shown in the figure below;
<p align="center">
  <img src="../images/app_connection_settings.png" width="300"/>
</p>

- Enter the correct IP in the IP input box and click the "Connection" button at the bottom. After a successful connection, return to the homepage and click the "Mobile" section to enter the Mobile page. 
- Note: The IP input box displays the last successfully connected IP address by default.

### 2. Mobile
"Mobile" mainly includes settings, voice input, camera, multimodal, brush functions, etc.

#### 2.1 Return to Home Page
Click the top left return to home button ![](../images/app_home_button.png) to return to the home page.

#### 2.2 Settings
Click the top right settings button ![](../images/app_setting_button.png), the page will pop up a settings window, as shown below. Click the ![](../images/app_close_button.png) button or outside the window to close the window.

<p align="center">
  <img src="../images/app_setting.png" width="300"/>
</p>

##### 2.2.1 Album
Click Album to enter the gallery page, loading 80 images at a time, as shown below:

<p align="center">
  <img src="../images/app_album.png" width="300"/>
</p>

- Click Reindex, if indexing is successful, the page will prompt success, indicating that all images in the gallery have been successfully indexed. If it fails, it will prompt: failure. After selecting images, click Reindex to index only the selected images.

- Click Select to trigger batch selection, all images on the page will display a checkmark icon at the bottom right; the page selection button changes to deselect, the Upload button changes to Delete, allowing images to be selected for deletion; click Cancel to return to the unselected state.

- Click Upload to call the album, select images to upload, the gallery dynamically displays, uploads are displayed immediately, up to 20 images can be selected at a time. During the upload process, click Cancel to stop uploading images (the page only displays successfully uploaded images).

- Click on an image to enlarge and preview it, as shown below; supports left and right sliding and deletion. The top displays the image page number, which can be clicked to return to the gallery.

<p align="center">
  <img src="../images/app_album_img.png" width="300"/>
</p>

- Click the top left return button on the gallery page ![](../images/app_back_button.png), the return button returns to the Mobile page, and the settings window is still displayed.

##### 2.2.2 Chat History
Click Chat history to enter the history dialogue page, displaying all dialogue content, as shown below; click Delete all to confirm the operation and clear the history dialogue.

<p align="center">
  <img src="../images/app_chat_history.png" width="300"/>
</p>

History dialogue display rules:
- Different Workflow dialogues are displayed separated by time, supporting up and down sliding.

- A single Workflow content dialogue includes text and images, with multiple image scenarios. Click on an image to preview it, and multiple image previews support sliding.

- The progress menu within a single Workflow supports clicking to expand, as shown below:

<p align="center">
  <img src="../images/app_chat_history2.png" width="300"/>
</p>

- Share: Click the share button under the Workflow dialogue, the share function is displayed at the bottom of the page, as shown below: sharing can be done as needed.

<p align="center">
  <img src="../images/app_chat_history3.png" width="300"/>
</p>

##### 2.2.3 Multi-turn Dialogue
Click Multi-turn dialogue to display the multi-turn dialogue dropdown menu, default is 1 turn, up to 10 turns can be set, as shown below:

<p align="center">
  <img src="../images/app_multi-turn_setting.png" width="300"/>
</p>

##### 2.2.4 Workflow Settings
Click Workflow Settings to enter the Workflow list selection page, as shown below:

<p align="center">
  <img src="../images/app_workflow_setting.png" width="300"/>
</p>

In the list, you can click to select the required Workflow, only single selection is supported. After selection, a checkmark ![](../images/app_check_button.png) icon is displayed. Click the refresh button ![](../images/app_refresh_button.png) to refresh the list.

##### 2.2.5 Parameter Settings
Click Parameter Settings to enter the custom parameter settings page, as shown below:

<p align="center">
  <img src="../images/app_parameter_setting.png" width="300"/>
</p>

Click +Add parameter, the page displays Parameter name\value input boxes, as shown below; the input boxes support deletion, and the input box can add up to 20. After adding 20, there is no +Add parameter button. Click SAVE to save successfully (the input box content can be empty to save successfully).

<p align="center">
  <img src="../images/app_parameter_setting2.png" width="300"/>
</p>

#### 2.3 Global Voice
![](../images/app_voice_button.png) Default is on, click to turn off, click to switch to on prompt: Voice auto-play is on, switch to off prompt: Voice auto-play is off.

#### 2.4 Camera
![](../images/app_camera_button.png) Default is rear, click to switch to front, the page previews the camera screen in real-time, page gestures: ① click to focus ② pinch to zoom, after zooming, a 1X button is displayed, click the 1X button to return to 1X zoom, the 1X button disappears.

#### 2.5 Voice Dialogue
Long press the voice button to trigger the voice recognition function, long press to speak and then release, the page displays the dialogue section, as shown below:

<p align="center">
  <img src="../images/app_voice_dialog.png" width="600"/>
</p>

Note: When the model reply content has images, click the image to enlarge and preview.

##### 2.5.1 Expand
![](../images/app_expand_button.png) Click the expand button to display the entire dialogue section, as shown below:

<p align="center">
  <img src="../images/app_voice_dailog2.png" width="300"/>
</p>

Click the collapse button at the top of the image ![](../images/app_collapse_button.png) to collapse the dialogue.

##### 2.5.2 Workflow
![](../images/app_workflow_name.png) is the Workflow name of the current dialogue. Click the button on the right ![](../images/app_workflow_button.png) to display the Workflow progress, as shown below:

<p align="center">
  <img src="../images/app_workflow_progress.png" width="300"/>
</p>

The progress menu supports expanding and collapsing.

##### 2.5.3 Regenerate
![](../images/app_workflow_button2.png) The regenerate button is displayed under the nearest model reply content. Click to regenerate and overwrite the previous reply content.

##### 2.5.4 Voice Broadcast
![](../images/app_play_voice.png) The small voice button is displayed under the nearest model reply content. When voice is playing, it is displayed as ![](../images/app_stop_voice.png). After the nearest model reply ends or is manually clicked, it is displayed as ![](../images/app_play_voice.png). After the nearest model reply ends, click this button to replay the nearest model reply content;
- When the global voice button is on, voice broadcast is on by default. After turning off the global voice, there is no voice broadcast. At this time, click the small voice button to replay the nearest model reply content.

##### 2.5.5 Stop Generating
![](../images/app_stop_generating.png) Stop generating, in the content output state, you can manually click to stop generating and interrupt the model reply.

#### 2.6 Voice - Timing Mode
Long press the voice button to speak, do not release, slide up to timing ![](../images/app_time_button.png) and then release, the page enters the timing mode frame extraction 5-second countdown ![](../images/app_time_button2.png), timing frame extraction mode, voice input cannot be clicked, the button is grayed out; after the countdown ends, the dialogue module is displayed to show the dialogue content; (during the 5-second countdown, click the countdown to end the timing frame extraction early).

#### 2.7 Cancel Sending
Long press the voice button to speak, do not release, slide up to ![](../images/app_cancel_button.png) and then release, cancel sending.

#### 2.8 Brush
![](../images/app_brush_button1.png) Default is grayed out, click to enable the brush function, the page displays brush color and eraser buttons as shown below:

<p align="center">
  <img src="../images/app_brush_button2.png" width="300"/>
</p>

Supports selecting different colors for brush annotation on the real-time camera preview page; click the eraser ![](../images/app_brush_button3.png) to remove all brush annotations; click the brush button ![](../images/app_brush_button4.png) to turn off the brush function (brush marks are displayed on the dialogue images using the brush in the history dialogue page).

