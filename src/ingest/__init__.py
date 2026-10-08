"""Ingestion module for Signal-to-Shock."""
from src.ingest.base import BaseIngestClient
from src.ingest.cache import FileCache
from src.ingest.newsapi_client import NewsAPIClient
from src.ingest.gdelt_client import GDELTClient
from src.ingest.social_loader import SocialLoader

__all__ = [
    "BaseIngestClient",
    "FileCache",
    "NewsAPIClient",
    "GDELTClient",
    "SocialLoader",
]
