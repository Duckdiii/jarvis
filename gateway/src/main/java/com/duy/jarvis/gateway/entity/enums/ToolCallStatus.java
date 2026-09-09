package com.duy.jarvis.gateway.entity.enums;

/**
 * Execution status of a tool call.
 * Directly addresses the silent failure edge case.
 */
public enum ToolCallStatus {
    SUCCESS,
    FAILED,
    TIMEOUT,
    AWAITING_CONFIRMATION
}
