# import
import requests
from nicegui import ui, app, Client, events, run
from fastapi import Request
import time
import base64
from dotenv import load_dotenv
import os

# ----- USAGE TRACKING ----- #

load_dotenv()

runtime_tracker = {}

completion_tracker = []

API_ENDPOINT = "https://nix-api-3gwo3skrxq-nw.a.run.app"
SCRIPT_ID = "8d57117c-d617-41d0-94b1-8ae1c6461049"

API_URL = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer " + os.getenv("OPENAI_API_KEY"),
    "Content-Type": "application/json"
}

def start_run(client: Client):
    print("Starting run for user: " + client.ip + " with client ID: " + client.id)
    existing_client = runtime_tracker.get(client.ip)
    if existing_client:
        existing_session = existing_client.get(client.id)
        if existing_session:
            print("Session with same ID already exists for user, updating start time")
        existing_client[client.id] = {"start_time": client.created}
    else:
        print("User does not exist in tracker, creating new user and session")
        runtime_tracker[client.ip] = {client.id: {"start_time": client.created}}

def end_run(client: Client):
    print("Ending run for user: " + client.ip + " with client ID: " + client.id)
    existing_client = runtime_tracker.get(client.ip)
    if existing_client:
        existing_session = existing_client.get(client.id)
        if existing_session:
            completed_run = {"rid": client.id, "uid": existing_client["uid"], 
                             "start_time": existing_session["start_time"], "end_time": time.time(),
                             }
            completion_tracker.append(completed_run)
            existing_client.pop(client.id)
        else:
            print("Error ending run: Session does not exist")
    else:
        print("Error ending run: Client does not exist")

def tag_run(request: Request, uid: str = None):
    existing_client = runtime_tracker.get(request.client.host)

    print("Tagging run for user: " + request.client.host + " with UID: " + uid)
    if existing_client:
        existing_client["uid"] = uid # TODO: Get UID from request
    else:
        print("Client does not exist, starting & tagging run")
        runtime_tracker[request.client.host] = {"start_time": time.time(), "uid": uid}

def shutdown_app():
    print("Shutting down")
    print("Exporting all completed sessions")
    for session in completion_tracker:
        print("Exporting session:")
        print(session)
        try:
            requests.post(url = API_ENDPOINT + "/scripts/{sid}/run".format(sid = SCRIPT_ID), json=session)
        except:
            print("Error exporting session")
    
app.on_connect(start_run)
app.on_disconnect(end_run)
app.on_shutdown(shutdown_app)

# ----- GLOBAL STYLING ----- #
            
ui.button.default_classes("rounded-md bg-blue-grey-6 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-grey-5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-grey-6 w-96")
ui.textarea.default_classes("block rounded-md border-none py-1.5 text-blue-grey-9 shadow-sm placeholder:text-blue-grey-4 focus:ring-2 focus:ring-inset focus:ring-blue-grey-6 sm:text-sm sm:leading-6 w-96")
ui.input.default_classes("block rounded-md border-0 py-1.5 text-blue-grey-9 shadow-sm placeholder:text-blue-grey-4 focus:ring-2 focus:ring-inset focus:ring-blue-grey-6 sm:text-sm sm:leading-6 w-96")
ui.number.default_classes("block rounded-md border-0 py-1.5 text-blue-grey-9 shadow-sm placeholder:text-blue-grey-4 focus:ring-2 focus:ring-inset focus:ring-blue-grey-6 sm:text-sm sm:leading-6 w-96")
ui.label.default_classes("max-w-xl text-base leading-7 text-blue-grey-7 lg:max-w-lg w-96")
ui.html.default_classes("max-w-xl text-base leading-7 text-blue-grey-7 lg:max-w-lg w-96")
ui.image.default_classes("max-w-xl text-base leading-7 text-blue-grey-7 lg:max-w-lg w-96")
ui.markdown.default_classes("max-w-xl text-base leading-7 text-blue-grey-7 lg:max-w-lg w-96")
ui.select.default_classes("mt-2 block rounded-md border-0 py-1.5 pl-3 pr-10 text-blue-grey-9 focus:ring-2 focus:ring-blue-grey-6 sm:text-sm sm:leading-6 w-96")
ui.switch.default_classes("relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-grey-6 focus:ring-offset-2 w-96")
ui.upload.default_classes("mt-2 block rounded-md border-0 py-1.5 text-blue-grey-9 shadow-sm focus:ring-2 focus:ring-inset focus:ring-blue-grey-6 sm:text-sm sm:leading-6 w-96").default_props("color=blue-grey")
        
# ----- WEB UI ----- #

@ui.page("/") # uid must be passed as a query parameter
def page(request: Request, uid: str):
    tag_run(request, uid)

    # Process and display image
    async def process_image(e: events.UploadEventArguments):
        image = base64.b64encode(e.content.read())
        image_bytes = image.decode()
        ui.image(f'data:{e.type};base64,{image_bytes}')
        with ui.row():
            loading_spinner = ui.spinner()
            generated_text = ui.label("Generating alt text...")
        response = await run.io_bound(generate_alt_text, image_bytes, context_input.value, keywords_input.value, int(char_limit_input.value))
        loading_spinner.delete()
        generated_text.set_text(response["choices"][0]["message"]["content"])

    # Create static UI
    ui.label("Define settings below (optional):")
    context_input = ui.input(label="Context", placeholder="We are an e-commerce website selling digital tools").classes("w-96")
    keywords_input = ui.input(label="Keywords", placeholder="digital tools, software, technology").classes("w-96")
    char_limit_input = ui.number(label="Max characters", value=120, format="%.0f", min=1, max=1000, step=1).classes("w-96")
    
    ui.label("Upload image below:")
    ui.upload(on_upload=process_image, auto_upload=True).props("accept=image/*")

    ui.separator()

# ----- SCRIPT ----- #

def generate_alt_text(image_bytes, context=None, keywords=None, char_limit=120):
    
    # A token is roughly 4 characters
    est_tokens = char_limit * 4

    base_prompt = "You are an SEO specialist and you need to write an alt text for this image. What would you write? Return only the alt text, with no additional output. Limit your response to {char_limit} characters. ".format(char_limit=char_limit)
    if context:
        base_prompt += "The user has provided the following context regarding the image, which you should use to inform the generated alt text: {context}. ".format(context=context)
    if keywords:
        base_prompt += "The user has provided the following keywords which you should optimise the alt text for: {keywords}.".format(keywords=keywords)

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": base_prompt
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/*;base64,{image_bytes}"
            }
            }
        ]
        }
    ],
    "max_tokens": est_tokens
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        return response.json()
    except:
        return {"choices": [{"message": {"content": "Error generating alt text, please try again"}}]}

ui.run()