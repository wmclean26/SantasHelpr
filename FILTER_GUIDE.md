# eBay API Filter Reference Guide

## Updated `search_ebay()` Function

### All Available Parameters:

```python
search_ebay(
    query="search term",                    # Required
    price_range="min..max",                 # Optional: e.g., "10..50"
    condition_filter="NEW|USED",            # Optional: condition names or IDs
    delivery_country="US",                  # Optional: 2-letter country code
    delivery_postal_code="90210",           # Optional: ZIP/postal code
    guaranteed_delivery_days=3,             # Optional: days for guaranteed delivery
    max_delivery_cost=0,                    # Optional: 0 for free shipping
    sort_by="price"                         # Optional: sort option
)
```

---

## Condition Names

Use condition **names** instead of numeric IDs:

| Condition Name | ID | Description |
|----------------|-----|-------------|
| `NEW` | 1000 | Brand new item |
| `LIKE_NEW` | 1500 | Like new |
| `NEW_OTHER` | 1750 | New with minor imperfections |
| `CERTIFIED_REFURBISHED` | 2000 | Certified refurbished |
| `SELLER_REFURBISHED` | 2500 | Seller refurbished |
| `USED` | 3000 | Used condition |
| `VERY_GOOD` | 4000 | Very good used |
| `GOOD` | 5000 | Good used |
| `ACCEPTABLE` | 6000 | Acceptable used |
| `FOR_PARTS_OR_NOT_WORKING` | 7000 | For parts/not working |

**Examples:**
```python
condition_filter="NEW"              # New items only
condition_filter="NEW|USED"         # New or used
condition_filter="1000|3000"        # Can still use IDs
```

---

## Delivery Location Filters

### `delivery_country`
- 2-letter ISO country code
- Examples: `"US"`, `"GB"`, `"CA"`, `"AU"`
- Shows items that ship to that country
- Affects shipping cost calculations

### `delivery_postal_code`
- Must be used with `delivery_country`
- Provides accurate shipping costs for specific location
- Examples: `"10001"` (NYC), `"90210"` (Beverly Hills), `"60601"` (Chicago)

**Example:**
```python
# Items deliverable to Los Angeles
search_ebay(
    query="laptop",
    delivery_country="US",
    delivery_postal_code="90001"
)
```

**Benefits:**
- More accurate shipping costs
- Better delivery time estimates
- Can combine with `sort="distance"` for nearest items

---

## Shipping Filters

### `max_delivery_cost`
- Maximum acceptable shipping cost
- Use `0` for **FREE SHIPPING only**
- Use float for max cost: `5.00`, `10.99`

**Examples:**
```python
max_delivery_cost=0      # Free shipping only
max_delivery_cost=5.00   # Shipping $5 or less
max_delivery_cost=10.99  # Shipping $10.99 or less
```

### `guaranteed_delivery_days`
- Filter by guaranteed delivery time
- Requires both `delivery_country` AND `delivery_postal_code`
- Integer value (e.g., `1`, `2`, `3`, `5`)

**Example:**
```python
# Get within 3 days to NYC
search_ebay(
    query="gaming keyboard",
    delivery_country="US",
    delivery_postal_code="10001",
    guaranteed_delivery_days=3
)
```

---

## Sort Options

### `sort_by` parameter values:

| Value | Description |
|-------|-------------|
| `"price"` | Price: Low to High (default) |
| `"-price"` | Price: High to Low |
| `"distance"` | Nearest items first (requires delivery location) |
| `"newlyListed"` | Newest listings first |

**Examples:**
```python
sort_by="price"         # Cheapest first
sort_by="-price"        # Most expensive first
sort_by="newlyListed"   # Latest listings first
sort_by="distance"      # Nearest (needs delivery_postal_code)
```

---

## Example Use Cases

### 1. Budget Shopping with Free Shipping
```python
search_ebay(
    query="wireless mouse",
    price_range="10..30",
    condition_filter="NEW",
    max_delivery_cost=0,
    sort_by="price"
)
```

