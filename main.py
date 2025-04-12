# import
import requests
from nixgui import ui, events
import base64
from dotenv import load_dotenv
import os

# ----- API SETUP ----- #

load_dotenv()

API_URL = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer " + os.getenv("OPENAI_API_KEY"),
    "Content-Type": "application/json"
}

# ----- USER INTERFACE ----- #

@ui.page("/")
def main():

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

    # Create initial UI
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

    base_prompt = "You are an SEO specialist and you need to write ADA-compliant alt text for this image. What would you write? Return only the alt text, with no additional output. Limit your response to {char_limit} characters. ".format(char_limit=char_limit)
    if context:
        base_prompt += "The user has provided the following context regarding the image, which you should use to inform the generated alt text: {context}. ".format(context=context)
    if keywords:
        base_prompt += "The user has provided the following keywords which you should optimise the alt text for: {keywords}.".format(keywords=keywords)

    payload = {
    "model": "gpt-4o-mini",
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
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()
    except:
        return {"choices": [{"message": {"content": "Error generating alt text, please try again"}}]}

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()