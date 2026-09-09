-- ============================================================================
-- Jarvis Session DB Schema
-- Architecture v4: Shared between Gateway (Spring Boot) and Agent Runtime (Python)
-- ============================================================================

-- 1. User: Intentionally minimalist - knowledge lives in UserProfile / Fact
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. UserProfile: Container for facts (open-ended attribute set)
CREATE TABLE IF NOT EXISTS user_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    last_updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Fact: Extracted knowledge units with confidence score & chronological resolution
CREATE TABLE IF NOT EXISTS facts (
    id BIGSERIAL PRIMARY KEY,
    user_profile_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    fact_key VARCHAR(100) NOT NULL,
    fact_value TEXT NOT NULL,
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    source_session_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_facts_profile_key ON facts(user_profile_id, fact_key);
CREATE INDEX IF NOT EXISTS idx_facts_updated_at ON facts(updated_at);

-- 4. ConversationSession: Interaction session over VOICE or TEXT
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('VOICE', 'TEXT')),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE
);

-- 5. Message: Conversational turns in chronological order
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('USER', 'AGENT', 'SYSTEM')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_session_timestamp ON messages(session_id, timestamp);

-- 6. EpisodicMemory: Compacted events with recency-first ranking
CREATE TABLE IF NOT EXISTS episodic_memories (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_session_id BIGINT REFERENCES conversation_sessions(id) ON DELETE SET NULL,
    summary TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    embedding_ref VARCHAR(255) -- Pointer to vector stored in Qdrant
);

CREATE INDEX IF NOT EXISTS idx_episodic_timestamp ON episodic_memories(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_episodic_user_timestamp ON episodic_memories(user_id, timestamp DESC);

-- 7. ToolCall: Audit log of tool execution (parameters & result stored separately)
CREATE TABLE IF NOT EXISTS tool_calls (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    parameters TEXT NOT NULL,
    result TEXT,
    status VARCHAR(30) NOT NULL CHECK (status IN ('SUCCESS', 'FAILED', 'TIMEOUT', 'AWAITING_CONFIRMATION')),
    called_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_status ON tool_calls(status);

-- 8. Confirmation: Human-in-the-loop approval tracking
CREATE TABLE IF NOT EXISTS confirmations (
    id BIGSERIAL PRIMARY KEY,
    tool_call_id BIGINT NOT NULL UNIQUE REFERENCES tool_calls(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'TIMEOUT_DENIED')),
    requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_confirmations_status ON confirmations(status);

-- 9. ScheduledTask: Quartz cron tasks managed by Gateway
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    cron_expression VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    task_type VARCHAR(30) NOT NULL CHECK (task_type IN ('SIMPLE_REMINDER', 'AGENT_TASK')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_active ON scheduled_tasks(is_active);

-- 10. Notification: Dispatched reminders and alerts
CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    scheduled_task_id BIGINT REFERENCES scheduled_tasks(id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('VOICE', 'TEXT'))
);

CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at);
