# Voice-Activated SOC — Edge Deployment Notes

This document provides actionable instructions for deploying the voice-activated
SOC components on edge platforms such as the HiLens Kit and Atlas Edge 500.

## Overview

- We support two primary deployment targets:
  - HiLens Kit (typically CPU/GPU with OpenVINO or HiAI runtime)
  - Atlas Edge 500 (Ascend NPU with .om runtime)
- The repo provides helper scripts in `backend/core/vocalsoc/` to produce
  transportable bundles: `deploy_hilens.py` and `deploy_atlas.py`.

## Packaging

1. Ensure your runtime artifacts are present under `backend/core/vocalsoc`:
   - ASR model in IR format (.xml/.bin) for OpenVINO or .om for Ascend.
   - any vocab/lexicon files used by decoders.
   - `offline_cache_db/` and `voice_auth_db/` if you want to seed the device with data.

2. Use the helper scripts to create a deploy bundle:

   For HiLens:

       python -m backend.core.vocalsoc.deploy_hilens --out /tmp/vocalsoc_hilens.tar.gz

   For Atlas Edge 500:

       python -m backend.core.vocalsoc.deploy_atlas --out /tmp/vocalsoc_atlas.tar.gz

## Model conversion

- MindSpore -> ONNX -> OpenVINO IR: export your MindSpore model to ONNX, then use
  OpenVINO Model Optimizer to generate IR (.xml/.bin).
- MindSpore -> .om (Ascend): use the Ascend ATC toolchain to convert models to .om.
- Quantization: run post-training quantization (INT8) or quant-aware training to
  reduce inference latency and memory usage.

## On-device runtime

- HiLens: follow HiLens Studio or cloud console to upload the bundle. Provide an
  inference harness (preprocess/postprocess) that maps audio inputs to model inputs.
- Atlas Edge 500: copy the .om artifacts + runtime harness, then use Ascend runtime
  APIs to load and run inference on device.

## Air-gapped transfer

- Use `cache_tool.export-pack` to create a tarball and checksum for transfer.
- On target, `cache_tool.import-verify` then `cache_tool apply` to atomically swap
  the incoming cache into place.

## Testing and smoke checks

- Before deploying, run a smoke test on a representative audio file to verify
  preprocessing, model inference, and postprocessing.
- For HiLens/Atlas, ensure your inference harness includes small tests so the
  operator can validate the bundle on the device.

## Security notes

- If embeddings or user data are included in the bundle, encrypt them at rest
  (use `encryption.encrypt`) and/or use TPM sealing where available.
- Avoid shipping TPM-sealed blobs between devices — sealed blobs are bound to the
  originating TPM unless re-sealed.
# Voice-Activated SOC — Edge Deployment Notes

This document provides actionable instructions for deploying the voice-activated
SOC components on edge platforms such as the HiLens Kit and Atlas Edge 500.

Overview

- We support two primary deployment targets:
  - HiLens Kit (typically CPU/GPU with OpenVINO or HiAI runtime)
  - Atlas Edge 500 (Ascend NPU with .om runtime)
- The repo provides helper scripts in `backend/core/vocalsoc/` to produce
  transportable bundles: `deploy_hilens.py` and `deploy_atlas.py`.

Packaging

1. Ensure your runtime artifacts are present under `backend/core/vocalsoc`:
   - ASR model in IR format (.xml/.bin) for OpenVINO or .om for Ascend.
   - any vocab/lexicon files used by decoders.
   - `offline_cache_db/` and `voice_auth_db/` if you want to seed the device with data.

2. Use the helper scripts to create a deploy bundle:

   For HiLens:

       python -m backend.core.vocalsoc.deploy_hilens --out /tmp/vocalsoc_hilens.tar.gz

   For Atlas Edge 500:

       python -m backend.core.vocalsoc.deploy_atlas --out /tmp/vocalsoc_atlas.tar.gz

Model conversion

- MindSpore -> ONNX -> OpenVINO IR: export your MindSpore model to ONNX, then use
  OpenVINO Model Optimizer to generate IR (.xml/.bin).
