/*
 * Deep Packet Inspection (DPI) Engine Header
 *
 * High-performance DPI engine with:
 * - Stateful TCP/UDP stream reassembly
 * - Protocol dissectors (HTTP, TLS, DNS, SMTP, SMB, FTP)
 * - Pattern matching (regex + Snort-like rules)
 * - Anomaly detection
 * - Optional SSL/TLS interception
 * - Privacy-compliant logging
 *
 * Author: J.A.R.V.I.S. Team
 * Version: 1.0.0
 */

#ifndef DPI_ENGINE_H
#define DPI_ENGINE_H

#include <stdint.h>
#include <stddef.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * CONSTANTS & ENUMS
 * ======================================================================== */

#define DPI_MAX_RULES               10000
#define DPI_MAX_PATTERNS            50000
#define DPI_STREAM_TIMEOUT          300     /* 5 minutes */
#define DPI_REASSEMBLY_BUFFER_SIZE  (16 * 1024 * 1024)  /* 16 MB per stream */
#define DPI_MAX_STREAMS             100000
#define DPI_MAX_ALERTS              1000000

/* Protocol types */
typedef enum {
    DPI_PROTO_UNKNOWN = 0,
    DPI_PROTO_HTTP = 1,
    DPI_PROTO_HTTPS = 2,
    DPI_PROTO_DNS = 3,
    DPI_PROTO_SMTP = 4,
    DPI_PROTO_SMTPS = 5,
    DPI_PROTO_FTP = 6,
    DPI_PROTO_FTPS = 7,
    DPI_PROTO_SMB = 8,
    DPI_PROTO_SSH = 9,
    DPI_PROTO_TELNET = 10,
    DPI_PROTO_SNMP = 11,
    DPI_PROTO_QUIC = 12,
    DPI_PROTO_DTLS = 13,
    DPI_PROTO_MQTT = 14,
    DPI_PROTO_COAP = 15,
    DPI_PROTO_MAX = 16
} dpi_protocol_t;

/* Session state */
typedef enum {
    DPI_STATE_NEW = 0,
    DPI_STATE_ESTABLISHED = 1,
    DPI_STATE_CLOSING = 2,
    DPI_STATE_CLOSED = 3,
    DPI_STATE_ERROR = 4
} dpi_session_state_t;

/* Alert severity levels */
typedef enum {
    DPI_ALERT_INFO = 0,
    DPI_ALERT_WARNING = 1,
    DPI_ALERT_CRITICAL = 2,
    DPI_ALERT_MALWARE = 3,
    DPI_ALERT_ANOMALY = 4
} dpi_alert_severity_t;

/* Rule types */
typedef enum {
    DPI_RULE_REGEX = 0,
    DPI_RULE_SNORT = 1,
    DPI_RULE_YARA = 2,
    DPI_RULE_CONTENT = 3,
    DPI_RULE_BEHAVIORAL = 4
} dpi_rule_type_t;

/* TLS interception modes */
typedef enum {
    DPI_TLS_DISABLED = 0,
    DPI_TLS_PASSTHROUGH = 1,      /* Capture but don't decrypt */
    DPI_TLS_DECRYPT = 2,          /* Decrypt with key management */
    DPI_TLS_INSPECT = 3           /* Inspect ciphersuite without full decryption */
} dpi_tls_mode_t;

/* ========================================================================
 * STRUCTURES
 * ======================================================================== */

/* 5-tuple flow identifier */
typedef struct {
    uint32_t src_ip;
    uint32_t dst_ip;
    uint16_t src_port;
    uint16_t dst_port;
    uint8_t protocol;   /* IPPROTO_TCP, IPPROTO_UDP */
} dpi_flow_tuple_t;

/* Protocol classification result */
typedef struct {
    dpi_protocol_t protocol;
    uint8_t confidence;         /* 0-100 */
    uint32_t detection_tick;    /* When detected (in packets) */
    char app_name[64];          /* Application name (HTTP, SMTP, etc.) */
} dpi_protocol_result_t;

/* HTTP-specific dissection */
typedef struct {
    char method[16];            /* GET, POST, PUT, DELETE, etc. */
    char uri[2048];             /* Request URI */
    char host[256];             /* Host header */
    char user_agent[512];       /* User-Agent header */
    uint16_t status_code;       /* Response status (for responses) */
    uint64_t content_length;
    uint8_t is_request;
} dpi_http_data_t;

/* DNS-specific dissection */
typedef struct {
    uint16_t transaction_id;
    char query_name[256];
    uint16_t query_type;
    uint8_t is_query;
    uint8_t response_code;
    uint32_t *answered_ips;     /* Array of answered IPs */
    uint32_t answer_count;
} dpi_dns_data_t;

/* TLS-specific dissection */
typedef struct {
    uint8_t version_major;
    uint8_t version_minor;
    uint16_t cipher_suite;
    char sni[256];              /* Server Name Indication */
    char cert_subject[512];
    uint8_t is_client_hello;
    uint32_t cert_chain_depth;
} dpi_tls_data_t;

/* Anomaly detection result */
typedef struct {
    uint16_t anomaly_type;      /* Bitmask: port mismatch, timing, size, etc. */
    char description[256];
    uint8_t severity;           /* 0-10 */
} dpi_anomaly_t;

/* DPI Alert */
typedef struct {
    uint64_t alert_id;
    uint64_t timestamp_ns;
    dpi_flow_tuple_t flow;
    dpi_alert_severity_t severity;
    dpi_protocol_t protocol;
    uint32_t rule_id;
    char rule_name[256];
    char message[1024];
    
    /* Payload context */
    uint8_t *payload_sample;    /* First N bytes of matching payload */
    uint32_t payload_sample_len;
    uint32_t offset_in_stream;  /* Offset where pattern matched */
} dpi_alert_t;

