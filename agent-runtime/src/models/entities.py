"""Jarvis Domain Business Entities.

Includes all 10 domain entities matching the system architecture:
1. User
2. UserProfile
3. Fact
4. ConversationSession
5. Message
6. EpisodicMemory
7. ToolCall
8. Confirmation
9. ScheduledTask
10. Notification
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from .enums import (
    ChannelType,
    ConfirmationStatus,
    MessageRole,
    TaskType,
    ToolCallStatus,
)


def utc_now() -> datetime:
    """Return current UTC datetime with timezone."""
    return datetime.now(timezone.utc)


class User(BaseModel):
    """User entity - intentionally minimalist.

    All factual knowledge about the user is kept in UserProfile and Fact entities.
    """
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    name: str = Field(..., description="Tên hiển thị — dùng trong TTS (vd 'Chào Duy')")
    created_at: datetime = Field(default_factory=utc_now, description="Mốc bắt đầu dùng hệ thống")


class UserProfile(BaseModel):
    """UserProfile entity - acts strictly as a container for an open-ended set of Facts.

    Avoid hardcoding specific attributes here as user facts are dynamic.
    """
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int = Field(..., description="ID của user sở hữu profile")
    last_updated_at: datetime = Field(
        default_factory=utc_now,
        description="Mốc cập nhật gần nhất — dùng để quyết định có chạy lại Extraction Step không"
    )


class Fact(BaseModel):
    """Fact entity - individual extracted knowledge unit.

    Maintains confidence score and strict timestamps for chronological conflict resolution.
    """
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_profile_id: int = Field(..., description="ID của UserProfile container")
    key: str = Field(..., description="Tên fact, vd 'favorite_language', 'working_directory'")
    value: str = Field(..., description="Giá trị hiện tại, vd 'Rust'")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Mức chắc chắn khi Extraction Step tự trích xuất (0.0 - 1.0)"
    )
    source_session_id: Optional[int] = Field(
        None,
        description="Fact được rút ra từ session nào (audit trail)"
    )
    created_at: datetime = Field(default_factory=utc_now, description="Lần đầu ghi nhận")
    updated_at: datetime = Field(
        default_factory=utc_now,
        description="Lần cập nhật gần nhất — bắt buộc có để giải quyết mâu thuẫn fact theo thời gian"
    )


class ConversationSession(BaseModel):
    """ConversationSession entity - represents an interaction session."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: Optional[int] = Field(None, description="ID của user trong phiên")
    channel: ChannelType = Field(
        ...,
        description="VOICE hay TEXT — quyết định có cần chạy TTS phản hồi không"
    )
    started_at: datetime = Field(default_factory=utc_now, description="Mốc bắt đầu phiên")
    ended_at: Optional[datetime] = Field(
        None,
        description="Null nếu session đang mở — dùng để trigger Extraction Step khi session kết thúc/idle timeout"
    )


class Message(BaseModel):
    """Message entity - a single utterance or turn in a conversation."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    session_id: int = Field(..., description="Khóa ngoại tham chiếu ConversationSession")
    role: MessageRole = Field(..., description="USER/AGENT/SYSTEM — dùng để dựng lại đúng thứ tự context")
    content: str = Field(..., description="Nội dung lượt nói (đã qua STT nếu là voice)")
    timestamp: datetime = Field(
        default_factory=utc_now,
        description="Thứ tự chính xác trong session, quan trọng khi có ToolCall xen giữa"
    )


class EpisodicMemory(BaseModel):
    """EpisodicMemory entity - compacted memory of past events.

    Timestamp is the primary signal for recency ranking during memory retrieval.
    """
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int = Field(..., description="ID của user")
    source_session_id: Optional[int] = Field(None, description="Session nguồn tạo ra sự kiện này")
    summary: str = Field(..., description="Bản tóm tắt sự kiện (sản phẩm của Extraction/Compaction)")
    timestamp: datetime = Field(
        default_factory=utc_now,
        description="Bắt buộc có và chính xác — tín hiệu xếp hạng bậc nhất khi retrieval"
    )
    embedding_ref: Optional[str] = Field(
        None,
        description="Con trỏ tới vector trong Qdrant (không lưu trực tiếp vector ở đây)"
    )


class ToolCall(BaseModel):
    """ToolCall entity - tracks tool invocations.

    parameters and result are stored separately for auditability and Presidio redaction.
    """
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    session_id: int = Field(..., description="ID của session gọi tool")
    tool_name: str = Field(..., description="Tên tool: file_io, shell_exec, app_automation, browser_control...")
    parameters: str = Field(..., description="Tham số LLM truyền vào (JSON string) — lưu để audit")
    result: Optional[str] = Field(None, description="Kết quả trả về từ tool (cần lọc qua Presidio trước khi nạp vào prompt)")
    status: ToolCallStatus = Field(
        ...,
        description="SUCCESS/FAILED/TIMEOUT/AWAITING_CONFIRMATION — giải quyết edge case tool fail âm thầm"
    )
    called_at: datetime = Field(default_factory=utc_now, description="Mốc thời gian gọi tool")


class Confirmation(BaseModel):
    """Confirmation entity - human-in-the-loop approval tracking."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    tool_call_id: int = Field(..., description="ID của ToolCall cần xác nhận")
    status: ConfirmationStatus = Field(
        default=ConfirmationStatus.PENDING,
        description="PENDING/APPROVED/REJECTED/TIMEOUT_DENIED"
    )
    requested_at: datetime = Field(default_factory=utc_now, description="Mốc bắt đầu chờ xác nhận")
    responded_at: Optional[datetime] = Field(
        None,
        description="Null nếu chưa phản hồi — kết hợp với requestedAt để tính timeout (fail-safe = KHÔNG thực hiện)"
    )


class ScheduledTask(BaseModel):
    """ScheduledTask entity - Quartz scheduler job handled by Gateway.

    - SIMPLE_REMINDER: Gateway tự tạo Notification thẳng.
    - AGENT_TASK: Gateway forward request sang Agent Runtime qua WebSocket.
    """
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: Optional[int] = Field(None, description="ID của user")
    cron_expression: str = Field(..., description="Biểu thức lịch (Quartz cron syntax)")
    description: str = Field(..., description="Nội dung nhắc việc, vd 'Nhắc uống nước lúc 15h'")
    is_active: bool = Field(default=True, description="Cho phép tạm dừng mà không xóa hẳn task")
    task_type: TaskType = Field(..., description="SIMPLE_REMINDER hoặc AGENT_TASK")
    created_at: datetime = Field(default_factory=utc_now)


class Notification(BaseModel):
    """Notification entity - dispatched reminder or alert."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: Optional[int] = Field(None, description="ID của user nhận thông báo")
    scheduled_task_id: Optional[int] = Field(None, description="Tham chiếu ScheduledTask sinh ra thông báo (nếu có)")
    message: str = Field(..., description="Nội dung thông báo thực tế được gửi")
    sent_at: datetime = Field(default_factory=utc_now, description="Thời điểm gửi thật (xử lý catch-up logic nếu máy tắt)")
    channel: ChannelType = Field(..., description="Gửi qua voice hay chỉ hiện popup UI")
