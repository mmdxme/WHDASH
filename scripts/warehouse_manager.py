import json
import os
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class InventoryItem:
    sku: str
    quantity: int
    name: str = ""

class WarehouseManager:
    """
    Manages warehouse inventory using a 5-tier coordinate system:
    Rack(R) - Bay(B) - Level(L) - Position(P) - Bin(B)
    Example Format: 01-12-03-05-A
    """
    
    # Regex to validate the 5-tier format (e.g., 01-12-03-05-A)
    # R: 2 digits, B: 2 digits, L: 2 digits, P: 2 digits, Bin: 1-2 Alphanumerics
    COORD_PATTERN = re.compile(r'^\d{2}-\d{2}-\d{2}-\d{2}-[a-zA-Z0-9]{1,2}$')
    
    def __init__(self, data_file: str = "warehouse_data.json"):
        self.data_file = data_file
        # Structure: dict representing the flattened coordinate map, e.g., {"01-12-03-05-A": {"sku": "PN-123", "quantity": 10, "name": "Brake Pad"}}
        self.inventory: Dict[str, InventoryItem] = {}
        self.load_data()

    def load_data(self) -> None:
        """Loads inventory data from a JSON file if it exists."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    raw_data = json.load(f)
                    self.inventory = {
                        coord: InventoryItem(**item_data) 
                        for coord, item_data in raw_data.items()
                    }
                print(f"Loaded {len(self.inventory)} items from {self.data_file}.")
            except json.JSONDecodeError:
                print("Error reading data file. Starting with empty inventory.")
        else:
            print("No existing data found. Starting fresh.")

    def save_data(self) -> None:
        """Saves current inventory state to a JSON file."""
        with open(self.data_file, 'w') as f:
            # Convert dataclasses to dicts for JSON serialization
            serialized = {coord: asdict(item) for coord, item in self.inventory.items()}
            json.dump(serialized, f, indent=4)

    def validate_coordinate(self, coordinate: str) -> bool:
        """Validates if the provided coordinate matches the R-B-L-P-B format."""
        if not self.COORD_PATTERN.match(coordinate):
            print(f"Error: Invalid coordinate format '{coordinate}'. Expected R-B-L-P-B (e.g., 01-12-03-05-A).")
            return False
        return True

    def add_item(self, coordinate: str, sku: str, quantity: int, name: str = "") -> None:
        """Adds or updates an item at a specific coordinate."""
        coordinate = coordinate.upper()
        if not self.validate_coordinate(coordinate):
            return

        if quantity <= 0:
            print("Quantity must be strictly greater than zero to add.")
            return

        if coordinate in self.inventory:
            existing_item = self.inventory[coordinate]
            print(f"\nBin {coordinate} is currently occupied by: [{existing_item.sku}] {existing_item.name} (Qty: {existing_item.quantity})")
            
            # Simple CLI Prompt for Overwrite vs Increment
            choice = input(f"Do you want to (O)verwrite, (I)ncrement, or (C)ancel? [O/I/C]: ").strip().upper()
            
            if choice == 'O':
                self.inventory[coordinate] = InventoryItem(sku=sku, quantity=quantity, name=name)
                print(f"Overwrote Bin {coordinate} with {quantity}x [{sku}].")
            elif choice == 'I':
                if existing_item.sku != sku:
                    print(f"Warning: SKUs do not match! ({existing_item.sku} vs {sku}). Cannot cleanly increment different items.")
                    return
                existing_item.quantity += quantity
                print(f"Incremented qty. New balance for [{sku}] at {coordinate} is {existing_item.quantity}.")
            else:
                print("Operation cancelled.")
                return
        else:
            self.inventory[coordinate] = InventoryItem(sku=sku, quantity=quantity, name=name)
            print(f"Added {quantity}x [{sku}] to new location {coordinate}.")
            
        self.save_data()

    def remove_item(self, coordinate: str, remove_qty: Optional[int] = None) -> None:
        """
        Removes an item or reduces its quantity at a coordinate.
        If remove_qty is None or greater/equal to current stock, clears the bin entirely.
        """
        coordinate = coordinate.upper()
        if not self.validate_coordinate(coordinate):
            return

        if coordinate not in self.inventory:
            print(f"Error: Location {coordinate} is already empty or does not exist.")
            return

        item = self.inventory[coordinate]
        
        if remove_qty is None or remove_qty >= item.quantity:
            del self.inventory[coordinate]
            print(f"Cleared entirely: Removed all of [{item.sku}] from {coordinate}.")
        else:
            if remove_qty <= 0:
                print("Removal quantity must be greater than zero.")
                return
            item.quantity -= remove_qty
            print(f"Reduced stock. New balance for [{item.sku}] at {coordinate} is {item.quantity}.")
            
        self.save_data()

    def view(self, coordinate: Optional[str] = None) -> None:
        """Displays the contents of a specific coordinate or the entire inventory."""
        if coordinate:
            coordinate = coordinate.upper()
            if not self.validate_coordinate(coordinate):
                return
                
            if coordinate in self.inventory:
                item = self.inventory[coordinate]
                print(f"Location {coordinate} -> SKU: {item.sku} | Name: '{item.name}' | Qty: {item.quantity}")
            else:
                print(f"Location {coordinate} is empty.")
        else:
            if not self.inventory:
                print("\nThe warehouse is completely empty.")
                return
                
            print("\n--- Current Warehouse Inventory ---")
            # Sort by coordinates for clean display
            for coord in sorted(self.inventory.keys()):
                item = self.inventory[coord]
                print(f"[{coord}] : {item.quantity:>4}x {item.sku:<15} ({item.name})")
            print("-----------------------------------\n")


def interactive_menu():
    manager = WarehouseManager()
    
    while True:
        print("\n--- Warehouse 5-Tier Coordinate Manager ---")
        print("1. Add Item to Location")
        print("2. Remove/Reduce Item from Location")
        print("3. View Specific Location")
        print("4. View Entire Inventory")
        print("5. Exit")
        
        choice = input("Select an option (1-5): ").strip()
        
        if choice == '1':
            coord = input("Enter Coordinate (R-B-L-P-B, e.g. 01-12-03-05-A): ")
            sku = input("Enter SKU/Part Number: ")
            name = input("Enter Item Name (Optional): ")
            try:
                qty = int(input("Enter Quantity: "))
                manager.add_item(coord, sku, qty, name)
            except ValueError:
                print("Invalid quantity. Must be an integer.")
                
        elif choice == '2':
            coord = input("Enter Coordinate (R-B-L-P-B): ")
            qty_input = input("Enter Quantity to remove (Leave blank to clear bin entirely): ")
            if not qty_input.strip():
                manager.remove_item(coord)
            else:
                try:
                    qty = int(qty_input)
                    manager.remove_item(coord, qty)
                except ValueError:
                    print("Invalid quantity. Must be an integer.")
                    
        elif choice == '3':
            coord = input("Enter Coordinate (R-B-L-P-B): ")
            manager.view(coord)
            
        elif choice == '4':
            manager.view()
            
        elif choice == '5':
            print("Saving and exiting... Goodbye!")
            manager.save_data()
            break
            
        else:
            print("Invalid command. Please select 1-5.")

if __name__ == "__main__":
    interactive_menu()
