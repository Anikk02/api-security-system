"""
Shared filter-building helpers for the Developer Panel.

Centralizes WHERE-clause construction so every service (logs, debug, abuse)
applies filters the same way instead of re-implementing ad-hoc conditionals.
Mirrors the real RequestLog columns from app/db/models/request_log.py:
    id, request_uuid, identity_id, client_id, api_key_id,
    endpoint, method, ip_address, user_agent, status_code, action, created_at
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Select

from app.db.models.request_log import RequestLog


def apply_request_log_filters(
    query: Select,
    client_id: Optional[int] = None,
    identity_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    endpoint: Optional[str] = None,
    action: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Select:
    """
    Apply optional WHERE clauses to a RequestLog select() statement.
    Every parameter is optional — None skips that filter entirely.
    """
    if client_id is not None:
        query = query.where(RequestLog.client_id == client_id)
    if identity_id:
        query = query.where(RequestLog.identity_id == identity_id)
    if ip_address:
        query = query.where(RequestLog.ip_address == ip_address)
    if endpoint:
        query = query.where(RequestLog.endpoint == endpoint)
    if action:
        query = query.where(RequestLog.action == action)
    if start_time:
        query = query.where(RequestLog.created_at >= start_time)
    if end_time:
        query = query.where(RequestLog.created_at <= end_time)
    return query
