import argparse
import pandas as pd
from pathlib import Path
import pdfplumber
import sys
import os
from src.pdf_parser.utils import parse_description
from deep_translator import GoogleTranslator

# Translation mappings
HEADER_MAPPING = {
    "DATUM": "DATE",
    "TYP": "TYPE",
    "BESCHREIBUNG": "DESCRIPTION",
    "SALDO": "BALANCE",
}

TYPE_MAPPING = {
    "Handel": "TRADE",
    "Zinszahlung": "INTEREST_PAYMENT",
    "Erträge": "DIVIDENDS",
    "Prämie": "PREMIUM",
    "Kartentransaktion": "CARD_TRANSACTION",
    "Überweisung": "TRANSFER",
}


def translate_to_english(text: str) -> str:
    """Translate text to English using deep_translator."""
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception:
        return text  # Fallback to original text


def process_words_to_rows(page, headers):
    """
    Processes words extracted from a cropped page into structured rows.
    """
    words = page.extract_words()

    # Define column boundaries based on header x-coordinates
    header_boundaries = {}
    for i, header in enumerate(headers):
        x0 = header["x0"]
        x1 = headers[i + 1]["x0"] if i + 1 < len(headers) else page.width
        header_boundaries[header["text"]] = (x0, x1)

    # Group words into lines based on vertical proximity, preserving reading order
    lines = []
    current_line = []
    prev_top = None
    threshold = 10  # pixels threshold for line separation
    for word in words:
        if prev_top is not None and abs(word["top"] - prev_top) > threshold:
            if current_line:
                lines.append(current_line)
            current_line = []
        current_line.append(word)
        prev_top = word["top"]
    if current_line:
        lines.append(current_line)

    # Assemble rows from lines
    raw_rows = []
    current_row = None
    for line_words in lines:
        # Check if this line starts a new transaction (has a TYPE entry)
        has_typ = any(
            word["text"].strip()
            for word in line_words
            if header_boundaries["TYPE"][0] <= word["x0"] < header_boundaries["TYPE"][1]
        )

        if has_typ and current_row is not None:
            raw_rows.append(current_row)
            current_row = None

        if current_row is None:
            current_row = {h["text"]: [] for h in headers}

        # Append words to the current row's columns
        for word in line_words:
            for header_text, (x0, x1) in header_boundaries.items():
                if x0 <= word["x0"] < x1:
                    current_row[header_text].append(word["text"])
                    break

    if current_row is not None:
        raw_rows.append(current_row)

    # Join words in each column for all collected rows
    for i in range(len(raw_rows)):
        for header_text in raw_rows[i]:
            raw_rows[i][header_text] = " ".join(raw_rows[i][header_text])

    return pd.DataFrame(raw_rows)


