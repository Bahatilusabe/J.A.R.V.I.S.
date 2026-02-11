/*
 * Minimal PALISADE C wrapper template
 *
 * This file provides a tiny, self-contained C implementation that matches the
 * ABI expected by the Python `_PalisadeLib` scaffold in
 * `backend/core/blockchain_xdr/homomorphic_layer.py`.
 *
 * ABI (expected):
 *   int palisade_encrypt(const uint8_t* in, size_t in_len, uint8_t** out, size_t* out_len);
 *   int palisade_add(const uint8_t* a, size_t a_len, const uint8_t* b, size_t b_len, uint8_t** out, size_t* out_len);
 *   int palisade_decrypt(const uint8_t* in, size_t in_len, uint8_t** out, size_t* out_len);
 *   void palisade_free(uint8_t* ptr);
 *
 * This template intentionally implements a "toy" behavior so you can build
 * and test the Python scaffold without a real PALISADE build. It treats the
 * input bytes as UTF-8 JSON arrays of numbers (e.g. "[1.0,2.0,3.5]") for the
 * add path, and otherwise acts as an identity "encryption" (copy).
 *
 * Replace the bodies with real calls into PALISADE (or a C wrapper around
 * PALISADE) for production.
 */

#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>

/* Helper: parse a JSON array of doubles from ASCII input.
 * This is intentionally permissive: it walks the string and extracts numbers
 * using strtod. It returns a malloc'd array of doubles and sets *out_len.
 * The caller must free the returned pointer.
 */
static double* parse_numbers(const char* s, size_t len, size_t* out_len) {
    // Copy into a NUL-terminated buffer
    char* buf = (char*)malloc(len + 1);
    if (!buf) return NULL;
    memcpy(buf, s, len);
    buf[len] = '\0';

    double* arr = NULL;
    size_t cap = 0;
    size_t cnt = 0;
    char* p = buf;
    char* endptr;

    while (*p) {
        // skip non-number chars
        if ((*p >= '0' && *p <= '9') || *p == '+' || *p == '-' || *p == '.') {
            double v = strtod(p, &endptr);
            if (endptr == p) {
                // no number parsed
                p++;
                continue;
            }
            if (cnt + 1 > cap) {
                size_t ncap = cap ? cap * 2 : 8;
                double* tmp = (double*)realloc(arr, ncap * sizeof(double));
                if (!tmp) { free(arr); free(buf); return NULL; }
                arr = tmp; cap = ncap;
            }
            arr[cnt++] = v;
            p = endptr;
        } else {
            p++;
        }
    }

    free(buf);
    *out_len = cnt;
    return arr;
}

/* Helper: serialize an array of doubles to a JSON array string. Returns a
 * malloc'd buffer and sets out_len. Caller must free.
 */
static uint8_t* serialize_numbers(const double* arr, size_t n, size_t* out_len) {
    // first compute size conservatively
    size_t cap = 32 + n * 32;
    char* buf = (char*)malloc(cap);
    if (!buf) return NULL;
    char* p = buf;
    size_t rem = cap;

    int written = snprintf(p, rem, "[");
    if (written < 0) { free(buf); return NULL; }
    p += written; rem -= (size_t)written;

    for (size_t i = 0; i < n; ++i) {
        written = snprintf(p, rem, "%s%.17g", i ? "," : "", arr[i]);
        if (written < 0 || (size_t)written >= rem) {
            // resize
            size_t used = p - buf;
            cap = cap * 2 + 64;
            char* tmp = (char*)realloc(buf, cap);
            if (!tmp) { free(buf); return NULL; }
            buf = tmp;
            p = buf + used;
            rem = cap - used;
            written = snprintf(p, rem, "%s%.17g", i ? "," : "", arr[i]);
            if (written < 0 || (size_t)written >= rem) { free(buf); return NULL; }
        }
        p += written; rem -= (size_t)written;
    }

    written = snprintf(p, rem, "]");
    if (written < 0) { free(buf); return NULL; }
    p += written;

    size_t total = p - buf;
    uint8_t* out = (uint8_t*)malloc(total);
    if (!out) { free(buf); return NULL; }
    memcpy(out, buf, total);
    free(buf);
    *out_len = total;
    return out;
}

/* Identity "encrypt": just copy plaintext to allocated buffer */
int palisade_encrypt(const uint8_t* in, size_t in_len, uint8_t** out, size_t* out_len) {
    if (!in || !out || !out_len) return -1;
    uint8_t* buf = (uint8_t*)malloc(in_len);
    if (!buf) return -2;
    memcpy(buf, in, in_len);
    *out = buf;
    *out_len = in_len;
    return 0;
}

/* Add: parse both inputs as numeric arrays and return JSON of elementwise sum.
 * If parsing fails, return an error code.
 */
int palisade_add(const uint8_t* a, size_t a_len, const uint8_t* b, size_t b_len, uint8_t** out, size_t* out_len) {
    if (!a || !b || !out || !out_len) return -1;
    size_t na = 0, nb = 0;
    double* arr_a = parse_numbers((const char*)a, a_len, &na);
    double* arr_b = parse_numbers((const char*)b, b_len, &nb);
    if (!arr_a || !arr_b) { free(arr_a); free(arr_b); return -2; }
    if (na != nb) { free(arr_a); free(arr_b); return -3; }

    double* sum = (double*)malloc(sizeof(double) * na);
    if (!sum) { free(arr_a); free(arr_b); return -4; }
    for (size_t i = 0; i < na; ++i) sum[i] = arr_a[i] + arr_b[i];

    uint8_t* ser = serialize_numbers(sum, na, out_len);
    free(sum); free(arr_a); free(arr_b);
    if (!ser) return -5;
    *out = ser;
    return 0;
}

/* Identity "decrypt" (copy) */
int palisade_decrypt(const uint8_t* in, size_t in_len, uint8_t** out, size_t* out_len) {
    return palisade_encrypt(in, in_len, out, out_len);
}

/* Free allocated buffers */
void palisade_free(uint8_t* ptr) {
    if (ptr) free(ptr);
}
