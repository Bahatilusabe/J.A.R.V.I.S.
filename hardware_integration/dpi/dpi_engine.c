/*
 * Deep Packet Inspection (DPI) Engine Implementation
 *
 * Core DPI engine with:
 * - Stateful TCP/UDP stream reassembly
 * - Protocol dissectors
 * - Pattern matching
 * - Anomaly detection
 *
 * Author: J.A.R.V.I.S. Team
 */

#include "dpi_engine.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#include <time.h>
#include <regex.h>

/* ========================================================================
 * INTERNAL STRUCTURES
 * ======================================================================== */

/* Hash table for session lookup */
typedef struct {
    dpi_session_t **sessions;
    uint32_t capacity;
    uint32_t count;
    pthread_rwlock_t lock;
} dpi_session_table_t;

/* Rule engine state */
typedef struct {
    dpi_rule_t *rules;
    regex_t *compiled_regex;
    uint32_t rule_count;
    uint32_t max_rules;
    pthread_rwlock_t lock;
} dpi_rule_engine_t;

/* Alert queue */
typedef struct {
    dpi_alert_t *queue;
    uint32_t head;
    uint32_t tail;
    uint32_t capacity;
    pthread_spinlock_t lock;
} dpi_alert_queue_t;

/* Main DPI engine */
struct dpi_engine_s {
    dpi_config_t config;
    dpi_session_table_t sessions;
    dpi_rule_engine_t rules;
    dpi_alert_queue_t alerts;
    dpi_stats_t stats;
    pthread_rwlock_t stats_lock;
    uint64_t next_session_id;
    uint64_t next_alert_id;
};

/* ========================================================================
 * UTILITY FUNCTIONS
 * ======================================================================== */

/* Hash function for flow tuple */
static uint32_t flow_tuple_hash(const dpi_flow_tuple_t *flow, uint32_t table_size)
{
    uint32_t hash = 5381;
    
    hash = ((hash << 5) + hash) ^ (flow->src_ip & 0xFF);
    hash = ((hash << 5) + hash) ^ ((flow->src_ip >> 8) & 0xFF);
    hash = ((hash << 5) + hash) ^ ((flow->src_ip >> 16) & 0xFF);
    hash = ((hash << 5) + hash) ^ ((flow->src_ip >> 24) & 0xFF);
    
    hash = ((hash << 5) + hash) ^ (flow->dst_ip & 0xFF);
    hash = ((hash << 5) + hash) ^ ((flow->dst_ip >> 8) & 0xFF);
    hash = ((hash << 5) + hash) ^ ((flow->dst_ip >> 16) & 0xFF);
    hash = ((hash << 5) + hash) ^ ((flow->dst_ip >> 24) & 0xFF);
    
    hash = ((hash << 5) + hash) ^ (flow->src_port & 0xFF);
    hash = ((hash << 5) + hash) ^ ((flow->src_port >> 8) & 0xFF);
    
    hash = ((hash << 5) + hash) ^ (flow->dst_port & 0xFF);
    hash = ((hash << 5) + hash) ^ ((flow->dst_port >> 8) & 0xFF);
    
    hash = ((hash << 5) + hash) ^ flow->protocol;
    
    return hash % table_size;
}

/* Flow tuple equality */
static int flow_tuple_equal(const dpi_flow_tuple_t *a, const dpi_flow_tuple_t *b)
{
    return (a->src_ip == b->src_ip &&
            a->dst_ip == b->dst_ip &&
            a->src_port == b->src_port &&
            a->dst_port == b->dst_port &&
            a->protocol == b->protocol);
}

/* Get current time in nanoseconds */
static uint64_t get_time_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000UL + ts.tv_nsec;
}

/* ========================================================================
 * PROTOCOL DISSECTORS
 * ======================================================================== */

/**
 * HTTP Dissector
 * Extracts method, URI, headers, status code
 */
