/**
 * @file packet_capture.h
 * @brief High-performance packet capture engine with zero-copy semantics
 * 
 * Provides unified interface for multiple capture backends (DPDK, XDP, PF_RING)
 * with support for lossless buffering, timestamping, and flow metering.
 * 
 * Target: 10Gbps-400Gbps throughput depending on SKU
 * Dependencies: DPDK or XDP kernel modules
 * Security: Encrypted capture buffers, firmware integrity validation
 */

#ifndef PACKET_CAPTURE_H
#define PACKET_CAPTURE_H

#include <stdint.h>
#include <time.h>
#include <stdbool.h>
#include <netinet/in.h>
#include <net/ethernet.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================ */

/**
 * Supported capture backends
 */
typedef enum {
    CAPTURE_BACKEND_DPDK = 0,     /**< Intel DPDK (highest performance) */
    CAPTURE_BACKEND_XDP,          /**< Linux XDP/eBPF (in-kernel) */
    CAPTURE_BACKEND_PF_RING,      /**< PF_RING (kernel bypass) */
    CAPTURE_BACKEND_PCAP,         /**< libpcap (fallback/testing) */
} CaptureBackend;

/**
 * Packet direction/ingress-egress classification
 */
typedef enum {
    PACKET_DIR_UNKNOWN = 0,
    PACKET_DIR_INGRESS,
    PACKET_DIR_EGRESS,
    PACKET_DIR_MIRRORED,           /**< SPAN/ERSPAN mirrored copy */
} PacketDirection;

/**
 * Timestamp source and precision
 */
typedef enum {
    TS_SOURCE_NTP = 0,             /**< NTP synchronized (preferred) */
    TS_SOURCE_PTP,                 /**< PTP synchronized (nanosecond precision) */
    TS_SOURCE_KERNEL,              /**< Kernel timestamp */
    TS_SOURCE_HARDWARE,            /**< NIC hardware timestamp */
} TimestampSource;

/**
 * Packet metadata with timing and sequence info
 */
typedef struct {
    uint64_t packet_id;            /**< Global sequence number */
    uint64_t timestamp_ns;         /**< Nanosecond precision timestamp */
    TimestampSource ts_source;     /**< Timestamp source info */
    PacketDirection direction;     /**< Ingress/egress/mirrored */
    uint32_t interface_id;         /**< Physical interface identifier */
    uint16_t vlan_id;              /**< VLAN tag (if present) */
    uint16_t payload_length;       /**< Captured payload length */
    uint16_t wire_length;          /**< Original wire packet length */
    uint8_t encapsulation_level;   /**< Tunnel/GRE depth */
    uint8_t _reserved1;
} PacketMetadata;

/**
 * Captured packet structure (zero-copy capable)
 * Points directly to DMA buffer without copying
 */
typedef struct {
    PacketMetadata metadata;
    uint8_t *payload;              /**< Pointer to packet data (zero-copy) */
    uint32_t payload_size;         /**< Actual payload size */
} CapturedPacket;

/**
 * Flow tuple (5-tuple + VLAN)
 */
typedef struct {
    uint32_t src_ip;               /**< Source IPv4 */
    uint32_t dst_ip;               /**< Destination IPv4 */
    uint16_t src_port;             /**< Source port */
    uint16_t dst_port;             /**< Destination port */
    uint8_t protocol;              /**< Protocol number (TCP/UDP/ICMP) */
    uint16_t vlan_id;              /**< VLAN tag */
} FlowTuple;

/**
 * Flow statistics record
 */
typedef struct {
    FlowTuple tuple;
    uint64_t flow_id;              /**< Unique flow identifier */
    uint64_t first_packet_id;      /**< Sequence of first packet */
    uint64_t last_packet_id;       /**< Sequence of last packet */
    uint64_t first_seen_ns;        /**< Creation timestamp (ns) */
    uint64_t last_seen_ns;         /**< Last update timestamp (ns) */
    uint64_t packets;              /**< Total packets in flow */
    uint64_t bytes;                /**< Total bytes in flow */
    uint64_t bytes_fwd;            /**< Forward direction bytes */
    uint64_t bytes_rev;            /**< Reverse direction bytes */
    uint32_t flags;                /**< TCP flags seen in flow */
    uint16_t interface_id;         /**< Input interface */
    uint8_t state;                 /**< Flow state (ACTIVE, CLOSING, CLOSED) */
    uint8_t _reserved;
} FlowRecord;

