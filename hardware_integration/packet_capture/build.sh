#!/bin/bash
# Build script for packet capture engine
# Builds C/C++ packet capture library with multiple backend support

set -e

CMAKE_VERSION="3.22"
CC="${CC:-gcc}"
CXX="${CXX:-g++}"
BUILDDIR="${BUILDDIR:-.build}"
PREFIX="${PREFIX:-/usr/local}"
ARCH="${ARCH:-native}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== J.A.R.V.I.S. Packet Capture Engine Build ===${NC}"

# Check for required tools
for tool in gcc g++ make pkg-config; do
    if ! command -v $tool &> /dev/null; then
        echo -e "${RED}Error: $tool not found${NC}"
        exit 1
    fi
done

# Create build directory
mkdir -p "$BUILDDIR"
cd "$BUILDDIR"

# Compiler flags for high performance
CFLAGS="-O3 -march=$ARCH -mtune=$ARCH"
CFLAGS="$CFLAGS -fno-stack-protector -fno-asynchronous-unwind-tables"
CFLAGS="$CFLAGS -Wall -Wextra -Wformat -Werror=format-security"

# Position-independent code for shared library
CFLAGS="$CFLAGS -fPIC"

# Enable hardware optimizations
CFLAGS="$CFLAGS -mavx2 -mavx512f -mavx512dq"

# Check for backend availability
echo "Checking for available backends..."

DPDK_AVAILABLE=0
if pkg-config --exists libdpdk; then
    echo -e "${GREEN}✓${NC} DPDK available"
    DPDK_AVAILABLE=1
fi

XDP_AVAILABLE=0
if [ -f /usr/include/linux/bpf.h ]; then
    echo -e "${GREEN}✓${NC} XDP available"
    XDP_AVAILABLE=1
fi

PFRING_AVAILABLE=0
if pkg-config --exists pfring; then
    echo -e "${GREEN}✓${NC} PF_RING available"
    PFRING_AVAILABLE=1
fi

# Compile packet capture core
echo -e "\n${YELLOW}Compiling packet capture core...${NC}"

CFLAGS_FINAL="$CFLAGS"
if [ "$DPDK_AVAILABLE" = "1" ]; then
    DPDK_CFLAGS=$(pkg-config --cflags libdpdk)
    CFLAGS_FINAL="$CFLAGS_FINAL $DPDK_CFLAGS"
fi

$CC $CFLAGS_FINAL -c ../hardware_integration/packet_capture/packet_capture.c \
    -o packet_capture.o

# Build backend selection module
echo -e "${YELLOW}Building backend selection module...${NC}"

$CC $CFLAGS_FINAL -c - <<'EOF' -o backend_selection.o
#include <stdio.h>
#include <stdlib.h>

#ifdef DPDK_AVAILABLE
int dpdk_backend_available() { return 1; }
#else
int dpdk_backend_available() { return 0; }
#endif

#ifdef XDP_AVAILABLE
int xdp_backend_available() { return 1; }
#else
int xdp_backend_available() { return 0; }
#endif
EOF

# Link into shared library
echo -e "${YELLOW}Linking shared library...${NC}"

LDFLAGS="-shared -Wl,-soname,libpacket_capture.so"
LDFLAGS="$LDFLAGS -Wl,--gc-sections -Wl,--strip-all"

if [ "$DPDK_AVAILABLE" = "1" ]; then
    DPDK_LDFLAGS=$(pkg-config --libs libdpdk)
    LDFLAGS="$LDFLAGS $DPDK_LDFLAGS"
fi

$CC $LDFLAGS packet_capture.o backend_selection.o \
    -o libpacket_capture.so -lpthread -lm

# Create library info
echo -e "${YELLOW}Creating library info...${NC}"

cat > libpacket_capture.pc <<EOF
prefix=$PREFIX
libdir=\${prefix}/lib
includedir=\${prefix}/include

Name: Packet Capture Engine
Description: High-performance packet capture with zero-copy semantics
Version: 1.0.0
Libs: -L\${libdir} -lpacket_capture -lpthread -lm
Cflags: -I\${includedir}
EOF

# Generate header documentation
echo -e "${YELLOW}Generating documentation...${NC}"

$CC -E -x c-header -dD ../hardware_integration/packet_capture/packet_capture.h \
    -o packet_capture_preprocessed.h 2>/dev/null || true

# Run tests if available
if [ -f ../hardware_integration/packet_capture/test_packet_capture.c ]; then
    echo -e "${YELLOW}Building tests...${NC}"
    
    $CC $CFLAGS_FINAL -c ../hardware_integration/packet_capture/test_packet_capture.c \
        -o test_packet_capture.o
    
    $CC test_packet_capture.o packet_capture.o backend_selection.o \
        -o test_packet_capture \
        -lpthread -lm $(pkg-config --libs libdpdk 2>/dev/null || true)
    
    echo -e "${GREEN}✓ Test binary created: test_packet_capture${NC}"
fi

echo -e "\n${GREEN}=== Build Complete ===${NC}"
echo -e "Shared library: ${GREEN}$BUILDDIR/libpacket_capture.so${NC}"
echo -e "Backends enabled:"
[ "$DPDK_AVAILABLE" = "1" ] && echo -e "  ${GREEN}✓${NC} DPDK (Intel Data Plane)"
[ "$XDP_AVAILABLE" = "1" ] && echo -e "  ${GREEN}✓${NC} XDP (Linux eBPF)"
[ "$PFRING_AVAILABLE" = "1" ] && echo -e "  ${GREEN}✓${NC} PF_RING (Kernel Bypass)"
echo -e "  ${GREEN}✓${NC} libpcap (Fallback)"

echo -e "\nTo install:"
echo "  sudo install -m 0755 libpacket_capture.so $PREFIX/lib/"
echo "  sudo install -m 0644 ../hardware_integration/packet_capture/packet_capture.h $PREFIX/include/"
echo "  sudo install -m 0644 libpacket_capture.pc $PREFIX/lib/pkgconfig/"
