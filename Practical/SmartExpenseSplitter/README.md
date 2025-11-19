# Smart Expense Splitter

The Smart Expense Splitter showcases how to parse human-readable expense logs, build a debt graph and compute a minimal set of transactions to settle the balances.

## Input format

Each expense is written as `description;amount;payer;consumer1,consumer2,...`. The amount uses decimal notation, the payer is the person who paid for the expense and the consumers list includes everyone that benefited from the purchase (the payer can be part of the consumer list as well).

```
Groceries;120.00;Alice;Alice,Bob,Carla
Museum tickets;60.00;Bob;Alice,Bob,Carla
Dinner;90.00;Carla;Bob,Carla
```

## CLI usage

The module exposes a CLI entry point:

```
python -m Practical.SmartExpenseSplitter.cli --file trip.txt --pretty --output plan.json
```

You can also mix file inputs with inline `--expense` arguments.

## Example scenario

Given the sample inputs above the CLI prints:

```
Optimized Settlement Plan:
 - Bob pays Alice 45.00
 - Carla pays Alice 15.00
```

The JSON file contains the same plan ready to share with the group.
