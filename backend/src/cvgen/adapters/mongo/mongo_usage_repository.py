from __future__ import annotations

import datetime as dt
import os
from typing import Any, Dict, Optional

from pymongo import MongoClient

from cvgen.domain.ports.usage_repository import UsageRepository


class MongoUsageRepository(UsageRepository):
    def __init__(
        self,
        *,
        mongo_url: str,
        mongo_db: str,
        collection: str = "cv_usages",
    ) -> None:
        self._mongo_url = mongo_url
        self._mongo_db = mongo_db
        self._collection = collection
        self._client = MongoClient(mongo_url)
        self._coll = self._client[mongo_db][collection]

    def log_usage(
        self,
        *,
        ip: str,
        user_agent: str,
        output_format: str,
        font_color: Optional[str],
        payload: Dict[str, Any],
    ) -> None:
        doc = {
            "created_at": dt.datetime.utcnow(),
            "ip": ip,
            "user_agent": user_agent,
            "output_format": output_format,
            "font_color": font_color,
            "payload": payload,
        }
        self._coll.insert_one(doc)


def build_mongo_usage_repository() -> MongoUsageRepository:
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongo_db = os.getenv("MONGODB_DB", "cv_generator")
    return MongoUsageRepository(mongo_url=mongo_url, mongo_db=mongo_db)

