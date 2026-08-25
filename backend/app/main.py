"""FastAPI app skeleton — First Vertical Slice only.

Routes cover exactly: Create Case, upload one questionnaire (which
identifies its questions), list questions, create a SUBMISSION action, and
read the case/actions back. See docs/spec/README-Team-Specs.md, "First
Vertical Slice", and backend/README.md for the scope boundary.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import actions, cases, documents, evidence, questions
from app.routers import auth as auth_router

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(cases.router)
app.include_router(documents.router)
app.include_router(questions.router)
app.include_router(actions.router)
app.include_router(evidence.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
