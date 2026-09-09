package com.duy.jarvis.gateway.entity;

import com.duy.jarvis.gateway.entity.enums.ChannelType;
import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * ConversationSession entity - represents an interaction session over VOICE or TEXT.
 */
@Entity
@Table(name = "conversation_sessions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ConversationSession {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private ChannelType channel;

    @Column(name = "started_at", nullable = false)
    private OffsetDateTime startedAt;

    /**
     * Null if session is currently active.
     * Used to trigger Extraction Step when session ends or times out.
     */
    @Column(name = "ended_at")
    private OffsetDateTime endedAt;

    @OneToMany(mappedBy = "session", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<Message> messages = new ArrayList<>();

    @OneToMany(mappedBy = "session", cascade = CascadeType.ALL)
    @Builder.Default
    private List<ToolCall> toolCalls = new ArrayList<>();

    @PrePersist
    protected void onCreate() {
        if (startedAt == null) {
            startedAt = OffsetDateTime.now();
        }
    }
}
