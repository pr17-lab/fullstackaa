import hashlib
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.core.database import get_db
from app.core.config import settings
from app.models.job_cache import JobCache

router = APIRouter()

def get_fallback_jobs(job_role: str) -> Dict[str, Any]:
    encoded_role = urllib.parse.quote(job_role)
    fallback_jobs = [
        {
            "job_id": f"linkedin-{job_role}",
            "job_title": f"Search on LinkedIn",
            "employer_name": "LinkedIn",
            "job_city": "India",
            "job_country": "IN",
            "job_apply_link": f"https://www.linkedin.com/jobs/search/?keywords={encoded_role}",
            "job_description": f"Click to search for recent {job_role} roles on LinkedIn.",
            "job_posted_at_datetime_utc": datetime.now(timezone.utc).isoformat()
        },
        {
            "job_id": f"indeed-{job_role}",
            "job_title": f"Search on Indeed",
            "employer_name": "Indeed",
            "job_city": "India",
            "job_country": "IN",
            "job_apply_link": f"https://www.indeed.com/jobs?q={encoded_role}",
            "job_description": f"Click to search for recent {job_role} roles on Indeed.",
            "job_posted_at_datetime_utc": datetime.now(timezone.utc).isoformat()
        },
        {
            "job_id": f"naukri-{job_role}",
            "job_title": f"Search on Naukri",
            "employer_name": "Naukri",
            "job_city": "India",
            "job_country": "IN",
            "job_apply_link": f"https://www.naukri.com/{job_role.replace(' ', '-')}-jobs",
            "job_description": f"Click to search for recent {job_role} roles on Naukri.",
            "job_posted_at_datetime_utc": datetime.now(timezone.utc).isoformat()
        }
    ]
    return {
        "job_role": job_role,
        "source": "fallback",
        "jobs": fallback_jobs,
        "cached": False,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/listings/{job_role_encoded}")
async def get_job_listings(job_role_encoded: str, db: Session = Depends(get_db)):
    job_role = urllib.parse.unquote(job_role_encoded)
    cache_key = hashlib.md5(job_role.encode('utf-8')).hexdigest()
    now_utc = datetime.now(timezone.utc)

    # 1. Check Cache
    cached_entry = db.query(JobCache).filter(JobCache.query_key == cache_key).first()
    
    # Make sure we handle naive datetimes correctly if SQLite/PG returns them
    is_valid_cache = False
    if cached_entry and cached_entry.expires_at:
        expires = cached_entry.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires > now_utc:
            is_valid_cache = True

    if is_valid_cache:
        return {
            "job_role": job_role,
            "source": cached_entry.source,
            "jobs": cached_entry.raw_results,
            "cached": True,
            "fetched_at": cached_entry.fetched_at.isoformat() if cached_entry.fetched_at else None
        }

    # 2. If no valid cache and no API key, return fallbacks
    if not settings.RAPIDAPI_KEY:
        return get_fallback_jobs(job_role)

    # 3. Call JSearch API
    url = "https://jsearch.p.rapidapi.com/search"
    query = f"{job_role} fresher India"
    querystring = {"query": query, "page": "1", "num_pages": "1", "date_posted": "month"}
    headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            
            if "data" not in data or not data["data"]:
                return get_fallback_jobs(job_role)
                
            raw_jobs = data["data"]
            parsed_jobs = []
            
            for j in raw_jobs:
                desc = j.get("job_description", "")
                if desc and len(desc) > 300:
                    desc = desc[:297] + "..."
                    
                parsed_jobs.append({
                    "job_id": j.get("job_id", ""),
                    "job_title": j.get("job_title", ""),
                    "employer_name": j.get("employer_name", ""),
                    "job_city": j.get("job_city", ""),
                    "job_country": j.get("job_country", ""),
                    "job_apply_link": j.get("job_apply_link", ""),
                    "job_description": desc,
                    "job_posted_at_datetime_utc": j.get("job_posted_at_datetime_utc", "")
                })

            # 4. Save to Cache
            expires_time = now_utc + timedelta(hours=24)
            fetched_time = now_utc
            
            stmt = insert(JobCache).values(
                query_key=cache_key,
                job_title=job_role,
                source="jsearch",
                raw_results=parsed_jobs,
                job_count=len(parsed_jobs),
                fetched_at=fetched_time,
                expires_at=expires_time
            )
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['query_key'],
                set_={
                    'job_title': stmt.excluded.job_title,
                    'source': stmt.excluded.source,
                    'raw_results': stmt.excluded.raw_results,
                    'job_count': stmt.excluded.job_count,
                    'fetched_at': stmt.excluded.fetched_at,
                    'expires_at': stmt.excluded.expires_at
                }
            )
            
            db.execute(stmt)
            db.commit()

            return {
                "job_role": job_role,
                "source": "jsearch",
                "jobs": parsed_jobs,
                "cached": False,
                "fetched_at": fetched_time.isoformat()
            }

    except Exception as e:
        print(f"JSearch API Error: {e}")
        return get_fallback_jobs(job_role)
