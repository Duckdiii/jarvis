package com.duy.jarvis.gateway.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

/**
 * EpisodicMemory entity - compacted event summary for long-term memory retrieval.
 * Recency ranking relies on the mandatory, indexed timestamp attribute.
 */
@Entity
@Table(name = "episodic_memories", indexes = {
    @Index(name = "idx_episodic_timestamp", columnList = "timestamp DESC"),
    @Index(name = "idx_episodic_user_timestamp", columnList = "user_id, timestamp DESC")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EpisodicMemory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "source_session_id")
    private Long sourceSessionId;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String summary;

    /**
     * Mandatory and precise timestamp for recency-first retrieval ranking.
     */
    @Column(nullable = false)
    private OffsetDateTime timestamp;

    /**
     * Vector pointer/ID in Qdrant (vectors are stored in Qdrant, this is only a reference).
     */
    @Column(name = "embedding_ref", length = 255)
    private String embeddingRef;

    @PrePersist
    protected void onCreate() {
        if (timestamp == null) {
            timestamp = OffsetDateTime.now();
        }
    }
}
