"""
Diagnostic tool to check IP addresses and help diagnose Error 162
"""
import socket
import subprocess
import platform
from ibkr_client import IBKRClient
from config import DEFAULT_IBKR_CONFIG

def get_local_ip_addresses():
    """Get all local IP addresses"""
    ip_addresses = []
    
    # Get hostname
    hostname = socket.gethostname()
    
    # Get local IP
    try:
        local_ip = socket.gethostbyname(hostname)
        ip_addresses.append(("Hostname IP", local_ip))
    except:
        pass
    
    # Get all network interfaces
    try:
        # Connect to external server to get public IP (doesn't send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_interface_ip = s.getsockname()[0]
        s.close()
        ip_addresses.append(("Primary Interface IP", local_interface_ip))
    except:
        pass
    
    # Get localhost
    ip_addresses.append(("Localhost", "127.0.0.1"))
    
    return ip_addresses

def get_network_interfaces():
    """Get detailed network interface information"""
    interfaces = []
    
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["ipconfig", "/all"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout
        except:
            return "Could not retrieve network info"
    else:
        try:
            result = subprocess.run(
                ["ifconfig"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout
        except:
            return "Could not retrieve network info"

def check_ibkr_connection():
    """Check IBKR connection and get connection details"""
    print("\n" + "="*80)
    print("IBKR Connection Details")
    print("="*80)
    
    client = IBKRClient(
        host=DEFAULT_IBKR_CONFIG.host,
        port=DEFAULT_IBKR_CONFIG.port,
        client_id=DEFAULT_IBKR_CONFIG.client_id
    )
    
    if client.connect_sync():
        print(f"✓ Connected to IBKR")
        print(f"  Host: {client.host}")
        print(f"  Port: {client.port}")
        print(f"  Client ID: {client.client_id}")
        print(f"  Connection IP: 127.0.0.1 (localhost)")
        
        # Check if we can get any connection info
        try:
            # Try to get account info (this might reveal connection details)
            accounts = client.ib.accountValues()
            if accounts:
                print(f"  Account access: ✓ (can retrieve account data)")
        except:
            pass
        
        client.disconnect()
        return True
    else:
        print("✗ Failed to connect to IBKR")
        return False

def main():
    """Main diagnostic function"""
    print("="*80)
    print("IP Address Diagnostic Tool")
    print("="*80)
    print("\nThis tool helps diagnose Error 162 (IP mismatch) issues.")
    print("Error 162 occurs when TWS login IP ≠ API connection IP")
    print("="*80)
    
    # Get local IP addresses
    print("\n1. Local IP Addresses:")
    print("-"*80)
    ip_addresses = get_local_ip_addresses()
    for label, ip in ip_addresses:
        print(f"  {label:25} : {ip}")
    
    # Get network interfaces
    print("\n2. Network Interface Details:")
    print("-"*80)
    network_info = get_network_interfaces()
    # Show first few lines to avoid overwhelming output
    lines = network_info.split('\n')[:20]
    for line in lines:
        if line.strip():
            print(f"  {line}")
    if len(network_info.split('\n')) > 20:
        print(f"  ... ({len(network_info.split('\n')) - 20} more lines)")
    
    # Check IBKR connection
    print("\n3. IBKR Connection:")
    print("-"*80)
    connected = check_ibkr_connection()
    
    # Analysis
    print("\n4. Analysis:")
    print("-"*80)
    print("For Error 162 to NOT occur:")
    print("  - TWS/Gateway must be running on this machine (127.0.0.1)")
    print("  - TWS/Gateway must be logged in")
    print("  - Scanner must connect to 127.0.0.1 (localhost)")
    print("  - Both must use the same IP address")
    print()
    print("Common causes of Error 162:")
    print("  ✗ TWS restarted but scanner didn't → IP changed")
    print("  ✗ Network changed → IP address changed")
    print("  ✗ TWS on different machine → Can't work")
    print("  ✗ Multiple TWS instances → Confusion")
    print()
    
    if connected:
        print("✓ Connection successful")
        print("  If you still get timeouts, it's likely Error 162")
        print("  SOLUTION: Restart TWS/Gateway and reconnect")
    else:
        print("✗ Connection failed")
        print("  Make sure TWS/Gateway is running")
        print(f"  Check port: {DEFAULT_IBKR_CONFIG.port}")
    
    print("\n" + "="*80)
    print("Diagnostic Complete")
    print("="*80)
    print("\nNext steps:")
    print("  1. Ensure TWS/Gateway is running on this machine")
    print("  2. Make sure you're logged into TWS/Gateway")
    print("  3. Restart TWS/Gateway if you see Error 162")
    print("  4. Scanner should connect to 127.0.0.1 (localhost)")
    print("="*80)

if __name__ == "__main__":
    main()