def main():
    parser = argparse.ArgumentParser(description="Parse Trade Republic PDF exports.")
    parser.add_argument(
        "--input_folder",
        type=str,
        default="tr_pdf_exports",
        help="Folder containing PDF exports.",
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        default="outputs",
        help="Folder to save the output CSV files.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_folder)
    output_path = Path(args.output_folder)
    output_path.mkdir(exist_ok=True)

    all_trades = []
    all_transactions = []
    for pdf_file in input_path.glob("*.pdf"):
        print(f"Processing: {pdf_file}")
        with pdfplumber.open(pdf_file) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                # Find the "Umsatzübersicht" header and footer to define the table area
                header_text = page.search("UMSATZÜBERSICHT")
                footer_text = page.search("Seite")

                if page_idx == 0:
                    # First page: require "UMSATZÜBERSICHT"
                    if not header_text:
                        continue
                    y0 = header_text[0]["bottom"]
                else:
                    # Continuation pages: table starts at top
                    y0 = 0

                y1 = footer_text[0]["top"] if footer_text else page.height

                cropped_page = page.crop((0, y0, page.width, y1))

                # Find the precise header words to define columns
                header_words = sorted(
                    [
                        word
                        for word in cropped_page.extract_words()
                        if word["text"]
                        in [
                            "DATUM",
                            "TYP",
                            "BESCHREIBUNG",
                            "SALDO",
                        ]
                    ],
                    key=lambda w: w["x0"],
                )

                # Translate headers to English
                header_words = [
                    {**w, "text": HEADER_MAPPING.get(w["text"], w["text"])}
                    for w in header_words
                ]

                if not header_words:
                    continue

                page_df = process_words_to_rows(cropped_page, header_words)

                # Translate types and descriptions to English
                page_df["TYPE"] = page_df["TYPE"].map(lambda x: TYPE_MAPPING.get(x, x))
                page_df["DESCRIPTION"] = page_df["DESCRIPTION"].apply(
                    translate_to_english
                )

                # Process all transactions
                transactions_df = page_df.copy()

                # Parse amounts for transactions
                def parse_transaction_amount(row):
                    besch = row["DESCRIPTION"]
                    typ = row["TYPE"]
                    amount = 0.0

                    # Extract amount from description (e.g., "1,84 €" or "2.000,00 €")
                    import re

                    amount_match = re.search(r"([\d.,]+)\s*€", besch)
                    if amount_match:
                        amount_str = amount_match.group(1)
                        # Handle German format: remove dots, replace comma with dot
                        amount_str = amount_str.replace(".", "").replace(",", ".")
                        if not amount_str:
                            amount = 0.0
                        else:
                            try:
                                amount = float(amount_str)
                            except ValueError:
                                amount = 0.0
                        # Determine direction
                        if (
                            typ in ["INTEREST_PAYMENT", "DIVIDENDS", "PREMIUM"]
                            or "Incoming" in besch
                        ):
                            pass  # positive
                        elif (
                            typ in ["CARD_TRANSACTION", "TRANSFER"]
                            or "Outgoing" in besch
                        ):
                            amount = -amount
                        elif typ == "TRADE":
                            amount = 0  # Trades are not cash transactions
                    row["AMOUNT"] = amount
                    return row

                transactions_df = transactions_df.apply(
                    parse_transaction_amount, axis=1
                )
                # Filter out headers, footers, and empty rows
                valid_types = [
                    "INTEREST_PAYMENT",
                    "TRADE",
                    "DIVIDENDS",
                    "PREMIUM",
                    "CARD_TRANSACTION",
                    "TRANSFER",
                ]
                transactions_df = transactions_df[
                    transactions_df["TYPE"].notna()
                    & transactions_df["TYPE"].isin(valid_types)
                ]
                transactions_df = transactions_df[
                    ["DATE", "TYPE", "DESCRIPTION", "AMOUNT", "BALANCE"]
                ]
                all_transactions.append(transactions_df)

                # Process trades separately
                trades_df = page_df[page_df["TYPE"] == "TRADE"].copy()

                if not trades_df.empty:
                    parsed_data = trades_df["DESCRIPTION"].apply(parse_description)

                    # Create a new DataFrame from the parsed data
                    final_trades = pd.DataFrame(
                        parsed_data.tolist(), index=trades_df.index
                    )
                    final_trades["DATE"] = trades_df["DATE"]

                    # Rename columns to the final format
                    final_trades.rename(
                        columns={
                            "isin": "ISIN",
                            "name": "NAME",
                            "quantity": "QUANTITY",
                            "price": "PRICE",
                            "trade_type": "TRADE_TYPE",
                        },
                        inplace=True,
                    )
                    all_trades.append(final_trades)

    if all_trades:
        pd.concat(all_trades).to_csv(output_path / "trades.csv", index=False)
        print(
            f"Saved {len(pd.concat(all_trades))} trades to {output_path / 'trades.csv'}"
        )

    if all_transactions:
        transactions_csv = output_path / "transactions.csv"
        pd.concat(all_transactions).to_csv(transactions_csv, index=False)
        print(
            f"Saved {len(pd.concat(all_transactions))} transactions to {transactions_csv}"
        )

    # Validation
    # if all_trades and all_transactions:
    #     trades_csv = output_path / "trades.csv"
    #     transactions_csv = output_path / "transactions.csv"
    #     report = validate_extraction(
    #         str(pdf_file), str(trades_csv), str(transactions_csv)
    #     )
    #     print_report(report)
    #     print(
    #         f"Saved {len(pd.concat(all_transactions))} transactions to {output_path / 'transactions.csv'}"
    #     )


if __name__ == "__main__":
    main()
