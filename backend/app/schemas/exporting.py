from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ExportPackageRequest(BaseModel):
    export_type: str = Field(default="ready_to_publish", min_length=1, max_length=60)
    include_copies: bool = True
    write_event_date_metadata: bool = True
    group_by_type: bool = True
    include_summary: bool = True


class ExportPackageItemResponse(BaseModel):
    id: int
    package_id: int
    content_piece_id: int | None
    generated_copy_id: int | None
    enhanced_media_id: int | None
    item_type: str
    output_path: str
    absolute_output_path: str
    item_order: int | None
    metadata_written: bool
    metadata_status: str | None
    error_message: str | None
    created_at: datetime


class ExportPackageResponse(BaseModel):
    id: int
    event_id: int
    name: str
    export_type: str
    output_path: str
    absolute_output_path: str
    status: str
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None
    items: list[ExportPackageItemResponse]


class ExportPackageRunResponse(BaseModel):
    job_id: int
    package: ExportPackageResponse
    total_pieces: int
    media_exported: int
    copies_exported: int
    failed_items: int
    summary_path: str | None


class ExportPackageListResponse(BaseModel):
    items: list[ExportPackageResponse]


class OpenExportFolderResponse(BaseModel):
    package_id: int
    path: str
    opened: bool
    message: str
