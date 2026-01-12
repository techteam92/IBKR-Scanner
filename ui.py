"""
Dual Volume Scanner UI - Pre-Market and RTH Scanners
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from typing import List, Optional
import threading
from datetime import datetime
import os

from ibkr_client import IBKRClient
from scanner_premarket import PreMarketScanner
from scanner_rth import RTHScanner
from config import PreMarketConfig, RTHConfig, IBKRConfig, DEFAULT_IBKR_CONFIG


def show_auto_dismiss_warning(root, title, message, timeout=10):
    """
    Show a warning messagebox that automatically dismisses after timeout seconds
    
    Args:
        root: Tkinter root window
        title: Dialog title
        message: Message text
        timeout: Auto-dismiss timeout in seconds (default: 10)
    """
    # Create a Toplevel window that looks like a messagebox
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.geometry("500x300")
    dialog.transient(root)
    dialog.grab_set()  # Make it modal
    
    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    # Create frame with padding
    frame = ttk.Frame(dialog, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Warning icon (or just text)
    ttk.Label(frame, text="⚠️", font=("Arial", 24)).pack(pady=(0, 10))
    
    # Title
    ttk.Label(frame, text=title, font=("Arial", 12, "bold")).pack(pady=(0, 10))
    
    # Message (with word wrapping)
    message_label = ttk.Label(frame, text=message, wraplength=450, justify=tk.LEFT)
    message_label.pack(pady=(0, 20), fill=tk.BOTH, expand=True)
    
    # Countdown label
    countdown_label = ttk.Label(frame, text=f"Auto-closing in {timeout} seconds...", 
                                font=("Arial", 9), foreground="gray")
    countdown_label.pack(pady=(0, 10))
    
    # OK button
    ok_button = ttk.Button(frame, text="OK", command=dialog.destroy)
    ok_button.pack()
    
    # Auto-dismiss countdown
    def update_countdown(remaining):
        if remaining > 0:
            countdown_label.config(text=f"Auto-closing in {remaining} seconds...")
            root.after(1000, lambda: update_countdown(remaining - 1))
        else:
            dialog.destroy()
    
    # Start countdown
    root.after(1000, lambda: update_countdown(timeout - 1))
    
    # Focus on dialog
    dialog.focus_set()


class DualVolumeScannerUI:
    """Main UI for Dual Volume Scanner"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Dual Volume Scanner - Pre-Market & RTH")
        self.root.geometry("1400x900")
        
        # IBKR client
        self.ibkr_client = None
        self.connected = False
        
        # Scanners
        self.pm_scanner = None
        self.rth_scanner = None
        
        # Data
        self.tickers = []
        self.pm_results = pd.DataFrame()
        self.rth_results = pd.DataFrame()
        
        # Auto-refresh
        self.auto_refresh_enabled = False
        self.auto_refresh_interval = 60  # seconds
        self.auto_refresh_job = None
        self.last_update_time = None
        
        # Build UI
        self.build_ui()
        
        # Initialize scanners with default configs
        self.update_scanners()
    
    def build_ui(self):
        """Build the user interface"""
        # Top frame for connection and ticker input
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        # Connection frame
        conn_frame = ttk.LabelFrame(top_frame, text="IBKR Connection", padding="5")
        conn_frame.pack(side=tk.LEFT, padx=5)
        
        self.conn_status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.conn_status_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(conn_frame, text="Connect", command=self.connect_ibkr).pack(side=tk.LEFT, padx=5)
        ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_ibkr).pack(side=tk.LEFT, padx=5)
        
        # Ticker input frame
        ticker_frame = ttk.LabelFrame(top_frame, text="Ticker List", padding="5")
        ticker_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Direct input option
        input_row = ttk.Frame(ticker_frame)
        input_row.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(input_row, text="Enter Tickers:").pack(side=tk.LEFT, padx=5)
        self.ticker_input = tk.Text(input_row, height=2, width=40)
        self.ticker_input.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.ticker_input.insert("1.0", "AAPL, TSLA, SPY")  # Default example
        
        ttk.Button(input_row, text="Load from Input", command=self.load_tickers_from_input).pack(side=tk.LEFT, padx=5)
        
        # File load option (alternative)
        file_row = ttk.Frame(ticker_frame)
        file_row.pack(fill=tk.X)
        
        self.ticker_file_label = ttk.Label(file_row, text="Or load from file:")
        self.ticker_file_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(file_row, text="Load from File", command=self.load_tickers).pack(side=tk.LEFT, padx=5)
        
        # Auto-refresh frame
        refresh_frame = ttk.LabelFrame(top_frame, text="Auto-Refresh", padding="5")
        refresh_frame.pack(side=tk.LEFT, padx=5)
        
        self.auto_refresh_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(refresh_frame, text="Enable", variable=self.auto_refresh_var,
                       command=self.toggle_auto_refresh).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(refresh_frame, text="Interval (sec):").pack(side=tk.LEFT, padx=5)
        self.refresh_interval_var = tk.StringVar(value="60")
        ttk.Entry(refresh_frame, textvariable=self.refresh_interval_var, width=6).pack(side=tk.LEFT, padx=2)
        
        self.last_update_label = ttk.Label(refresh_frame, text="Last update: Never", foreground="gray")
        self.last_update_label.pack(side=tk.LEFT, padx=5)
        
        # Main container for two scanners
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Pre-Market Scanner Panel
        self.build_premarket_panel(main_container)
        
        # RTH Scanner Panel
        self.build_rth_panel(main_container)
    
    def build_premarket_panel(self, parent):
        """Build pre-market scanner panel"""
        pm_frame = ttk.LabelFrame(parent, text="Pre-Market Volume Scanner (04:00-09:30 ET)", padding="10")
        pm_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Settings frame
        pm_settings = ttk.Frame(pm_frame)
        pm_settings.pack(fill=tk.X, pady=5)
        
        # Enable checkbox
        self.pm_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(pm_settings, text="Enable Pre-Market Scanner", variable=self.pm_enabled,
                       command=self.update_scanners).pack(side=tk.LEFT, padx=5)
        
        # Min relative volume
        ttk.Label(pm_settings, text="Min Rel Vol:").pack(side=tk.LEFT, padx=5)
        self.pm_min_rel_vol = tk.StringVar(value="3.0")
        ttk.Entry(pm_settings, textvariable=self.pm_min_rel_vol, width=8).pack(side=tk.LEFT, padx=2)
        
        # Min avg volume
        ttk.Label(pm_settings, text="Min Avg Vol:").pack(side=tk.LEFT, padx=5)
        self.pm_min_avg_vol = tk.StringVar(value="0")
        ttk.Entry(pm_settings, textvariable=self.pm_min_avg_vol, width=10).pack(side=tk.LEFT, padx=2)
        
        # Scan button
        ttk.Button(pm_settings, text="Scan Pre-Market", command=self.scan_premarket).pack(side=tk.RIGHT, padx=5)
        
        # Results table
        pm_table_frame = ttk.Frame(pm_frame)
        pm_table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview with scrollbars
        pm_scroll_y = ttk.Scrollbar(pm_table_frame, orient=tk.VERTICAL)
        pm_scroll_x = ttk.Scrollbar(pm_table_frame, orient=tk.HORIZONTAL)
        
        columns = ('Ticker', 'Timeframe', 'TodayVol', 'Avg10DVol', 'DailyVol', 'RelVol', 'PercentDiff', 'Notes')
        self.pm_tree = ttk.Treeview(pm_table_frame, columns=columns, show='headings',
                                    yscrollcommand=pm_scroll_y.set, xscrollcommand=pm_scroll_x.set)
        
        pm_scroll_y.config(command=self.pm_tree.yview)
        pm_scroll_x.config(command=self.pm_tree.xview)
        
        # Configure columns
        self.pm_tree.heading('Ticker', text='Ticker', command=lambda: self.sort_treeview(self.pm_tree, 'Ticker', False, False))
        self.pm_tree.heading('Timeframe', text='Timeframe', command=lambda: self.sort_treeview(self.pm_tree, 'Timeframe', False, False))
        self.pm_tree.heading('TodayVol', text='Today Vol', command=lambda: self.sort_treeview(self.pm_tree, 'TodayVol', True, True))
        self.pm_tree.heading('Avg10DVol', text='Avg 10D Vol', command=lambda: self.sort_treeview(self.pm_tree, 'Avg10DVol', True, True))
        self.pm_tree.heading('DailyVol', text='Daily Vol', command=lambda: self.sort_treeview(self.pm_tree, 'DailyVol', True, True))
        self.pm_tree.heading('RelVol', text='Rel Vol', command=lambda: self.sort_treeview(self.pm_tree, 'RelVol', True, True))
        self.pm_tree.heading('PercentDiff', text='% Diff', command=lambda: self.sort_treeview(self.pm_tree, 'PercentDiff', True, True))
        self.pm_tree.heading('Notes', text='Notes')
        
        self.pm_tree.column('Ticker', width=80)
        self.pm_tree.column('Timeframe', width=80)
        self.pm_tree.column('TodayVol', width=100)
        self.pm_tree.column('Avg10DVol', width=100)
        self.pm_tree.column('DailyVol', width=110)
        self.pm_tree.column('RelVol', width=80)
        self.pm_tree.column('PercentDiff', width=80)
        self.pm_tree.column('Notes', width=200)
        
        # Pack treeview and scrollbars
        self.pm_tree.grid(row=0, column=0, sticky='nsew')
        pm_scroll_y.grid(row=0, column=1, sticky='ns')
        pm_scroll_x.grid(row=1, column=0, sticky='ew')
        pm_table_frame.grid_rowconfigure(0, weight=1)
        pm_table_frame.grid_columnconfigure(0, weight=1)
    
    def build_rth_panel(self, parent):
        """Build RTH scanner panel"""
        rth_frame = ttk.LabelFrame(parent, text="Regular Hours Volume Scanner (09:30-16:00 ET)", padding="10")
        rth_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Settings frame
        rth_settings = ttk.Frame(rth_frame)
        rth_settings.pack(fill=tk.X, pady=5)
        
        # Enable checkbox
        self.rth_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(rth_settings, text="Enable RTH Scanner", variable=self.rth_enabled,
                       command=self.update_scanners).pack(side=tk.LEFT, padx=5)
        
        # Timeframes
        ttk.Label(rth_settings, text="Timeframes:").pack(side=tk.LEFT, padx=5)
        self.rth_timeframes = {}
        for tf in [5, 10, 15, 30, 60]:
            var = tk.BooleanVar(value=True)
            self.rth_timeframes[tf] = var
            ttk.Checkbutton(rth_settings, text=f"{tf}m", variable=var).pack(side=tk.LEFT, padx=2)
        
        # Min relative volume
        ttk.Label(rth_settings, text="Min Rel Vol:").pack(side=tk.LEFT, padx=5)
        self.rth_min_rel_vol = tk.StringVar(value="3.0")
        ttk.Entry(rth_settings, textvariable=self.rth_min_rel_vol, width=8).pack(side=tk.LEFT, padx=2)
        
        # Min avg volume
        ttk.Label(rth_settings, text="Min Avg Vol:").pack(side=tk.LEFT, padx=5)
        self.rth_min_avg_vol = tk.StringVar(value="0")
        ttk.Entry(rth_settings, textvariable=self.rth_min_avg_vol, width=10).pack(side=tk.LEFT, padx=2)
        
        # Scan button
        ttk.Button(rth_settings, text="Scan RTH", command=self.scan_rth).pack(side=tk.RIGHT, padx=5)
        
        # Results table
        rth_table_frame = ttk.Frame(rth_frame)
        rth_table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview with scrollbars
        rth_scroll_y = ttk.Scrollbar(rth_table_frame, orient=tk.VERTICAL)
        rth_scroll_x = ttk.Scrollbar(rth_table_frame, orient=tk.HORIZONTAL)
        
        columns = ('Ticker', 'Timeframe', 'TodayVol', 'Avg10DVol', 'DailyVol', 'RelVol', 'PercentDiff', 'Notes')
        self.rth_tree = ttk.Treeview(rth_table_frame, columns=columns, show='headings',
                                     yscrollcommand=rth_scroll_y.set, xscrollcommand=rth_scroll_x.set)
        
        rth_scroll_y.config(command=self.rth_tree.yview)
        rth_scroll_x.config(command=self.rth_tree.xview)
        
        # Configure columns
        self.rth_tree.heading('Ticker', text='Ticker', command=lambda: self.sort_treeview(self.rth_tree, 'Ticker', False, False))
        self.rth_tree.heading('Timeframe', text='Timeframe', command=lambda: self.sort_treeview(self.rth_tree, 'Timeframe', False, False))
        self.rth_tree.heading('TodayVol', text='Today Vol', command=lambda: self.sort_treeview(self.rth_tree, 'TodayVol', True, True))
        self.rth_tree.heading('Avg10DVol', text='Avg 10D Vol', command=lambda: self.sort_treeview(self.rth_tree, 'Avg10DVol', True, True))
        self.rth_tree.heading('DailyVol', text='Daily Vol', command=lambda: self.sort_treeview(self.rth_tree, 'DailyVol', True, True))
        self.rth_tree.heading('RelVol', text='Rel Vol', command=lambda: self.sort_treeview(self.rth_tree, 'RelVol', True, True))
        self.rth_tree.heading('PercentDiff', text='% Diff', command=lambda: self.sort_treeview(self.rth_tree, 'PercentDiff', True, True))
        self.rth_tree.heading('Notes', text='Notes')
        
        self.rth_tree.column('Ticker', width=80)
        self.rth_tree.column('Timeframe', width=80)
        self.rth_tree.column('TodayVol', width=100)
        self.rth_tree.column('Avg10DVol', width=100)
        self.rth_tree.column('DailyVol', width=110)
        self.rth_tree.column('RelVol', width=80)
        self.rth_tree.column('PercentDiff', width=80)
        self.rth_tree.column('Notes', width=200)
        
        # Pack treeview and scrollbars
        self.rth_tree.grid(row=0, column=0, sticky='nsew')
        rth_scroll_y.grid(row=0, column=1, sticky='ns')
        rth_scroll_x.grid(row=1, column=0, sticky='ew')
        rth_table_frame.grid_rowconfigure(0, weight=1)
        rth_table_frame.grid_columnconfigure(0, weight=1)
    
    def connect_ibkr(self):
        """Connect to IBKR"""
        if self.connected:
            messagebox.showinfo("Info", "Already connected to IBKR")
            return
        
        try:
            self.ibkr_client = IBKRClient(
                host=DEFAULT_IBKR_CONFIG.host,
                port=DEFAULT_IBKR_CONFIG.port,
                client_id=DEFAULT_IBKR_CONFIG.client_id
            )
            
            if self.ibkr_client.connect_sync():
                self.connected = True
                self.conn_status_label.config(text="Connected", foreground="green")
                self.update_scanners()
                messagebox.showinfo("Success", "Connected to IBKR successfully")
            else:
                messagebox.showerror("Error", "Failed to connect to IBKR. Make sure TWS or IB Gateway is running.")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def disconnect_ibkr(self):
        """Disconnect from IBKR"""
        if self.ibkr_client:
            self.ibkr_client.disconnect()
            self.ibkr_client = None
        self.connected = False
        self.conn_status_label.config(text="Disconnected", foreground="red")
        self.pm_scanner = None
        self.rth_scanner = None
    
    def load_tickers_from_input(self):
        """Load ticker list from direct input"""
        try:
            # Get text from input field
            input_text = self.ticker_input.get("1.0", tk.END).strip()
            
            if not input_text:
                messagebox.showwarning("Warning", "Please enter at least one ticker symbol")
                return
            
            tickers = []
            # Parse input - handle comma, space, or newline separated
            for separator in [',', '\n', ' ', '\t']:
                if separator in input_text:
                    parts = input_text.split(separator)
                    for part in parts:
                        ticker = part.strip().upper()
                        if ticker and not ticker.startswith('#'):
                            # Remove any extra characters
                            ticker = ''.join(c for c in ticker if c.isalnum() or c in ['.', '-'])
                            if ticker:
                                tickers.append(ticker)
                    break
            
            # If no separator found, treat entire input as single ticker
            if not tickers:
                ticker = input_text.strip().upper()
                ticker = ''.join(c for c in ticker if c.isalnum() or c in ['.', '-'])
                if ticker:
                    tickers.append(ticker)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tickers = []
            for ticker in tickers:
                if ticker not in seen:
                    seen.add(ticker)
                    unique_tickers.append(ticker)
            
            if not unique_tickers:
                messagebox.showwarning("Warning", "No valid ticker symbols found")
                return
            
            self.tickers = unique_tickers
            self.ticker_file_label.config(text=f"{len(unique_tickers)} tickers loaded from input")
            messagebox.showinfo("Success", f"Loaded {len(unique_tickers)} ticker(s): {', '.join(unique_tickers[:10])}{'...' if len(unique_tickers) > 10 else ''}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tickers: {str(e)}")
    
    def load_tickers(self):
        """Load ticker list from file"""
        file_path = filedialog.askopenfilename(
            title="Select Ticker List",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            tickers = []
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Handle CSV format
                        if ',' in line:
                            ticker = line.split(',')[0].strip().upper()
                        else:
                            ticker = line.upper()
                        if ticker:
                            tickers.append(ticker)
            
            # Remove duplicates
            seen = set()
            unique_tickers = []
            for ticker in tickers:
                if ticker not in seen:
                    seen.add(ticker)
                    unique_tickers.append(ticker)
            
            self.tickers = unique_tickers
            self.ticker_file_label.config(text=f"{len(unique_tickers)} tickers loaded from {os.path.basename(file_path)}")
            messagebox.showinfo("Success", f"Loaded {len(unique_tickers)} ticker(s) from file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tickers: {str(e)}")
    
    def update_scanners(self):
        """Update scanner configurations"""
        if not self.connected or not self.ibkr_client:
            return
        
        # Update pre-market scanner
        # Premarket doesn't use timeframes (only Total PM volume)
        pm_config = PreMarketConfig(
            timeframes=[],  # Empty list - only Total PM volume will be calculated
            min_relative_volume=float(self.pm_min_rel_vol.get() or "3.0"),
            min_avg_volume=int(self.pm_min_avg_vol.get() or "0"),
            enabled=self.pm_enabled.get()
        )
        self.pm_scanner = PreMarketScanner(pm_config, self.ibkr_client)
        
        # Update RTH scanner
        rth_timeframes = [tf for tf, var in self.rth_timeframes.items() if var.get()]
        rth_config = RTHConfig(
            timeframes=rth_timeframes if rth_timeframes else [5, 10, 15, 30, 60],
            min_relative_volume=float(self.rth_min_rel_vol.get() or "3.0"),
            min_avg_volume=int(self.rth_min_avg_vol.get() or "0"),
            enabled=self.rth_enabled.get()
        )
        self.rth_scanner = RTHScanner(rth_config, self.ibkr_client)
    
    def scan_premarket(self):
        """Scan pre-market volume"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to IBKR")
            return
        
        if not self.tickers:
            messagebox.showerror("Error", "No tickers loaded")
            return
        
        # Update scanner config
        self.update_scanners()
        
        # IMPORTANT:
        # IBKR (ib_insync) historical data calls must run in the main thread.
        # Running them from a background thread causes timeouts / no data.
        # So we run the scan synchronously in the main thread.
        self._scan_premarket_thread()
    
    def _scan_premarket_thread(self, is_auto_refresh=False):
        """Thread function for pre-market scan"""
        try:
            if not is_auto_refresh:
                self.root.after(0, lambda: self.conn_status_label.config(text="Scanning Pre-Market...", foreground="orange"))
            
            # Premarket only uses Total PM volume (no timeframes)
            pm_timeframes = []
            
            # Update status with progress
            total_tickers = len(self.tickers)
            print(f"\nStarting Pre-Market scan: {total_tickers} tickers (Total PM volume only)")
            
            # Scan with progress updates
            all_results = []
            for idx, ticker in enumerate(self.tickers, 1):
                status_msg = f"Scanning Pre-Market... ({idx}/{total_tickers}) {ticker}"
                # Use default parameter to capture value correctly
                self.root.after(0, lambda s=status_msg: self.conn_status_label.config(text=s, foreground="orange"))
                print(f"Scanning {ticker} ({idx}/{total_tickers})...")
                
                try:
                    ticker_results = self.pm_scanner.scan_ticker(ticker, pm_timeframes)
                    all_results.extend(ticker_results)
                    print(f"  ✓ {ticker}: {len(ticker_results)} results")
                except Exception as e:
                    print(f"  ✗ {ticker}: Error - {str(e)}")
                    # Add error result for this ticker (Total PM row only)
                    all_results.append({
                        'Ticker': ticker,
                        'Timeframe': 'Total PM',
                        'TodayVol': 0,
                        'Avg10DVol': 0,
                        'DailyVol': 0,
                        'RelVol': 0.0,
                        'PercentDiff': 0.0,
                        'Notes': f"Error: {str(e)}"
                    })
            
            # Create DataFrame and apply filters
            import pandas as pd
            df = pd.DataFrame(all_results)
            
            if not df.empty:
                # Apply filters - but keep errors and "No data" results
                valid_mask = (~df['Notes'].str.contains('Error|No data|IP mismatch', case=False, na=False))
                
                if valid_mask.any():
                    valid_df = df[valid_mask].copy()
                    min_rel_vol = float(self.pm_min_rel_vol.get() or "3.0")
                    min_avg_vol = int(self.pm_min_avg_vol.get() or "0")
                    
                    # Add notes for filtered results
                    below_rel_vol = valid_df['RelVol'] < min_rel_vol
                    below_avg_vol = valid_df['Avg10DVol'] < min_avg_vol
                    
                    valid_df.loc[below_rel_vol, 'Notes'] = valid_df.loc[below_rel_vol, 'Notes'].apply(
                        lambda x: f"Below min rel vol ({min_rel_vol}x)" if not x else x
                    )
                    valid_df.loc[below_avg_vol, 'Notes'] = valid_df.loc[below_avg_vol, 'Notes'].apply(
                        lambda x: f"Below min avg vol ({min_avg_vol})" if not x else x
                    )
                    
                    # Keep results that pass filters
                    filtered_valid = valid_df[
                        (valid_df['RelVol'] >= min_rel_vol) &
                        (valid_df['Avg10DVol'] >= min_avg_vol)
                    ]
                    
                    # Keep filtered-out results with notes explaining why
                    filtered_out = valid_df[
                        (valid_df['RelVol'] < min_rel_vol) |
                        (valid_df['Avg10DVol'] < min_avg_vol)
                    ]
                    
                    error_df = df[~valid_mask]
                    # Combine: passed filters + filtered out (with notes) + errors
                    df = pd.concat([filtered_valid, filtered_out, error_df], ignore_index=True)
                    
                    # Print diagnostic info (only for manual scans, not auto-refresh)
                    if len(filtered_out) > 0 and not getattr(self, '_is_auto_refresh_scan', False):
                        print(f"\n⚠️  {len(filtered_out)} results filtered out:")
                        print(f"   Min RelVol: {min_rel_vol}x, Min AvgVol: {min_avg_vol}")
                        print(f"   {len(filtered_valid)} results passed filters")
                    elif len(filtered_out) > 0 and getattr(self, '_is_auto_refresh_scan', False):
                        # Quiet mode for auto-refresh
                        print(f"   [{len(filtered_valid)}/{len(valid_df)} passed filters]")
                else:
                    # All results are errors/no data
                    df = df
            
            self.pm_results = df
            
            # Print results summary to terminal
            print("\n" + "="*80)
            print("PRE-MARKET SCAN RESULTS SUMMARY")
            print("="*80)
            if df.empty:
                print("No results found (all filtered out or errors)")
            else:
                print(f"Total results: {len(df)}")
                print("\nResults by Ticker:")
                print("-"*80)
                for ticker in df['Ticker'].unique():
                    ticker_df = df[df['Ticker'] == ticker]
                    print(f"\n{ticker}:")
                    for _, row in ticker_df.iterrows():
                        print(f"  {row['Timeframe']:>6} | TodayVol: {row['TodayVol']:>10,} | "
                              f"Avg10DVol: {row['Avg10DVol']:>10,} | "
                              f"RelVol: {row['RelVol']:>6.2f}x | "
                              f"%Diff: {row['PercentDiff']:>7.1f}% | "
                              f"{row['Notes']}")
                print("\n" + "="*80)
            
            # Update UI in main thread
            self.root.after(0, lambda: self.update_pm_table(df))
            self.root.after(0, lambda: self.update_last_update_time())
            self.root.after(0, lambda: self.conn_status_label.config(text="Connected", foreground="green"))
            
            # Schedule next auto-refresh if enabled
            self.root.after(0, lambda: self.schedule_next_refresh())
            
            # Show summary message
            print(f"\nScan complete: {len(df)} results")
            
            # Count results by type
            if not df.empty:
                passed_filters = len(df[~df['Notes'].str.contains('Below min|Error|No data|IP mismatch', case=False, na=False)])
                filtered_out = len(df[df['Notes'].str.contains('Below min', case=False, na=False)])
                errors = len(df[df['Notes'].str.contains('Error|No data|IP mismatch', case=False, na=False)])
                
                if passed_filters == 0 and filtered_out > 0:
                    # Results exist but all filtered out
                    min_rel_vol = float(self.pm_min_rel_vol.get() or "3.0")
                    min_avg_vol = int(self.pm_min_avg_vol.get() or "0")
                    msg = (f"Scan completed: {len(df)} results found, but all were filtered out.\n\n"
                           f"Scanned {total_tickers} tickers.\n\n"
                           f"Current filters:\n"
                           f"- Min RelVol: {min_rel_vol}x\n"
                           f"- Min AvgVol: {min_avg_vol}\n\n"
                           f"💡 Tip: Lower the Min RelVol threshold (try 1.0 or 2.0) to see results.\n"
                           f"Filtered results are still shown in the table with notes.\n\n"
                           f"Check console for detailed results.")
                    self.root.after(0, lambda: show_auto_dismiss_warning(self.root, "Scan Complete - All Filtered", msg))
                elif df.empty:
                    self.root.after(0, lambda: messagebox.showinfo("Scan Complete", 
                        f"Scan completed but no results found.\n\n"
                        f"Scanned {total_tickers} tickers.\n\n"
                        "Check:\n"
                        "- Market is in pre-market hours (4:00 AM - 9:30 AM ET)\n"
                        "- Ticker symbols are correct\n"
                        "- Check console for detailed error messages."))
            else:
                count = len(df)
                self.root.after(0, lambda: self.conn_status_label.config(
                    text=f"Connected - {count} results found", foreground="green"))
        except Exception as e:
            import traceback
            error_msg = f"Scan error: {str(e)}\n\n{traceback.format_exc()}"
            print(f"\nFATAL ERROR: {error_msg}")
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.conn_status_label.config(text="Connected", foreground="green"))
    
    def scan_rth(self):
        """Scan RTH volume"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to IBKR")
            return
        
        if not self.tickers:
            messagebox.showerror("Error", "No tickers loaded")
            return
        
        # Update scanner config
        self.update_scanners()
        
        # IMPORTANT:
        # IBKR (ib_insync) historical data calls must run in the main thread.
        # Running them from a background thread causes timeouts / no data.
        # So we run the scan synchronously in the main thread.
        self._scan_rth_thread()
    
    def _scan_rth_thread(self, is_auto_refresh=False):
        """Thread function for RTH scan"""
        try:
            if not is_auto_refresh:
                self.root.after(0, lambda: self.conn_status_label.config(text="Scanning RTH...", foreground="orange"))
            
            rth_timeframes = [tf for tf, var in self.rth_timeframes.items() if var.get()]
            if not rth_timeframes:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "Please select at least one timeframe"))
                self.root.after(0, lambda: self.conn_status_label.config(text="Connected", foreground="green"))
                return
            
            # Update status with progress
            total_tickers = len(self.tickers)
            print(f"\nStarting RTH scan: {total_tickers} tickers, {len(rth_timeframes)} timeframes")
            
            # Scan with progress updates
            all_results = []
            for idx, ticker in enumerate(self.tickers, 1):
                status_msg = f"Scanning RTH... ({idx}/{total_tickers}) {ticker}"
                # Use default parameter to capture value correctly
                self.root.after(0, lambda s=status_msg: self.conn_status_label.config(text=s, foreground="orange"))
                print(f"Scanning {ticker} ({idx}/{total_tickers})...")
                
                try:
                    ticker_results = self.rth_scanner.scan_ticker(ticker, rth_timeframes)
                    all_results.extend(ticker_results)
                    print(f"  ✓ {ticker}: {len(ticker_results)} results")
                except Exception as e:
                    print(f"  ✗ {ticker}: Error - {str(e)}")
                    # Add error result for this ticker
                    for tf in rth_timeframes:
                        all_results.append({
                            'Ticker': ticker,
                            'Timeframe': f"{tf}m",
                            'TodayVol': 0,
                            'Avg10DVol': 0,
                            'RelVol': 0.0,
                            'PercentDiff': 0.0,
                            'Notes': f"Error: {str(e)}"
                        })
            
            # Create DataFrame and apply filters
            import pandas as pd
            df = pd.DataFrame(all_results)
            
            if not df.empty:
                # Apply filters - but keep errors and "No data" results
                valid_mask = (~df['Notes'].str.contains('Error|No data|IP mismatch', case=False, na=False))
                
                if valid_mask.any():
                    valid_df = df[valid_mask].copy()
                    min_rel_vol = float(self.rth_min_rel_vol.get() or "3.0")
                    min_avg_vol = int(self.rth_min_avg_vol.get() or "0")
                    
                    # Add notes for filtered results
                    below_rel_vol = valid_df['RelVol'] < min_rel_vol
                    below_avg_vol = valid_df['Avg10DVol'] < min_avg_vol
                    
                    valid_df.loc[below_rel_vol, 'Notes'] = valid_df.loc[below_rel_vol, 'Notes'].apply(
                        lambda x: f"Below min rel vol ({min_rel_vol}x)" if not x else x
                    )
                    valid_df.loc[below_avg_vol, 'Notes'] = valid_df.loc[below_avg_vol, 'Notes'].apply(
                        lambda x: f"Below min avg vol ({min_avg_vol})" if not x else x
                    )
                    
                    # Keep results that pass filters
                    filtered_valid = valid_df[
                        (valid_df['RelVol'] >= min_rel_vol) &
                        (valid_df['Avg10DVol'] >= min_avg_vol)
                    ]
                    
                    # Keep filtered-out results with notes explaining why
                    filtered_out = valid_df[
                        (valid_df['RelVol'] < min_rel_vol) |
                        (valid_df['Avg10DVol'] < min_avg_vol)
                    ]
                    
                    error_df = df[~valid_mask]
                    # Combine: passed filters + filtered out (with notes) + errors
                    df = pd.concat([filtered_valid, filtered_out, error_df], ignore_index=True)
                    
                    # Print diagnostic info (only for manual scans, not auto-refresh)
                    if len(filtered_out) > 0 and not getattr(self, '_is_auto_refresh_scan', False):
                        print(f"\n⚠️  {len(filtered_out)} results filtered out:")
                        print(f"   Min RelVol: {min_rel_vol}x, Min AvgVol: {min_avg_vol}")
                        print(f"   {len(filtered_valid)} results passed filters")
                    elif len(filtered_out) > 0 and getattr(self, '_is_auto_refresh_scan', False):
                        # Quiet mode for auto-refresh
                        print(f"   [{len(filtered_valid)}/{len(valid_df)} passed filters]")
                else:
                    # All results are errors/no data
                    df = df
            
            self.rth_results = df
            
            # Print results summary to terminal
            print("\n" + "="*80)
            print("RTH SCAN RESULTS SUMMARY")
            print("="*80)
            if df.empty:
                print("No results found (all filtered out or errors)")
            else:
                print(f"Total results: {len(df)}")
                print("\nResults by Ticker:")
                print("-"*80)
                for ticker in df['Ticker'].unique():
                    ticker_df = df[df['Ticker'] == ticker]
                    print(f"\n{ticker}:")
                    for _, row in ticker_df.iterrows():
                        print(f"  {row['Timeframe']:>6} | TodayVol: {row['TodayVol']:>10,} | "
                              f"Avg10DVol: {row['Avg10DVol']:>10,} | "
                              f"RelVol: {row['RelVol']:>6.2f}x | "
                              f"%Diff: {row['PercentDiff']:>7.1f}% | "
                              f"{row['Notes']}")
                print("\n" + "="*80)
            
            # Update UI in main thread
            self.root.after(0, lambda: self.update_rth_table(df))
            self.root.after(0, lambda: self.update_last_update_time())
            self.root.after(0, lambda: self.conn_status_label.config(text="Connected", foreground="green"))
            
            # Schedule next auto-refresh if enabled
            self.root.after(0, lambda: self.schedule_next_refresh())
            
            # Show summary message
            print(f"\nScan complete: {len(df)} results")
            
            # Count results by type
            if not df.empty:
                passed_filters = len(df[~df['Notes'].str.contains('Below min|Error|No data|IP mismatch', case=False, na=False)])
                filtered_out = len(df[df['Notes'].str.contains('Below min', case=False, na=False)])
                errors = len(df[df['Notes'].str.contains('Error|No data|IP mismatch', case=False, na=False)])
                
                if passed_filters == 0 and filtered_out > 0:
                    # Results exist but all filtered out
                    min_rel_vol = float(self.rth_min_rel_vol.get() or "3.0")
                    min_avg_vol = int(self.rth_min_avg_vol.get() or "0")
                    msg = (f"Scan completed: {len(df)} results found, but all were filtered out.\n\n"
                           f"Scanned {total_tickers} tickers.\n\n"
                           f"Current filters:\n"
                           f"- Min RelVol: {min_rel_vol}x\n"
                           f"- Min AvgVol: {min_avg_vol}\n\n"
                           f"💡 Tip: Lower the Min RelVol threshold (try 1.0 or 2.0) to see results.\n"
                           f"Filtered results are still shown in the table with notes.\n\n"
                           f"Check console for detailed results.")
                    self.root.after(0, lambda: show_auto_dismiss_warning(self.root, "Scan Complete - All Filtered", msg))
                elif df.empty:
                    self.root.after(0, lambda: messagebox.showinfo("Scan Complete", 
                        f"Scan completed but no results found.\n\n"
                        f"Scanned {total_tickers} tickers.\n\n"
                        "Check:\n"
                        "- Market is open (9:30 AM - 4:00 PM ET)\n"
                        "- Ticker symbols are correct\n"
                        "- Check console for detailed error messages."))
            else:
                count = len(df)
                self.root.after(0, lambda: self.conn_status_label.config(
                    text=f"Connected - {count} results found", foreground="green"))
        except Exception as e:
            import traceback
            error_msg = f"Scan error: {str(e)}\n\n{traceback.format_exc()}"
            print(f"\nFATAL ERROR: {error_msg}")
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.conn_status_label.config(text="Connected", foreground="green"))
    
    def update_pm_table(self, df: pd.DataFrame):
        """Update pre-market results table"""
        # Clear existing items
        for item in self.pm_tree.get_children():
            self.pm_tree.delete(item)
        
        # Add new items
        if df.empty:
            # Show message if no results
            self.pm_tree.insert('', 'end', values=(
                'No Results', '', '', '', '', '', 
                'No data found. Check: 1) Market is open, 2) Tickers are valid, 3) Filters are not too restrictive'
            ))
        else:
            # Default sort by RelVol descending (handle errors with 0.0 RelVol)
            df_sorted = df.sort_values('RelVol', ascending=False)
            
            for _, row in df_sorted.iterrows():
                self.pm_tree.insert('', 'end', values=(
                    row['Ticker'],
                    row['Timeframe'],
                    row['TodayVol'],
                    row['Avg10DVol'],
                    row.get('DailyVol', 0),
                    row['RelVol'],
                    row['PercentDiff'],
                    row['Notes']
                ))
    
    def update_rth_table(self, df: pd.DataFrame):
        """Update RTH results table"""
        # Clear existing items
        for item in self.rth_tree.get_children():
            self.rth_tree.delete(item)
        
        # Add new items
        if df.empty:
            # Show message if no results
            self.rth_tree.insert('', 'end', values=(
                'No Results', '', '', '', '', '', 
                'No data found. Check: 1) Market is open, 2) Tickers are valid, 3) Filters are not too restrictive'
            ))
        else:
            # Default sort by RelVol descending (handle errors with 0.0 RelVol)
            df_sorted = df.sort_values('RelVol', ascending=False)
            
            for _, row in df_sorted.iterrows():
                self.rth_tree.insert('', 'end', values=(
                    row['Ticker'],
                    row['Timeframe'],
                    row['TodayVol'],
                    row['Avg10DVol'],
                    row.get('DailyVol', 0),
                    row['RelVol'],
                    row['PercentDiff'],
                    row['Notes']
                ))
    
    def sort_treeview(self, tree: ttk.Treeview, col: str, numeric: bool = False, reverse: bool = False):
        """Sort treeview by column"""
        # Get all items
        items = [(tree.set(item, col), item) for item in tree.get_children('')]
        
        # Sort
        if numeric:
            try:
                items.sort(key=lambda x: float(x[0]) if x[0] else 0, reverse=reverse)
            except ValueError:
                items.sort(key=lambda x: x[0], reverse=reverse)
        else:
            items.sort(key=lambda x: x[0], reverse=reverse)
        
        # Rearrange items
        for index, (val, item) in enumerate(items):
            tree.move(item, '', index)
        
        # Toggle reverse for next click
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, numeric, not reverse))
    
    def toggle_auto_refresh(self):
        """Enable/disable auto-refresh"""
        self.auto_refresh_enabled = self.auto_refresh_var.get()
        if self.auto_refresh_enabled:
            # Start auto-refresh
            try:
                self.auto_refresh_interval = int(self.refresh_interval_var.get() or "60")
                if self.auto_refresh_interval < 10:
                    self.auto_refresh_interval = 10  # Minimum 10 seconds
                    self.refresh_interval_var.set("10")
                    messagebox.showwarning("Warning", "Auto-refresh interval set to minimum 10 seconds")
            except ValueError:
                self.auto_refresh_interval = 60
                self.refresh_interval_var.set("60")
                messagebox.showerror("Error", "Invalid interval. Using default 60 seconds")
            
            print(f"Auto-refresh enabled: {self.auto_refresh_interval} seconds")
            self.schedule_next_refresh()
        else:
            # Stop auto-refresh
            if self.auto_refresh_job:
                self.root.after_cancel(self.auto_refresh_job)
                self.auto_refresh_job = None
            print("Auto-refresh disabled")
    
    def schedule_next_refresh(self):
        """Schedule the next auto-refresh"""
        if not self.auto_refresh_enabled:
            return
        
        if not self.connected or not self.tickers:
            # Can't refresh if not connected or no tickers
            return
        
        # Cancel existing job if any
        if self.auto_refresh_job:
            self.root.after_cancel(self.auto_refresh_job)
        
        # Schedule next refresh
        interval_ms = self.auto_refresh_interval * 1000
        self.auto_refresh_job = self.root.after(interval_ms, self.auto_refresh_scan)
        print(f"Next auto-refresh scheduled in {self.auto_refresh_interval} seconds")
    
    def auto_refresh_scan(self):
        """Perform auto-refresh scan"""
        if not self.auto_refresh_enabled or not self.connected or not self.tickers:
            return
        
        # Set flag to indicate this is an auto-refresh scan (for quieter output)
        self._is_auto_refresh_scan = True
        
        print(f"\n{'='*80}")
        print(f"AUTO-REFRESH: Starting automatic scan at {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}")
        
        # Update interval in case user changed it
        try:
            new_interval = int(self.refresh_interval_var.get() or "60")
            if new_interval != self.auto_refresh_interval:
                self.auto_refresh_interval = new_interval
                print(f"Auto-refresh interval updated to {self.auto_refresh_interval} seconds")
        except ValueError:
            pass
        
        # Determine which scanner to run based on current time
        from datetime import time as dt_time
        import pytz
        
        et_tz = pytz.timezone('US/Eastern')
        now_et = datetime.now(et_tz)
        current_time = now_et.time()
        
        # Pre-market: 04:00-09:30 ET
        # RTH: 09:30-16:00 ET
        pm_start = dt_time(4, 0)
        pm_end = dt_time(9, 30)
        rth_start = dt_time(9, 30)
        rth_end = dt_time(16, 0)
        
        scan_pm = pm_start <= current_time < pm_end
        scan_rth = rth_start <= current_time < rth_end
        
        # Run appropriate scans
        if scan_pm:
            print("Running Pre-Market scan (auto-refresh)...")
            self._scan_premarket_thread(is_auto_refresh=True)
        
        if scan_rth:
            print("Running RTH scan (auto-refresh)...")
            self._scan_rth_thread(is_auto_refresh=True)
        
        if not scan_pm and not scan_rth:
            print(f"Outside market hours ({current_time.strftime('%H:%M')} ET). Skipping auto-refresh.")
            # Schedule next refresh anyway
            self.schedule_next_refresh()
        
        # Clear the auto-refresh flag
        self._is_auto_refresh_scan = False
    
    def update_last_update_time(self):
        """Update the last update time label"""
        self.last_update_time = datetime.now()
        time_str = self.last_update_time.strftime('%H:%M:%S')
        self.last_update_label.config(text=f"Last update: {time_str}", foreground="green")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = DualVolumeScannerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

