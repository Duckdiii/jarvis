package com.duy.jarvis.gateway.repository;

import com.duy.jarvis.gateway.entity.Confirmation;
import com.duy.jarvis.gateway.entity.enums.ConfirmationStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface ConfirmationRepository extends JpaRepository<Confirmation, Long> {
    Optional<Confirmation> findByToolCallId(Long toolCallId);
    List<Confirmation> findByStatus(ConfirmationStatus status);
    List<Confirmation> findByStatusAndRequestedAtBefore(ConfirmationStatus status, OffsetDateTime threshold);
}
