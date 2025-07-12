import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import random
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

class LayoutGenerator:
    def __init__(self, hidden_dim=256):
        """Initialize the layout generator.
        
        Args:
            hidden_dim (int): Hidden dimension size for the layout generation model
        """
        self.hidden_dim = hidden_dim
        self.model = self._build_model()
        self.grid_size = (20, 20)  # Use a larger grid for more detail
    
    def _build_model(self):
        """Build the neural network model for layout generation."""
        # This is a simplified model architecture
        class LayoutNetwork(nn.Module):
            def __init__(self, input_dim, hidden_dim, output_dim=128):
                super().__init__()
                self.fc1 = nn.Linear(input_dim, hidden_dim)
                self.fc2 = nn.Linear(hidden_dim, hidden_dim * 2)
                self.fc3 = nn.Linear(hidden_dim * 2, output_dim)
            
            def forward(self, x):
                x = F.relu(self.fc1(x))
                x = F.relu(self.fc2(x))
                x = self.fc3(x)
                return x
        
        return LayoutNetwork(input_dim=768, hidden_dim=self.hidden_dim)
    
    def generate_layout(self, text_features):
        """Generate a 2D layout based on text features.
        
        Args:
            text_features (dict): Features extracted from the text description
            
        Returns:
            dict: 2D layout representation with room positions, sizes, etc.
        """
        # Convert the text features into a tensor
        feature_vector = self._prepare_features(text_features)
        
        # For now, use a rule-based approach instead of the model
        # In a real implementation, we'd use the model to generate the layout
        layout = self._rule_based_layout(text_features)
        
        # Visualize the layout
        layout_image_path = self._visualize_layout(layout)
        layout["visualization_path"] = layout_image_path
        
        return layout
    
    def _prepare_features(self, text_features):
        """Prepare text features for input to the layout model."""
        # In a real implementation, this would encode all the text features
        # For now, just return a placeholder
        return torch.zeros(768)
    
    def _rule_based_layout(self, text_features):
        """Generate a layout using rule-based methods based on text features."""
        rooms = text_features.get("rooms", [])
        room_count = len(rooms)
        grid_size = self.grid_size
        
        # Initialize the layout
        layout = {
            "rooms": [],
            "connections": [],
            "grid_size": grid_size
        }
        
        # Create a grid representation
        grid = np.zeros(grid_size, dtype=int)
        
        # No rooms? Return empty layout
        if not room_count:
            layout["grid"] = grid.tolist()
            return layout
        
        # Get layout strategy based on room count and types
        room_positions = self._generate_room_layout(rooms, grid_size)
        
        # Create room data and update grid
        for i, room in enumerate(rooms):
            x, y, width, height = room_positions[i]
            
            room_data = {
                "id": i,
                "type": room["type"],
                "name": room.get("id", room["type"]),
                "position": (x, y),
                "size": (width, height)
            }
            
            layout["rooms"].append(room_data)
            
            # Mark room in grid
            for dx in range(width):
                for dy in range(height):
                    if 0 <= x+dx < grid_size[0] and 0 <= y+dy < grid_size[1]:
                        grid[x+dx, y+dy] = i + 1
        
        # Generate connections between adjacent rooms
        for i in range(room_count):
            for j in range(i+1, room_count):
                if self._are_adjacent(room_positions[i], room_positions[j]):
                    layout["connections"].append({
                        "source": i,
                        "target": j,
                        "type": "door"
                    })
        
        layout["grid"] = grid.tolist()
        return layout
    
    def _generate_room_layout(self, rooms, grid_size):
        """Generate a room layout based on room count and types."""
        room_count = len(rooms)
        
        # Different layout strategies based on room count
        if room_count <= 1:
            return self._layout_single_room(rooms, grid_size)
        elif room_count <= 3:
            return self._layout_few_rooms(rooms, grid_size)
        elif room_count <= 6:
            return self._layout_medium_house(rooms, grid_size)
        else:
            return self._layout_large_house(rooms, grid_size)
    
    def _layout_single_room(self, rooms, grid_size):
        """Layout for a single room - centered in the grid."""
        positions = []
        
        # Single room takes up most of the space
        margin = 2
        width = grid_size[0] - 2*margin
        height = grid_size[1] - 2*margin
        positions.append((margin, margin, width, height))
        
        return positions
    
    def _layout_few_rooms(self, rooms, grid_size):
        """Layout for a few rooms (2-3) - simple arrangements."""
        positions = []
        room_count = len(rooms)
        
        # Get room types for smarter layout
        room_types = [room["type"] for room in rooms]
        
        if room_count == 2:
            # Two rooms - side by side
            # If one is a bathroom, make it smaller
            if "bathroom" in room_types:
                bath_idx = room_types.index("bathroom")
                other_idx = 1 - bath_idx  # The other room index
                
                # Bathroom is small, other room is larger
                if bath_idx == 0:
                    positions.append((2, 2, 6, 16))  # Bathroom
                    positions.append((8, 2, 10, 16))  # Other room
                else:
                    positions.append((2, 2, 10, 16))  # Other room
                    positions.append((12, 2, 6, 16))  # Bathroom
            else:
                # Equal sized rooms
                positions.append((2, 2, 8, 16))
                positions.append((10, 2, 8, 16))
        
        elif room_count == 3:
            # Check if we have bathroom, bedroom, and living room/kitchen
            has_bath = "bathroom" in room_types
            has_bedroom = "bedroom" in room_types
            has_living = "living room" in room_types or "kitchen" in room_types
            
            if has_bath and has_bedroom and has_living:
                # Common 3-room apartment layout
                bath_idx = room_types.index("bathroom")
                bed_idx = room_types.index("bedroom")
                living_idx = next((i for i, r in enumerate(room_types) 
                                if r in ["living room", "kitchen"]), 0)
                
                # Assign positions for each room
                room_positions = [None] * 3
                room_positions[bath_idx] = (2, 2, 6, 6)  # Bathroom is small
                room_positions[bed_idx] = (2, 8, 8, 10)  # Bedroom is medium
                room_positions[living_idx] = (10, 2, 8, 16)  # Living area is large
                
                positions = room_positions
            else:
                # Generic 3-room layout
                positions.append((2, 2, 10, 8))   # Room 1
                positions.append((2, 10, 10, 8))  # Room 2
                positions.append((12, 2, 6, 16))  # Room 3 (smaller)
        
        return positions
    
    def _layout_medium_house(self, rooms, grid_size):
        """Layout for a medium-sized house (4-6 rooms)."""
        positions = []
        room_count = len(rooms)
        
        # Get room types
        room_types = [room["type"] for room in rooms]
        
        # Check for key room types
        has_bath = "bathroom" in room_types
        has_bedroom = "bedroom" in room_types
        has_kitchen = "kitchen" in room_types
        has_living = "living room" in room_types
        
        # Start with a fixed layout for common room combinations
        if has_bath and has_bedroom and has_kitchen and has_living:
            # Find indices
            bath_idx = room_types.index("bathroom")
            kitchen_idx = room_types.index("kitchen")
            living_idx = room_types.index("living room")
            
            # Find bedroom indices - could be multiple
            bedroom_indices = [i for i, rt in enumerate(room_types) if rt == "bedroom"]
            
            # Create a basic layout with these rooms
            room_positions = [None] * room_count
            
            # Place key rooms
            room_positions[bath_idx] = (2, 2, 6, 6)       # Bathroom
            room_positions[kitchen_idx] = (8, 2, 6, 8)    # Kitchen
            room_positions[living_idx] = (14, 2, 6, 16)   # Living room
            
            # Place bedrooms
            bedroom_positions = [
                (2, 8, 6, 10),   # Bedroom 1
                (8, 10, 6, 8)    # Bedroom 2
            ]
            
            # Assign bedroom positions
            for i, idx in enumerate(bedroom_indices):
                if i < len(bedroom_positions):
                    room_positions[idx] = bedroom_positions[i]
            
            # Assign remaining rooms randomly
            remaining_positions = [
                (2, 13, 4, 5),
                (8, 15, 6, 3)
            ]
            
            unassigned = [i for i, pos in enumerate(room_positions) if pos is None]
            for i, idx in enumerate(unassigned):
                if i < len(remaining_positions):
                    room_positions[idx] = remaining_positions[i]
                else:
                    # Emergency fallback - shouldn't normally reach here
                    room_positions[idx] = (10, 10, 4, 4)
            
            positions = room_positions
        else:
            # Generic layout
            if room_count == 4:
                positions = [
                    (2, 2, 8, 8),    # Room 1
                    (2, 10, 8, 8),   # Room 2
                    (10, 2, 8, 8),   # Room 3
                    (10, 10, 8, 8)   # Room 4
                ]
            elif room_count == 5:
                positions = [
                    (2, 2, 6, 8),    # Room 1
                    (2, 10, 6, 8),   # Room 2
                    (8, 2, 6, 8),    # Room 3
                    (8, 10, 6, 8),   # Room 4
                    (14, 2, 4, 16)   # Room 5 (narrow)
                ]
            else:  # 6 rooms
                positions = [
                    (2, 2, 6, 6),    # Room 1
                    (2, 8, 6, 6),    # Room 2
                    (2, 14, 6, 4),   # Room 3
                    (8, 2, 6, 8),    # Room 4
                    (14, 2, 4, 8),   # Room 5
                    (8, 10, 10, 8)   # Room 6
                ]
        
        return positions
    
    def _layout_large_house(self, rooms, grid_size):
        """Layout for a large house (7+ rooms)."""
        positions = []
        room_count = len(rooms)
        
        # For large houses, use a grid-like approach
        cols = int(np.ceil(np.sqrt(room_count)))
        rows = int(np.ceil(room_count / cols))
        
        # Calculate cell size
        cell_width = (grid_size[0] - 2) // cols
        cell_height = (grid_size[1] - 2) // rows
        
        # Try to identify important rooms
        room_types = [room["type"] for room in rooms]
        important_rooms = ["living room", "kitchen", "master bedroom"]
        
        # Place rooms in a grid pattern
        for i in range(room_count):
            row = i // cols
            col = i % cols
            
            # Base position and size
            x = 1 + col * cell_width
            y = 1 + row * cell_height
            width = cell_width - 1
            height = cell_height - 1
            
            # Make important rooms a bit larger if possible
            room_type = room_types[i]
            if room_type in important_rooms:
                if col < cols - 1:  # Can expand right
                    width += 1
                if row < rows - 1:  # Can expand down
                    height += 1
            
            positions.append((x, y, width, height))
        
        return positions
    
    def _are_adjacent(self, pos1, pos2):
        """Check if two rooms are adjacent.
        
        Args:
            pos1: (x, y, width, height) of first room
            pos2: (x, y, width, height) of second room
            
        Returns:
            bool: True if rooms are adjacent
        """
        x1, y1, w1, h1 = pos1
        x2, y2, w2, h2 = pos2
        
        # Check if rooms are horizontally adjacent
        horizontal_adjacent = (
            (y1 <= y2 + h2 and y1 + h1 >= y2) and
            (x1 + w1 == x2 or x2 + w2 == x1)
        )
        
        # Check if rooms are vertically adjacent
        vertical_adjacent = (
            (x1 <= x2 + w2 and x1 + w1 >= x2) and
            (y1 + h1 == y2 or y2 + h2 == y1)
        )
        
        return horizontal_adjacent or vertical_adjacent
    
    def _visualize_layout(self, layout):
        """Visualize the layout and save to a file.
        
        Args:
            layout (dict): The layout to visualize
            
        Returns:
            str: Path to the saved visualization image
        """
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Set limits
        grid_size = layout["grid_size"]
        ax.set_xlim(0, grid_size[0])
        ax.set_ylim(0, grid_size[1])
        
        # Color map for different room types
        room_colors = {
            "kitchen": "lightblue",
            "bathroom": "lightgreen",
            "bedroom": "lightpink",
            "living room": "lightyellow",
            "dining room": "lightcoral",
            "office": "lightsalmon",
            "hallway": "lightgrey",
            "garage": "lightcyan"
        }
        
        # Draw each room
        for room in layout["rooms"]:
            x, y = room["position"]
            width, height = room["size"]
            room_type = room["type"]
            
            # Get color for room type, or random color if not in our map
            if room_type in room_colors:
                color = room_colors[room_type]
            else:
                # Generate a light random color
                r, g, b = [random.random() * 0.5 + 0.5 for _ in range(3)]
                color = (r, g, b)
            
            # Draw room rectangle
            rect = Rectangle((x, y), width, height, linewidth=1, 
                           edgecolor='black', facecolor=color, alpha=0.7)
            ax.add_patch(rect)
            
            # Add room label
            ax.text(x + width/2, y + height/2, room["name"],
                  horizontalalignment='center', verticalalignment='center')
        
        # Draw connections
        for conn in layout["connections"]:
            source_idx = conn["source"]
            target_idx = conn["target"]
            
            source_room = layout["rooms"][source_idx]
            target_room = layout["rooms"][target_idx]
            
            # Calculate centers of rooms
            sx, sy = source_room["position"]
            sw, sh = source_room["size"]
            source_center = (sx + sw/2, sy + sh/2)
            
            tx, ty = target_room["position"]
            tw, th = target_room["size"]
            target_center = (tx + tw/2, ty + th/2)
            
            # Draw connection
            ax.plot([source_center[0], target_center[0]], 
                  [source_center[1], target_center[1]], 'k--', linewidth=1)
        
        # Set title and labels
        ax.set_title('2D Layout')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_aspect('equal')
        
        # Save to file
        import os
        os.makedirs('output', exist_ok=True)
        output_path = 'output/layout.png'
        plt.savefig(output_path)
        plt.close(fig)
        
        return output_path