import markdown
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from methods import get_response_from_gemini
import html

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# In-memory storage for threads
threads = {}

def format_response(text: str) -> str:
    """
    Formats response text to:
    - Properly render code blocks.
    - Ensure line breaks are preserved.
    """

    md_extensions = ["fenced_code", "codehilite"]

    formatted_text = markdown.markdown(text, extensions=md_extensions)

    return f'<div class="normal-text">{formatted_text}</div>'

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate_response(request: Request, prompt: str = Form(...)):
    response_text = get_response_from_gemini(prompt)
    formatted_response = format_response(response_text)  # Format response
    formatted_prompt = format_response(prompt)  # Format prompt with Markdown

    return templates.TemplateResponse("index.html", {
        "request": request,
        "prompt": formatted_prompt,  # Pass formatted prompt
        "response_text": formatted_response,
        "show_create_thread": True  # Show create thread button when response is available
    })


@app.post("/create_thread")
async def create_thread(request: Request, response_text: str = Form(...)):
    thread_id = len(threads) + 1
    threads[thread_id] = response_text
    return RedirectResponse(url=f"/thread/{thread_id}", status_code=303)

@app.get("/thread/{thread_id}", response_class=HTMLResponse)
async def read_thread(request: Request, thread_id: int):
    thread_content = threads.get(thread_id, "Thread not found")
    formatted_content = format_response(thread_content)  # Apply formatting to threads
    return templates.TemplateResponse("thread.html", {
        "request": request,
        "thread_content": formatted_content
    })

@app.get("/search", response_class=HTMLResponse)
async def search_threads(request: Request):
    return templates.TemplateResponse("search.html", {
        "request": request,
        "threads": threads
    })