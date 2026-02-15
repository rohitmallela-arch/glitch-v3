# Firestore Schema (Glitch v2)

## system/shortage_ingest_state
Tracks baseline completion and last sweep metrics.
- baseline_completed: bool
- baseline_completed_at: timestamp
- last_sweep_mode: "baseline" | "delta"
- last_sweep_total_processed: int
- last_sweep_changed: int
- last_sweep_started_at: timestamp (iso)
- last_sweep_completed_at: timestamp (iso)

## users/{user_id}
- email: string
- phone: string
- telegram_chat_id: string
- created_at: timestamp

## subscriptions/{user_id}
Single-plan subscription state.
- status: "active" | "inactive" | ...
- stripe_customer_id: string
- stripe_subscription_id: string
- last_event_id: string
- last_event_type: string

## watchlists/{user_id}/items/{ndc_digits}
- ndc_digits: string
- added_at: string
- brand_name: string
- generic_name: string

## ndc_index/{ndc_digits}
DailyMed-derived index.
- ndc_digits: string
- brand_name: string
- generic_name: string
- manufacturer: string
- spl_xml_source: string
- source: "dailymed_bulk"
- updated_at: string (iso)

## shortages/{ndc_digits}
- ndc_digits: string
- status: string
- last_updated: string
- shortage_start_date: string
- shortage_end_date: string
- reason: string
- resolution: string
- presentation: string
- brand_name: string
- generic_name: string
- manufacturer: string
- snapshot_hash: string
- source: "openfda"
- updated_at: string (iso)

## alerts/{alert_id}
- user_id: string
- channel: "telegram" | "sms"
- ndc_digits: string
- old_status: string
- new_status: string
- ok: bool
- created_at: string (iso)

## delivery_logs/{log_id}
- user_id: string
- channel: string
- ndc_digits: string
- ok: bool
- resp: object
- created_at: string (iso)


## ndc_watchers/{ndc_digits}/watchers/{user_id}
Reverse index for alert fanout.
- user_id: string

## ndc_alias_overrides/{ndc_digits}
Manual naming overrides.
- brand_name: string
- generic_name: string
- manufacturer: string
- updated_at: string

## users/{user_id}/rate_limits/{YYYYMMDD}
Transactional quota reservation.
- alerts_sent_total: int
- alerts_sent_by_ndc: map<string,int>
- updated_at: string
