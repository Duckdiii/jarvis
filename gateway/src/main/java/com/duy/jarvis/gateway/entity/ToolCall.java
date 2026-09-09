package com.duy.jarvis.gateway.entity;

import com.duy.jarvis.gateway.entity.enums.ToolCallStatus;
import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

/**
 * ToolCall entity - records tool execution for auditing, debugging, and redacting.
 * Note: parameters and result MUST be stored separately so Presidio can filter result.
 */
@Entity
@Table(name = "tool_calls", indexes = {
    @Index(name = "idx_tool_calls_session", columnList = "session_id"),
    @Index(name = "idx_tool_calls_status", columnList = "status")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ToolCall {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false)
    private ConversationSession session;

    @Column(name = "tool_name", nullable = false, length = 100)
    private String toolName;

    /**
     * Input arguments provided by LLM (JSON/Text format) - kept separate for auditing.
     */
    @Column(name = "parameters", nullable = false, columnDefinition = "TEXT")
    private String parameters;

    /**
     * Raw or redacted result returned from the tool - kept separate for Presidio filtering.
     */
    @Column(name = "result", columnDefinition = "TEXT")
    private String result;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private ToolCallStatus status;

    @Column(name = "called_at", nullable = false)
    private OffsetDateTime calledAt;

    @OneToOne(mappedBy = "toolCall", cascade = CascadeType.ALL)
    private Confirmation confirmation;

    @PrePersist
    protected void onCreate() {
        if (calledAt == null) {
            calledAt = OffsetDateTime.now();
        }
    }
}
