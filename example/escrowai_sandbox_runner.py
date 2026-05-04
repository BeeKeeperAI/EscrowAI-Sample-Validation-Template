# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BeekeeperAI, Inc. All rights reserved.
"""
================================================================================
 BeekeeperAI(R)  |  EscrowAI(R) Sandbox Runner
================================================================================

 Transparent console-logging wrapper for algorithms targeting the EscrowAI
 Trusted Execution Environment (TEE).

 Purpose
 -------
 When an algorithm runs inside an EscrowAI enclave it reports progress to the
 platform by calling `EnclaveSDK.LogApi.api_v1_log_post(...)`. Those messages
 are forwarded to the EscrowAI control plane but they are NOT printed locally,
 so developers testing in the Sandbox cannot see what their algorithm is doing
 without sprinkling `print()` / `logger` statements throughout their code.

 Adding such statements is undesirable because:
   * they must be removed (or conditionally gated) before the algorithm is
     shipped to a production TEE, and
   * they pollute the algorithm source with sandbox-only scaffolding.

 This runner solves the problem by monkey-patching `LogApi.api_v1_log_post`
 at import time so that every call is ALSO echoed to the local console. The
 user's algorithm source is never modified -- they simply invoke their script
 through this runner instead of invoking `python` directly.

 Usage
 -----
     python escrowai_sandbox_runner.py <your_algorithm.py> [args...]

 Example
 -------
     python escrowai_sandbox_runner.py preprocesswbknolog.py

 Scope & Restrictions
 --------------------
 SANDBOX-ONLY UTILITY. This runner is a developer convenience for use with
 the EscrowAI Sandbox environment only. It MUST NOT be packaged into, or
 executed inside, a production Trusted Execution Environment. The EscrowAI
 platform injects its own logging, data-protection, and audit pipelines
 inside the enclave; running this runner in that context would bypass
 platform-controlled telemetry and is unsupported.

 No Protected Health Information (PHI) or Personally Identifiable
 Information (PII) may be processed by any algorithm while this runner is
 active. The EscrowAI Sandbox is not an isolated TEE and provides no
 encryption or data-protection guarantees.

 License
 -------
 Licensed under the Apache License, Version 2.0 (the "License"); you may
 not use this file except in compliance with the License. You may obtain
 a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Disclaimer
 ----------
 THIS SOFTWARE IS PROVIDED BY BEEKEEPERAI, INC. "AS IS" AND ANY EXPRESS OR
 IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT
 ARE DISCLAIMED. IN NO EVENT SHALL BEEKEEPERAI, INC. BE LIABLE FOR ANY
 DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 SUCH DAMAGE.

 This runner is NOT a certified component of the EscrowAI platform and
 carries no certification, attestation, or compliance guarantees (HIPAA,
 GDPR, SOC 2, or otherwise). It is intended solely for local developer
 testing within the EscrowAI Sandbox.

 Trademarks
 ----------
 BeekeeperAI(R) and EscrowAI(R) are registered trademarks of BeekeeperAI,
 Inc. All other trademarks are the property of their respective owners.

 Third-Party Notices
 -------------------
 This runner uses only the Python standard library. Algorithms executed
 through this runner typically depend on the EnclaveSDK Python package,
 which is distributed separately under its own license terms. Refer to
 the EnclaveSDK package metadata for attribution and license details.
================================================================================
"""

import sys
import os
import runpy
import datetime


# ---------------------------------------------------------------------------
# Hook installer
# ---------------------------------------------------------------------------
# We patch `EnclaveSDK.LogApi.api_v1_log_post` at the CLASS level. Python
# caches imported modules in `sys.modules`, so every `import EnclaveSDK` (or
# `from EnclaveSDK import LogApi`) in the user's script -- including in any
# submodules or deeply nested packages -- resolves to the same class object
# we have patched here. Consequently every log post, regardless of where it
# originates in the user's codebase, will be echoed to the console.
# ---------------------------------------------------------------------------

def _install_log_hook() -> None:
    """
    Wrap `EnclaveSDK.LogApi.api_v1_log_post` so that every invocation prints
    a human-readable line to stderr in addition to posting to the EscrowAI
    sandbox API. stderr is used (rather than stdout) so the log stream stays
    separate from any data the algorithm itself may write to stdout.
    """
    import EnclaveSDK  # deferred import -- the SDK must be installed in the
                       # same environment the user's algorithm runs in

    # Keep a reference to the genuine method so we can still call through.
    _original_log_post = EnclaveSDK.LogApi.api_v1_log_post

    def _hooked_log_post(self, log_data, *args, **kwargs):
        # ------------------------------------------------------------------
        # Extract `message` and `status` from the LogData payload. We defend
        # against both the typed attribute form (LogData instance) and the
        # dict form (`to_dict()`) because different SDK versions may shape
        # the object slightly differently.
        # ------------------------------------------------------------------
        message = ""
        status = ""
        if hasattr(log_data, "message"):
            message = log_data.message or ""
        if hasattr(log_data, "status"):
            status = log_data.status or ""
        if not message and hasattr(log_data, "to_dict"):
            payload = log_data.to_dict()
            message = payload.get("message", "")
            status = status or payload.get("status", "")

        # Human-readable timestamp lets developers correlate console output
        # with wall-clock events (e.g. when watching the EscrowAI UI).
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [EscrowAI] [{status}] {message}",
              file=sys.stderr, flush=True)

        # Delegate to the real SDK method so the log still reaches the
        # sandbox API -- the hook is additive, not replacing.
        return _original_log_post(self, log_data, *args, **kwargs)

    EnclaveSDK.LogApi.api_v1_log_post = _hooked_log_post


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Basic argument validation.
    if len(sys.argv) < 2:
        print("Usage: python escrowai_sandbox_runner.py <script.py> [args...]",
              file=sys.stderr)
        sys.exit(1)

    script = sys.argv[1]

    if not os.path.isfile(script):
        print(f"[EscrowAI] Error: script '{script}' not found.",
              file=sys.stderr)
        sys.exit(1)

    # Install the hook BEFORE the user's code (or any of its imports) runs,
    # otherwise a submodule could theoretically snapshot the original method
    # before we have a chance to wrap it.
    _install_log_hook()

    # Present the user's script with a clean sys.argv so tools like argparse
    # behave exactly as if the script had been invoked via `python script.py`.
    sys.argv = sys.argv[1:]

    # Announce startup to the console for developer visibility.
    print(f"[EscrowAI] Sandbox runner starting '{script}' "
          f"at {datetime.datetime.now().isoformat(timespec='seconds')}",
          file=sys.stderr, flush=True)

    # `runpy.run_path` executes the target file as if it were `__main__`,
    # which preserves the standard `if __name__ == '__main__':` entry point
    # convention used by most EscrowAI example algorithms.
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()