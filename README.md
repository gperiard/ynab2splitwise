# YNAB to Splitwise Synchronizer

Python script that synchronizes flagged transactions from You Need A Budget (YNAB) to Splitwise.

It supports multiple account configurations and is designed to be run as a cron job at least once a day.

## How it Works
The script uses the YNAB and Splitwise APIs to perform the synchronization. It first fetches all transactions from YNAB for the past day and filters the ones flagged with a blue color. For each of these transactions, it creates an expense in Splitwise. If the expense is successfully created, the transaction is marked as synchronized in YNAB by setting the flag color to green.


## Setup

1. Clone this repository to your local machine.
2. Create a config.yml file in the root directory of the project with the following structure:
   ```yaml
   accounts:
    - name: Account 1
        ynab_api_key: YOUR_YNAB_API_KEY
        budget_id: YOUR_YNAB_BUDGET_ID
        splitwise_api_key: YOUR_SPLITWISE_API_KEY
        group_id: YOUR_SPLITWISE_GROUP_ID
    - name: Account 2 # Optional
        ynab_api_key: YOUR_YNAB_API_KEY
        budget_id: YOUR_YNAB_BUDGET_ID
        splitwise_api_key: YOUR_SPLITWISE_API_KEY
        group_id: YOUR_SPLITWISE_GROUP_ID
   ```
3. Replace YOUR_YNAB_API_KEY, YOUR_YNAB_BUDGET_ID, YOUR_SPLITWISE_API_KEY, and YOUR_SPLITWISE_GROUP_ID with your actual API keys and IDs.


## Usage
This project uses poetry to manage its dependencies

To run the script, simply execute python sync.py in your terminal. The script will synchronize all flagged transactions from the past day from YNAB to Splitwise for each account specified in the config.yml file.

## Contributing
Pull requests are welcome.

## License
This project is licensed under the  GNU GPLv3 License - see the LICENSE file for details.
