#!/bin/bash
# Set PostgreSQL password
echo "Setting postgres user password..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'pgpass';"
echo "Password set successfully!"

# Verify connection
echo ""
echo "Testing connection..."
psql -U postgres -h localhost -d postgres -c "SELECT version();"
