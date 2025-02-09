import markdown
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from methods import get_response_from_gemini, generate_response_Llama, generate_response_deepseek ,store_query_embedding_and_result_in_mongodb ,find_relevant_documents
import html
import asyncio

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


async def get_all_responses(prompt: str):
    """
    Get responses from all models concurrently
    """
    global prompt_db, gemini_res, llama_res, deepseek_res
    try:
        # Run all model calls concurrently
        gemini_task = asyncio.create_task(get_response_from_gemini(prompt))
        llama_task = asyncio.create_task(generate_response_Llama(prompt))
        deepseek_task = asyncio.create_task(generate_response_deepseek(prompt))

        # Wait for all tasks to complete
        responses = await asyncio.gather(
            gemini_task,
            llama_task,
            deepseek_task,
            return_exceptions=True
        )

        # Handle any exceptions
        gemini_response = format_response(str(responses[0])) if not isinstance(responses[0],
                                                                               Exception) else f"Error: {str(responses[0])}"
        llama_response = format_response(str(responses[1])) if not isinstance(responses[1],
                                                                              Exception) else f"Error: {str(responses[1])}"
        deepseek_response = format_response(str(responses[2])) if not isinstance(responses[2],
                                                                                 Exception) else f"Error: {str(responses[2])}"

        prompt_db = prompt
        gemini_res = str(responses[0])
        llama_res= str(responses[1])
        deepseek_res = str(responses[2])
        return gemini_response, llama_response, deepseek_response

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return error_msg, error_msg, error_msg


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate_response(request: Request, prompt: str = Form(...)):
    formatted_prompt = format_response(prompt)

    # Get responses from all models
    gemini_response, llama_response, deepseek_response = await get_all_responses(prompt)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "prompt": formatted_prompt,
        "gemini_response": gemini_response,
        "llama_response": llama_response,
        "deepseek_response": deepseek_response,
        "show_create_thread": True
    })


@app.post("/create_thread")
async def create_thread(request: Request, response_text: str = Form(...)):
    response_from_db = store_query_embedding_and_result_in_mongodb(prompt_db,gemini_res, llama_res, deepseek_res)
    # return response_from_db
    return RedirectResponse(url=f"/", status_code=303)


@app.get("/thread/{thread_id}", response_class=HTMLResponse)
async def read_thread(request: Request, thread_id: int):
    thread_content = threads.get(thread_id, "Thread not found")
    formatted_content = format_response(thread_content)
    return templates.TemplateResponse("thread.html", {
        "request": request,
        "thread_content": formatted_content
    })


@app.get("/search", response_class=HTMLResponse)
async def search_threads(request: Request ,prompt: str = Form(...)):
    list_of_res = find_relevant_documents(prompt,5)
    return list_of_res
    # return templates.TemplateResponse("search.html", {
    #     "request": request,
    #     "threads": threads
    # })