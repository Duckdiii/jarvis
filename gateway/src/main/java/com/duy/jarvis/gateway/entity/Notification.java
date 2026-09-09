package com.duy.jarvis.gateway.entity;

import com.duy.jarvis.gateway.entity.enums.ChannelType;
import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

/**
 * Notification entity - record of an alert/reminder dispatched to the user.
 * sentAt records actual dispatch time to handle catch-up logic.
 */
@Entity
@Table(name = "notifications", indexes = {
    @Index(name = "idx_notifications_sent_at", columnList = "sent_at")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Notification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "scheduled_task_id")
    private ScheduledTask scheduledTask;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String message;

    @Column(name = "sent_at", nullable = false)
    private OffsetDateTime sentAt;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private ChannelType channel;

    @PrePersist
    protected void onCreate() {
        if (sentAt == null) {
            sentAt = OffsetDateTime.now();
        }
    }
}
