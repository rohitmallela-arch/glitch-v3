# Centralized collection names to prevent drift.

COL_SYSTEM = "system"
DOC_INGEST_STATE = "shortage_ingest_state"

COL_USERS = "users"
COL_SUBSCRIPTIONS = "subscriptions"
COL_WATCHLISTS = "watchlists"  # watchlists/{user_id}/items/{ndc_digits}
COL_NDC_INDEX = "ndc_index"
COL_SHORTAGES = "shortages"
COL_SHORTAGE_VARIANTS = "variants"  # shortages/{ndc}/variants/{variant_key}
COL_ALERTS = "alerts"
COL_DELIVERY_LOGS = "delivery_logs"
COL_WEEKLY_RECAPS = "weekly_recaps"


# Watcher index: ndc_watchers/{ndc_digits}/watchers/{user_id}
COL_NDC_WATCHERS = "ndc_watchers"

# Manual override: ndc_alias_overrides/{ndc_digits}
COL_NDC_ALIAS_OVERRIDES = "ndc_alias_overrides"
