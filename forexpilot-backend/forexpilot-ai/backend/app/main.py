from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routes import accounts, analytics, auth, bot, settings as settings_routes, strategies, trades
from app.core.config import settings
from app.core.database import init_db
from app.core.security import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.environment != "development" and settings.secret_key == "change-me":
        raise RuntimeError("Set a strong SECRET_KEY before running outside development")
    init_db()
    yield


app = FastAPI(title="ForexPilot AI API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
for r in (accounts, trades, strategies, analytics, settings_routes, bot):
    app.include_router(r.router, dependencies=[Depends(get_current_user)])


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}
