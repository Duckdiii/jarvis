"""Enums for Jarvis business entities."""

from enum import Enum


class ChannelType(str, Enum):
    """Communication channel used for interaction.

    Decides whether TTS response is required.
    """
    VOICE = "VOICE"
    TEXT = "TEXT"


class MessageRole(str, Enum):
    """Role of the speaker in a conversation session."""
    USER = "USER"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


class ToolCallStatus(str, Enum):
    """Execution status of a tool call.

    Directly prevents silent failures from reporting success.
    """
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"


class ConfirmationStatus(str, Enum):
    """Lifecycle status of a human-in-the-loop confirmation request."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    TIMEOUT_DENIED = "TIMEOUT_DENIED"


class TaskType(str, Enum):
    """Routing branch for a scheduled task.

    - SIMPLE_REMINDER: Handled directly by Gateway (creates Notification).
    - AGENT_TASK: Forwarded to Agent Runtime via WebSocket.
    """
    SIMPLE_REMINDER = "SIMPLE_REMINDER"
    AGENT_TASK = "AGENT_TASK"