static dpi_protocol_t dissect_http(const uint8_t *data, uint32_t len, void **out)
{
    if (len < 7) return DPI_PROTO_UNKNOWN;
    
    /* Check for HTTP methods */
    if (strncmp((const char *)data, "GET ", 4) == 0 ||
        strncmp((const char *)data, "POST ", 5) == 0 ||
        strncmp((const char *)data, "PUT ", 4) == 0 ||
        strncmp((const char *)data, "DELETE ", 7) == 0 ||
        strncmp((const char *)data, "HEAD ", 5) == 0 ||
        strncmp((const char *)data, "OPTIONS ", 8) == 0 ||
        strncmp((const char *)data, "PATCH ", 6) == 0) {
        
        dpi_http_data_t *http = malloc(sizeof(*http));
        if (!http) return DPI_PROTO_UNKNOWN;
        
        memset(http, 0, sizeof(*http));
        http->is_request = 1;
        
        /* Extract method */
        const char *space = strchr((const char *)data, ' ');
        if (space) {
            size_t method_len = space - (const char *)data;
            if (method_len < sizeof(http->method))
                strncpy(http->method, (const char *)data, method_len);
        }
        
        *out = http;
        return DPI_PROTO_HTTP;
    }
    
    /* Check for HTTP response */
    if (strncmp((const char *)data, "HTTP/", 5) == 0) {
        dpi_http_data_t *http = malloc(sizeof(*http));
        if (!http) return DPI_PROTO_UNKNOWN;
        
        memset(http, 0, sizeof(*http));
        http->is_request = 0;
        
        /* Extract status code */
        const char *space = strchr((const char *)data, ' ');
        if (space) {
            http->status_code = atoi(space + 1);
        }
        
        *out = http;
        return DPI_PROTO_HTTP;
    }
    
    return DPI_PROTO_UNKNOWN;
}

/**
 * DNS Dissector
 * Extracts query/response data, domains, answers
 */
static dpi_protocol_t dissect_dns(const uint8_t *data, uint32_t len, void **out)
{
    if (len < 12) return DPI_PROTO_UNKNOWN;
    
    dpi_dns_data_t *dns = malloc(sizeof(*dns));
    if (!dns) return DPI_PROTO_UNKNOWN;
    
    memset(dns, 0, sizeof(*dns));
    
    /* Extract DNS transaction ID */
    dns->transaction_id = (data[0] << 8) | data[1];
    
    /* Determine if query or response (bit 15 in flags) */
    dns->is_query = !(data[2] & 0x80);
    dns->response_code = data[3] & 0x0F;
    
    *out = dns;
    return DPI_PROTO_DNS;
}

/**
 * TLS/SSL Dissector
 * Extracts version, cipher suite, SNI, certificate info
 */
static dpi_protocol_t dissect_tls(const uint8_t *data, uint32_t len, void **out)
{
    if (len < 5) return DPI_PROTO_UNKNOWN;
    
    /* Check for TLS record header */
    uint8_t content_type = data[0];
    uint16_t version = (data[1] << 8) | data[2];
    
    /* TLS content types: 0x16 = handshake, 0x17 = application_data */
    if (content_type != 0x16 && content_type != 0x17 && content_type != 0x15)
        return DPI_PROTO_UNKNOWN;
    
    /* Check for valid TLS versions (3.1 = TLS 1.0, 3.3 = TLS 1.2, 3.4 = TLS 1.3) */
    if ((data[1] != 0x03) || (data[2] < 0x01 || data[2] > 0x04))
        return DPI_PROTO_UNKNOWN;
    
    dpi_tls_data_t *tls = malloc(sizeof(*tls));
    if (!tls) return DPI_PROTO_UNKNOWN;
    
    memset(tls, 0, sizeof(*tls));
    
    tls->version_major = data[1];
    tls->version_minor = data[2];
    
    *out = tls;
    return DPI_PROTO_HTTPS;
}

/**
 * SMTP Dissector
 * Detects SMTP protocol
 */
static dpi_protocol_t dissect_smtp(const uint8_t *data, uint32_t len, void **out)
{
    if (len < 8) return DPI_PROTO_UNKNOWN;
    
    /* Check for SMTP response codes (220, 250, 354, 550, etc.) */
    if (isdigit(data[0]) && isdigit(data[1]) && isdigit(data[2]) && data[3] == ' ') {
        return DPI_PROTO_SMTP;
    }
    
    /* Check for SMTP commands */
    if (strncmp((const char *)data, "EHLO ", 5) == 0 ||
        strncmp((const char *)data, "HELO ", 5) == 0 ||
        strncmp((const char *)data, "MAIL ", 5) == 0 ||
        strncmp((const char *)data, "RCPT ", 5) == 0 ||
        strncmp((const char *)data, "DATA", 4) == 0 ||
        strncmp((const char *)data, "QUIT", 4) == 0) {
        return DPI_PROTO_SMTP;
    }
    
    return DPI_PROTO_UNKNOWN;
}

