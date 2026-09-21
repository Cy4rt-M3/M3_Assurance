"""Report Publisher Service — publishes reports and handles delivery."""

from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.report_generator.repository import get_report
from apps.report_publisher.channels import dispatch, is_supported
from apps.report_publisher.models import DeliveryRequest, DeliveryStatus
from apps.report_publisher.repository import create_delivery, list_deliveries
from apps.shared.db import build_engine, build_session_factory, check_db
from apps.shared.settings import Settings

_settings = Settings()
_engine = build_engine(_settings.database_url)
_session_factory = build_session_factory(_engine)

app = FastAPI(
    title="Report Publisher Service",
    description="Publishes reports and handles delivery.",
    version="0.1.0",
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide one database session per request."""
    async with _session_factory() as session:
        yield session


@app.get("/health")
async def health() -> dict[str, object]:
    """Liveness + dependency check for report-publisher."""
    db_ok = await check_db(_engine)
    return {
        "service": "report-publisher",
        "port": _settings.port_report_publisher,
        "db": db_ok,
        "redis": True,
    }


@app.post("/api/v1/publish", response_model=DeliveryStatus)
async def publish(
    request: DeliveryRequest,
    session: AsyncSession = Depends(get_session),
) -> DeliveryStatus:
    """Deliver a stored report through a channel."""
    report = await get_report(session, request.report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"Report '{request.report_id}' not found",
        )
    if not is_supported(request.channel):
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported channel '{request.channel}'",
        )

    delivered = dispatch(request.channel, request.recipient)
    history = await list_deliveries(session, request.report_id)
    status = DeliveryStatus(
        delivery_id=f"{request.report_id}-del-{len(history) + 1:03d}",
        report_id=request.report_id,
        channel=request.channel,
        recipient=request.recipient,
        status="delivered" if delivered else "failed",
    )
    return await create_delivery(session, status)


@app.get(
    "/api/v1/deliveries/{report_id}",
    response_model=list[DeliveryStatus],
)
async def deliveries_for_report(
    report_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[DeliveryStatus]:
    """Return the delivery history for a report."""
    return await list_deliveries(session, report_id)
