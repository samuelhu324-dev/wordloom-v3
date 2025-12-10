#!/bin/bash
# Configure PostgreSQL to accept TCP connections with password authentication

echo "Configuring PostgreSQL for remote TCP connections..."

# Backup original pg_hba.conf
sudo cp /etc/postgresql/14/main/pg_hba.conf /etc/postgresql/14/main/pg_hba.conf.backup

# Add TCP connection line if not exists (allow from 127.0.0.1 and ::1 with password)
# The line should be before the existing IPv4/IPv6 lines
sudo sed -i '/^# IPv4 local connections:/i host    all             all             127.0.0.1/32            scram-sha-256' /etc/postgresql/14/main/pg_hba.conf

echo "✅ pg_hba.conf updated"

# Also update postgresql.conf to listen on localhost
echo "Configuring PostgreSQL to listen on localhost..."
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/g" /etc/postgresql/14/main/postgresql.conf

echo "✅ postgresql.conf updated"

# Restart PostgreSQL
echo "Restarting PostgreSQL..."
sudo service postgresql restart

echo "✅ PostgreSQL restarted"
echo ""
echo "Configuration complete!"