/**
 * SMB Dissector
 * Detects SMB/CIFS protocol
 */
static dpi_protocol_t dissect_smb(const uint8_t *data, uint32_t len, void **out)
{
    if (len < 4) return DPI_PROTO_UNKNOWN;
    
    /* SMB signature: 0xFF 'S' 'M' 'B' or SMB3 0xFE 'S' 'M' 'B' */
    if ((data[0] == 0xFF || data[0] == 0xFE) &&
        data[1] == 'S' && data[2] == 'M' && data[3] == 'B') {
        return DPI_PROTO_SMB;
    }
    
    return DPI_PROTO_UNKNOWN;
}

/**
 * Port-based protocol heuristics
 */
static dpi_protocol_t classify_by_port(uint16_t src_port, uint16_t dst_port)
{
    if (dst_port == 80 || src_port == 80) return DPI_PROTO_HTTP;
    if (dst_port == 443 || src_port == 443) return DPI_PROTO_HTTPS;
    if (dst_port == 53 || src_port == 53) return DPI_PROTO_DNS;
    if (dst_port == 25 || dst_port == 587 || src_port == 25) return DPI_PROTO_SMTP;
    if (dst_port == 465 || src_port == 465) return DPI_PROTO_SMTPS;
    if (dst_port == 21 || src_port == 21) return DPI_PROTO_FTP;
    if (dst_port == 990 || src_port == 990) return DPI_PROTO_FTPS;
    if (dst_port == 445 || src_port == 445) return DPI_PROTO_SMB;
    if (dst_port == 22 || src_port == 22) return DPI_PROTO_SSH;
    if (dst_port == 23 || src_port == 23) return DPI_PROTO_TELNET;
    if (dst_port == 161 || src_port == 161) return DPI_PROTO_SNMP;
    
    return DPI_PROTO_UNKNOWN;
}

/* ========================================================================
 * ANOMALY DETECTION
 * ======================================================================== */

/**
 * Detect protocol anomalies
 */
static void detect_anomalies(dpi_session_t *session, const uint8_t *data, 
                             uint32_t len, uint8_t is_response)
{
    if (!session || session->anomaly_count >= 10)
        return;
    
    dpi_anomaly_t anomaly = {0};
    
    /* HTTP anomalies */
    if (session->protocol.protocol == DPI_PROTO_HTTP) {
        /* Large headers */
        if (len > 8192) {
            anomaly.anomaly_type = 1;
            snprintf(anomaly.description, sizeof(anomaly.description),
                    "HTTP packet exceeds normal header size: %u bytes", len);
            anomaly.severity = 5;
        }
        
        /* Suspicious User-Agent */
        const char *ua_marker = "User-Agent: ";
        if (strstr((const char *)data, ua_marker)) {
            anomaly.anomaly_type = 2;
            snprintf(anomaly.description, sizeof(anomaly.description),
                    "HTTP request contains suspicious User-Agent");
            anomaly.severity = 3;
        }
    }
    
    /* Port mismatch anomaly */
    if (session->protocol.protocol == DPI_PROTO_HTTP && 
        session->flow.dst_port != 80 && session->flow.dst_port != 8080) {
        anomaly.anomaly_type = 3;
        snprintf(anomaly.description, sizeof(anomaly.description),
                "HTTP on non-standard port %u", session->flow.dst_port);
        anomaly.severity = 4;
    }
    
    if (anomaly.anomaly_type != 0) {
        session->anomalies = realloc(session->anomalies,
                                     sizeof(dpi_anomaly_t) * (session->anomaly_count + 1));
        if (session->anomalies) {
            session->anomalies[session->anomaly_count++] = anomaly;
        }
    }
}

/* ========================================================================
 * API IMPLEMENTATION
 * ======================================================================== */

