from pdf2image import convert_from_path
import os

pdf_path = "tr_pdf_exports/tr_account_statement_last_month.pdf"
output_path = "output/page_1.png"

if not os.path.exists("output"):
    os.makedirs("output")

pages = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
pages[0].save(output_path, "PNG")
print(f"Saved {output_path}")
