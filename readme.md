# Tax Form Annotation System

A production-ready system for annotating and rendering U.S. tax forms with pixel-perfect accuracy.

## Quick Start

```bash
# Install dependencies
pip install reportlab

# Run the renderer
python form_renderer.py
```

Output: `completed_form_1040.pdf`

## Features

✅ **Precise Positioning** - Absolute coordinates in points (1/72 inch)  
✅ **Nested Data Access** - JSONPath syntax: `taxpayer.name.first`, `income.wages.w2_forms[0].employer`  
✅ **Auto Formatting** - Currency, SSN masking, dates, checkboxes  
✅ **Validation** - Required fields, regex patterns, ranges  
✅ **Type Safe** - Python dataclasses with full type hints  

## File Structure

```
├── tax_annotation_system.py      # Core data models
├── form_renderer.py               # PDF generator
├── form_1040_annotation.json     # Example annotation
├── tax_data_2024.json            # Sample taxpayer data
└── SPECIFICATION.md              # Full documentation
```

## Example Usage

```python
from form_renderer import TaxFormRenderer

renderer = TaxFormRenderer(
    annotation_file='form_1040_annotation.json',
    data_file='tax_data_2024.json'
)

renderer.render_to_pdf('output.pdf')
```

## Key Design Decisions

**Absolute Positioning** - IRS forms require pixel-perfect accuracy  
**JSONPath Syntax** - Intuitive for deeply nested tax data  
**Separated Concerns** - Formatting, validation, and rendering are independent  

## Architecture

```
FormAnnotation
├── FormMetadata (form number, year, dimensions)
└── FieldAnnotation[] (position, formatting, validation)
    ├── Position (x, y, coordinate_system)
    ├── ValueReference (path to nested data)
    ├── FormattingRule (currency, dates, masks)
    └── ValidationRule[] (required, regex, range)
```

## Sample Annotation

```json
{
  "field_id": "1040_ssn",
  "position": {"x": 470, "y": 150},
  "dimensions": {"width": 120, "height": 20},
  "value_reference": {"path": "taxpayer.ssn"},
  "formatting": {
    "format_type": "mask",
    "parameters": {"pattern": "XXX-XX-####"}
  },
  "character_spacing": 8.5
}
```

## Requirements

- Python 3.8+
- reportlab 4.0+

## Documentation

See `SPECIFICATION.md` for complete technical documentation including:
- Full API reference
- Positioning system details
- Formatting options
- Validation rules
- Best practices

---