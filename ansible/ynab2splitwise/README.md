ynab2splitwise
=========



Requirements
------------

This role requires docker to be install on the target host.

Role Variables
--------------

Required:
- y2s_accounts_configuration: List of accounts and their configuration. See ynab2splitwise documentation for details.

With defaults:
- y2s_image_repository: Docker image repository for the ynab2splitwise image, "
- y2s_image_tag: Docker image tag
- y2s_cron_minute: Cron Minute
- y2s_cron_hour: Cron Hour
- y2s_cron_day: Cron Day
- y2s_cron_month: Cron Month
- y2s_cron_weekday: Cron Weekday

Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      vars_file:
        - vault.yml # Contains y2s_accounts_configuration with credentials
      roles:
         - role: gperiard.ynab2splitwise


License
-------

GNU GPLv3