### 2. Quick Delivery to Specific Location
```python
search_ebay(
    query="birthday gift",
    price_range="20..100",
    delivery_country="US",
    delivery_postal_code="60601",
    guaranteed_delivery_days=2,
    sort_by="price"
)
```

### 3. Local Deals (Nearest First)
```python
search_ebay(
    query="furniture",
    price_range="50..500",
    delivery_country="US",
    delivery_postal_code="90001",
    max_delivery_cost=20,
    sort_by="distance"  # Closest items first
)
```

### 4. Best Deals (Any Condition)
```python
search_ebay(
    query="iPhone 13",
    price_range="300..600",
    condition_filter="NEW|CERTIFIED_REFURBISHED|USED",
    max_delivery_cost=0,
    sort_by="price"
)
```

### 5. High-End Shopping
```python
search_ebay(
    query="designer watch",
    price_range="1000..5000",
    condition_filter="NEW",
    delivery_country="US",
    delivery_postal_code="10001",
    sort_by="-price"  # Most expensive first
)
```

---

## Headers Enhancement

When using delivery location, the function automatically adds the `X-EBAY-C-ENDUSERCTX` header:

```python
# Automatically added if delivery_country + delivery_postal_code provided
headers["X-EBAY-C-ENDUSERCTX"] = "contextualLocation=country%3DUS%2Czip%3D90210"
```

This provides:
- More accurate shipping costs
- Better delivery estimates
- Improved search relevance

---

## Testing

Run the test script to see all features in action:

```bash
python test_new_filters.py
```

This will test:
1. ✅ Condition names (NEW, USED, etc.)
2. ✅ Free shipping filter
3. ✅ Delivery location filtering
4. ✅ Guaranteed delivery days
5. ✅ Sort options (price ascending/descending)
6. ✅ Combined filters

---

## Integration Examples

### Update `integration.py`:
```python
from EbayAPI.ebay_call import search_ebay, display_results

# Ask user for filters
product = input("Product name: ")
min_price = input("Min price (or blank): ")
max_price = input("Max price (or blank): ")
free_shipping = input("Free shipping only? (y/n): ").lower() == 'y'
zip_code = input("Your ZIP code (optional): ")

# Search with filters
results = search_ebay(
    query=product,
    price_range=f"{min_price or ''}..{max_price or ''}",
    condition_filter="NEW|USED",
    delivery_country="US" if zip_code else None,
    delivery_postal_code=zip_code if zip_code else None,
    max_delivery_cost=0 if free_shipping else None,
    sort_by="price"
)

formatted = display_results(results)
```

### Update GUI with new options:
```python
# Add to gui_with_images.py
self.free_shipping_var = tk.BooleanVar()
ttk.Checkbutton(search_frame, text="Free Shipping Only", 
                variable=self.free_shipping_var).grid(...)

self.zip_entry = ttk.Entry(search_frame)
ttk.Label(search_frame, text="ZIP:").grid(...)
self.zip_entry.grid(...)

# In search function:
results = search_ebay(
    query=product,
    price_range=f"{min_price}..{max_price}",
    condition_filter="NEW|USED",
    delivery_country="US" if self.zip_entry.get() else None,
    delivery_postal_code=self.zip_entry.get() if self.zip_entry.get() else None,
    max_delivery_cost=0 if self.free_shipping_var.get() else None,
    sort_by="price"
)
```

---

## Notes

- **Condition filter**: Can mix names and IDs (e.g., `"NEW|3000"`)
- **Guaranteed delivery**: Only works with both country AND postal code
- **Sort by distance**: Requires delivery location to be meaningful
- **Free shipping**: `max_delivery_cost=0` is very effective
- **Multiple conditions**: Use `|` separator (e.g., `"NEW|USED|CERTIFIED_REFURBISHED"`)
