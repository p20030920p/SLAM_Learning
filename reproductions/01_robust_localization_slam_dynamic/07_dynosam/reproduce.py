#!/usr/bin/env python3
"""01-07 · DynoSAM — recorded as blocked, with the reason machine-checkable.

This folder has no `run()` on purpose. DynoSAM is the one reproduction here whose
blocker is not data, not a missing library, and not taste - it is that the
upstream build **cannot be configured** without a CUDA toolchain, so there is
nothing to run and nothing to measure.

Evidence (full version in `work/feasibility.md`, gathered 2026-10-05 by reading
the checkout at commit 8c20caa):

  * `dynosam_nn/CMakeLists.txt:3`  project(dynosam_nn LANGUAGES C CXX CUDA)
  * `dynosam_nn/CMakeLists.txt:105` compiles a `.cu` source;
    `:128-129` link TensorRT and CUDA::cudart unconditionally.
    `DYNOSAM_NN_USE_TRT` (:31) only downgrades an error to a warning - it removes
    nothing from the build.
  * `dynosam/include/dynosam/frontend/vision/FeatureTracker.hpp:33` includes
    `<opencv2/cudaoptflow.hpp>` unconditionally, and `FeatureTracker.cc:60` calls
    `cv::cuda::SparsePyrLKOpticalFlow::create()` without the
    `DYNO_CUDA_OPENCV_ENABLED` guard the detector code does use.
  * `dynosam/CMakeLists.txt:32,143` - the core `dynosam` library needs
    `dynosam_nn`.
  * This machine: `nvcc` not found, no `/usr/local/cuda*`, no `NvInfer.h`,
    system OpenCV `cvconfig.h` says `/* #undef HAVE_CUDA */`.

Two things that look like escape hatches and are not:

  * **Runtime flags do not help.** The no-TensorRT path already exists and is the
    *default* (`config/FrontendParams.yaml:62 prefer_provided_object_detection:
    true`), and `feature_detector_type` can be set to `GFTT`. The block is at
    configure/compile time, before any of that matters.
  * **The dataset is not the blocker.** `data.acfr.usyd.edu.au` is an open index
    (no registration); OMD S4U is 552 frames, ~8.3 GB. Downloading it would be
    wasted work on this machine.

Reviving this folder needs a hardware change (a CUDA GPU) - not a code change
here. Forking the upstream to stub out CUDA would produce a pipeline the authors
never ran, so its ATE would not be their 0.11 m.
"""

from __future__ import annotations


def require(ctx):
    return ("GPU/CUDA absent, and DynoSAM cannot even `cmake`-configure without it: "
            "dynosam_nn/CMakeLists.txt:3 declares `LANGUAGES C CXX CUDA`, :105 compiles a "
            ".cu source, :128-129 link TensorRT + cudart unconditionally, and "
            "FeatureTracker.hpp:33 includes <opencv2/cudaoptflow.hpp> with no guard "
            "(nvcc/NvInfer.h/CUDA OpenCV are all absent here). Runtime flags cannot help - "
            "the no-TensorRT path is already the default. Evidence: work/feasibility.md. "
            "Needs a CUDA GPU, not data or code changes.")