/* DPI Session (maintained per flow) */
typedef struct {
    uint64_t session_id;
    dpi_flow_tuple_t flow;
    dpi_session_state_t state;
    dpi_protocol_result_t protocol;
    
    /* Stream reassembly */
    uint8_t *fwd_buffer;        /* Forward direction buffer */
    uint32_t fwd_buffer_used;
    uint32_t fwd_seq;
    
    uint8_t *rev_buffer;        /* Reverse direction buffer */
    uint32_t rev_buffer_used;
    uint32_t rev_seq;
    
    /* Protocol-specific data */
    void *http_data;
    void *dns_data;
    void *tls_data;
    
    /* Anomalies detected */
    dpi_anomaly_t *anomalies;
    uint32_t anomaly_count;
    
    /* Timing info */
    uint64_t created_ns;
    uint64_t last_seen_ns;
    uint32_t packets_seen;
    uint64_t total_bytes;
} dpi_session_t;

/* DPI Rule definition */
typedef struct {
    uint32_t rule_id;
    dpi_rule_type_t type;
    char name[256];
    char description[1024];
    dpi_alert_severity_t severity;
    
    /* Rule content */
    char *pattern;              /* Regex or signature */
    uint32_t pattern_len;
    
    /* Scope */
    dpi_protocol_t protocol;    /* DPI_PROTO_UNKNOWN = all protocols */
    uint16_t port_range_start;  /* 0 = all ports */
    uint16_t port_range_end;
    uint8_t applies_to_request;
    uint8_t applies_to_response;
    
    /* Metadata */
    char category[64];          /* malware, exploit, policy_violation, etc. */
    uint64_t created_at;
    uint64_t last_modified;
    uint8_t enabled;
} dpi_rule_t;

/* DPI Configuration */
typedef struct {
    dpi_tls_mode_t tls_mode;
    uint8_t enable_anomaly_detection;
    uint8_t enable_malware_detection;
    uint32_t reassembly_timeout_sec;
    uint32_t max_concurrent_sessions;
    uint64_t memory_limit_mb;
    
    /* Logging */
    uint8_t log_all_alerts;
    uint8_t log_tls_keys;       /* RFC 5116 SSLKEYLOGFILE format */
    char log_dir[256];
    
    /* Privacy */
    uint8_t redact_pii;
    uint8_t anonymize_ips;
} dpi_config_t;

/* DPI Engine handle */
typedef struct dpi_engine_s dpi_engine_t;

/* DPI Statistics */
typedef struct {
    uint64_t packets_processed;
    uint64_t bytes_processed;
    uint64_t flows_created;
    uint64_t flows_terminated;
    uint32_t active_sessions;
    uint64_t alerts_generated;
    uint64_t anomalies_detected;
    
    /* Per-protocol stats */
    uint64_t http_packets;
    uint64_t dns_packets;
    uint64_t tls_packets;
    uint64_t smtp_packets;
    uint64_t smb_packets;
    
    /* Performance metrics */
    double avg_processing_time_us;
    double max_packet_processing_us;
    uint32_t buffer_utilization_percent;
} dpi_stats_t;

/* ========================================================================
 * API FUNCTIONS
 * ======================================================================== */

/**
 * Initialize DPI engine with configuration
 * Returns: Engine handle or NULL on error
 */
dpi_engine_t *dpi_init(const dpi_config_t *config);

/**
 * Process a packet through the DPI engine
 * Returns: Number of alerts generated (0 if none)
 */
uint32_t dpi_process_packet(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow,
    const uint8_t *packet_data,
    uint32_t packet_len,
    uint64_t timestamp_ns,
    uint8_t is_response,
    dpi_alert_t **alerts_out
);

/**
 * Add a DPI rule to the engine
 * Returns: Rule ID or 0 on error
 */
uint32_t dpi_add_rule(
    dpi_engine_t *engine,
    const dpi_rule_t *rule
);

/**
 * Remove a DPI rule
 * Returns: 0 on success, -1 on error
 */
int dpi_remove_rule(
    dpi_engine_t *engine,
    uint32_t rule_id
);

/**
 * Get active alerts
 * Returns: Number of alerts retrieved
 */
uint32_t dpi_get_alerts(
    dpi_engine_t *engine,
    dpi_alert_t *alerts,
    uint32_t max_alerts,
    uint8_t clear_after_read
);

/**
 * Get DPI statistics
 */
dpi_stats_t dpi_get_stats(dpi_engine_t *engine);

/**
 * Get session details
 * Returns: Session pointer or NULL
 */
dpi_session_t *dpi_get_session(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow
);

/**
 * Classify protocol for a flow
 * Returns: Protocol classification result
 */
dpi_protocol_result_t dpi_classify_protocol(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow
);

/**
 * Enable/disable TLS interception for specific flows
 */
int dpi_set_tls_mode(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow,
    dpi_tls_mode_t mode
);

/**
 * Get session protocol data (HTTP, DNS, TLS, etc.)
 */
void *dpi_get_protocol_data(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow,
    dpi_protocol_t protocol
);

/**
 * Terminate a session and cleanup
 */
int dpi_terminate_session(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow
);

/**
 * Get engine statistics
 */
dpi_stats_t dpi_get_engine_stats(dpi_engine_t *engine);

/**
 * Cleanup and shutdown DPI engine
 */
void dpi_shutdown(dpi_engine_t *engine);

#ifdef __cplusplus
}
#endif

#endif /* DPI_ENGINE_H */