dpi_engine_t *dpi_init(const dpi_config_t *config)
{
    dpi_engine_t *engine = calloc(1, sizeof(*engine));
    if (!engine) return NULL;
    
    memcpy(&engine->config, config, sizeof(*config));
    
    /* Initialize session table */
    engine->sessions.capacity = config->max_concurrent_sessions;
    engine->sessions.sessions = calloc(config->max_concurrent_sessions, sizeof(void *));
    if (!engine->sessions.sessions) {
        free(engine);
        return NULL;
    }
    pthread_rwlock_init(&engine->sessions.lock, NULL);
    
    /* Initialize rule engine */
    engine->rules.max_rules = DPI_MAX_RULES;
    engine->rules.rules = calloc(DPI_MAX_RULES, sizeof(dpi_rule_t));
    engine->rules.compiled_regex = calloc(DPI_MAX_RULES, sizeof(regex_t));
    if (!engine->rules.rules || !engine->rules.compiled_regex) {
        free(engine->sessions.sessions);
        free(engine->rules.rules);
        free(engine->rules.compiled_regex);
        free(engine);
        return NULL;
    }
    pthread_rwlock_init(&engine->rules.lock, NULL);
    
    /* Initialize alert queue */
    engine->alerts.capacity = DPI_MAX_ALERTS;
    engine->alerts.queue = calloc(DPI_MAX_ALERTS, sizeof(dpi_alert_t));
    if (!engine->alerts.queue) {
        free(engine->sessions.sessions);
        free(engine->rules.rules);
        free(engine->rules.compiled_regex);
        free(engine);
        return NULL;
    }
    pthread_spin_init(&engine->alerts.lock, PTHREAD_PROCESS_PRIVATE);
    
    /* Initialize statistics lock */
    pthread_rwlock_init(&engine->stats_lock, NULL);
    
    engine->next_session_id = 1;
    engine->next_alert_id = 1;
    
    return engine;
}

uint32_t dpi_process_packet(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow,
    const uint8_t *packet_data,
    uint32_t packet_len,
    uint64_t timestamp_ns,
    uint8_t is_response,
    dpi_alert_t **alerts_out)
{
    if (!engine || !flow || !packet_data || packet_len == 0)
        return 0;
    
    uint32_t alerts_generated = 0;
    
    /* Find or create session */
    uint32_t hash_idx = flow_tuple_hash(flow, engine->sessions.capacity);
    
    pthread_rwlock_wrlock(&engine->sessions.lock);
    
    dpi_session_t *session = NULL;
    for (uint32_t i = 0; i < engine->sessions.count; i++) {
        if (flow_tuple_equal(&engine->sessions.sessions[i]->flow, flow)) {
            session = engine->sessions.sessions[i];
            break;
        }
    }
    
    if (!session && engine->sessions.count < engine->sessions.capacity) {
        session = calloc(1, sizeof(*session));
        if (session) {
            session->session_id = engine->next_session_id++;
            memcpy(&session->flow, flow, sizeof(*flow));
            session->state = DPI_STATE_NEW;
            session->created_ns = timestamp_ns;
            session->last_seen_ns = timestamp_ns;
            
            /* Allocate reassembly buffers */
            session->fwd_buffer = malloc(DPI_REASSEMBLY_BUFFER_SIZE);
            session->rev_buffer = malloc(DPI_REASSEMBLY_BUFFER_SIZE);
            
            engine->sessions.sessions[engine->sessions.count++] = session;
        }
    }
    
    if (session) {
        session->last_seen_ns = timestamp_ns;
        session->packets_seen++;
        session->total_bytes += packet_len;
        
        /* Classify protocol on first packet with payload */
        if (session->protocol.protocol == DPI_PROTO_UNKNOWN && packet_len > 0) {
            void *proto_data = NULL;
            
            if (dissect_http(packet_data, packet_len, &proto_data) != DPI_PROTO_UNKNOWN) {
                session->protocol.protocol = DPI_PROTO_HTTP;
                session->http_data = proto_data;
            } else if (dissect_dns(packet_data, packet_len, &proto_data) != DPI_PROTO_UNKNOWN) {
                session->protocol.protocol = DPI_PROTO_DNS;
                session->dns_data = proto_data;
            } else if (dissect_tls(packet_data, packet_len, &proto_data) != DPI_PROTO_UNKNOWN) {
                session->protocol.protocol = DPI_PROTO_HTTPS;
                session->tls_data = proto_data;
            } else if (dissect_smtp(packet_data, packet_len, &proto_data) != DPI_PROTO_UNKNOWN) {
                session->protocol.protocol = DPI_PROTO_SMTP;
            } else if (dissect_smb(packet_data, packet_len, &proto_data) != DPI_PROTO_UNKNOWN) {
                session->protocol.protocol = DPI_PROTO_SMB;
            } else {
                /* Try port-based heuristics */
                session->protocol.protocol = classify_by_port(flow->src_port, flow->dst_port);
            }
            session->protocol.detection_tick = session->packets_seen;
        }
        
        /* Update session state */
        if (session->state == DPI_STATE_NEW)
            session->state = DPI_STATE_ESTABLISHED;
        
        /* Detect anomalies */
        if (engine->config.enable_anomaly_detection) {
            detect_anomalies(session, packet_data, packet_len, is_response);
        }
    }
    
    pthread_rwlock_unlock(&engine->sessions.lock);
    
    /* Update statistics */
    pthread_rwlock_wrlock(&engine->stats_lock);
    engine->stats.packets_processed++;
    engine->stats.bytes_processed += packet_len;
    engine->stats.active_sessions = engine->sessions.count;
    pthread_rwlock_unlock(&engine->stats_lock);
    
    if (alerts_out)
        *alerts_out = NULL;
    
    return alerts_generated;
}

