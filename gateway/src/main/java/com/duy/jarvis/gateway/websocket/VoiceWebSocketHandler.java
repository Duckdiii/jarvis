package com.duy.jarvis.gateway.websocket;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * WebSocket Handler cho Voice Layer & Desktop App.
 *
 * Theo quy ước CLAUDE.md:
 * - Gateway CHỈ đóng vai trò proxy / relay thông điệp và router.
 * - Gateway KHÔNG chứa Agent logic, KHÔNG chứa Prompt template, KHÔNG phân tích ngữ nghĩa.
 * - Kết nối CHỈ bind trên 127.0.0.1.
 */
@Slf4j
@Component
public class VoiceWebSocketHandler extends TextWebSocketHandler {

    private final ObjectMapper objectMapper;
    private final HttpClient httpClient;
    private final Map<String, WebSocketSession> activeSessions = new ConcurrentHashMap<>();

    @Value("${jarvis.agent-runtime.url:http://127.0.0.1:8000/api/chat}")
    private String agentRuntimeUrl;

    public VoiceWebSocketHandler(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(3))
                .build();
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        activeSessions.put(session.getId(), session);
        log.info("[Gateway-WS] Client kết nối thành công: sessionId={}, remoteAddress={}",
                session.getId(), session.getRemoteAddress());
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        activeSessions.remove(session.getId());
        log.info("[Gateway-WS] Client ngắt kết nối: sessionId={}, status={}", session.getId(), status);
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        log.debug("[Gateway-WS] Nhận bản tin thô: {}", payload);

        JsonNode rootNode;
        try {
            rootNode = objectMapper.readTree(payload);
        } catch (Exception e) {
            log.error("[Gateway-WS] Không thể parse JSON: {}", payload, e);
            sendErrorMessage(session, "unknown", "INVALID_JSON", "Nội dung bản tin không đúng định dạng JSON");
            return;
        }

        String type = rootNode.path("type").asText("");
        String sessionId = rootNode.path("session_id").asText(session.getId());

        switch (type) {
            case "user_audio_transcript" -> handleUserAudioTranscript(session, sessionId, rootNode);
            case "session_state" -> handleSessionState(session, sessionId, rootNode);
            case "ping" -> sendPong(session, sessionId);
            default -> {
                log.warn("[Gateway-WS] Nhận thông điệp type không xác định: {}", type);
                sendErrorMessage(session, sessionId, "UNKNOWN_TYPE", "Loại thông điệp '" + type + "' không được hỗ trợ");
            }
        }
    }

    private void handleUserAudioTranscript(WebSocketSession session, String sessionId, JsonNode rootNode) {
        JsonNode payload = rootNode.path("payload");
        String text = payload.path("text").asText("").trim();

        log.info("[Gateway-WS] Relay nhận dạng giọng nói: sessionId='{}', text='{}'", sessionId, text);

        if (text.isEmpty()) {
            sendErrorMessage(session, sessionId, "EMPTY_TEXT", "Văn bản nhận dạng từ giọng nói bị rỗng");
            return;
        }

        // Báo trạng thái THINKING sang client
        sendSessionState(session, sessionId, "THINKING", "Đang chuyển tiếp sang Agent Runtime");

        // Forward nguyên vẹn sang Agent Runtime qua HTTP Relay
        try {
            ObjectNode forwardRequest = objectMapper.createObjectNode();
            forwardRequest.put("session_id", sessionId);
            forwardRequest.put("message", text);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(agentRuntimeUrl))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(10))
                    .POST(HttpRequest.BodyPublishers.ofString(forwardRequest.toString()))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                JsonNode responseJson = objectMapper.readTree(response.body());
                String agentReply = responseJson.path("response").asText("");

                log.info("[Gateway-WS] Nhận kết quả từ Agent Runtime: '{}'", agentReply);

                // Gửi trả agent_response_text lại Voice Layer
                ObjectNode replyEnvelope = objectMapper.createObjectNode();
                replyEnvelope.put("type", "agent_response_text");
                replyEnvelope.put("session_id", sessionId);
                replyEnvelope.put("message_id", UUID.randomUUID().toString());
                replyEnvelope.put("timestamp", System.currentTimeMillis());

                ObjectNode replyPayload = replyEnvelope.putObject("payload");
                replyPayload.put("text", agentReply);
                if (responseJson.has("duration_ms")) {
                    replyPayload.put("execution_duration_ms", responseJson.get("duration_ms").asDouble());
                }

                sendTextMessage(session, replyEnvelope.toString());
            } else {
                log.error("[Gateway-WS] Agent Runtime trả về HTTP {}: {}", response.statusCode(), response.body());
                sendErrorMessage(session, sessionId, "AGENT_ERROR", "Agent Runtime báo lỗi: HTTP " + response.statusCode());
            }
        } catch (IOException | InterruptedException e) {
            log.error("[Gateway-WS] Lỗi kết nối Agent Runtime tại {}: {}", agentRuntimeUrl, e.getMessage());
            sendErrorMessage(session, sessionId, "AGENT_UNAVAILABLE", "Không thể kết nối tới Agent Runtime (" + e.getMessage() + ")");
        } finally {
            // Chuyển trạng thái về IDLE khi hoàn tất
            sendSessionState(session, sessionId, "IDLE", "Vòng lặp tương tác thoại hoàn tất");
        }
    }

    private void handleSessionState(WebSocketSession session, String sessionId, JsonNode rootNode) {
        String state = rootNode.path("payload").path("state").asText("");
        log.debug("[Gateway-WS] Cập nhật session_state: sessionId={}, state={}", sessionId, state);
    }

    private void sendPong(WebSocketSession session, String sessionId) {
        ObjectNode pong = objectMapper.createObjectNode();
        pong.put("type", "pong");
        pong.put("session_id", sessionId);
        pong.put("timestamp", System.currentTimeMillis());
        sendTextMessage(session, pong.toString());
    }

    private void sendSessionState(WebSocketSession session, String sessionId, String state, String detail) {
        ObjectNode envelope = objectMapper.createObjectNode();
        envelope.put("type", "session_state");
        envelope.put("session_id", sessionId);
        envelope.put("message_id", UUID.randomUUID().toString());
        envelope.put("timestamp", System.currentTimeMillis());

        ObjectNode payload = envelope.putObject("payload");
        payload.put("state", state);
        payload.put("detail", detail);

        sendTextMessage(session, envelope.toString());
    }

    private void sendErrorMessage(WebSocketSession session, String sessionId, String code, String message) {
        ObjectNode envelope = objectMapper.createObjectNode();
        envelope.put("type", "error");
        envelope.put("session_id", sessionId);
        envelope.put("message_id", UUID.randomUUID().toString());
        envelope.put("timestamp", System.currentTimeMillis());

        ObjectNode payload = envelope.putObject("payload");
        payload.put("code", code);
        payload.put("message", message);

        sendTextMessage(session, envelope.toString());
    }

    private synchronized void sendTextMessage(WebSocketSession session, String text) {
        if (session.isOpen()) {
            try {
                session.sendMessage(new TextMessage(text));
            } catch (IOException e) {
                log.error("[Gateway-WS] Lỗi gửi thông điệp tới session {}: {}", session.getId(), e.getMessage());
            }
        }
    }
}
