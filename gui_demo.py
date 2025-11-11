"""
Enhanced GUI to display eBay and Amazon search results with images and all filter options
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import webbrowser
from EbayAPI.ebay_call import search_ebay, display_results as ebay_display_results
from RapidAmazon.rapidapi_amazon import search_amazon


def load_image_from_url(url, size=(150, 150)):
    """
    Download and resize an image from a URL.
    
    Args:
        url (str): Image URL
        size (tuple): Target size (width, height)
    
    Returns:
        ImageTk.PhotoImage: Tkinter-compatible image
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        # Open image from bytes
        img = Image.open(BytesIO(response.content))
        
        # Resize to fit
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


class ProductDisplayGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("eBay & Amazon Product Search - Enhanced")
        self.root.geometry("1200x750")
        
        # Keep references to images so they don't get garbage collected
        self.image_references = []
        self.current_ebay_items = []  # Store current eBay results
        self.current_amazon_items = []  # Store current Amazon results
        
        # Create main container
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Search section - Now with multiple rows for all filters
        search_frame = ttk.LabelFrame(main_frame, text="Search Filters", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Row 0: Product and Price
        ttk.Label(search_frame, text="Product:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.product_entry = ttk.Entry(search_frame, width=25)
        self.product_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.product_entry.insert(0, "Lego star wars")
        
        ttk.Label(search_frame, text="Min $:").grid(row=0, column=2, padx=(15, 0), sticky=tk.W)
        self.min_price_entry = ttk.Entry(search_frame, width=10)
        self.min_price_entry.grid(row=0, column=3, padx=5, sticky=tk.W)
        self.min_price_entry.insert(0, "30")
        
        ttk.Label(search_frame, text="Max $:").grid(row=0, column=4, sticky=tk.W)
        self.max_price_entry = ttk.Entry(search_frame, width=10)
        self.max_price_entry.grid(row=0, column=5, padx=5, sticky=tk.W)
        self.max_price_entry.insert(0, "100")
        
        # Row 1: Condition and Sort
        ttk.Label(search_frame, text="Condition:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.condition_var = tk.StringVar(value="NEW|USED")
        condition_combo = ttk.Combobox(search_frame, textvariable=self.condition_var, width=22, 
                                       values=["NEW", "USED", "NEW|USED", "CERTIFIED_REFURBISHED", 
                                              "SELLER_REFURBISHED", "NEW|CERTIFIED_REFURBISHED"])
        condition_combo.grid(row=1, column=1, padx=5, pady=(5, 0), sticky=tk.W)
        
        ttk.Label(search_frame, text="Sort By:").grid(row=1, column=2, padx=(15, 0), pady=(5, 0), sticky=tk.W)
        self.sort_var = tk.StringVar(value="price")
        sort_combo = ttk.Combobox(search_frame, textvariable=self.sort_var, width=18,
                                  values=["price", "-price", "newlyListed", "distance"],
                                  state="readonly")
        sort_combo.grid(row=1, column=3, columnspan=2, padx=5, pady=(5, 0), sticky=tk.W)
        
        # Row 2: Delivery Location
        ttk.Label(search_frame, text="Delivery Country:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.country_var = tk.StringVar(value="US")
        country_combo = ttk.Combobox(search_frame, textvariable=self.country_var, width=22,
                                     values=["US", "GB", "CA", "AU", "DE", "FR", "IT", "ES"],
                                     state="readonly")
        country_combo.grid(row=2, column=1, padx=5, pady=(5, 0), sticky=tk.W)
        
        ttk.Label(search_frame, text="ZIP/Postal:").grid(row=2, column=2, padx=(15, 0), pady=(5, 0), sticky=tk.W)
        self.postal_entry = ttk.Entry(search_frame, width=10)
        self.postal_entry.grid(row=2, column=3, padx=5, pady=(5, 0), sticky=tk.W)
        
        # Row 3: Shipping Options
        ttk.Label(search_frame, text="Max Shipping $:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.max_ship_entry = ttk.Entry(search_frame, width=10)
        self.max_ship_entry.grid(row=3, column=1, padx=5, pady=(5, 0), sticky=tk.W)
        
        self.free_shipping_var = tk.BooleanVar()
        free_ship_check = ttk.Checkbutton(search_frame, text="Free Shipping Only", 
                                         variable=self.free_shipping_var,
                                         command=self.toggle_free_shipping)
        free_ship_check.grid(row=3, column=2, columnspan=2, padx=(15, 0), pady=(5, 0), sticky=tk.W)
        
        ttk.Label(search_frame, text="Delivery Days:").grid(row=3, column=4, sticky=tk.W, pady=(5, 0))
        self.delivery_days_entry = ttk.Entry(search_frame, width=10)
        self.delivery_days_entry.grid(row=3, column=5, padx=5, pady=(5, 0), sticky=tk.W)
        
        # Row 4: Amazon Sort
        ttk.Label(search_frame, text="Amazon Sort:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.amazon_sort_var = tk.StringVar(value="RELEVANCE")
        amazon_sort_combo = ttk.Combobox(search_frame, textvariable=self.amazon_sort_var, width=22,
                                         values=["RELEVANCE", "LOW_HIGH_PRICE", "HIGH_LOW_PRICE", 
                                                "REVIEWS", "BEST_SELLERS", "NEWEST"],
                                         state="readonly")
        amazon_sort_combo.grid(row=4, column=1, padx=5, pady=(5, 0), sticky=tk.W)
        
        # Search button (spans multiple columns)
        self.search_btn = ttk.Button(search_frame, text="🔍 Search Both", command=self.do_search)
        self.search_btn.grid(row=5, column=0, columnspan=6, pady=(10, 0), sticky=tk.EW, padx=50)
        
        # Results section with scrollbar
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(results_frame)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def toggle_free_shipping(self):
        """When free shipping is checked, set max shipping to 0"""
        if self.free_shipping_var.get():
            self.max_ship_entry.delete(0, tk.END)
            self.max_ship_entry.insert(0, "0")
            self.max_ship_entry.config(state='disabled')
        else:
            self.max_ship_entry.config(state='normal')
            self.max_ship_entry.delete(0, tk.END)
    
    def clear_results(self):
        """Clear previous results"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.image_references.clear()
        self.current_ebay_items = []
        self.current_amazon_items = []
    
    def do_search(self):
        """Perform eBay and Amazon search and display results with all filters"""
        self.clear_results()
        self.status_var.set("Searching eBay and Amazon...")
        self.root.update()
        
        # Get search parameters
        product = self.product_entry.get()
        min_price = self.min_price_entry.get()
        max_price = self.max_price_entry.get()
        condition = self.condition_var.get()
        sort_by = self.sort_var.get()
        amazon_sort = self.amazon_sort_var.get()
        
        # Delivery location
        country = self.country_var.get() if self.country_var.get() else None
        postal = self.postal_entry.get().strip() if self.postal_entry.get().strip() else None
        
        # Shipping options
        max_ship = self.max_ship_entry.get().strip()
        max_ship_cost = float(max_ship) if max_ship else None
        
        # Guaranteed delivery
        delivery_days = self.delivery_days_entry.get().strip()
        guaranteed_days = int(delivery_days) if delivery_days else None
        
        ebay_count = 0
        amazon_count = 0
        
        # Search eBay
        try:
            # Build price range
            price_range = None
            if min_price or max_price:
                price_range = f"{min_price or ''}..{max_price or ''}"
            
            # Search eBay with all filters
            ebay_results = search_ebay(
                query=product,
                price_range=price_range,
                condition_filter=condition if condition else None,
                delivery_country=country,
                delivery_postal_code=postal,
                guaranteed_delivery_days=guaranteed_days,
                max_delivery_cost=max_ship_cost,
                sort_by=sort_by
            )
            
            if ebay_results:
                formatted = ebay_display_results(ebay_results)
                ebay_items = formatted.get("items", [])
                if ebay_items:
                    self.current_ebay_items = ebay_items[:5]  # Limit to 5
                    ebay_count = len(self.current_ebay_items)
                    
        except Exception as e:
            print(f"eBay search error: {e}")
            import traceback
            traceback.print_exc()
        
        # Search Amazon
        amazon_error = None
        try:
            print(f"Searching Amazon for: {product}")
            # Convert prices to int (Amazon API expects integers, not floats)
            amazon_min_price = int(float(min_price)) if min_price else None
            amazon_max_price = int(float(max_price)) if max_price else None
            
            amazon_results = search_amazon(
                query=product,
                min_price=amazon_min_price,
                max_price=amazon_max_price,
                sort_by=amazon_sort if amazon_sort != "RELEVANCE" else None
            )
            
            print(f"Amazon results: {type(amazon_results)}")
            if amazon_results:
                print(f"Amazon results keys: {amazon_results.keys()}")
                if "error" in amazon_results:
                    amazon_error = amazon_results['error']
                    print(f"Amazon API Error: {amazon_error}")
                elif "products" in amazon_results:
                    amazon_items = amazon_results.get("products", [])
                    print(f"Found {len(amazon_items)} Amazon items")
                    if amazon_items:
                        self.current_amazon_items = amazon_items[:5]  # Limit to 5
                        amazon_count = len(self.current_amazon_items)
                else:
                    print(f"Unexpected Amazon response structure: {list(amazon_results.keys())}")
                    
        except Exception as e:
            amazon_error = str(e)
            print(f"Amazon search error: {e}")
            import traceback
            traceback.print_exc()
        
        # Display results
        if ebay_count > 0 or amazon_count > 0:
            self.display_combined_results(amazon_error=amazon_error)
            status_msg = f"Found {ebay_count} eBay items, {amazon_count} Amazon items"
            if amazon_error and ebay_count > 0:
                status_msg += " (Amazon error - see below)"
            self.status_var.set(status_msg)
        else:
            if amazon_error:
                self.status_var.set(f"Search failed - Amazon: {amazon_error[:50]}...")
                error_frame = ttk.LabelFrame(self.scrollable_frame, text="Amazon API Error", padding="10")
                error_frame.pack(fill=tk.X, padx=10, pady=10)
                error_text = tk.Text(error_frame, height=4, wrap=tk.WORD, font=("Arial", 9))
                error_text.pack(fill=tk.X)
                error_text.insert("1.0", amazon_error)
                error_text.config(state='disabled')
            else:
                self.status_var.set("No items found")
            ttk.Label(self.scrollable_frame, text="No results found. Try adjusting your filters.", 
                     font=("Arial", 12)).pack(pady=20)
    
    def display_combined_results(self, amazon_error=None):
        """Display both eBay and Amazon results in sections"""
        # eBay Section
        if self.current_ebay_items:
            ebay_header = ttk.LabelFrame(self.scrollable_frame, text=f"eBay Results ({len(self.current_ebay_items)} items)", 
                                        padding="10")
            ebay_header.pack(fill=tk.X, padx=5, pady=5)
            
            for i, item in enumerate(self.current_ebay_items):
                self.display_ebay_item(ebay_header, item, i)
        
        # Amazon Section
        if self.current_amazon_items:
            amazon_header = ttk.LabelFrame(self.scrollable_frame, text=f"Amazon Results ({len(self.current_amazon_items)} items)", 
                                          padding="10")
            amazon_header.pack(fill=tk.X, padx=5, pady=5)
            
            for i, item in enumerate(self.current_amazon_items):
                self.display_amazon_item(amazon_header, item, i)
        elif amazon_error:
            # Show Amazon error if no items but there was an error
            amazon_header = ttk.LabelFrame(self.scrollable_frame, text="Amazon Results (Error)", 
                                          padding="10")
            amazon_header.pack(fill=tk.X, padx=5, pady=5)
            
            error_text = tk.Text(amazon_header, height=3, wrap=tk.WORD, font=("Arial", 9), 
                               background="#ffe6e6")
            error_text.pack(fill=tk.X, padx=5, pady=5)
            error_text.insert("1.0", f"⚠️ Amazon API Error:\n{amazon_error}")
            error_text.config(state='disabled')
    
    def display_ebay_item(self, parent, item, index):
        """Display a single eBay item"""
        # Create frame for each item
        item_frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=2)
        item_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Left side - Image (clickable to open details)
        image_frame = ttk.Frame(item_frame, cursor="hand2")
        image_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Load and display image
        images = item.get("images", [])
        if images and images[0]:
            img = load_image_from_url(images[0], size=(100, 100))
            if img:
                self.image_references.append(img)  # Keep reference
                img_label = ttk.Label(image_frame, image=img, cursor="hand2")
                img_label.pack()
                # Click image to see details
                img_label.bind("<Button-1>", lambda e, idx=index, src="ebay": self.show_item_details(src, idx))
            else:
                ttk.Label(image_frame, text="No Image\nAvailable", 
                         width=12, anchor=tk.CENTER).pack()
        else:
            ttk.Label(image_frame, text="No Image\nAvailable", 
                     width=12, anchor=tk.CENTER).pack()
        
        # Right side - Details
        details_frame = ttk.Frame(item_frame)
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title (clickable)
        title_label = ttk.Label(details_frame, text=item.get("title", "N/A"), 
                               font=("Arial", 10, "bold"), wraplength=600, 
                               foreground="blue", cursor="hand2")
        title_label.pack(anchor=tk.W)
        title_label.bind("<Button-1>", lambda e, idx=index, src="ebay": self.show_item_details(src, idx))
        
        # Price with discount if available
        price_text = f"Price: {item.get('price', 'N/A')}"
        market_price = item.get('market_price', {})
        if market_price.get('discount_percentage'):
            price_text += f" (Save {market_price.get('discount_percentage')}% - was ${market_price.get('original')})"
        
        price_label = ttk.Label(details_frame, text=price_text, 
                               font=("Arial", 10, "bold"), foreground="green")
        price_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Condition and Seller
        info_text = f"Condition: {item.get('condition', 'N/A')}"
        if item.get('seller_feedbackPercentage') != 'N/A':
            info_text += f" | Seller: {item.get('seller_feedbackPercentage')}% positive"
        ttk.Label(details_frame, text=info_text).pack(anchor=tk.W)
        
        # Location and Shipping
        location = item.get('itemLocation', 'N/A')
        shipping_opts = item.get('shippingOptions', [])
        shipping_text = f"Location: {location}"
        if shipping_opts:
            ship_cost = shipping_opts[0].get('cost', 'N/A')
            if ship_cost == '0.0' or ship_cost == 0:
                shipping_text += " | FREE SHIPPING"
            else:
                shipping_text += f" | Shipping: ${ship_cost}"
        ttk.Label(details_frame, text=shipping_text, foreground="navy").pack(anchor=tk.W)
        
        # Description
        desc = item.get('description', 'N/A')
        if desc != 'N/A' and len(desc) > 80:
            desc = desc[:80] + "..."
        ttk.Label(details_frame, text=desc, 
                 wraplength=600, foreground="gray", font=("Arial", 9, "italic")).pack(anchor=tk.W, pady=(5, 0))
        
        # Buttons frame
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(anchor=tk.W, pady=(5, 0))
        
        # Details button
        details_btn = ttk.Button(button_frame, text="📋 Full Details", 
                                command=lambda idx=index, src="ebay": self.show_item_details(src, idx))
        details_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # View on eBay button
        view_btn = ttk.Button(button_frame, text="🔗 View on eBay", 
                             command=lambda url=item.get('url'): self.open_url(url))
        view_btn.pack(side=tk.LEFT)
    
    def display_amazon_item(self, parent, item, index):
        """Display a single Amazon item"""
        # Create frame for each item
        item_frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=2)
        item_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Left side - Image (clickable to open details)
        image_frame = ttk.Frame(item_frame, cursor="hand2")
        image_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Load and display image
        img_url = item.get("product_photo")
        if img_url:
            img = load_image_from_url(img_url, size=(100, 100))
            if img:
                self.image_references.append(img)  # Keep reference
                img_label = ttk.Label(image_frame, image=img, cursor="hand2")
                img_label.pack()
                # Click image to see details
                img_label.bind("<Button-1>", lambda e, idx=index, src="amazon": self.show_item_details(src, idx))
            else:
                ttk.Label(image_frame, text="No Image\nAvailable", 
                         width=12, anchor=tk.CENTER).pack()
        else:
            ttk.Label(image_frame, text="No Image\nAvailable", 
                     width=12, anchor=tk.CENTER).pack()
        
        # Right side - Details
        details_frame = ttk.Frame(item_frame)
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title (clickable) - Extract from URL if title is just "LEGO"
        title = item.get("product_title", "N/A")
        if title == "LEGO" or title == "N/A":
            # Try to extract name from URL
            url = item.get("product_url", "")
            if url:
                title = self.extract_product_name_from_url(url)
        
        title_label = ttk.Label(details_frame, text=title, 
                               font=("Arial", 10, "bold"), wraplength=600, 
                               foreground="blue", cursor="hand2")
        title_label.pack(anchor=tk.W)
        title_label.bind("<Button-1>", lambda e, idx=index, src="amazon": self.show_item_details(src, idx))
        
        # Price
        price = item.get('product_price', 'N/A')
        price_label = ttk.Label(details_frame, text=f"Price: ${price}", 
                               font=("Arial", 10, "bold"), foreground="green")
        price_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Rating and Prime
        info_parts = []
        if item.get('product_star_rating'):
            info_parts.append(f"⭐ {item.get('product_star_rating')} stars")
        if item.get('product_num_ratings'):
            info_parts.append(f"({item.get('product_num_ratings')} reviews)")
        if item.get('is_prime'):
            info_parts.append("📦 Prime")
        
        if info_parts:
            ttk.Label(details_frame, text=" | ".join(info_parts)).pack(anchor=tk.W)
        
        # Delivery Info - split into cost and dates
        delivery_info = item.get('product_delivery_info', '')
        if delivery_info:
            # Parse delivery info to extract cost and dates
            delivery_cost = ""
            delivery_dates = ""
            
            # Try to extract cost (e.g., "$4.99 delivery" or "FREE delivery")
            if "FREE delivery" in delivery_info:
                delivery_cost = "FREE"
                # Extract dates after "FREE delivery"
                remaining = delivery_info.replace("FREE delivery", "").strip()
            elif "$" in delivery_info:
                # Extract cost up to "delivery"
                cost_end = delivery_info.find("delivery")
                if cost_end != -1:
                    delivery_cost = delivery_info[:cost_end].strip()
                    remaining = delivery_info[cost_end + 8:].strip()  # Skip "delivery"
                else:
                    remaining = delivery_info
            else:
                remaining = delivery_info
            
            # Extract date range (e.g., "Nov 21 - 25")
            # Look for pattern with month name
            import re
            date_match = re.search(r'([A-Z][a-z]{2}\s+\d{1,2}(?:\s*-\s*\d{1,2})?)', remaining)
            if date_match:
                delivery_dates = date_match.group(1)
            
            # Display delivery info on two lines
            if delivery_cost:
                cost_text = f"🚚 Shipping: {delivery_cost}"
                ttk.Label(details_frame, text=cost_text).pack(anchor=tk.W)
            
            if delivery_dates:
                dates_text = f"📅 Delivery: {delivery_dates}"
                ttk.Label(details_frame, text=dates_text).pack(anchor=tk.W)
        
        # Buttons frame
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(anchor=tk.W, pady=(5, 0))
        
        # Details button
        details_btn = ttk.Button(button_frame, text="📋 Full Details", 
                                command=lambda idx=index, src="amazon": self.show_item_details(src, idx))
        details_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # View on Amazon button
        view_btn = ttk.Button(button_frame, text="🔗 View on Amazon", 
                             command=lambda url=item.get('product_url'): self.open_url(url))
        view_btn.pack(side=tk.LEFT)
    
    def extract_product_name_from_url(self, url):
        """Extract product name from Amazon URL"""
        try:
            # Amazon URLs format: https://www.amazon.com/PRODUCT-NAME-WITH-DASHES/dp/ASIN
            # Extract the part between .com/ and /dp/
            import re
            match = re.search(r'amazon\.com/([^/]+)/dp/', url)
            if match:
                name_part = match.group(1)
                # Replace dashes with spaces and decode URL encoding
                import urllib.parse
                decoded_name = urllib.parse.unquote(name_part)
                # Replace dashes with spaces
                readable_name = decoded_name.replace('-', ' ')
                # Capitalize words properly
                readable_name = ' '.join(word.capitalize() for word in readable_name.split())
                return readable_name
            return "LEGO"
        except:
            return "LEGO"
    
    def show_item_details(self, source, item_index):
        """Show detailed view of an item in a new window"""
        if source == "ebay":
            if item_index >= len(self.current_ebay_items):
                return
            item = self.current_ebay_items[item_index]
            self.show_ebay_details(item)
        else:  # amazon
            if item_index >= len(self.current_amazon_items):
                return
            item = self.current_amazon_items[item_index]
            self.show_amazon_details(item)
    
    def show_ebay_details(self, item):
        """Show detailed eBay item view"""
        
        # Create new window
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Details - {item.get('title', 'Item')[:50]}...")
        detail_window.geometry("800x600")
        
        # Create scrollable frame
        canvas = tk.Canvas(detail_window)
        scrollbar = ttk.Scrollbar(detail_window, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Content frame
        content = ttk.Frame(scrollable, padding="20")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(content, text=item.get('title', 'N/A'), 
                               font=("Arial", 14, "bold"), wraplength=750)
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Images section
        images = item.get("images", [])
        if images:
            img_frame = ttk.LabelFrame(content, text=f"Images ({len([i for i in images if i])} available)", padding="10")
            img_frame.pack(fill=tk.X, pady=(0, 10))
            
            img_container = ttk.Frame(img_frame)
            img_container.pack()
            
            for idx, img_url in enumerate(images[:5]):  # Show first 5 images
                if img_url:
                    img = load_image_from_url(img_url, size=(120, 120))
                    if img:
                        self.image_references.append(img)
                        img_label = ttk.Label(img_container, image=img)
                        img_label.grid(row=0, column=idx, padx=5)
        
        # Price section
        price_frame = ttk.LabelFrame(content, text="Price Information", padding="10")
        price_frame.pack(fill=tk.X, pady=(0, 10))
        
        price_text = tk.Text(price_frame, height=4, wrap=tk.WORD, font=("Arial", 10))
        price_text.pack(fill=tk.X)
        
        price_info = f"Current Price: {item.get('price', 'N/A')}\n"
        market_price = item.get('market_price', {})
        if market_price.get('original'):
            price_info += f"Original Price: ${market_price.get('original')}\n"
            price_info += f"Discount: ${market_price.get('discount')} ({market_price.get('discount_percentage')}% OFF)\n"
        
        shipping_opts = item.get('shippingOptions', [])
        if shipping_opts:
            ship_cost = shipping_opts[0].get('cost')
            if ship_cost == '0.0' or ship_cost == 0:
                price_info += "Shipping: FREE"
            else:
                price_info += f"Shipping: ${ship_cost} {shipping_opts[0].get('currency', '')}"
        
        price_text.insert("1.0", price_info)
        price_text.config(state='disabled')
        
        # Item Details section
        details_frame = ttk.LabelFrame(content, text="Item Details", padding="10")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        details_text = tk.Text(details_frame, height=8, wrap=tk.WORD, font=("Arial", 10))
        details_text.pack(fill=tk.X)
        
        details_info = f"Condition: {item.get('condition', 'N/A')}\n"
        details_info += f"Location: {item.get('itemLocation', 'N/A')}\n"
        details_info += f"Created: {item.get('itemCreationDate', 'N/A')}\n"
        details_info += f"Watch Count: {item.get('watchCount', 'N/A')}\n\n"
        
        categories = item.get('categories', [])
        if categories:
            details_info += f"Categories: {' > '.join(categories)}\n"
        
        details_text.insert("1.0", details_info)
        details_text.config(state='disabled')
        
        # Description section
        desc = item.get('description', 'N/A')
        if desc and desc != 'N/A':
            desc_frame = ttk.LabelFrame(content, text="Description", padding="10")
            desc_frame.pack(fill=tk.X, pady=(0, 10))
            
            desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD, font=("Arial", 10))
            desc_text.pack(fill=tk.X)
            desc_text.insert("1.0", desc)
            desc_text.config(state='disabled')
        
        # Seller Information
        seller_frame = ttk.LabelFrame(content, text="Seller Information", padding="10")
        seller_frame.pack(fill=tk.X, pady=(0, 10))
        
        seller_text = tk.Text(seller_frame, height=2, wrap=tk.WORD, font=("Arial", 10))
        seller_text.pack(fill=tk.X)
        
        seller_info = f"Feedback Score: {item.get('seller_feedbackPercentage', 'N/A')}\n"
        seller_text.insert("1.0", seller_info)
        seller_text.config(state='disabled')
        
        # Shipping Details
        if shipping_opts:
            shipping_frame = ttk.LabelFrame(content, text="Shipping Details", padding="10")
            shipping_frame.pack(fill=tk.X, pady=(0, 10))
            
            shipping_text = tk.Text(shipping_frame, height=4, wrap=tk.WORD, font=("Arial", 10))
            shipping_text.pack(fill=tk.X)
            
            for idx, opt in enumerate(shipping_opts, 1):
                ship_info = f"Option {idx}:\n"
                ship_info += f"  Cost: ${opt.get('cost', 'N/A')} {opt.get('currency', '')}\n"
                if opt.get('minDelivery'):
                    ship_info += f"  Est. Delivery: {opt.get('minDelivery', '')} to {opt.get('maxDelivery', '')}\n"
                shipping_text.insert(tk.END, ship_info)
            
            shipping_text.config(state='disabled')
        
        # Action buttons
        button_frame = ttk.Frame(content)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(button_frame, text="🔗 Open on eBay", 
                  command=lambda: self.open_url(item.get('url'))).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", 
                  command=detail_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_amazon_details(self, item):
        """Show detailed Amazon item view"""
        
        # Extract proper title from URL if needed
        title = item.get("product_title", "N/A")
        if title == "LEGO" or title == "N/A":
            url = item.get("product_url", "")
            if url:
                title = self.extract_product_name_from_url(url)
        
        # Create new window
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Details - {title[:50]}...")
        detail_window.geometry("800x600")
        
        # Create scrollable frame
        canvas = tk.Canvas(detail_window)
        scrollbar = ttk.Scrollbar(detail_window, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Content frame
        content = ttk.Frame(scrollable, padding="20")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(content, text=title, 
                               font=("Arial", 14, "bold"), wraplength=750)
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Image section
        img_url = item.get("product_photo")
        if img_url:
            img_frame = ttk.LabelFrame(content, text="Product Image", padding="10")
            img_frame.pack(fill=tk.X, pady=(0, 10))
            
            img = load_image_from_url(img_url, size=(250, 250))
            if img:
                self.image_references.append(img)
                img_label = ttk.Label(img_frame, image=img)
                img_label.pack()
        
        # Price section
        price_frame = ttk.LabelFrame(content, text="Price Information", padding="10")
        price_frame.pack(fill=tk.X, pady=(0, 10))
        
        price_text = tk.Text(price_frame, height=3, wrap=tk.WORD, font=("Arial", 10))
        price_text.pack(fill=tk.X)
        
        price_info = f"Price: ${item.get('product_price', 'N/A')}\n"
        
        if item.get('is_prime'):
            price_info += "📦 Prime Eligible: Yes\n"
        
        price_info += f"Original Price: ${item.get('product_original_price', 'N/A')}"
        
        price_text.insert("1.0", price_info)
        price_text.config(state='disabled')
        
        # Rating section
        rating_frame = ttk.LabelFrame(content, text="Customer Reviews", padding="10")
        rating_frame.pack(fill=tk.X, pady=(0, 10))
        
        rating_text = tk.Text(rating_frame, height=2, wrap=tk.WORD, font=("Arial", 10))
        rating_text.pack(fill=tk.X)
        
        rating_info = ""
        if item.get('product_star_rating'):
            rating_info += f"⭐ Rating: {item.get('product_star_rating')} stars\n"
        if item.get('product_num_ratings'):
            rating_info += f"Total Reviews: {item.get('product_num_ratings')}"
        
        if rating_info:
            rating_text.insert("1.0", rating_info)
        else:
            rating_text.insert("1.0", "No ratings available")
        rating_text.config(state='disabled')
        
        # Availability section
        avail_frame = ttk.LabelFrame(content, text="Availability", padding="10")
        avail_frame.pack(fill=tk.X, pady=(0, 10))
        
        avail_text = tk.Text(avail_frame, height=2, wrap=tk.WORD, font=("Arial", 10))
        avail_text.pack(fill=tk.X)
        
        avail_info = f"In Stock: {item.get('product_availability', 'N/A')}\n"
        avail_info += f"ASIN: {item.get('asin', 'N/A')}"
        
        avail_text.insert("1.0", avail_info)
        avail_text.config(state='disabled')
        
        # Delivery Information
        delivery_info = item.get('product_delivery_info', '')
        if delivery_info:
            delivery_frame = ttk.LabelFrame(content, text="Delivery Information", padding="10")
            delivery_frame.pack(fill=tk.X, pady=(0, 10))
            
            delivery_text = tk.Text(delivery_frame, height=4, wrap=tk.WORD, font=("Arial", 10))
            delivery_text.pack(fill=tk.X)
            
            # Parse delivery info
            import re
            delivery_display = "Raw Info: " + delivery_info + "\n\n"
            
            # Extract shipping cost
            if "FREE delivery" in delivery_info:
                delivery_display += "🚚 Shipping Cost: FREE\n"
            elif "$" in delivery_info:
                cost_match = re.search(r'\$[\d.]+', delivery_info)
                if cost_match:
                    delivery_display += f"🚚 Shipping Cost: {cost_match.group()}\n"
            
            # Extract delivery dates
            date_match = re.search(r'([A-Z][a-z]{2}\s+\d{1,2}(?:\s*-\s*\d{1,2})?)', delivery_info)
            if date_match:
                delivery_display += f"📅 Estimated Arrival: {date_match.group(1)}\n"
            
            delivery_text.insert("1.0", delivery_display)
            delivery_text.config(state='disabled')
        
        # Additional Info
        if item.get('product_minimum_offer_price') or item.get('climate_pledge_friendly'):
            extra_frame = ttk.LabelFrame(content, text="Additional Information", padding="10")
            extra_frame.pack(fill=tk.X, pady=(0, 10))
            
            extra_text = tk.Text(extra_frame, height=3, wrap=tk.WORD, font=("Arial", 10))
            extra_text.pack(fill=tk.X)
            
            extra_info = ""
            if item.get('product_minimum_offer_price'):
                extra_info += f"Minimum Offer Price: ${item.get('product_minimum_offer_price')}\n"
            if item.get('climate_pledge_friendly'):
                extra_info += "🌱 Climate Pledge Friendly: Yes\n"
            
            extra_text.insert("1.0", extra_info)
            extra_text.config(state='disabled')
        
        # Action buttons
        button_frame = ttk.Frame(content)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(button_frame, text="🔗 Open on Amazon", 
                  command=lambda: self.open_url(item.get('product_url'))).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", 
                  command=detail_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def open_url(self, url):
        """Open URL in default browser"""
        webbrowser.open(url)


def main():
    root = tk.Tk()
    app = ProductDisplayGUI(root)
    root.mainloop()


if __name__ == "__main__":
    # Check if PIL is installed
    try:
        import PIL
        print("✓ PIL/Pillow is installed")
    except ImportError:
        print("❌ PIL/Pillow is not installed!")
        print("Install it with: pip install Pillow")
        exit(1)
    
    main()
