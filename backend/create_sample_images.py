#!/usr/bin/env python3
"""
Create sample invoice images for OCR testing
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_sample_invoice(image_path: str, text: str, font_size: int = 20):
    """Create a sample invoice image with text"""
    # Create image
    width, height = 800, 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    try:
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Draw text
    y_position = 50
    for line in text.split('\n'):
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += font_size + 5

    # Save image
    image.save(image_path)
    print(f"Created sample invoice: {image_path}")

def main():
    """Create sample invoice images"""
    uploads_dir = Path("backend/uploads")
    uploads_dir.mkdir(exist_ok=True)

    # Sample invoice text
    invoice_text = """INVOICE
Invoice #: INV-2024-001
Date: 2024-12-27

Bill To:
John Doe
123 Main Street
Anytown, USA 12345

Description                    Qty    Price    Total
Web Development Services       1     $500.00  $500.00
Hosting Setup                  1     $100.00  $100.00
Maintenance                    12    $50.00   $600.00

Subtotal: $1,200.00
Tax (10%): $120.00
Total: $1,320.00

Thank you for your business!
"""

    # Create sample images
    sample_files = [
        ("sample_invoice_1.png", invoice_text),
        ("sample_invoice_2.jpg", invoice_text.replace("INV-2024-001", "INV-2024-002")),
        ("sample_invoice_3.png", invoice_text.replace("John Doe", "Jane Smith")),
    ]

    for filename, text in sample_files:
        image_path = uploads_dir / filename
        create_sample_invoice(str(image_path), text)

    print(f"\nCreated {len(sample_files)} sample invoice images in {uploads_dir}")

if __name__ == "__main__":
    main()