/**
 * NetFlow v5 / IPFIX compatible flow record for export
 */
typedef struct {
    FlowRecord flow;
    uint32_t nexthop_ipv4;         /**< IPv4 next hop */
    uint32_t src_as;               /**< Source AS number */
    uint32_t dst_as;               /**< Destination AS number */
    uint8_t src_mask;              /**< Source netmask bits */
    uint8_t dst_mask;              /**< Destination netmask bits */
    uint8_t tcp_flags_final;       /**< Final TCP flags */
} NetFlowRecord;

/**
 * Capture session handle (opaque)
 */
typedef struct capture_session CaptureSession;

/**
 * Capture statistics
 */
typedef struct {
    uint64_t packets_captured;     /**< Total packets captured */
    uint64_t packets_dropped;      /**< Packets dropped due to buffer full */
    uint64_t packets_errors;       /**< Packets with errors */
    uint64_t bytes_captured;       /**< Total bytes captured */
    uint64_t buffer_used_pct;      /**< Buffer utilization percentage */
    uint64_t flows_active;         /**< Active flows in table */
    uint64_t flows_total;          /**< Total flows seen */
    uint32_t rx_errors;            /**< NIC RX errors */
    uint32_t tx_errors;            /**< NIC TX errors */
    double avg_pps;                /**< Average packets/second */
    double avg_throughput_mbps;    /**< Average throughput in Mbps */
} CaptureStats;

/**
 * Callback function for packet processing
 * Return false to stop processing, true to continue
 */
typedef bool (*PacketCallback)(const CapturedPacket *packet, void *user_data);

/**
 * Callback for flow export events
 */
typedef void (*FlowExportCallback)(const NetFlowRecord *flow, void *user_data);

/**
 * Callback for errors and warnings
 */
typedef void (*ErrorCallback)(const char *message, int error_code, void *user_data);

/* ============================================================================
 * API FUNCTIONS
 * ============================================================================ */

/**
 * Initialize packet capture engine
 * 
 * @param backend Preferred capture backend (will auto-select if unavailable)
 * @param interface_name Network interface to capture on (e.g., "eth0", "any")
 * @param buffer_size_mb Ring buffer size in megabytes
 * @param enable_ts Timestamp source (TS_SOURCE_PTP preferred)
 * @return Handle to capture session, NULL on error
 */
CaptureSession *capture_init(
    CaptureBackend backend,
    const char *interface_name,
    uint32_t buffer_size_mb,
    TimestampSource enable_ts
);

/**
 * Start packet capture
 * 
 * @param session Capture session handle
 * @param snaplen Snap length (0 = full packets)
 * @param filter BPF filter string (e.g., "tcp port 80", NULL = all packets)
 * @return 0 on success, -1 on error
 */
int capture_start(CaptureSession *session, uint16_t snaplen, const char *filter);

/**
 * Stop packet capture
 * 
 * @param session Capture session handle
 * @return 0 on success
 */
int capture_stop(CaptureSession *session);

/**
 * Process captured packets
 * Calls callback for each packet in the ring buffer
 * Uses zero-copy memory mapping where possible
 * 
 * @param session Capture session handle
 * @param callback Function to call for each packet
 * @param user_data Context passed to callback
 * @param timeout_ms Timeout in milliseconds (0 = non-blocking)
 * @return Number of packets processed, -1 on error
 */
int capture_poll(
    CaptureSession *session,
    PacketCallback callback,
    void *user_data,
    uint32_t timeout_ms
);

/**
 * Set packet filter (BPF expression)
 * Can be changed at runtime without stopping capture
 * 
 * @param session Capture session handle
 * @param filter BPF filter expression
 * @return 0 on success, -1 on parse error
 */
