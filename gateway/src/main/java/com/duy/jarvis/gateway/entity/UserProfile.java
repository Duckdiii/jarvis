package com.duy.jarvis.gateway.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * UserProfile entity - serves strictly as a container for an open-ended collection of Facts.
 * Does not contain hardcoded preference columns.
 */
@Entity
@Table(name = "user_profiles")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserProfile {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(name = "last_updated_at", nullable = false)
    private OffsetDateTime lastUpdatedAt;

    @OneToMany(mappedBy = "userProfile", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<Fact> facts = new ArrayList<>();

    @PrePersist
    @PreUpdate
    protected void onUpdate() {
        if (lastUpdatedAt == null) {
            lastUpdatedAt = OffsetDateTime.now();
        }
    }
}
