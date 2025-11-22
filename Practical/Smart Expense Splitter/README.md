# Smart Expense Splitter

The Smart Expense Splitter showcases how to parse human-readable expense logs, build a debt graph and compute a minimal set of transactions to settle the balances.

## 📋 Table of Contents
- [Input Format](#input-format)
- [Usage](#usage)
- [Example](#example)

## 📝 Input Format

Each expense is written as:
```
description;amount;payer;consumer1,consumer2,...
```

-   **amount**: Decimal notation (e.g., 120.00).
-   **payer**: The person who paid.
-   **consumers**: Comma-separated list of beneficiaries (can include the payer).

### Example File (`trip.txt`)
```text
Groceries;120.00;Alice;Alice,Bob,Carla
Museum tickets;60.00;Bob;Alice,Bob,Carla
Dinner;90.00;Carla;Bob,Carla
```

## 🚀 Usage

The module exposes a CLI entry point:

```bash
python -m Practical.SmartExpenseSplitter.cli --file trip.txt --pretty --output plan.json
```

### Options
-   `--file <path>`: Path to input text file.
-   `--expense "<string>"`: Specify an expense inline. Can be used multiple times.
-   `--pretty`: Print human-readable plan to stdout.
-   `--output <path>`: Save plan to a JSON file.

## 💡 Example

Given the sample inputs above, the CLI calculates the net debts and outputs a minimized transaction list:

```text
Optimized Settlement Plan:
 - Bob pays Alice 45.00
 - Carla pays Alice 15.00
```

*Note: While Bob paid 60, his share of total expenses was higher than what he paid, so he owes money. Alice paid 120, which was more than her fair share, so she receives money.*
