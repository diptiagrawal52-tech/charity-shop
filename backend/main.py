import os
import pathlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Verify Gemini API Key exists
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # We will log a warning, but not crash immediately on startup so the server can run
    # and provide health endpoints or raise errors dynamically on requests.
    print("WARNING: GEMINI_API_KEY environment variable is not set. Please configure it in your .env file.")

# Configure Gemini Client if key exists
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(
    title="Charity Shop Smart Triage Assistant API",
    description="Backend AI microservice for triaging charity shop operational crises using gemini-2.5-flash.",
    version="1.0.0"
)

# Enable CORS for decoupled frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve frontend path relative to main.py
BASE_DIR = pathlib.Path(__file__).parent.parent
FRONTEND_INDEX = BASE_DIR / "frontend" / "index.html"

# Define request schema
class TriageRequest(BaseModel):
    volunteers_scheduled: int = Field(..., ge=0, description="Number of volunteers scheduled to work today.")
    volunteers_present: int = Field(..., ge=0, description="Number of volunteers who actually showed up.")
    key_roles_missing: list[str] = Field(default=[], description="List of missing key roles (e.g., Till, Sorter).")
    donation_bags_clothing: int = Field(default=0, ge=0, description="Bags of clothing donated today.")
    donation_boxes_misc: int = Field(default=0, ge=0, description="Boxes of books, media, or bric-a-brac donated today.")
    donation_high_value_items: list[str] = Field(default=[], description="Noted high-value items or special donations.")
    daily_revenue_target: float = Field(..., gt=0, description="Today's retail sales target in GBP (£).")
    current_campaign_focus: str = Field(default="General Research", description="Current retail/fundraising campaign focus.")

# Define response schema
class TriageResponse(BaseModel):
    status: str
    triage_plan: str  # Markdown formatted plan returned by Gemini

SYSTEM_PROMPT = """
You are an expert Social Enterprise Consultant and Principal Retail Operations Architect specializing in Cancer Research UK charity shops. Your goal is to guide resource-strapped shop managers through operational crises to maximize efficiency and fundraising output.

When analyzing the daily store conditions, you MUST create a highly actionable, encouraging, and structured response. You must enforce the following three markdown sections exactly:

### [VOLUNTEER ROSTER RESCUE]
- Provide a concrete strategy to allocate the remaining staff and volunteers.
- Address missing key roles (e.g. Till, Sorter, Backroom) with clear cross-training shifts or emergency adjustments.
- Give a timeline of roles (e.g., morning rotation vs afternoon rotation) to avoid volunteer burnout.

### [DONATION TRIAGE]
- Create a fast-track sorting strategy for the incoming items.
- Provide guidelines on how to quickly spot high-value "gems" (e.g. vintage tags, rare media, designer brands, silver/gold) to prioritize putting on the shop floor immediately.
- Suggest safe holding strategies for bulk stock if volunteer capacity is too low to process everything.

### [DAILY REVENUE FOCUS]
- Detail 2-3 specific visual merchandising or tactical pricing strategies aligned with the daily revenue target and current campaign focus.
- Remind the manager and team how today's sales directly connect to funding life-saving cancer research trials. Keep this motivating but operationally practical.

CRITICAL RULES:
1. You must maintain an encouraging, urgent, and professional tone.
2. Use bullet points and bold highlights for readability under high stress.
3. Only use the three section headers defined above. Do not invent new top-level headers.
"""

@app.get("/")
async def read_index():
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(FRONTEND_INDEX)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_api_configured": GEMINI_API_KEY is not None
    }

@app.post("/api/triage", response_model=TriageResponse)
async def get_triage_plan(payload: TriageRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="Gemini API Key is missing. Please set GEMINI_API_KEY in the environment or .env file."
        )
    
    # Reconfigure just in case env changed dynamically
    genai.configure(api_key=api_key)

    try:
        # Construct the user message
        user_message = f"""
        Analyze today's store parameters and generate a Triage Plan:
        
        - Volunteer Status: Scheduled: {payload.volunteers_scheduled}, Present: {payload.volunteers_present}. Missing key roles: {', '.join(payload.key_roles_missing) if payload.key_roles_missing else 'None'}.
        - Donation Influx: {payload.donation_bags_clothing} bags of clothing, {payload.donation_boxes_misc} boxes of books/bric-a-brac. Special items noted: {', '.join(payload.donation_high_value_items) if payload.donation_high_value_items else 'None'}.
        - Fundraising Goal: Target: £{payload.daily_revenue_target:.2f}. Campaign Focus: "{payload.current_campaign_focus}".
        """

        # Call Gemini API
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        response = model.generate_content(
            user_message,
            generation_config={"temperature": 0.2}
        )
        
        return TriageResponse(
            status="success",
            triage_plan=response.text
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
