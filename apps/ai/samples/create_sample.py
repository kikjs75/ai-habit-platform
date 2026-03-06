"""
Generate 10 sample images with different nutrition label content for OCR testing.

Usage:
    python create_sample.py

Output:
    sample_01.png ~ sample_10.png
"""

from PIL import Image, ImageDraw

SAMPLES = [
    {
        "filename": "sample_01.png",
        "lines": [
            "Nutrition Facts",
            "Product: Whole Milk",
            "Serving Size 1 cup (240ml)",
            "",
            "Calories 150",
            "Total Fat 8g",
            "Protein 8g",
            "Total Carbohydrate 12g",
            "Sodium 120mg",
        ],
    },
    {
        "filename": "sample_02.png",
        "lines": [
            "Nutrition Facts",
            "Product: Greek Yogurt",
            "Serving Size 150g",
            "",
            "Calories 100",
            "Total Fat 0g",
            "Protein 17g",
            "Total Carbohydrate 6g",
            "Sodium 65mg",
        ],
    },
    {
        "filename": "sample_03.png",
        "lines": [
            "Nutrition Facts",
            "Product: Chicken Breast",
            "Serving Size 100g",
            "",
            "Calories 165",
            "Total Fat 3.6g",
            "Protein 31g",
            "Total Carbohydrate 0g",
            "Sodium 74mg",
        ],
    },
    {
        "filename": "sample_04.png",
        "lines": [
            "Nutrition Facts",
            "Product: Brown Rice",
            "Serving Size 1 cup cooked (195g)",
            "",
            "Calories 216",
            "Total Fat 1.8g",
            "Protein 5g",
            "Total Carbohydrate 45g",
            "Sodium 10mg",
        ],
    },
    {
        "filename": "sample_05.png",
        "lines": [
            "Nutrition Facts",
            "Product: Salmon Fillet",
            "Serving Size 100g",
            "",
            "Calories 208",
            "Total Fat 13g",
            "Protein 20g",
            "Total Carbohydrate 0g",
            "Sodium 59mg",
        ],
    },
    {
        "filename": "sample_06.png",
        "lines": [
            "Nutrition Facts",
            "Product: Almond Butter",
            "Serving Size 2 tbsp (32g)",
            "",
            "Calories 190",
            "Total Fat 17g",
            "Protein 7g",
            "Total Carbohydrate 7g",
            "Sodium 0mg",
        ],
    },
    {
        "filename": "sample_07.png",
        "lines": [
            "Nutrition Facts",
            "Product: Banana",
            "Serving Size 1 medium (118g)",
            "",
            "Calories 105",
            "Total Fat 0.4g",
            "Protein 1.3g",
            "Total Carbohydrate 27g",
            "Sodium 1mg",
        ],
    },
    {
        "filename": "sample_08.png",
        "lines": [
            "Nutrition Facts",
            "Product: Cheddar Cheese",
            "Serving Size 1 oz (28g)",
            "",
            "Calories 113",
            "Total Fat 9g",
            "Protein 7g",
            "Total Carbohydrate 0.4g",
            "Sodium 174mg",
        ],
    },
    {
        "filename": "sample_09.png",
        "lines": [
            "Nutrition Facts",
            "Product: Oatmeal",
            "Serving Size 1 cup cooked (234g)",
            "",
            "Calories 166",
            "Total Fat 3.6g",
            "Protein 5.9g",
            "Total Carbohydrate 28g",
            "Sodium 9mg",
        ],
    },
    {
        "filename": "sample_10.png",
        "lines": [
            "Nutrition Facts",
            "Product: Avocado",
            "Serving Size 1/2 fruit (68g)",
            "",
            "Calories 114",
            "Total Fat 10g",
            "Protein 1.3g",
            "Total Carbohydrate 6g",
            "Sodium 5mg",
        ],
    },
]


def create_sample(filename: str, lines: list[str]) -> None:
    img = Image.new("RGB", (420, 320), color="white")
    draw = ImageDraw.Draw(img)

    y = 20
    for line in lines:
        draw.text((20, y), line, fill="black")
        y += 30

    img.save(filename)
    print(f"Created {filename}")


if __name__ == "__main__":
    for sample in SAMPLES:
        create_sample(sample["filename"], sample["lines"])
    print(f"\nDone — {len(SAMPLES)} images created.")
