package com.duy.jarvis.gateway.repository;

import com.duy.jarvis.gateway.entity.ScheduledTask;
import com.duy.jarvis.gateway.entity.enums.TaskType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface ScheduledTaskRepository extends JpaRepository<ScheduledTask, Long> {
    List<ScheduledTask> findByIsActiveTrue();
    List<ScheduledTask> findByTaskType(TaskType taskType);
}
