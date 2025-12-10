#!/bin/bash
# Create wordloom database

echo "Creating wordloom database..."
sudo -u postgres psql -c "CREATE DATABASE wordloom OWNER postgres;"
echo "✅ Database created"

echo "Testing connection from WSL2..."
psql -U postgres -h localhost -d wordloom -c "SELECT 'Connected!' as status;"
