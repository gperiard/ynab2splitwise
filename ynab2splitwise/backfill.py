import yaml
import logging
import os
import argparse
from sync import YNABClient


def backfill_splits(account_config: dict, dry_run: bool = False) -> None:
    """
    Backfills category splits for all previously synced transactions that haven't been split yet.

    Args:
        account_config (dict): The account configuration containing API keys and IDs
        dry_run (bool): If True, only shows what would be done without making actual changes
    """
    # Initialize YNAB client
    ynab = YNABClient(
        account_config["ynab_api_key"],
        account_config["budget_id"],
    )

    # Get all transactions
    response = ynab.request.get(
        f"{ynab.base_url}/budgets/{ynab.budget_id}/transactions"
    ).json()

    transactions = response["data"]["transactions"]

    # Filter for synced transactions (green flag) that don't have subtransactions
    synced_transactions = [
        t
        for t in transactions
        if t.get("flag_color") == "green"
        and (not t.get("subtransactions") or len(t.get("subtransactions")) == 0)
    ]

    if not synced_transactions:
        logging.info("No transactions found that need backfilling")
        return

    # Sort transactions by date for statistics
    synced_transactions.sort(key=lambda x: x["date"])
    first_transaction = synced_transactions[0]
    last_transaction = synced_transactions[-1]
    total_amount = (
        sum(abs(t["amount"]) for t in synced_transactions) / 1000
    )  # Convert to dollars

    logging.info(f"Found {len(synced_transactions)} transactions to backfill")
    logging.info(
        f"Date range: {first_transaction['date']} to {last_transaction['date']}"
    )
    logging.info(f"Total amount to be split: ${total_amount:.2f}")

    if dry_run:
        logging.info("DRY RUN - The following transactions would be split:")
        for t in synced_transactions:
            split_amount = t["amount"] // 2
            remaining_amount = t["amount"] - split_amount
            logging.info(
                f"Transaction: {t['date']} {t['payee_name']} "
                f"(${abs(t['amount']) / 1000:.2f}) would be split into:"
            )
            logging.info(f"  - Original category: ${abs(remaining_amount) / 1000:.2f}")
            logging.info(f"  - Splitwise category: ${abs(split_amount) / 1000:.2f}")
        logging.info("\nSummary:")
        logging.info(f"Total transactions to be updated: {len(synced_transactions)}")
        logging.info(
            f"First transaction date: {first_transaction['date']} ({first_transaction['payee_name']})"
        )
        logging.info(
            f"Last transaction date: {last_transaction['date']} ({last_transaction['payee_name']})"
        )
        logging.info(f"Total amount to be split: ${total_amount:.2f}")
        return

    # Process transactions in batches of 100 to avoid API limits
    batch_size = 100
    processed_count = 0
    for i in range(0, len(synced_transactions), batch_size):
        batch = synced_transactions[i : i + batch_size]
        try:
            ynab.set_transactions_synced(batch)
            processed_count += len(batch)
            logging.info(f"Successfully backfilled batch of {len(batch)} transactions")
        except Exception as e:
            logging.error(f"Failed to backfill batch starting at index {i}: {e}")

    logging.info("\nBackfill Summary:")
    logging.info(f"Total transactions processed: {processed_count}")
    logging.info(
        f"First transaction date: {first_transaction['date']} ({first_transaction['payee_name']})"
    )
    logging.info(
        f"Last transaction date: {last_transaction['date']} ({last_transaction['payee_name']})"
    )
    logging.info(f"Total amount split: ${total_amount:.2f}")


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Backfill YNAB transaction splits")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making actual changes",
    )
    args = parser.parse_args()

    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())
    logging.info("Starting YNAB to Splitwise backfill")
    if args.dry_run:
        logging.info("Running in DRY RUN mode - no changes will be made")

    # Load config
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)

    # Process each account in configuration
    for account in config["accounts"]:
        logging.info(f"Backfilling splits for account: {account['name']}")
        backfill_splits(account, dry_run=args.dry_run)
        logging.info(f"Finished backfilling account: {account['name']}")

    logging.info("Finished YNAB to Splitwise backfill")


if __name__ == "__main__":
    main()
