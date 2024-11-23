import requests
import yaml
import logging
import os

from datetime import datetime, timedelta

YNAB_QUEUED_COLOR = os.environ.get("YNAB_QUEUED_COLOR", "blue")
YNAB_SYNCED_COLOR = os.environ.get("YNAB_SYNCED_COLOR", "green")


# YNABClient is a minimal client for the YNAB API
class YNABClient:
    """
    A class for interacting with the YNAB API to sync transactions.

    Attributes:
    - base_url (str): The base URL for the YNAB API.
    - queued_color (str): The flag color for transactions that are queued for sync.
    - synced_color (str): The flag color for transactions that have been synced.
    - api_key (str): The API key for authenticating with the YNAB API.
    - budget_id (str): The ID of the budget to sync transactions for.
    - request (requests.Session): A session object for making requests to the YNAB API.
    """

    base_url = "https://api.ynab.com/v1"

    def __init__(self, api_key, budget_id):
        """
        Initializes a new instance of the YNABClient class.

        Args:
        - api_key (str): The API key for authenticating with the YNAB API.
        - budget_id (str): The ID of the budget to sync transactions for.
        """
        self.api_key = api_key
        self.budget_id = budget_id
        self.request = requests.Session()
        self.request.headers.update({"Authorization": f"Bearer {api_key}"})
        self._splitwise_category_id = None

    def get_splitwise_category_id(self) -> str:
        """
        Gets the category ID for the Splitwise category, creating it if it doesn't exist.

        Returns:
        - str: The ID of the Splitwise category
        """
        if self._splitwise_category_id:
            return self._splitwise_category_id

        # Get all categories
        response = self.request.get(
            f"{self.base_url}/budgets/{self.budget_id}/categories"
        ).json()

        category_groups = response["data"]["category_groups"]

        # Look for Splitwise category
        for group in category_groups:
            for category in group["categories"]:
                if category["name"] == "Splitwise":
                    self._splitwise_category_id = category["id"]
                    return self._splitwise_category_id

        # If we get here, we need to create the category
        # First find the first category group that's not hidden
        group_id = next(g["id"] for g in category_groups if not g.get("hidden"))

        # Create Splitwise category
        response = self.request.post(
            f"{self.base_url}/budgets/{self.budget_id}/categories",
            json={"category": {"name": "Splitwise", "category_group_id": group_id}},
        ).json()

        self._splitwise_category_id = response["data"]["category"]["id"]
        return self._splitwise_category_id

    def get_queued_transactions(self, since_date=None) -> list:
        """
        Gets all transactions from YNAB that are queued for sync.

        Args:
        - since_date (str): The date to get transactions since (in ISO format).

        Returns:
        - A list of transactions that are queued for sync.
        """
        params = {}
        if since_date:
            params["since_date"] = since_date

        transactions = self.request.get(
            f"{self.base_url}/budgets/{self.budget_id}/transactions",
            params=params,
        ).json()["data"]["transactions"]

        queued_transactions = [
            t for t in transactions if t.get("flag_color") == YNAB_QUEUED_COLOR
        ]

        return queued_transactions

    def set_transactions_synced(self, transactions) -> None:
        """
        Sets the flag color of the transactions to indicate that they have been synced
        and splits the amount between the original category and Splitwise category.

        Args:
        - transactions (list): A list of transactions to mark as synced.

        Raises:
        - Exception: If the request to set the transactions as synced fails.
        """
        splitwise_category_id = self.get_splitwise_category_id()

        payload = {"transactions": []}

        for t in transactions:
            # Calculate split amount (50% of original)
            split_amount = t["amount"] // 2
            remaining_amount = t["amount"] - split_amount

            transaction_update = {
                "id": t["id"],
                "flag_color": YNAB_SYNCED_COLOR,
                "subtransactions": [
                    {
                        "amount": remaining_amount,
                        "category_id": t.get("category_id"),
                        "payee_id": t.get("payee_id"),
                    },
                    {
                        "amount": split_amount,
                        "category_id": splitwise_category_id,
                        "payee_id": t.get("payee_id"),
                    },
                ],
            }
            payload["transactions"].append(transaction_update)

        response = self.request.patch(
            f"{self.base_url}/budgets/{self.budget_id}/transactions",
            json=payload,
        )
        if response.status_code != 200:
            logging.error(f"{response.status_code}: {response.json()}")
            raise Exception("Failed to set transactions as synced")


# SplitwiseClient is a minimal client for the Splitwise API
class SplitwiseClient:
    base_url = "https://secure.splitwise.com/api/v3.0"

    def __init__(self, api_key, group_id):
        self.api_key = api_key
        self.group_id = group_id
        self.request = requests.Session()
        self.request.headers.update({"Authorization": f"Bearer {api_key}"})

    def create_expense(self, description: str, cost: int, date):
        payload = {
            "cost": cost,
            "description": description,
            "group_id": self.group_id,
            "date": datetime.strptime(date, "%Y-%m-%d").date().isoformat(),
            "split_equally": "true",
        }
        response = self.request.post(f"{self.base_url}/create_expense", json=payload)
        if response.status_code != 200 or response.json().get("errors"):
            logging.error(f"{response.status_code}: {response.json()}")
            raise Exception("Failed to create expense")


# sync will sync all transactions from YNAB to Splitwise
def sync(account_config: dict) -> None:
    # Initialize clients
    ynab = YNABClient(
        account_config["ynab_api_key"],
        account_config["budget_id"],
    )
    splitwise = SplitwiseClient(
        account_config["splitwise_api_key"],
        account_config["group_id"],
    )

    # Get all transactions from YNAB since yesterday
    since_date = (
        datetime.now().date() - timedelta(days=int(os.environ.get("SINCE_DAYS", 1)))
    ).isoformat()
    ynab_transactions = ynab.get_queued_transactions(since_date=since_date)
    expensed_transactions = []

    logging.debug(ynab_transactions)

    # Create expenses in Splitwise
    for yt in ynab_transactions:
        print(
            f"Processing: [{yt['date']}] {yt['payee_name']} for {yt['amount'] / 1000}"
        )
        try:
            splitwise.create_expense(
                description=f"{yt['payee_name']} {yt['memo'] or ''}",
                cost=str(abs(yt["amount"] / 1000)),
                date=yt["date"],
            )
            expensed_transactions.append(yt)
        except Exception as e:
            logging.exception("Failed to create expense in Splitwise: %s", e)

    # Set transactions as synced in YNAB
    if expensed_transactions:
        try:
            ynab.set_transactions_synced(expensed_transactions)
        except requests.HTTPError as e:
            logging.exception(e)
            logging.error("Failed to set transactions as synced")

    logging.info(f"Synced {len(expensed_transactions)} transactions")


def main(config: dict):
    # Sync each account in configuration
    for account in config["accounts"]:
        logging.info(f"Syncing account: {account['name']}")
        sync(account)
        logging.info(f"Finished syncing account: {account['name']}")


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())
    logging.info("Starting YNAB to Splitwise sync")

    # Load config
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)

    main(config)

    logging.info("Finished YNAB to Splitwise sync")
