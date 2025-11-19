# Trade Republic PDF Statement Structure

## Overview
Trade Republic account statements are PDF documents containing transaction history. The structure is consistent across statements, with a header, transaction table, and footer.

## Page Layout

### Header Section (Top ~20% of page)
- **Trade Republic Bank GmbH** branding
- Account holder information (name, address)
- Account period (e.g., "01 Okt. 2025 - 31 Okt. 2025")
- Account number and IBAN
- **KONTOÜBERSICHT** (Account Overview) - summary info
- **UMSATZÜBERSICHT** (Transaction Overview) - marks start of transaction table

### Transaction Table (Middle ~60% of page)
- **Headers**: DATUM | TYP | BESCHREIBUNG | ZAHLUNGSEINGANG | ZAHLUNGSAUSGANG | SALDO
- **Columns**:
  - DATUM: Date (DD Mmm. YYYY, may be split across lines)
  - TYP: Transaction type (e.g., Handel, Zinszahlung, Erträge, Prämie)
  - BESCHREIBUNG: Description (may span multiple lines, includes ISIN, name, quantity, price)
  - ZAHLUNGSEINGANG: Incoming amount
  - ZAHLUNGSAUSGANG: Outgoing amount
  - SALDO: Balance
- **Row Structure**: Each transaction is one logical row, but descriptions often wrap to multiple PDF lines
- **Multi-line Handling**: Date may be split (e.g., "01" on one line, "Okt. 2025" on next), descriptions continue on subsequent lines

### Footer Section (Bottom ~20% of page)
- Page number (e.g., "Seite 1 von 8")
- Legal information, addresses
- Trade Republic contact details

## Key Observations
- Table starts after "UMSATZÜBERSICHT" text (page 1 only; continuation pages begin at top)
- Transactions are grouped by type, with multi-line descriptions
- Amounts use comma as decimal separator (German format: "2.000,00 €" for 2000.00)
- Footer starts with "Seite" text
- Multi-page tables require page-specific cropping logic

## Extraction Strategy
- **Cropping:** Page 1: "UMSATZÜBERSICHT" to "Seite"; Pages 2+: top (y0=0) to "Seite"
- Use column boundaries based on header positions
- Handle multi-line rows by combining lines until next transaction type
- Parse descriptions for structured data (ISIN, quantity, price)
- Validate extraction with automated checks (e.g., count matches)