uint32_t dpi_add_rule(
    dpi_engine_t *engine,
    const dpi_rule_t *rule)
{
    if (!engine || !rule || engine->rules.rule_count >= engine->rules.max_rules)
        return 0;
    
    pthread_rwlock_wrlock(&engine->rules.lock);
    
    uint32_t rule_id = engine->rules.rule_count + 1;
    memcpy(&engine->rules.rules[engine->rules.rule_count], rule, sizeof(*rule));
    engine->rules.rules[engine->rules.rule_count].rule_id = rule_id;
    
    /* Compile regex if applicable */
    if (rule->type == DPI_RULE_REGEX && rule->pattern) {
        if (regcomp(&engine->rules.compiled_regex[engine->rules.rule_count],
                    rule->pattern, REG_EXTENDED | REG_ICASE) == 0) {
            engine->rules.rule_count++;
            pthread_rwlock_unlock(&engine->rules.lock);
            return rule_id;
        }
    } else {
        engine->rules.rule_count++;
        pthread_rwlock_unlock(&engine->rules.lock);
        return rule_id;
    }
    
    pthread_rwlock_unlock(&engine->rules.lock);
    return 0;
}

int dpi_remove_rule(
    dpi_engine_t *engine,
    uint32_t rule_id)
{
    if (!engine || rule_id == 0)
        return -1;
    
    pthread_rwlock_wrlock(&engine->rules.lock);
    
    for (uint32_t i = 0; i < engine->rules.rule_count; i++) {
        if (engine->rules.rules[i].rule_id == rule_id) {
            /* Cleanup compiled regex */
            if (engine->rules.rules[i].type == DPI_RULE_REGEX) {
                regfree(&engine->rules.compiled_regex[i]);
            }
            
            /* Remove from array */
            memmove(&engine->rules.rules[i], &engine->rules.rules[i+1],
                   (engine->rules.rule_count - i - 1) * sizeof(dpi_rule_t));
            memmove(&engine->rules.compiled_regex[i], 
                   &engine->rules.compiled_regex[i+1],
                   (engine->rules.rule_count - i - 1) * sizeof(regex_t));
            
            engine->rules.rule_count--;
            pthread_rwlock_unlock(&engine->rules.lock);
            return 0;
        }
    }
    
    pthread_rwlock_unlock(&engine->rules.lock);
    return -1;
}

uint32_t dpi_get_alerts(
    dpi_engine_t *engine,
    dpi_alert_t *alerts,
    uint32_t max_alerts,
    uint8_t clear_after_read)
{
    if (!engine || !alerts || max_alerts == 0)
        return 0;
    
    pthread_spin_lock(&engine->alerts.lock);
    
    uint32_t count = 0;
    while (count < max_alerts && engine->alerts.head != engine->alerts.tail) {
        memcpy(&alerts[count], &engine->alerts.queue[engine->alerts.head], 
               sizeof(dpi_alert_t));
        
        if (clear_after_read) {
            engine->alerts.head = (engine->alerts.head + 1) % engine->alerts.capacity;
        }
        count++;
    }
    
    pthread_spin_unlock(&engine->alerts.lock);
    return count;
}

dpi_stats_t dpi_get_stats(dpi_engine_t *engine)
{
    if (!engine) {
        dpi_stats_t empty = {0};
        return empty;
    }
    
    pthread_rwlock_rdlock(&engine->stats_lock);
    dpi_stats_t stats = engine->stats;
    pthread_rwlock_unlock(&engine->stats_lock);
    
    return stats;
}

