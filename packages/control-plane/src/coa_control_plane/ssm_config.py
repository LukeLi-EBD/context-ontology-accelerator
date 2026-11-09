# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""SSM-backed configuration lookups for SMUS.

The SSM client now comes from the ``ConfigProvider`` port (provider ``ssm``),
resolved per call exactly like the previous ``boto3.client`` call: no shared
client is created and no default provider is assumed. A missing
``COA_PROVIDER_CONFIG`` raises the catalog's configuration error on first use.
"""

from __future__ import annotations

import os

from coa_runtime.registry import resolve
from coa_runtime.settings import Settings


def get_smus_domain_id(ssm_prefix: str, region_name: str | None = None) -> str:
    """Read the SMUS domain ID from SSM Parameter Store.

    Args:
        ssm_prefix: SSM path prefix (e.g. ``/coa``).
        region_name: Overrides ``AWS_REGION`` for this lookup. Omitted means
            the environment's region, as before.

    Returns:
        The SMUS domain ID string.

    Raises:
        ValueError: if the parameter is missing or empty.
        coa_runtime.errors.ConfigurationError: if no ``ConfigProvider`` is
            configured.
        coa_ports.PortError: if reading the parameter fails (as opposed to
            the parameter being absent).
    """
    param_name = f"{ssm_prefix}/smus/domain-id"
    environment = dict(os.environ)
    if region_name:
        environment["AWS_REGION"] = region_name
    provider = resolve("ConfigProvider", Settings(environment)).instance
    value = provider.get(param_name)
    if not value:
        raise ValueError(f"SMUS domain ID not found at SSM parameter: {param_name}")
    return value
