# -*- coding: utf-8 -*-
"""
監控告警 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from pydantic import BaseModel

from services.monitor import monitor, AlertLevel, AlertType
from services.auth_middleware import require_auth, require_admin
from services.auth import User

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


# ===== 請求模型 =====

class ResolveAlertRequest(BaseModel):
    alert_id: int


# ===== 告警端點 =====

@router.get("/alerts")
async def get_alerts(
    limit: int = Query(50, ge=1, le=200),
    level: Optional[str] = None,
    unread_only: bool = False,
    user: User = Depends(require_auth)
):
    """取得告警列表"""
    alert_level = None
    if level:
        try:
            alert_level = AlertLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"無效的告警等級: {level}")

    alerts = monitor.db.get_alerts(
        limit=limit,
        level=alert_level,
        unread_only=unread_only
    )

    return {
        "alerts": alerts,
        "unread_count": monitor.db.get_unread_count()
    }


@router.get("/alerts/unread-count")
async def get_unread_count(user: User = Depends(require_auth)):
    """取得未讀告警數量"""
    return {"count": monitor.db.get_unread_count()}


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int, user: User = Depends(require_auth)):
    """標記告警已讀"""
    success = monitor.db.mark_read(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="告警不存在")
    return {"success": True}


@router.post("/alerts/read-all")
async def mark_all_read(user: User = Depends(require_auth)):
    """標記所有告警已讀"""
    count = monitor.db.mark_all_read()
    return {"success": True, "marked_count": count}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, admin: User = Depends(require_admin)):
    """解決告警（管理員）"""
    success = monitor.db.resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="告警不存在")
    return {"success": True}


# ===== 指標端點 =====

@router.get("/metrics/{name}")
async def get_metrics(
    name: str,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(1000, ge=1, le=5000),
    user: User = Depends(require_auth)
):
    """取得指標歷史"""
    metrics = monitor.db.get_metrics(name, hours, limit)
    return {"metrics": metrics, "name": name}


@router.get("/metrics")
async def list_available_metrics(user: User = Depends(require_auth)):
    """列出可用的指標"""
    return {
        "available_metrics": [
            {"name": "download_count", "description": "下載次數", "unit": "次"},
            {"name": "download_size", "description": "下載大小", "unit": "bytes"},
            {"name": "error_count", "description": "錯誤次數", "unit": "次"},
            {"name": "disk_free_mb", "description": "磁碟剩餘空間", "unit": "MB"},
            {"name": "queue_size", "description": "佇列大小", "unit": "個"},
            {"name": "active_downloads", "description": "進行中下載", "unit": "個"},
        ]
    }


# ===== 事件端點 =====

@router.get("/events")
async def get_events(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(require_auth)
):
    """取得系統事件"""
    events = monitor.db.get_events(hours, limit)
    return {"events": events}


# ===== 儀表板端點 =====

@router.get("/dashboard")
async def get_dashboard_stats(user: User = Depends(require_auth)):
    """取得儀表板統計資料"""
    return monitor.get_dashboard_stats()


# ===== 管理員端點 =====

@router.post("/admin/cleanup")
async def cleanup_old_data(
    days: int = Query(30, ge=7, le=365),
    admin: User = Depends(require_admin)
):
    """清理舊資料（管理員）"""
    monitor.db.cleanup_old_data(days)
    return {"success": True, "message": f"已清理 {days} 天前的資料"}


@router.get("/admin/thresholds")
async def get_thresholds(admin: User = Depends(require_admin)):
    """取得監控閾值設定"""
    return {"thresholds": monitor.thresholds}


@router.put("/admin/thresholds")
async def update_thresholds(
    thresholds: dict,
    admin: User = Depends(require_admin)
):
    """更新監控閾值（管理員）"""
    for key, value in thresholds.items():
        if key in monitor.thresholds:
            monitor.thresholds[key] = value
    return {"success": True, "thresholds": monitor.thresholds}
