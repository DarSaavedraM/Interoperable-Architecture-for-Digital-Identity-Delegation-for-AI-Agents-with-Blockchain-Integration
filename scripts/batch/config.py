"""
Configuration for batch request generation and metrics collection.
"""

# Random seed for reproducibility
RANDOM_SEED = 42

# Number of requests to generate
# 1200 requests provides optimal sample size for robust descriptive statistics:
# - 75 observations per cell for depth>0 (sufficient for P95/P99 percentiles)
# - 300 observations per cell for depth=0 (more than sufficient)
NUM_REQUESTS = 1200

# Profile distribution (balanced for statistical comparison)
PROFILE_DISTRIBUTION = {
    "VC-JWT": 0.5,  # 50% VC-JWT
    "VC-LD": 0.5    # 50% VC-LD
}

# Chain depth distribution (balanced for statistical analysis)
CHAIN_DEPTH_DISTRIBUTION = {
    0: 0.25,  # 25% no delegation
    1: 0.25,  # 25% depth 1
    2: 0.25,  # 25% depth 2
    3: 0.25   # 25% depth 3
}

# Blockchain anchor distribution (when enabled)
ANCHOR_DISTRIBUTION = {
    True: 0.5,   # 50% with require_anchor: true
    False: 0.5   # 50% with require_anchor: false
}

# Available actions for scope variation
AVAILABLE_ACTIONS = ["initiate", "quote", "approve", "cancel", "view"]
SCOPE_RESOURCES = ["payments:transfer", "payments:withdrawal", "account:access"]

# Policy IDs
POLICY_WITHOUT_ANCHOR = "P-001"
POLICY_WITH_ANCHOR = "P-001-ANCHOR"  # Will be normalized to P001ANCHOR

