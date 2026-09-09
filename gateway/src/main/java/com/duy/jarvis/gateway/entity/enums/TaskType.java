package com.duy.jarvis.gateway.entity.enums;

/**
 * Scheduled task execution route:
 * - SIMPLE_REMINDER: Handled directly by Gateway (creates Notification).
 * - AGENT_TASK: Forwarded to Agent Runtime via WebSocket.
 */
public enum TaskType {
    SIMPLE_REMINDER,
    AGENT_TASK
}
