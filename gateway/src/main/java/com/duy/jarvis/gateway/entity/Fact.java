package com.duy.jarvis.gateway.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

/**
 * Fact entity - stores extracted facts about the user.
 * Includes confidence score and strict timestamp tracking for conflict resolution.
 */
@Entity
@Table(name = "facts", indexes = {
    @Index(name = "idx_facts_profile_key", columnList = "user_profile_id, fact_key"),
    @Index(name = "idx_facts_updated_at", columnList = "updated_at")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Fact {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_profile_id", nullable = false)
    private UserProfile userProfile;

    @Column(name = "fact_key", nullable = false, length = 100)
    private String key;

    @Column(name = "fact_value", nullable = false, columnDefinition = "TEXT")
    private String value;

    @Column(nullable = false)
    private float confidence;

    @Column(name = "source_session_id")
    private Long sourceSessionId;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    /**
     * Mandatory attribute for timestamp-based conflict resolution (e.g. "prefers Java" -> "prefers Rust").
     */
    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        OffsetDateTime now = OffsetDateTime.now();
        if (createdAt == null) {
            createdAt = now;
        }
        if (updatedAt == null) {
            updatedAt = now;
        }
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = OffsetDateTime.now();
    }
}
