package com.duy.jarvis.gateway.entity;

import com.duy.jarvis.gateway.entity.enums.MessageRole;
import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

/**
 * Message entity - represents a single utterance/turn in a session.
 */
@Entity
@Table(name = "messages", indexes = {
    @Index(name = "idx_messages_session_timestamp", columnList = "session_id, timestamp")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Message {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false)
    private ConversationSession session;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private MessageRole role;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(nullable = false)
    private OffsetDateTime timestamp;

    @PrePersist
    protected void onCreate() {
        if (timestamp == null) {
            timestamp = OffsetDateTime.now();
        }
    }
}
