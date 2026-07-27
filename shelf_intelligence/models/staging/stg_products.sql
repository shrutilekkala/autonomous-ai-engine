select
    sku_id,
    product_name,
    brand,
    category,
    subcategory,
    unit_price,
    unit_cost,
    unit_weight_g,
    shelf_life_days,
    is_perishable,
    supplier_id,
    barcode,
    pack_size,
    reorder_point,
    safety_stock
from {{ source('raw', 'raw_products') }}