"""
Tax Form Renderer - Complete Implementation
Renders tax data onto PDF forms using annotation specifications
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class TaxFormRenderer:
    """
    Main class for rendering tax forms from annotations and data.
    """
    
    def __init__(self, annotation_file: str, data_file: str):
        """
        Initialize renderer with annotation and data files.
        
        Args:
            annotation_file: Path to JSON annotation file
            data_file: Path to JSON tax data file
        """
        with open(annotation_file, 'r') as f:
            self.annotation = json.load(f)
        
        with open(data_file, 'r') as f:
            self.data = json.load(f)
        
        self.errors = []
        self.warnings = []
    
    def resolve_value_reference(self, path: str, default: Any = None) -> Any:
        """
        Resolve a JSONPath-like reference to a value in nested data.
        
        Args:
            path: Dot-separated path (e.g., "taxpayer.name.first")
            default: Default value if path not found
            
        Returns:
            Resolved value or default
            
        Examples:
            "taxpayer.name.first" -> "John"
            "income.wages[0].amount" -> 50000
            "deductions.itemized.medical.total" -> 5000.50
        """
        if not path or path == "":
            return default
        
        keys = path.split('.')
        value = self.data
        
        try:
            for key in keys:
                # Handle array indices [n]
                if '[' in key and ']' in key:
                    base_key = key[:key.index('[')]
                    index = int(key[key.index('[')+1:key.index(']')])
                    value = value.get(base_key, [])[index]
                else:
                    value = value.get(key)
                    
                if value is None:
                    return default
            
            return value
        except (KeyError, IndexError, TypeError, AttributeError):
            return default
    
    def format_value(self, value: Any, formatting: Optional[Dict]) -> str:
        """
        Apply formatting rules to a value.
        
        Args:
            value: Raw value to format
            formatting: Formatting rule dictionary
            
        Returns:
            Formatted string
        """
        if value is None:
            return ""
        
        if not formatting:
            return str(value)
        
        format_type = formatting.get('format_type', '')
        params = formatting.get('parameters', {})
        
        if format_type == 'currency':
            return self._format_currency(value, params)
        elif format_type == 'mask':
            return self._format_mask(value, params)
        elif format_type == 'date':
            return self._format_date(value, params)
        elif format_type == 'percentage':
            return self._format_percentage(value, params)
        elif format_type == 'checkbox':
            return self._format_checkbox(value, params)
        else:
            return str(value)
    
    def _format_currency(self, value: Union[int, float], params: Dict) -> str:
        """Format currency values"""
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return "0.00"
        
        decimal_places = params.get('decimal_places', 2)
        show_cents = params.get('show_cents', True)
        symbol = params.get('currency_symbol', '$')
        separator = params.get('thousands_separator', ',')
        negative_format = params.get('negative_format', 'parentheses')
        
        # Handle negative values
        is_negative = num_value < 0
        num_value = abs(num_value)
        
        # Format with thousands separator
        if show_cents:
            formatted = f"{num_value:,.{decimal_places}f}"
        else:
            formatted = f"{int(num_value):,}"
        
        # Add currency symbol
        if symbol:
            formatted = f"{symbol}{formatted}"
        
        # Handle negative formatting
        if is_negative:
            if negative_format == 'parentheses':
                formatted = f"({formatted})"
            else:
                formatted = f"-{formatted}"
        
        return formatted
    
    def _format_mask(self, value: str, params: Dict) -> str:
        """Format masked values (SSN, EIN, etc.)"""
        pattern = params.get('pattern', '')
        value_str = str(value).replace('-', '').replace(' ', '')
        
        result = ""
        val_idx = 0
        
        for char in pattern:
            if char in ['#', 'X']:
                if val_idx < len(value_str):
                    result += value_str[val_idx]
                    val_idx += 1
            else:
                result += char
        
        return result
    
    def _format_date(self, value: str, params: Dict) -> str:
        """Format date values"""
        output_format = params.get('format', 'MM/DD/YYYY')
        input_format = params.get('input_format', 'ISO8601')
        
        try:
            if input_format == 'ISO8601':
                date_obj = datetime.fromisoformat(value)
            else:
                date_obj = datetime.strptime(value, input_format)
            
            # Convert to output format
            if output_format == 'MM/DD/YYYY':
                return date_obj.strftime('%m/%d/%Y')
            elif output_format == 'DD/MM/YYYY':
                return date_obj.strftime('%d/%m/%Y')
            elif output_format == 'YYYY-MM-DD':
                return date_obj.strftime('%Y-%m-%d')
            else:
                return date_obj.strftime(output_format)
        except (ValueError, AttributeError):
            return str(value)
    
    def _format_percentage(self, value: Union[int, float], params: Dict) -> str:
        """Format percentage values"""
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return "0.00%"
        
        decimal_places = params.get('decimal_places', 2)
        multiply_by_100 = params.get('multiply_by_100', True)
        show_symbol = params.get('show_symbol', True)
        
        if multiply_by_100:
            num_value *= 100
        
        formatted = f"{num_value:.{decimal_places}f}"
        
        if show_symbol:
            formatted += "%"
        
        return formatted
    
    def _format_checkbox(self, value: Any, params: Dict) -> str:
        """Format checkbox values"""
        checked_symbol = params.get('checked_symbol', 'X')
        unchecked_symbol = params.get('unchecked_symbol', '')
        
        # Convert value to boolean
        is_checked = False
        if isinstance(value, bool):
            is_checked = value
        elif isinstance(value, str):
            is_checked = value.lower() in ['true', 'yes', '1', 'x']
        elif isinstance(value, (int, float)):
            is_checked = value != 0
        
        return checked_symbol if is_checked else unchecked_symbol
    
    def validate_value(self, value: Any, validations: List[Dict]) -> List[str]:
        """
        Validate value against validation rules.
        
        Args:
            value: Value to validate
            validations: List of validation rule dictionaries
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        for validation in validations:
            rule_type = validation.get('rule_type', '')
            params = validation.get('parameters', {})
            error_msg = validation.get('error_message', f'{rule_type} validation failed')
            
            if rule_type == 'required':
                if value is None or str(value).strip() == '':
                    errors.append(error_msg)
            
            elif rule_type == 'regex':
                pattern = params.get('pattern', '')
                if not re.match(pattern, str(value)):
                    errors.append(error_msg)
            
            elif rule_type == 'range':
                try:
                    num_value = float(value)
                    min_val = params.get('min')
                    max_val = params.get('max')
                    
                    if min_val is not None and num_value < min_val:
                        errors.append(error_msg)
                    if max_val is not None and num_value > max_val:
                        errors.append(error_msg)
                except (ValueError, TypeError):
                    errors.append(f"Value must be numeric for range validation")
            
            elif rule_type == 'length':
                min_length = params.get('min_length', 0)
                max_length = params.get('max_length', float('inf'))
                length = len(str(value))
                
                if not (min_length <= length <= max_length):
                    errors.append(error_msg)
        
        return errors
    
    def render_to_pdf(self, output_file: str, show_debug_boxes: bool = False):
        """
        Render the complete form to PDF.
        
        Args:
            output_file: Path to output PDF file
            show_debug_boxes: If True, draw field boundary boxes
        """
        c = canvas.Canvas(output_file, pagesize=letter)
        
        metadata = self.annotation.get('metadata', {})
        fields = self.annotation.get('fields', [])
        
        # Group fields by page
        pages = {}
        for field in fields:
            page_num = field.get('page_number', 1)
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(field)
        
        # Render each page
        for page_num in sorted(pages.keys()):
            page_fields = pages[page_num]
            
            # Set page dimensions if specified
            page_dims = metadata.get('page_dimensions', {}).get(str(page_num))
            if page_dims:
                c.setPageSize((page_dims['width'], page_dims['height']))
            else:
                c.setPageSize(letter)
            
            # Render fields on this page
            for field in page_fields:
                self._render_field(c, field, show_debug_boxes)
            
            c.showPage()
        
        c.save()
        
        print(f"\n✓ PDF generated: {output_file}")
        
        if self.errors:
            print(f"\n⚠ {len(self.errors)} errors encountered:")
            for error in self.errors[:10]:  # Show first 10
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠ {len(self.warnings)} warnings:")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  - {warning}")
    
    def _render_field(self, c: canvas.Canvas, field: Dict, show_debug: bool):
        """Render a single field on the canvas"""
        field_id = field.get('field_id', 'unknown')
        
        # Resolve value
        value_ref = field.get('value_reference', {})
        path = value_ref.get('path', '')
        default = value_ref.get('default_value')
        
        value = self.resolve_value_reference(path, default)
        
        # Skip if no value and not required
        if value is None and not field.get('required', False):
            return
        
        # Validate
        validations = field.get('validation', [])
        validation_errors = self.validate_value(value, validations)
        if validation_errors:
            self.errors.extend([f"{field_id}: {err}" for err in validation_errors])
            if field.get('required', False):
                return  # Skip rendering if required field fails validation
        
        # Format value
        formatting = field.get('formatting')
        formatted_value = self.format_value(value, formatting)
        
        # Get positioning and dimensions
        position = field.get('position', {})
        dimensions = field.get('dimensions', {})
        padding = field.get('padding', {'top': 0, 'right': 2, 'bottom': 0, 'left': 2})
        
        x = position.get('x', 0)
        y = position.get('y', 0)
        width = dimensions.get('width', 100)
        height = dimensions.get('height', 20)
        
        # Convert percentage coordinates if needed
        coord_system = position.get('coordinate_system', 'absolute')
        if coord_system == 'percentage':
            page_width, page_height = c._pagesize
            x = (x / 100) * page_width
            y = (y / 100) * page_height
            width = (width / 100) * page_width
            height = (height / 100) * page_height
        
        # Convert Y coordinate (PDF origin is bottom-left, we use top-left)
        page_width, page_height = c._pagesize
        y = page_height - y - height
        
        # Set font
        font_style = field.get('font_style', {})
        font_family = font_style.get('font_family', 'Courier')
        font_size = font_style.get('font_size', 10)
        
        # Map font family names
        font_map = {
            'Courier': 'Courier',
            'Helvetica': 'Helvetica',
            'Times-Roman': 'Times-Roman'
        }
        font_family = font_map.get(font_family, 'Courier')
        
        c.setFont(font_family, font_size)
        
        # Debug: Draw field box
        if show_debug:
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.setLineWidth(0.5)
            c.rect(x, y, width, height, stroke=1, fill=0)
        
        # Handle character spacing (for SSN, EIN, etc.)
        character_spacing = field.get('character_spacing')
        if character_spacing:
            self._render_character_spaced(
                c, formatted_value, x + padding['left'], 
                y + height/2, character_spacing
            )
            return
        
        # Calculate text position based on alignment
        alignment = field.get('alignment', 'left')
        text_width = c.stringWidth(formatted_value, font_family, font_size)
        text_x = x + padding['left']
        
        if alignment == 'right':
            text_x = x + width - text_width - padding['right']
        elif alignment == 'center':
            text_x = x + (width - text_width) / 2
        
        # Handle overflow
        overflow = field.get('overflow_behavior', 'truncate')
        if overflow == 'shrink' and text_width > (width - padding['left'] - padding['right']):
            # Shrink font to fit
            scale = (width - padding['left'] - padding['right']) / text_width
            new_size = font_size * scale * 0.95  # 95% to add small margin
            c.setFont(font_family, new_size)
            text_width = c.stringWidth(formatted_value, font_family, new_size)
            
            # Recalculate position
            if alignment == 'right':
                text_x = x + width - text_width - padding['right']
            elif alignment == 'center':
                text_x = x + (width - text_width) / 2
        
        elif overflow == 'truncate':
            max_length = field.get('max_length')
            if max_length and len(formatted_value) > max_length:
                formatted_value = formatted_value[:max_length]
                self.warnings.append(f"{field_id}: Value truncated to {max_length} characters")
        
        # Render text (vertically centered in box)
        text_y = y + (height - font_size) / 2 + font_size * 0.3
        c.drawString(text_x, text_y, formatted_value)
    
    def _render_character_spaced(self, c: canvas.Canvas, text: str, 
                                 x: float, y: float, spacing: float):
        """Render text with fixed character spacing (for SSN boxes, etc.)"""
        current_x = x
        for char in text:
            if char not in ['-', ' ']:  # Skip separators
                c.drawString(current_x, y, char)
                current_x += spacing


# Example usage
if __name__ == "__main__":
    # Create renderer
    renderer = TaxFormRenderer(
        annotation_file='form_1040_annotation.json',
        data_file='tax_data_2024.json'
    )
    
    # Render to PDF
    renderer.render_to_pdf(
        output_file='completed_form_1040.pdf',
        show_debug_boxes=False  # Set to True to see field boundaries
    )
    
    print("\n" + "="*60)
    print("Form rendering complete!")
    print("="*60)