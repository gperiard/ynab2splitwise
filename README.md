# YNAB to Splitwise Synchronizer

Python script that synchronizes flagged transactions from You Need A Budget (YNAB) to Splitwise.

It supports multiple account configurations and is designed to be run as a cron job at least once a day.

## How it Works
The script uses the YNAB and Splitwise APIs to perform the synchronization. It first fetches all transactions from YNAB for the past day and filters the ones flagged with a blue color. For each of these transactions, it creates an expense in Splitwise. If the expense is successfully created, the transaction is marked as synchronized in YNAB by setting the flag color to green.

When a transaction is successfully synced to Splitwise, its amount is automatically split in YNAB:
- 50% remains in the original budget category
- 50% is moved to a "Splitwise" category (which is created automatically if it doesn't exist)

This split categorization helps track shared expenses in your budget while maintaining accurate category spending records.

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
This project uses poetry to manage its dependencies.

### Local Development
You can use this setup to locally develop and test this script.
It will build the docker image and mount the code as a volume in the container.

1. `docker-compose up`

### Production
This docker-compose file uses the registry to pull the image and mount only the configuration file.

```
docker-compose -f docker-compose.prod.yml up
```

Alternatively you can use a docker command directly:

```
docker run -v ./config.yml:/app/config.yml ghcr.io/gperiard/ynab2splitwise:latest
```

### Backfilling Category Splits
If you've been using this script before the category split feature was added, you can use the backfill script to split all previously synced transactions.

#### Using Docker Compose (Recommended)
```bash
# Preview changes without making them
docker-compose run --rm syncer python ynab2splitwise/backfill.py --dry-run

# Actually perform the backfill
docker-compose run --rm syncer python ynab2splitwise/backfill.py
```

#### Using Python Directly
```bash
# Preview changes without making them
python ynab2splitwise/backfill.py --dry-run

# Actually perform the backfill
python ynab2splitwise/backfill.py
```

The backfill script will:
1. Find all transactions marked as synced (green flag)
2. For any that don't already have split categories:
   - Split the amount 50/50 between the original category and the Splitwise category
   - Preserve all other transaction details

The script processes transactions in batches to avoid API limits and provides logging output to track progress. Using the `--dry-run` option will show you exactly what changes would be made without actually making them, which is useful for reviewing the impact before committing the changes.

### Run as a cronjob
Ultimately, this script is meant to be run as a cronjob.

Here's a configuration example to run the script every hour:
```
0 * * * * docker run -v <CONFIGURATION PATH>:/app/config.yml ghcr.io/gperiard/ynab2splitwise:latest
```

#### Provision with Ansible
There's an Ansible role in this project to simplify the configuration of the cronjob.

1. Add this repo in your requirements.yml file:
   ```
   roles:
    - src: https://github.com/gperiard/ynab2splitwise.git
        version: v0.2.0
        name: ynab2splitwise
   ```
2. Download it.
   ```
   ansible-galaxy install -r requirements.yml
   ```
3. Create a playbook. Here's an example:
   ```yaml
   # cronjobs.yml
   ---
   - hosts: cronjobs.periard.ca
     become: true
     vars_file:
     - vault.yml # <- contains your account configuration under y2s_accounts_configuration
     roles:
       - role: ynab2splitwise
         y2s_config_dir: /opt/docker/ynab2splitwise
   ```
4. Run it.
   ```
   ansible-playbook -i inventory cronjobs.yml
   ```

## Contributing
Pull requests are welcome.

## License
This project is licensed under the  GNU GPLv3 License - see the LICENSE file for details.