- MindSpore -> .om (Ascend): use the Ascend ATC toolchain to convert models to .om.
- Quantization: run post-training quantization (INT8) or quant-aware training to
  reduce inference latency and memory usage.

On-device runtime

- HiLens: follow HiLens Studio or cloud console to upload the bundle. Provide an
  inference harness (preprocess/postprocess) that maps audio inputs to model inputs.
- Atlas Edge 500: copy the .om artifacts + runtime harness, then use Ascend runtime
  APIs to load and run inference on device.

Air-gapped transfer

- Use `cache_tool.export-pack` to create a tarball and checksum for transfer.
- On target, `cache_tool.import-verify` then `cache_tool apply` to atomically swap
  the incoming cache into place.

Testing and smoke checks

- Before deploying, run a smoke test on a representative audio file to verify
  preprocessing, model inference, and postprocessing.
- For HiLens/Atlas, ensure your inference harness includes small tests so the
  operator can validate the bundle on the device.

Security notes

- If embeddings or user data are included in the bundle, encrypt them at rest
  (use `encryption.encrypt`) and/or use TPM sealing where available.
- Avoid shipping TPM-sealed blobs between devices — sealed blobs are bound to the
  originating TPM unless re-sealed.
Voice-Activated SOC — Edge Deployment Notes
=========================================

This document provides actionable instructions for deploying the voice-activated
SOC components on edge platforms such as the HiLens Kit and Atlas Edge 500.

## Overview
- We support two primary deployment targets:
  - HiLens Kit (typically CPU/GPU with OpenVINO or HiAI runtime)
  - Atlas Edge 500 (Ascend NPU with .om runtime)
- The repo provides helper scripts in `backend/core/vocalsoc/` to produce
  transportable bundles: `deploy_hilens.py` and `deploy_atlas.py`.

## Packaging
1. Ensure your runtime artifacts are present under `backend/core/vocalsoc`:
   - ASR model in IR format (.xml/.bin) for OpenVINO or .om for Ascend.
   - any vocab/lexicon files used by decoders.
   - `offline_cache_db/` and `voice_auth_db/` if you want to seed the device with data.

2. Use the helper scripts to create a deploy bundle:

   For HiLens:
       python -m backend.core.vocalsoc.deploy_hilens --out /tmp/vocalsoc_hilens.tar.gz

   For Atlas Edge 500:
       python -m backend.core.vocalsoc.deploy_atlas --out /tmp/vocalsoc_atlas.tar.gz

## Model conversion
- MindSpore -> ONNX -> OpenVINO IR: export your MindSpore model to ONNX, then use
  OpenVINO Model Optimizer to generate IR (.xml/.bin).
- MindSpore -> .om (Ascend): use the Ascend ATC toolchain to convert models to .om.
- Quantization: run post-training quantization (INT8) or quant-aware training to
  reduce inference latency and memory usage.

## On-device runtime
- HiLens: follow HiLens Studio or cloud console to upload the bundle. Provide an
  inference harness (preprocess/postprocess) that maps audio inputs to model inputs.
- Atlas Edge 500: copy the .om artifacts + runtime harness, then use Ascend runtime
  APIs to load and run inference on device.

## Air-gapped transfer
- Use `cache_tool.export-pack` to create a tarball and checksum for transfer.
- On target, `cache_tool.import-verify` then `cache_tool apply` to atomically swap
  the incoming cache into place.

## Testing and smoke checks
- Before deploying, run a smoke test on a representative audio file to verify
  preprocessing, model inference, and postprocessing.
- For HiLens/Atlas, ensure your inference harness includes small tests so the
  operator can validate the bundle on the device.

## Security notes
- If embeddings or user data are included in the bundle, encrypt them at rest
  (use `encryption.encrypt`) and/or use TPM sealing where available.
- Avoid shipping TPM-sealed blobs between devices — sealed blobs are bound to the
  originating TPM unless re-sealed.