int capture_set_filter(CaptureSession *session, const char *filter);

/**
 * Get current capture statistics
 * 
 * @param session Capture session handle
 * @param stats Output statistics structure
 * @return 0 on success
 */
int capture_get_stats(CaptureSession *session, CaptureStats *stats);

/**
 * Enable flow metering/aggregation
 * 
 * @param session Capture session handle
 * @param table_size Maximum number of concurrent flows
 * @param idle_timeout_sec Timeout to age out inactive flows
 * @return 0 on success
 */
int capture_flow_enable(
    CaptureSession *session,
    uint32_t table_size,
    uint32_t idle_timeout_sec
);

/**
 * Disable flow metering
 * 
 * @param session Capture session handle
 * @return 0 on success
 */
int capture_flow_disable(CaptureSession *session);

/**
 * Get flow by tuple
 * 
 * @param session Capture session handle
 * @param tuple Flow tuple
 * @param flow Output flow record
 * @return 0 if found, 1 if not found, -1 on error
 */
int capture_flow_lookup(
    CaptureSession *session,
    const FlowTuple *tuple,
    FlowRecord *flow
);

/**
 * Get all active flows
 * Caller must free returned array
 * 
 * @param session Capture session handle
 * @param flows Output array pointer (caller frees)
 * @param count Output count
 * @return 0 on success
 */
int capture_flow_get_all(
    CaptureSession *session,
    FlowRecord **flows,
    uint32_t *count
);

/**
 * Enable NetFlow/IPFIX export
 * 
 * @param session Capture session handle
 * @param collector_ip Export destination IP
 * @param collector_port Export destination port (default 2055)
 * @param export_interval_sec Flow export interval
 * @param callback Optional callback for local flow export events
 * @return 0 on success
 */
int capture_netflow_enable(
    CaptureSession *session,
    const char *collector_ip,
    uint16_t collector_port,
    uint32_t export_interval_sec,
    FlowExportCallback callback
);

/**
 * Set up encryption for capture buffers
 * 
 * @param session Capture session handle
 * @param cipher_suite Cipher suite (e.g., "AES-256-GCM")
 * @param key_file Path to encrypted key file
 * @return 0 on success
 */
int capture_set_encryption(
    CaptureSession *session,
    const char *cipher_suite,
    const char *key_file
);

/**
 * Verify firmware signature
 * Must be called before buffer access in production
 * 
 * @param firmware_path Path to firmware binary
 * @param signature_path Path to signature file
 * @return 0 if valid, 1 if invalid, -1 on error
 */
int capture_verify_firmware(
    const char *firmware_path,
    const char *signature_path
);

/**
 * Set error callback
 * 
 * @param session Capture session handle
 * @param callback Error callback function
 * @param user_data Context passed to callback
 */
void capture_set_error_callback(
    CaptureSession *session,
    ErrorCallback callback,
    void *user_data
);

/**
 * Free capture session
 * Stops capture and releases all resources
 * 
 * @param session Capture session handle
 */
void capture_cleanup(CaptureSession *session);

/* ============================================================================
 * UTILITY FUNCTIONS
 * ============================================================================ */

/**
 * Convert flow tuple to string representation
 * 
 * @param tuple Flow tuple
 * @param buffer Output buffer (min 64 bytes)
 * @return Pointer to buffer
 */
const char *flow_tuple_to_string(const FlowTuple *tuple, char *buffer);

/**
 * Get backend name string
 * 
 * @param backend Backend type
 * @return Backend name string
 */
const char *capture_backend_name(CaptureBackend backend);

/**
 * Get available backends on this system
 * 
 * @param backends Output array for supported backends
 * @return Number of supported backends
 */
int capture_get_available_backends(CaptureBackend *backends);

/**
 * Calculate flow ID from tuple (deterministic hash)
 * 
 * @param tuple Flow tuple
 * @return Flow ID
 */
uint64_t flow_tuple_hash(const FlowTuple *tuple);

#ifdef __cplusplus
}
#endif

#endif /* PACKET_CAPTURE_H */
