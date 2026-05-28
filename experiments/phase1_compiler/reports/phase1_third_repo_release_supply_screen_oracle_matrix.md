# Third Repo Oracle Matrix

What happened: changed-test oracle availability was separated from raw candidate inventory.

Why it matters: issue-only rows without changed tests stay inventory only and are not certified.

| Repo | Oracle Classifications |
| --- | --- |
| cachetools | {'changed_test_oracle_available': 87, 'oracle_missing_inventory_only': 21} |
| click | {'changed_test_oracle_available': 273, 'oracle_missing_inventory_only': 25} |
| jinja2 | {'changed_test_oracle_available': 242, 'oracle_missing_inventory_only': 50} |
| packaging | {'changed_test_oracle_available': 181, 'oracle_missing_inventory_only': 119} |
