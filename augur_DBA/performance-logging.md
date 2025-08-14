# Look at Database Performance / Performance Profile

1. Login in as the postgresql user, or a user with `superuser` privileges
2. Set these values: 
    ```sql 
    ALTER SYSTEM SET log_min_duration_statement = 0;
    ALTER SYSTEM SET log_duration = 'on';
    ALTER SYSTEM SET log_statement = 'all';
    ALTER SYSTEM SET log_line_prefix = '%m [%p] %q%u@%d %a ';
    SELECT pg_reload_conf();
    ```
3. This will generate a **TON** of logs. 
4. Check these logs using `pgbadger` [`sudo apt install pgbadger`] 
5. This PGBadger Command will produce a very detailed report (version 13.1):
    ```bash
    pgbadger -f stderr -v --top=100 \
    --pie-limit=20 \
    --exclude-query="^(COPY|VACUUM)" \
    --outdir ~/pgbadger_reports \
    /var/log/postgresql/postgresql-17-main.log
    ```

    Obviously, replace the log location with wherever your exists (this location is standard for Ubuntu 24.x) and make sure the directory you are writing to exists. 

6. If you are interested in tracking connection information (how many, how long, activity), these parameters are also necessary: 
    ```sql
    ALTER SYSTEM SET log_connections = 'on';
    ALTER SYSTEM SET log_disconnections = 'on';
    ALTER SYSTEM SET log_hostname = 'on';
    ALTER SYSTEM SET log_line_prefix = '%m [%p] %h %u@%d %a ';
    SELECT pg_reload_conf();
    ```