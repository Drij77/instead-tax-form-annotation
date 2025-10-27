from typing import List, Dict, Optional, Union, Literal
from dataclasses import dataclass, field
from enum import Enum
import json

class FieldType(Enum):
    """Types of form fields"""
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    SSN = "ssn"
    CHECKBOX = "checkbox"
    SIGNATURE = "signature"
    EIN = "ein"
    PERCENTAGE = "percentage"

class AlignmentType(Enum):
    """Text alignment options"""
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"

class CoordinateSystem(Enum):
    """Coordinate system types"""
    ABSOLUTE = "absolute"  # Fixed pixels from origin
    PERCENTAGE = "percentage"  # Percentage of page dimensions

@dataclass
class Position:
    """
    Position on the form page.
    Supports both absolute (pixels) and percentage-based positioning.
    Origin is top-left corner (0,0).
    """
    x: float
    y: float
    coordinate_system: CoordinateSystem = CoordinateSystem.ABSOLUTE
    
    def to_dict(self) -> Dict:
        return {
            "x": self.x,
            "y": self.y,
            "coordinate_system": self.coordinate_system.value
        }

@dataclass
class Dimensions:
    """Width and height of a field box"""
    width: float
    height: float
    
    def to_dict(self) -> Dict:
        return {
            "width": self.width,
            "height": self.height
        }

@dataclass
class FontStyle:
    """Font styling options for rendering text"""
    font_family: str = "Courier"
    font_size: int = 10
    bold: bool = False
    italic: bool = False
    color: str = "#000000"  # Hex color code
    
    def to_dict(self) -> Dict:
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "bold": self.bold,
            "italic": self.italic,
            "color": self.color
        }

@dataclass
class ValueReference:
    """
    Reference to a value in a nested data structure.
    Uses JSONPath-like syntax for deep nesting.
    Examples:
    - "taxpayer.name.first"
    - "income.wages[0].amount"
    - "deductions.medical.total"
    """
    path: str
    default_value: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "default_value": self.default_value
        }

@dataclass
class ValidationRule:
    """Validation rules for field values"""
    rule_type: Literal["required", "regex", "range", "length", "custom"]
    parameters: Dict = field(default_factory=dict)
    error_message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "rule_type": self.rule_type,
            "parameters": self.parameters,
            "error_message": self.error_message
        }

@dataclass
class FormattingRule:
    """
    Formatting rules for field values.
    Examples:
    - Currency: {"type": "currency", "decimal_places": 2, "show_cents": true}
    - SSN: {"type": "mask", "pattern": "XXX-XX-####"}
    - Date: {"type": "date", "format": "MM/DD/YYYY"}
    """
    format_type: str
    parameters: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "format_type": self.format_type,
            "parameters": self.parameters
        }

@dataclass
class FieldAnnotation:
    """
    Complete annotation for a single field on a tax form.
    """
    field_id: str  # Unique identifier (e.g., "1040_line1a")
    field_name: str  # Human-readable name
    field_type: FieldType
    position: Position
    dimensions: Dimensions
    value_reference: ValueReference
    
    # Optional attributes
    alignment: AlignmentType = AlignmentType.LEFT
    font_style: FontStyle = field(default_factory=FontStyle)
    max_length: Optional[int] = None
    formatting: Optional[FormattingRule] = None
    validation: List[ValidationRule] = field(default_factory=list)
    overflow_behavior: Literal["truncate", "shrink", "wrap", "error"] = "truncate"
    character_spacing: Optional[float] = None  # For fixed-width character boxes
    padding: Dict[str, float] = field(default_factory=lambda: {"top": 0, "right": 2, "bottom": 0, "left": 2})
    
    # Metadata
    page_number: int = 1
    required: bool = False
    description: str = ""
    irs_line_reference: str = ""  # Official IRS line number
    
    def to_dict(self) -> Dict:
        return {
            "field_id": self.field_id,
            "field_name": self.field_name,
            "field_type": self.field_type.value,
            "position": self.position.to_dict(),
            "dimensions": self.dimensions.to_dict(),
            "value_reference": self.value_reference.to_dict(),
            "alignment": self.alignment.value,
            "font_style": self.font_style.to_dict(),
            "max_length": self.max_length,
            "formatting": self.formatting.to_dict() if self.formatting else None,
            "validation": [v.to_dict() for v in self.validation],
            "overflow_behavior": self.overflow_behavior,
            "character_spacing": self.character_spacing,
            "padding": self.padding,
            "page_number": self.page_number,
            "required": self.required,
            "description": self.description,
            "irs_line_reference": self.irs_line_reference
        }

