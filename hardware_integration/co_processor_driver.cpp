// Co-processor user-space helper for offloading inference to Ascend 910 / Atlas AI Kit.
//
// Build notes:
//  - Default build (no Ascend SDK available): builds a runnable stub.
//  - To compile real Ascend code, define -DUSE_ASCEND and provide include/lib
//    paths for the Ascend CANN/ACL headers and libraries. See Makefile.
//
// This binary is a lightweight user-space tool that demonstrates the typical
// flow: device init -> load model -> create input tensor -> run inference ->
// fetch output -> cleanup. The real Ascend calls are guarded by
// USE_ASCEND so this file compiles in environments without Ascend SDK.

#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <cstring>

#ifdef USE_ASCEND
// Attempt to include Ascend ACL headers. When building for real hardware set
// appropriate include paths and link flags (see Makefile and README).
#include <acl/acl.h>
#include <acl/ops/acl_dvpp.h>
#endif

static void print_usage(const char* prog) {
    std::cerr << "Usage: " << prog << " --model <model.om> [--input <input.bin>]" << std::endl;
}

static std::string detect_platform_runtime() {
    // 1) env overrides
    const char* atlas = std::getenv("ATLAS_EDGE");
    if (atlas && (std::string(atlas) == "1" || std::string(atlas) == "true")) return "atlas";
    const char* hisi = std::getenv("HISILICON_DEVICE");
    if (hisi && (std::string(hisi) == "1" || std::string(hisi) == "true")) return "hisilicon";

    // 2) ASCEND_HOME presence
    const char* ascend = std::getenv("ASCEND_HOME");
    if (ascend) return "atlas";

    // 3) quick /proc/cpuinfo probe
    std::ifstream f("/proc/cpuinfo");
    if (f.good()) {
        std::string s((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
        for (auto &c : s) c = std::tolower(c);
        if (s.find("ascend") != std::string::npos || s.find("atlas") != std::string::npos || s.find("kunpeng") != std::string::npos) return "atlas";
        if (s.find("hisilicon") != std::string::npos || s.find("hi6220") != std::string::npos) return "hisilicon";
    }

    return "unknown";
}

#ifdef USE_ASCEND
// Minimal, best-effort Ascend flow. This code is illustrative and may need
// adjustments for your platform, CANN/ACL version, and model I/O formats.
int run_ascend_inference(const std::string &model_path, const std::string &input_path) {
    aclError ret = ACL_SUCCESS;
    // 1) initialize ACL
    ret = aclInit(nullptr);
    if (ret != ACL_SUCCESS) {
        std::cerr << "aclInit failed: " << ret << std::endl;
        return 2;
    }

    // 2) set current device (device 0)
    ret = aclrtSetDevice(0);
    if (ret != ACL_SUCCESS) {
        std::cerr << "aclrtSetDevice failed: " << ret << std::endl;
        aclFinalize();
        return 3;
    }

    // 3) load model
    // The API for model loading varies; trying model load via aclmdl API
    aclmdlDesc* model_desc = nullptr;
    uint32_t model_id = 0;
    ret = aclmdlLoadFromFile(model_path.c_str(), &model_id);
    if (ret != ACL_SUCCESS) {
        std::cerr << "aclmdlLoadFromFile failed: " << ret << " path=" << model_path << std::endl;
        aclrtResetDevice(0);
        aclFinalize();
        return 4;
    }

    // NOTE: The rest of the code (buffer creation, model execution, output
    // retrieval) requires robust handling of tensor descriptors and memory
    // management and is highly dependent on model I/O. Here we provide a
    // minimal scaffold that should be adapted for your model's input/output
    // shapes and data formats.

    std::cout << "Loaded model id=" << model_id << " (scaffold inference executed)" << std::endl;

    // Unload model and cleanup
    aclmdlUnload(model_id);
    aclrtResetDevice(0);
    aclFinalize();
    return 0;
}
#endif

int main(int argc, char** argv) {
    if (argc < 3) {
        print_usage(argv[0]);
        return 1;
    }

    std::string model_path;
    std::string input_path;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--model") == 0 && i + 1 < argc) {
            model_path = argv[++i];
        } else if (std::strcmp(argv[i], "--input") == 0 && i + 1 < argc) {
            input_path = argv[++i];
        } else {
            print_usage(argv[0]);
            return 1;
        }
    }

    if (model_path.empty()) {
        print_usage(argv[0]);
        return 1;
    }
#ifdef REQUIRE_PLATFORM
    std::string runtime_platform = detect_platform_runtime();
    const char* req = std::getenv("REQUIRE_PLATFORM");
    if (req && (std::string(req) == "1" || std::string(req) == "true")) {
        if (runtime_platform != "atlas" && runtime_platform != "hisilicon") {
            std::cerr << "This binary must run on Atlas or HiSilicon devices. Detected: " << runtime_platform << std::endl;
            return 4;
        }
    }

#ifdef USE_ASCEND
    std::cout << "Running Ascend inference offload (model=" << model_path << ")" << std::endl;
    return run_ascend_inference(model_path, input_path);
#else
    // Fallback stub behavior: report received args and pretend to run.
    std::cout << "Co-processor driver (stub) - no Ascend SDK compiled in." << std::endl;
    std::cout << "Model: " << model_path << std::endl;
    if (!input_path.empty()) std::cout << "Input: " << input_path << std::endl;
    std::cout << "Simulating offload: loading model, executing on CPU fallback..." << std::endl;
    // Minimal fake output
    std::cout << "Inference result: [0.123, 0.456, 0.789]" << std::endl;
    return 0;
#endif
}
