# Tax Form Annotation System - Technical Specification

## Overview

A JSON-based annotation system for mapping taxpayer data to U.S. tax form fields with precise positioning and automatic formatting.

---

## Core Data Structure

### FormAnnotation (Root)

```json
{
  "version": "1.0.0",
  "metadata": { /* FormMetadata */ },
  "fields": [ /* Array of FieldAnnotation */ ]
}
```

### FormMetadata

```json
{
  "form_number": "1040",
  "form_name": "U.S. Individual Income Tax Return",
  "tax_year": 2024,
  "page_dimensions": {
    "1": {"width": 612, "height": 792}
  }
}
```

### FieldAnnotation

```json
{
  "field_id": "1040_line1_wages",
  "field_type": "currency",
  "position": {"x": 480, "y": 350, "coordinate_system": "absolute"},
  "dimensions": {"width": 110, "height": 18},
  "value_reference": {"path": "income.wages.total", "default_value": "0.00"},
  "alignment": "right",
  "font_style": {"font_family": "Courier", "font_size": 10},
  "formatting": { /* FormattingRule */ },
  "validation": [ /* ValidationRule[] */ ],
  "required": true
}
```

---

## Positioning System

### Absolute Coordinates (Recommended)

- **Unit:** Points (1/72 inch)
- **Origin:** Top-left (0, 0)
- **Letter Size:** 612 × 792 points

```json
{
  "position": {"x": 50, "y": 150, "coordinate_system": "absolute"},
  "dimensions": {"width": 200, "height": 20}
}
```

### Percentage Coordinates

```json
{
  "position": {"x": 8.2, "y": 18.9, "coordinate_system": "percentage"}
}
```

---

## Value Reference (Nested Data Access)

Uses JSONPath-like dot notation:

```json
{
  "path": "taxpayer.name.first",
  "default_value": null
}
```

### Examples

| Path | Accesses |
|------|----------|
| `taxpayer.ssn` | Simple nested object |
| `income.wages.w2_forms[0].employer` | Array element |
| `deductions.itemized.medical.total` | Deep nesting |

### Resolution Algorithm

1. Split path by `.` delimiter
2. Handle array indices with `[n]` notation
3. Traverse object tree
4. Return value or default if not found

---

## Field Types

| Type | Description | Example |
|------|-------------|---------|
| `text` | Plain text | Name, address |
| `currency` | Dollar amounts | $95,000.00 |
| `ssn` | Social Security Number | 123-45-6789 |
| `date` | Dates | 04/15/2025 |
| `checkbox` | True/false | X or blank |
| `number` | Numeric values | 2 (dependents) |
| `percentage` | Percentages | 22.5% |

---

## Formatting Rules

### Currency

```json
{
  "format_type": "currency",
  "parameters": {
    "decimal_places": 2,
    "thousands_separator": ",",
    "currency_symbol": "$",
    "negative_format": "parentheses"
  }
}
```

**Input:** `95000` → **Output:** `$95,000.00`

### SSN/EIN Masking

```json
{
  "format_type": "mask",
  "parameters": {"pattern": "XXX-XX-####"}
}
```

**Input:** `123456789` → **Output:** `123-45-6789`

### Date

```json
{
  "format_type": "date",
  "parameters": {
    "format": "MM/DD/YYYY",
    "input_format": "ISO8601"
  }
}
```

**Input:** `2025-04-15` → **Output:** `04/15/2025`

### Checkbox

```json
{
  "format_type": "checkbox",
  "parameters": {
    "checked_symbol": "X",
    "unchecked_symbol": ""
  }
}
```

---

## Validation Rules

### Required

```json
{
  "rule_type": "required",
  "parameters": {},
  "error_message": "This field is required"
}
```

### Regex

```json
{
  "rule_type": "regex",
  "parameters": {"pattern": "^\\d{3}-\\d{2}-\\d{4}$"},
  "error_message": "SSN must be in format XXX-XX-XXXX"
}
```

### Range

```json
{
  "rule_type": "range",
  "parameters": {"min": 0, "max": 999999999.99},
  "error_message": "Amount must be between 0 and 999,999,999.99"
}
```

### Length

```json
{
  "rule_type": "length",
  "parameters": {"min_length": 1, "max_length": 50}
}
```

---

## Alignment & Overflow

### Alignment Options

- `left` - Left-aligned text
- `right` - Right-aligned (common for currency)
- `center` - Centered (common for checkboxes)

### Overflow Behavior

- `truncate` - Cut text at max_length
- `shrink` - Reduce font size to fit
- `wrap` - Multi-line (future)
- `error` - Throw validation error

---

## Special Features

### Character Spacing (for SSN boxes)

```json
{
  "character_spacing": 8.5,
  "formatting": {"format_type": "mask", "parameters": {"pattern": "XXX-XX-####"}}
}
```

Renders each digit with fixed spacing for individual boxes.

### Padding

```json
{
  "padding": {"top": 2, "right": 3, "bottom": 2, "left": 2}
}
```

Inner spacing from field box edges (in points).

---

## Complete Example

### Annotation

```json
{
  "field_id": "1040_ssn",
  "field_type": "ssn",
  "position": {"x": 470, "y": 150, "coordinate_system": "absolute"},
  "dimensions": {"width": 120, "height": 20},
  "value_reference": {"path": "taxpayer.ssn"},
  "alignment": "center",
  "character_spacing": 8.5,
  "formatting": {
    "format_type": "mask",
    "parameters": {"pattern": "XXX-XX-####"}
  },
  "validation": [
    {
      "rule_type": "required",
      "error_message": "SSN is required"
    }
  ]
}
```

### Tax Data

```json
{
  "taxpayer": {
    "name": {"first": "John", "last": "Doe"},
    "ssn": "123-45-6789"
  }
}
```

### Result

The value `123-45-6789` is rendered at position (470, 150) with character spacing of 8.5 points.

---

## Implementation Guide

### Step 1: Load Files

```python
import json

with open('annotation.json') as f:
    annotation = json.load(f)

with open('data.json') as f:
    data = json.load(f)
```

### Step 2: Resolve Value Reference

```python
def resolve_path(data, path):
    keys = path.split('.')
    value = data
    for key in keys:
        if '[' in key:  # Handle arrays
            base = key[:key.index('[')]
            index = int(key[key.index('[')+1:key.index(']')])
            value = value[base][index]
        else:
            value = value[key]
    return value
```

### Step 3: Apply Formatting

```python
def format_currency(value, params):
    formatted = f"{float(value):,.{params['decimal_places']}f}"
    return f"{params['currency_symbol']}{formatted}"
```

### Step 4: Render to PDF

```python
from reportlab.pdfgen import canvas

c = canvas.Canvas("output.pdf")
c.setFont("Courier", 10)
c.drawString(x, y, formatted_value)
c.save()
```