@dataclass
class FormMetadata:
    """Metadata about the tax form"""
    form_number: str  # e.g., "1040", "W-2"
    form_name: str
    tax_year: int
    form_version: str = "1.0"
    page_dimensions: Dict[int, Dimensions] = field(default_factory=dict)  # page_number -> dimensions
    pdf_template_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "form_number": self.form_number,
            "form_name": self.form_name,
            "tax_year": self.tax_year,
            "form_version": self.form_version,
            "page_dimensions": {k: v.to_dict() for k, v in self.page_dimensions.items()},
            "pdf_template_url": self.pdf_template_url
        }

@dataclass
class FormAnnotation:
    """
    Complete annotation specification for a tax form.
    This is the top-level structure containing all field annotations.
    """
    metadata: FormMetadata
    fields: List[FieldAnnotation]
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "metadata": self.metadata.to_dict(),
            "fields": [f.to_dict() for f in self.fields]
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Export annotation to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FormAnnotation':
        """Create FormAnnotation from dictionary"""
        # Implementation would parse dict back to objects
        pass
    
    def get_field_by_id(self, field_id: str) -> Optional[FieldAnnotation]:
        """Retrieve a field annotation by its ID"""
        for field in self.fields:
            if field.field_id == field_id:
                return field
        return None
    
    def get_fields_by_page(self, page_number: int) -> List[FieldAnnotation]:
        """Get all fields on a specific page"""
        return [f for f in self.fields if f.page_number == page_number]


# Example Usage
if __name__ == "__main__":
    # Create a sample Form 1040 annotation
    form_1040 = FormAnnotation(
        metadata=FormMetadata(
            form_number="1040",
            form_name="U.S. Individual Income Tax Return",
            tax_year=2024,
            page_dimensions={
                1: Dimensions(width=612, height=792)  # Letter size in points
            },
            pdf_template_url="https://www.irs.gov/pub/irs-pdf/f1040.pdf"
        ),
        fields=[
            FieldAnnotation(
                field_id="1040_first_name",
                field_name="First Name",
                field_type=FieldType.TEXT,
                position=Position(x=50, y=150, coordinate_system=CoordinateSystem.ABSOLUTE),
                dimensions=Dimensions(width=200, height=20),
                value_reference=ValueReference(path="taxpayer.name.first"),
                alignment=AlignmentType.LEFT,
                font_style=FontStyle(font_family="Courier", font_size=10),
                max_length=30,
                required=True,
                irs_line_reference="Line 1a"
            ),
            FieldAnnotation(
                field_id="1040_ssn",
                field_name="Social Security Number",
                field_type=FieldType.SSN,
                position=Position(x=400, y=150, coordinate_system=CoordinateSystem.ABSOLUTE),
                dimensions=Dimensions(width=120, height=20),
                value_reference=ValueReference(path="taxpayer.ssn"),
                alignment=AlignmentType.CENTER,
                character_spacing=8.0,  # Fixed spacing between digits
                formatting=FormattingRule(
                    format_type="mask",
                    parameters={"pattern": "XXX-XX-####"}
                ),
                validation=[
                    ValidationRule(
                        rule_type="regex",
                        parameters={"pattern": r"^\d{3}-\d{2}-\d{4}$"},
                        error_message="SSN must be in format XXX-XX-XXXX"
                    )
                ],
                required=True,
                irs_line_reference="SSN"
            ),
            FieldAnnotation(
                field_id="1040_line1_wages",
                field_name="Wages, salaries, tips",
                field_type=FieldType.CURRENCY,
                position=Position(x=450, y=300, coordinate_system=CoordinateSystem.ABSOLUTE),
                dimensions=Dimensions(width=100, height=15),
                value_reference=ValueReference(
                    path="income.wages.total",
                    default_value="0.00"
                ),
                alignment=AlignmentType.RIGHT,
                formatting=FormattingRule(
                    format_type="currency",
                    parameters={
                        "decimal_places": 2,
                        "show_cents": True,
                        "currency_symbol": "$",
                        "thousands_separator": ","
                    }
                ),
                validation=[
                    ValidationRule(
                        rule_type="range",
                        parameters={"min": 0, "max": 999999999.99},
                        error_message="Amount must be between 0 and 999,999,999.99"
                    )
                ],
                required=True,
                irs_line_reference="Line 1"
            )
        ]
    )
    
    # Export to JSON
    print(form_1040.to_json())