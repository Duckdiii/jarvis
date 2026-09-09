package com.duy.jarvis.gateway.entity;

import com.duy.jarvis.gateway.entity.enums.TaskType;
import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

/**
 * ScheduledTask entity - Quartz scheduler job representation managed by Gateway.
 * - SIMPLE_REMINDER: Gateway creates Notification directly.
 * - AGENT_TASK: Gateway forwards to Agent Runtime via WebSocket.
 */
@Entity
@Table(name = "scheduled_tasks", indexes = {
    @Index(name = "idx_scheduled_tasks_active", columnList = "is_active"),
    @Index(name = "idx_scheduled_tasks_type", columnList = "task_type")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ScheduledTask {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @Column(name = "cron_expression", nullable = false, length = 100)
    private String cronExpression;

    @Column(nullable = false, length = 500)
    private String description;

    @Column(name = "is_active", nullable = false)
    @Builder.Default
    private boolean isActive = true;

    @Enumerated(EnumType.STRING)
    @Column(name = "task_type", nullable = false, length = 30)
    private TaskType taskType;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = OffsetDateTime.now();
        }
    }
}
