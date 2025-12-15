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
        
        self.ticker_file_label = ttk.Label(ticker_frame, text="No file loaded")
        self.ticker_file_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(ticker_frame, text="Load Tickers", command=self.load_tickers).pack(side=tk.LEFT, padx=5)
        
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
        
        # Timeframes
        ttk.Label(pm_settings, text="Timeframes:").pack(side=tk.LEFT, padx=5)
        self.pm_timeframes = {}
        for tf in [5, 10, 15, 30, 60]:
            var = tk.BooleanVar(value=True)
            self.pm_timeframes[tf] = var
            ttk.Checkbutton(pm_settings, text=f"{tf}m", variable=var).pack(side=tk.LEFT, padx=2)
        
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
        
        columns = ('Ticker', 'Timeframe', 'TodayVol', 'Avg10DVol', 'RelVol', 'PercentDiff', 'Notes')
        self.pm_tree = ttk.Treeview(pm_table_frame, columns=columns, show='headings',
                                    yscrollcommand=pm_scroll_y.set, xscrollcommand=pm_scroll_x.set)
        
        pm_scroll_y.config(command=self.pm_tree.yview)
        pm_scroll_x.config(command=self.pm_tree.xview)
        
        # Configure columns
        self.pm_tree.heading('Ticker', text='Ticker', command=lambda: self.sort_treeview(self.pm_tree, 'Ticker', False, False))
        self.pm_tree.heading('Timeframe', text='Timeframe', command=lambda: self.sort_treeview(self.pm_tree, 'Timeframe', False, False))
        self.pm_tree.heading('TodayVol', text='Today Vol', command=lambda: self.sort_treeview(self.pm_tree, 'TodayVol', True, True))
        self.pm_tree.heading('Avg10DVol', text='Avg 10D Vol', command=lambda: self.sort_treeview(self.pm_tree, 'Avg10DVol', True, True))
        self.pm_tree.heading('RelVol', text='Rel Vol', command=lambda: self.sort_treeview(self.pm_tree, 'RelVol', True, True))
        self.pm_tree.heading('PercentDiff', text='% Diff', command=lambda: self.sort_treeview(self.pm_tree, 'PercentDiff', True, True))
        self.pm_tree.heading('Notes', text='Notes')
        
        self.pm_tree.column('Ticker', width=80)
        self.pm_tree.column('Timeframe', width=80)
        self.pm_tree.column('TodayVol', width=100)
        self.pm_tree.column('Avg10DVol', width=100)
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
        
        columns = ('Ticker', 'Timeframe', 'TodayVol', 'Avg10DVol', 'RelVol', 'PercentDiff', 'Notes')
        self.rth_tree = ttk.Treeview(rth_table_frame, columns=columns, show='headings',
                                     yscrollcommand=rth_scroll_y.set, xscrollcommand=rth_scroll_x.set)
        
        rth_scroll_y.config(command=self.rth_tree.yview)
        rth_scroll_x.config(command=self.rth_tree.xview)
        
        # Configure columns
        self.rth_tree.heading('Ticker', text='Ticker', command=lambda: self.sort_treeview(self.rth_tree, 'Ticker', False, False))
        self.rth_tree.heading('Timeframe', text='Timeframe', command=lambda: self.sort_treeview(self.rth_tree, 'Timeframe', False, False))
        self.rth_tree.heading('TodayVol', text='Today Vol', command=lambda: self.sort_treeview(self.rth_tree, 'TodayVol', True, True))
        self.rth_tree.heading('Avg10DVol', text='Avg 10D Vol', command=lambda: self.sort_treeview(self.rth_tree, 'Avg10DVol', True, True))
        self.rth_tree.heading('RelVol', text='Rel Vol', command=lambda: self.sort_treeview(self.rth_tree, 'RelVol', True, True))
        self.rth_tree.heading('PercentDiff', text='% Diff', command=lambda: self.sort_treeview(self.rth_tree, 'PercentDiff', True, True))
        self.rth_tree.heading('Notes', text='Notes')
        
        self.rth_tree.column('Ticker', width=80)
        self.rth_tree.column('Timeframe', width=80)
        self.rth_tree.column('TodayVol', width=100)
        self.rth_tree.column('Avg10DVol', width=100)
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
            
            self.tickers = tickers
            self.ticker_file_label.config(text=f"{len(tickers)} tickers loaded from {os.path.basename(file_path)}")
            messagebox.showinfo("Success", f"Loaded {len(tickers)} tickers")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tickers: {str(e)}")
    
    def update_scanners(self):
        """Update scanner configurations"""
        if not self.connected or not self.ibkr_client:
            return
        
        # Update pre-market scanner
        pm_timeframes = [tf for tf, var in self.pm_timeframes.items() if var.get()]
        pm_config = PreMarketConfig(
            timeframes=pm_timeframes if pm_timeframes else [5, 10, 15, 30, 60],
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
        
        # Run scan in thread
        thread = threading.Thread(target=self._scan_premarket_thread)
        thread.daemon = True
        thread.start()
    
    def _scan_premarket_thread(self):
        """Thread function for pre-market scan"""
        try:
            self.root.after(0, lambda: self.conn_status_label.config(text="Scanning Pre-Market...", foreground="orange"))
            
            pm_timeframes = [tf for tf, var in self.pm_timeframes.items() if var.get()]
            if not pm_timeframes:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "Please select at least one timeframe"))
                self.root.after(0, lambda: self.conn_status_label.config(text="Connected", foreground="green"))
                return
            
            # Update status with progress
            total_tickers = len(self.tickers)
            print(f"\nStarting Pre-Market scan: {total_tickers} tickers, {len(pm_timeframes)} timeframes")
            
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
                    # Add error result for this ticker
                    for tf in pm_timeframes:
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
                    valid_df = df[valid_mask]
                    filtered_valid = valid_df[
                        (valid_df['RelVol'] >= float(self.pm_min_rel_vol.get() or "3.0")) &
                        (valid_df['Avg10DVol'] >= int(self.pm_min_avg_vol.get() or "0"))
                    ]
                    error_df = df[~valid_mask]
                    df = pd.concat([filtered_valid, error_df], ignore_index=True)
            
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
            self.root.after(0, lambda: self.conn_status_label.config(text="Connected", foreground="green"))
            
            # Show summary message
            print(f"\nScan complete: {len(df)} results")
            if df.empty:
                self.root.after(0, lambda: messagebox.showinfo("Scan Complete", 
                    f"Scan completed but no results found.\n\n"
                    f"Scanned {total_tickers} tickers.\n\n"
                    "Check:\n"
                    "- Market is in pre-market hours (4:00 AM - 9:30 AM ET)\n"
                    "- Ticker symbols are correct\n"
                    "- Filters are not too restrictive\n"
                    "- Lower Min Rel Vol if needed\n\n"
                    "Check console for detailed error messages."))
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
        
        # Run scan in thread
        thread = threading.Thread(target=self._scan_rth_thread)
        thread.daemon = True
        thread.start()
    
    def _scan_rth_thread(self):
        """Thread function for RTH scan"""
        try:
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
                    valid_df = df[valid_mask]
                    filtered_valid = valid_df[
                        (valid_df['RelVol'] >= float(self.rth_min_rel_vol.get() or "3.0")) &
                        (valid_df['Avg10DVol'] >= int(self.rth_min_avg_vol.get() or "0"))
                    ]
                    error_df = df[~valid_mask]
                    df = pd.concat([filtered_valid, error_df], ignore_index=True)
            
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
            self.root.after(0, lambda: self.conn_status_label.config(text="Connected", foreground="green"))
            
            # Show summary message
            print(f"\nScan complete: {len(df)} results")
            if df.empty:
                self.root.after(0, lambda: messagebox.showinfo("Scan Complete", 
                    f"Scan completed but no results found.\n\n"
                    f"Scanned {total_tickers} tickers.\n\n"
                    "Check:\n"
                    "- Market is open (9:30 AM - 4:00 PM ET)\n"
                    "- Ticker symbols are correct\n"
                    "- Filters are not too restrictive\n"
                    "- Lower Min Rel Vol if needed\n\n"
                    "Check console for detailed error messages."))
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


def main():
    """Main entry point"""
    root = tk.Tk()
    app = DualVolumeScannerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

