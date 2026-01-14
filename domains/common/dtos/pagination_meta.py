from pydantic import BaseModel, Field


# Pagination 메타데이터 DTO
class PaginationMeta(BaseModel):
    total_count: int = Field(..., description="전체 항목의 개수")
    skip: int = Field(..., description="현재 건너뛴 항목 수 (Offset)")
    limit: int = Field(..., description="페이지당 최대 항목 수 (Limit)")
    is_last_page: bool = Field(..., description="마지막 페이지 여부")
    total_pages: int = Field(..., description="전체 페이지 수")