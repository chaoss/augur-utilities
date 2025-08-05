for i in {1..8}; do
  echo "host all all 0.0.0.0/0 md5" > postgres/augur$i/pg_hba.conf

  cat > postgres/augur$i/postgresql.conf <<EOF
listen_addresses = '*'
max_connections = 1000
shared_buffers = 1GB
work_mem = 64MB
maintenance_work_mem = 256MB
effective_cache_size = 2GB
wal_buffers = 64MB
max_wal_size = 1GB
min_wal_size = 80MB
hba_file = '/etc/postgresql/pg_hba.conf'
EOF
done
