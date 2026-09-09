package com.duy.jarvis.gateway.entity;

import com.duy.jarvis.gateway.entity.enums.ConfirmationStatus;
import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

/**
 * Confirmation entity - human-in-the-loop approval mechanism.
 * Uses requestedAt & respondedAt for timeout calculation. Fail-safe default = DO NOT EXECUTE.
 */
@Entity
@Table(name = "confirmations", indexes = {
    @Index(name = "idx_confirmations_status", columnList = "status"),
    @Index(name = "idx_confirmations_requested_at", columnList = "requested_at")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Confirmation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "tool_call_id", nullable = false, unique = true)
    private ToolCall toolCall;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private ConfirmationStatus status;

    @Column(name = "requested_at", nullable = false)
    private OffsetDateTime requestedAt;

    /**
     * Null if user has not yet responded. Used to calculate timeout against requestedAt.
     */
    @Column(name = "responded_at")
    private OffsetDateTime respondedAt;

    @PrePersist
    protected void onCreate() {
        if (requestedAt == null) {
            requestedAt = OffsetDateTime.now();
        }
        if (status == null) {
            status = ConfirmationStatus.PENDING;
        }
    }
}
