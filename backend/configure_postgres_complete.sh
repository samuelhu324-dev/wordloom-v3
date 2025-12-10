#!/bin/bash
# Configure PostgreSQL to accept connections from Windows host

echo "Getting WSL2 IP address..."
WSL2_IP=$(hostname -I | awk '{print $1}')
echo "WSL2 IP: $WSL2_IP"

# Update postgresql.conf to listen on all interfaces
echo ""
echo "Configuring postgresql.conf to listen on 0.0.0.0..."
sudo sed -i "s/listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/14/main/postgresql.conf

# Add line to pg_hba.conf to allow from Windows/WSL host
echo ""
echo "Updating pg_hba.conf for TCP connections..."

# Check if Windows connection line already exists
if ! sudo grep -q "host    all             all             0.0.0.0/0" /etc/postgresql/14/main/pg_hba.conf; then
    # Add before the existing IPv4 local connections line
    sudo sed -i '/^# IPv4 local connections:/i host    all             all             0.0.0.0/0               scram-sha-256' /etc/postgresql/14/main/pg_hba.conf
    echo "✅ Added 0.0.0.0/0 to pg_hba.conf"
else
    echo "✅ Connection line already exists"
fi

# Restart PostgreSQL
echo ""
echo "Restarting PostgreSQL..."
sudo service postgresql restart

echo ""
echo "✅ PostgreSQL configuration updated!"
echo "   Listen address: 0.0.0.0"
echo "   Auth method: scram-sha-256"