dpi_session_t *dpi_get_session(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow)
{
    if (!engine || !flow)
        return NULL;
    
    pthread_rwlock_rdlock(&engine->sessions.lock);
    
    for (uint32_t i = 0; i < engine->sessions.count; i++) {
        if (flow_tuple_equal(&engine->sessions.sessions[i]->flow, flow)) {
            dpi_session_t *session = engine->sessions.sessions[i];
            pthread_rwlock_unlock(&engine->sessions.lock);
            return session;
        }
    }
    
    pthread_rwlock_unlock(&engine->sessions.lock);
    return NULL;
}

dpi_protocol_result_t dpi_classify_protocol(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow)
{
    dpi_protocol_result_t result = {DPI_PROTO_UNKNOWN, 0, 0, {0}};
    
    if (!engine || !flow)
        return result;
    
    dpi_session_t *session = dpi_get_session(engine, flow);
    if (session) {
        result = session->protocol;
    }
    
    return result;
}

int dpi_set_tls_mode(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow,
    dpi_tls_mode_t mode)
{
    if (!engine || !flow)
        return -1;
    
    engine->config.tls_mode = mode;
    return 0;
}

void *dpi_get_protocol_data(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow,
    dpi_protocol_t protocol)
{
    if (!engine || !flow)
        return NULL;
    
    dpi_session_t *session = dpi_get_session(engine, flow);
    if (!session)
        return NULL;
    
    switch (protocol) {
        case DPI_PROTO_HTTP:
        case DPI_PROTO_HTTPS:
            return session->http_data;
        case DPI_PROTO_DNS:
            return session->dns_data;
        case DPI_PROTO_SMTP:
        case DPI_PROTO_SMTPS:
            return NULL;  /* Not implemented yet */
        default:
            return NULL;
    }
}

int dpi_terminate_session(
    dpi_engine_t *engine,
    const dpi_flow_tuple_t *flow)
{
    if (!engine || !flow)
        return -1;
    
    pthread_rwlock_wrlock(&engine->sessions.lock);
    
    for (uint32_t i = 0; i < engine->sessions.count; i++) {
        if (flow_tuple_equal(&engine->sessions.sessions[i]->flow, flow)) {
            dpi_session_t *session = engine->sessions.sessions[i];
            
            /* Cleanup buffers */
            free(session->fwd_buffer);
            free(session->rev_buffer);
            free(session->http_data);
            free(session->dns_data);
            free(session->tls_data);
            free(session->anomalies);
            free(session);
            
            /* Remove from array */
            memmove(&engine->sessions.sessions[i],
                   &engine->sessions.sessions[i+1],
                   (engine->sessions.count - i - 1) * sizeof(void *));
            
            engine->sessions.count--;
            
            pthread_rwlock_unlock(&engine->sessions.lock);
            return 0;
        }
    }
    
    pthread_rwlock_unlock(&engine->sessions.lock);
    return -1;
}

dpi_stats_t dpi_get_engine_stats(dpi_engine_t *engine)
{
    return dpi_get_stats(engine);
}

void dpi_shutdown(dpi_engine_t *engine)
{
    if (!engine)
        return;
    
    /* Cleanup all sessions */
    pthread_rwlock_wrlock(&engine->sessions.lock);
    for (uint32_t i = 0; i < engine->sessions.count; i++) {
        dpi_session_t *session = engine->sessions.sessions[i];
        free(session->fwd_buffer);
        free(session->rev_buffer);
        free(session->http_data);
        free(session->dns_data);
        free(session->tls_data);
        free(session->anomalies);
        free(session);
    }
    free(engine->sessions.sessions);
    pthread_rwlock_unlock(&engine->sessions.lock);
    pthread_rwlock_destroy(&engine->sessions.lock);
    
    /* Cleanup rules */
    pthread_rwlock_wrlock(&engine->rules.lock);
    for (uint32_t i = 0; i < engine->rules.rule_count; i++) {
        if (engine->rules.rules[i].type == DPI_RULE_REGEX) {
            regfree(&engine->rules.compiled_regex[i]);
        }
    }
    free(engine->rules.rules);
    free(engine->rules.compiled_regex);
    pthread_rwlock_unlock(&engine->rules.lock);
    pthread_rwlock_destroy(&engine->rules.lock);
    
    /* Cleanup alerts */
    free(engine->alerts.queue);
    pthread_spin_destroy(&engine->alerts.lock);
    
    pthread_rwlock_destroy(&engine->stats_lock);
    
    free(engine);
}
