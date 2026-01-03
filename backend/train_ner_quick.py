"""
Train NER model quickly with sample invoice data
No external dataset needed - self-contained training
"""
import spacy
from spacy.training import Example
from spacy.util import minibatch
import random
from pathlib import Path
import json

# Sample training data - Vietnamese invoice fields
TRAIN_DATA = [
    ("Tổng tiền 1.500.000 VND", {"entities": [(11, 21, "TOTAL_AMOUNT"), (22, 25, "CURRENCY")]}),
    ("Số hóa đơn: HD123456", {"entities": [(13, 21, "INVOICE_NUMBER")]}),
    ("Ngày: 25/12/2024", {"entities": [(6, 16, "DATE")]}),
    ("Người bán: Công ty ABC", {"entities": [(11, 22, "VENDOR_NAME")]}),
    ("Mã số thuế: 0123456789", {"entities": [(12, 22, "TAX_ID")]}),
    ("Điện thoại: 0987654321", {"entities": [(12, 22, "PHONE")]}),
    ("Địa chỉ: 123 Đường Nguyễn Văn Cừ, Quận 5, TP.HCM", {"entities": [(9, 48, "ADDRESS")]}),
    ("Email: contact@example.com", {"entities": [(7, 26, "EMAIL")]}),
    ("Mã khách hàng: KH12345", {"entities": [(15, 22, "CUSTOMER_ID")]}),
    ("Tiền cọc: 500.000đ", {"entities": [(11, 18, "DEPOSIT")]}),
    ("VAT 10% = 150.000", {"entities": [(0, 7, "VAT"), (10, 17, "VAT_AMOUNT")]}),
    ("Thành tiền: 1.650.000 VNĐ", {"entities": [(12, 21, "TOTAL"), (22, 25, "CURRENCY")]}),
    
    # Real electricity bill patterns
    ("TIỀN ĐIỆN THÁNG 12/2024", {"entities": [(0, 10, "ITEM"), (17, 24, "DATE")]}),
    ("Số tiền thanh toán: 1.234.567 đ", {"entities": [(20, 29, "AMOUNT"), (30, 31, "CURRENCY")]}),
    ("Mã khách hàng PE123456", {"entities": [(15, 23, "CUSTOMER_ID")]}),
    ("Kỳ ghi chỉ số: 01/12/2024 - 31/12/2024", {"entities": [(16, 26, "START_DATE"), (29, 39, "END_DATE")]}),
    ("Chỉ số cũ: 1234 kWh", {"entities": [(11, 15, "OLD_READING")]}),
    ("Chỉ số mới: 1456 kWh", {"entities": [(12, 16, "NEW_READING")]}),
    ("Điện năng tiêu thụ: 222 kWh", {"entities": [(21, 24, "CONSUMPTION")]}),
    
    # More variations
    ("HD-2024-001", {"entities": [(0, 11, "INVOICE_NUMBER")]}),
    ("Total: 2.000.000đ", {"entities": [(7, 16, "AMOUNT")]}),
    ("Thuế GTGT 8%", {"entities": [(0, 12, "VAT")]}),
    ("Ngày lập: 15/01/2025", {"entities": [(10, 20, "DATE")]}),
    ("SDT: 0901234567", {"entities": [(5, 15, "PHONE")]}),
]

def train_ner():
    """Train a custom NER model from scratch"""
    print("🚀 Starting NER training...")
    
    # Create blank Vietnamese model
    nlp = spacy.blank("vi")
    
    # Add NER pipeline
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
    else:
        ner = nlp.get_pipe("ner")
    
    # Add entity labels
    entity_labels = set()
    for _, annotations in TRAIN_DATA:
        for ent in annotations.get("entities"):
            entity_labels.add(ent[2])
    
    for label in entity_labels:
        ner.add_label(label)
    
    print(f"📋 Entity labels: {entity_labels}")
    
    # Prepare training data
    train_examples = []
    for text, annotations in TRAIN_DATA:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, annotations)
        train_examples.append(example)
    
    # Training loop
    optimizer = nlp.begin_training()
    
    print("🎓 Training for 30 iterations...")
    for iteration in range(30):
        random.shuffle(train_examples)
        losses = {}
        
        # Batch training
        batches = minibatch(train_examples, size=2)
        for batch in batches:
            nlp.update(batch, drop=0.5, losses=losses, sgd=optimizer)
        
        if iteration % 5 == 0:
            print(f"Iteration {iteration}: Loss = {losses.get('ner', 0):.4f}")
    
    # Save model
    output_dir = Path(__file__).parent / "models" / "invoice_ner"
    output_dir.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(output_dir)
    
    print(f"✅ Model saved to {output_dir}")
    
    # Test the model
    print("\n🧪 Testing model:")
    test_texts = [
        "Tổng tiền: 3.456.789 VND",
        "Số hóa đơn HD987654",
        "Ngày 20/12/2024",
        "Mã khách hàng PE123456"
    ]
    
    for text in test_texts:
        doc = nlp(text)
        print(f"\nText: {text}")
        if doc.ents:
            for ent in doc.ents:
                print(f"  - {ent.text} ({ent.label_})")
        else:
            print("  - No entities found")
    
    # Save entity labels for reference
    labels_file = output_dir / "entity_labels.json"
    labels_file.write_text(json.dumps(list(entity_labels), ensure_ascii=False, indent=2))
    print(f"\n📝 Entity labels saved to {labels_file}")
    
    return nlp, output_dir

if __name__ == "__main__":
    model, path = train_ner()
    print(f"\n🎉 Training complete! Model ready at: {path}")
    print("\n💡 To use this model:")
    print("   nlp = spacy.load('models/invoice_ner')")
