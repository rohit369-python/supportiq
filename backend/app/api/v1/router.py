"""Aggregate API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, tickets, chatbot

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(tickets.router)
api_router.include_router(chatbot.router)

# Placeholder routers for remaining modules (extend as needed)
# from app.api.v1 import customers, knowledge, analytics, admin, notifications
# api_router.include_router(customers.router)
# ...