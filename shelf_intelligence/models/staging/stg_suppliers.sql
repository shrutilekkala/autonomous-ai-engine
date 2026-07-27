select
    supplier_id,
    supplier_name,
    country,
    lead_time_days_avg,
    lead_time_days_std,
    reliability_score,
    min_order_qty,
    cast(contract_start as date) as contract_start,
    payment_terms_days
from {{ source('raw', 'raw_suppliers') }}