"""
Professional Floor Plan Renderer
-------------------------------
Creates architectural-style floor plans with furniture layouts and proper doorways
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.path import Path
import matplotlib.transforms as transforms
import matplotlib.colors as mcolors
import matplotlib as mpl
from datetime import datetime

class FloorPlanRenderer:
    def __init__(self):
        """Initialize the floor plan renderer."""
        # Define room colors (with transparency)
        self.room_colors = {
            "bedroom": "#FFC0CB",       # Light pink
            "kitchen": "#ADD8E6",       # Light blue
            "bathroom": "#90EE90",      # Light green
            "washroom": "#90EE90",      # Light green (same as bathroom)
            "living room": "#FFFFE0",   # Light yellow
            "tv lounge": "#FFDAB9",     # Peach
            "lobby": "#FFE4B5",         # Moccasin
            "hallway": "#F5F5DC",       # Beige
            "entrance": "#FFE4C4",      # Bisque
            "main entrance": "#FFE4C4", # Bisque (same as entrance)
            "terrace": "#E0FFFF",       # Light cyan
            "garage": "#D3D3D3",        # Light gray
            "car parking": "#D3D3D3",   # Light gray (same as garage)
            "stairs": "#E6E6FA",        # Lavender
            "dining room": "#FFB6C1",   # Light pink
            "corridor": "#F5F5DC",      # Beige for corridors
        }
        
        # Room fixture elements
        self.room_fixtures = {
            "bedroom": self._draw_bedroom_furniture,
            "kitchen": self._draw_kitchen_furniture,
            "bathroom": self._draw_bathroom_fixtures,
            "washroom": self._draw_bathroom_fixtures,
            "living room": self._draw_living_room_furniture,
            "tv lounge": self._draw_tv_lounge_furniture,
            "garage": self._draw_garage_items,
            "car parking": self._draw_garage_items,
            "dining room": self._draw_dining_room_furniture,
            "stairs": self._draw_stairs,
            "corridor": self._draw_corridor_elements,
        }
        
        # Wall properties
        self.wall_thickness = 0.25  # 25cm walls
        self.wall_color = '#FF0000'  # Red walls
        self.door_width = 0.9        # 90cm door width
        self.room_padding = 0.3      # Padding around rooms
        
        # Set rendering style - modern look
        plt.style.use('default')
        mpl.rcParams['font.family'] = 'sans-serif'
        mpl.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    
    def render(self, layout, output_path="output/floor_plan.png"):
        """Render a professional-looking floor plan."""
        stories = layout.get("stories", 1)
        
        # Get plot size and calculate proper figure size
        plot_size = layout.get("plot_size", {})
        if "width_meters" in plot_size and "length_meters" in plot_size:
            width = plot_size["width_meters"]
            height = plot_size["length_meters"]
            ratio = height / width
            fig_width = 14
            fig_height = fig_width * ratio
        else:
            fig_width, fig_height = 14, 10
            
        # Create the figure
        fig, axes = plt.subplots(stories, 1, figsize=(fig_width, fig_height * stories))
        if stories == 1:
            axes = [axes]
            
        # Set plot title with dimensions
        dimensions_text = ""
        if "width_meters" in plot_size and "length_meters" in plot_size:
            dimensions_text = f"\nDimensions: {plot_size['width_meters']:.1f}m × {plot_size['length_meters']:.1f}m"
        
        fig.suptitle(f"Floor Plan with Doors & Movement Space{dimensions_text}", fontsize=16, y=0.98)
        
        # Add plot information
        plot_info = ""
        if "plot_size" in layout:
            plot_size = layout["plot_size"]
            if "marla" in plot_size and "kanal" in plot_size:
                plot_info += f"Plot Size: {plot_size['marla']:.2f} Marla ({plot_size['kanal']:.2f} Kanal)"
                
        if plot_info:
            fig.text(0.5, 0.95, plot_info, ha='center', fontsize=10)
        
        # Process each story
        for story in range(1, stories + 1):
            ax = axes[story - 1]
            ax.set_title(f"Floor {story}", fontsize=14)
            
            # Set equal aspect and remove axis ticks for clarity
            ax.set_aspect('equal')
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_frame_on(False)  # Remove border
            
            # Filter rooms for this story
            story_rooms = [r for r in layout["rooms"] if r.get("story", 1) == story]
            
            # Get valid doors for this story
            story_doors = []
            for door in layout.get("doors", []):
                connects = door.get("connects", [-1, -1])
                if any(idx >= 0 and idx < len(layout["rooms"]) and 
                       layout["rooms"][idx].get("story", 1) == story for idx in connects):
                    story_doors.append(door)
            
            # Draw the floor plan
            self._draw_floor_plan(ax, story_rooms, story_doors, layout)
            
            # Set axis limits with some padding
            all_x = [r["position"][0] for r in story_rooms] + [r["position"][0] + r["size"][0] for r in story_rooms]
            all_y = [r["position"][1] for r in story_rooms] + [r["position"][1] + r["size"][1] for r in story_rooms]
            
            if all_x and all_y:  # If we have rooms
                padding = 2
                ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
                ax.set_ylim(min(all_y) - padding, max(all_y) + padding)
                
            # Add scale bar
            scale_length = 5  # 5 meters
            scale_x = min(all_x) + 2 if all_x else 2
            scale_y = min(all_y) + 2 if all_y else 2
            self._add_scale_bar(ax, scale_x, scale_y, scale_length)
            
            # Add north arrow
            arrow_x = max(all_x) - 2 if all_x else 10
            arrow_y = min(all_y) + 2 if all_y else 2
            self._add_north_arrow(ax, arrow_x, arrow_y)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        fig.text(0.5, 0.01, f"Generated: {timestamp}", ha='center', fontsize=8)
        
        # Adjust layout and save
        plt.tight_layout(rect=[0, 0.02, 1, 0.95])
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return output_path
    
    def _draw_floor_plan(self, ax, rooms, doors, layout):
        """Draw the complete floor plan with walls, doors and furniture."""
        # First pass: Draw room fill colors
        for room in rooms:
            self._draw_room_fill(ax, room)
        
        # Second pass: Draw interior features (furniture, fixtures)
        for room in rooms:
            self._draw_room_fixtures(ax, room)
        
        # Third pass: Draw the walls (so they appear on top of room fill)
        for room in rooms:
            self._draw_room_walls(ax, room, rooms)
        
        # Fourth pass: Draw doors
        self._draw_all_doors(ax, rooms, doors)
        
        # Fifth pass: Add room labels and dimensions
        for room in rooms:
            self._add_room_label_and_dimensions(ax, room)
            
        # Add main entrance marker if present
        for door in doors:
            if door.get("type") == "main_entrance":
                self._draw_main_entrance(ax, door)
    
    def _draw_room_fill(self, ax, room):
        """Draw the room fill with the appropriate color."""
        x, y = room["position"]
        w, h = room["size"]
        room_type = room["type"].lower()
        
        # Get the room color
        if room_type in self.room_colors:
            color = self.room_colors[room_type]
        else:
            color = '#F8F8F8'  # Default off-white
        
        # Draw room fill
        rect = patches.Rectangle(
            (x, y), w, h,
            facecolor=color,
            edgecolor='none',
            alpha=0.7,
            zorder=1
        )
        ax.add_patch(rect)
    
    def _draw_room_walls(self, ax, room, all_rooms):
        """Draw room walls with proper thickness and detect shared walls."""
        x, y = room["position"]
        w, h = room["size"]
        
        # Half wall thickness (for drawing walls centered on room boundaries)
        ht = self.wall_thickness / 2
        
        # Check all four walls and draw them
        walls = [
            {"name": "bottom", "coords": [(x-ht, y-ht), (x+w+ht, y-ht), (x+w+ht, y+ht), (x-ht, y+ht)], "shared": False},
            {"name": "right", "coords": [(x+w-ht, y-ht), (x+w+ht, y-ht), (x+w+ht, y+h+ht), (x+w-ht, y+h+ht)], "shared": False},
            {"name": "top", "coords": [(x-ht, y+h-ht), (x+w+ht, y+h-ht), (x+w+ht, y+h+ht), (x-ht, y+h+ht)], "shared": False},
            {"name": "left", "coords": [(x-ht, y-ht), (x+ht, y-ht), (x+ht, y+h+ht), (x-ht, y+h+ht)], "shared": False}
        ]
        
        # Check for shared walls with other rooms
        for other_room in all_rooms:
            if other_room == room:
                continue
                
            ox, oy = other_room["position"]
            ow, oh = other_room["size"]
            
            # Check bottom wall
            if abs(y - (oy + oh)) < 0.1 and (x + w > ox) and (x < ox + ow):
                walls[0]["shared"] = True
                
            # Check right wall
            if abs(x + w - ox) < 0.1 and (y + h > oy) and (y < oy + oh):
                walls[1]["shared"] = True
                
            # Check top wall
            if abs(y + h - oy) < 0.1 and (x + w > ox) and (x < ox + ow):
                walls[2]["shared"] = True
                
            # Check left wall
            if abs(x - (ox + ow)) < 0.1 and (y + h > oy) and (y < oy + oh):
                walls[3]["shared"] = True
        
        # Draw the walls
        for wall in walls:
            # Create a polygon for the wall
            poly = patches.Polygon(
                wall["coords"],
                closed=True,
                facecolor=self.wall_color,
                edgecolor='none',
                zorder=3  # Above room fill but below furniture
            )
            ax.add_patch(poly)
    
    def _draw_all_doors(self, ax, rooms, doors):
        """Draw all doors in the floor plan."""
        # Draw doors with proper swing
        for door in doors:
            if "position" not in door:
                continue
                
            door_pos = door["position"]
            orientation = door.get("orientation", "horizontal")
            door_width = door.get("width", self.door_width)
            door_type = door.get("type", "")
            connects = door.get("connects", [-1, -1])
            
            # Draw the door opening and swing
            self._draw_door(ax, door_pos, orientation, door_width, door_type)
    
    def _draw_door(self, ax, position, orientation, width, door_type=""):
        """Draw a door with proper swing arc."""
        x, y = position
        
        # Create door opening (gap in wall)
        if orientation == "horizontal":
            # Door on vertical wall
            opening = patches.Rectangle(
                (x - width/2, y - self.wall_thickness/2),
                width, self.wall_thickness,
                facecolor='white',
                edgecolor='none',
                zorder=3
            )
            
            # Door swing arc
            arc = patches.Arc(
                (x - width/4, y),
                width, width,
                angle=0,
                theta1=0, theta2=90,
                edgecolor='black',
                linewidth=1.5,
                zorder=4
            )
            
        else:  # vertical door
            # Door on horizontal wall
            opening = patches.Rectangle(
                (x - self.wall_thickness/2, y - width/2),
                self.wall_thickness, width,
                facecolor='white',
                edgecolor='none',
                zorder=3
            )
            
            # Door swing arc
            arc = patches.Arc(
                (x, y - width/4),
                width, width,
                angle=0,
                theta1=270, theta2=0,
                edgecolor='black',
                linewidth=1.5,
                zorder=4
            )
        
        # Add the door opening and swing
        ax.add_patch(opening)
        ax.add_patch(arc)
        
    def _draw_main_entrance(self, ax, door):
        """Draw special marking for main entrance door."""
        x, y = door["position"]
        
        # Add arrow pointing to entrance
        ax.arrow(
            x, y - 1.2,
            0, 0.8,
            head_width=0.3, head_length=0.3,
            fc='blue', ec='blue',
            linewidth=2,
            zorder=5
        )
        
        # Add "MAIN ENTRANCE" label
        ax.text(
            x, y - 1.5,
            "MAIN ENTRANCE",
            ha='center', va='center',
            fontsize=8, fontweight='bold',
            color='blue',
            zorder=5
        )
    
    def _add_room_label_and_dimensions(self, ax, room):
        """Add room label and dimensions."""
        x, y = room["position"]
        w, h = room["size"]
        room_type = room["type"].upper()
        
        # Add room label in the center
        ax.text(
            x + w/2, y + h/2,
            room_type,
            ha='center', va='center',
            fontsize=12, fontweight='bold',
            color='black',
            zorder=5
        )
        
        # Add room dimensions at the top
        ax.text(
            x + w/2, y + h * 0.9,
            f"{w:.1f}m × {h:.1f}m",
            ha='center', va='center',
            fontsize=8, color='black',
            zorder=5
        )
    
    def _draw_room_fixtures(self, ax, room):
        """Draw appropriate fixtures for each room type."""
        room_type = room["type"].lower()
        
        # Check if we have a drawing function for this room type
        if room_type in self.room_fixtures:
            self.room_fixtures[room_type](ax, room)
    
    def _draw_bedroom_furniture(self, ax, room):
        """Draw bedroom furniture."""
        x, y = room["position"]
        w, h = room["size"]
        
        # Draw a bed against the top wall
        bed_width = w * 0.5
        bed_height = h * 0.35
        bed_x = x + (w - bed_width) / 2
        bed_y = y + h - bed_height - 0.3
        
        # Bed frame
        bed = patches.Rectangle(
            (bed_x, bed_y),
            bed_width, bed_height,
            facecolor='bisque',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(bed)
        
        # Mattress
        mattress = patches.Rectangle(
            (bed_x + 0.05, bed_y + 0.05),
            bed_width - 0.1, bed_height - 0.1,
            facecolor='white',
            edgecolor='#D0D0D0',
            linewidth=0.5,
            zorder=2.1
        )
        ax.add_patch(mattress)
        
        # Pillow
        pillow_width = bed_width * 0.8
        pillow_height = bed_height * 0.2
        pillow_x = bed_x + (bed_width - pillow_width) / 2
        pillow_y = bed_y + bed_height - pillow_height - 0.1
        
        pillow = patches.Rectangle(
            (pillow_x, pillow_y),
            pillow_width, pillow_height,
            facecolor='white',
            edgecolor='#D0D0D0',
            linewidth=0.5,
            zorder=2.2
        )
        ax.add_patch(pillow)
        
        # Side table
        table_size = 0.6
        table_x = bed_x - table_size - 0.1
        table_y = bed_y + (bed_height - table_size) / 2
        
        table = patches.Rectangle(
            (table_x, table_y),
            table_size, table_size,
            facecolor='sienna',
            edgecolor='black',
            linewidth=0.5,
            zorder=2
        )
        ax.add_patch(table)
        
        # Wardrobe
        wardrobe_width = 0.7
        wardrobe_height = 1.8
        wardrobe_x = x + w - wardrobe_width - 0.3
        wardrobe_y = y + 0.3
        
        wardrobe = patches.Rectangle(
            (wardrobe_x, wardrobe_y),
            wardrobe_width, wardrobe_height,
            facecolor='burlywood',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(wardrobe)
        
        # Add door lines to wardrobe
        door_line_x = wardrobe_x + wardrobe_width/2
        ax.plot(
            [door_line_x, door_line_x],
            [wardrobe_y, wardrobe_y + wardrobe_height],
            'k-', linewidth=0.5, zorder=2.1
        )
    
    def _draw_bathroom_fixtures(self, ax, room):
        """Draw bathroom fixtures with realistic shapes."""
        x, y = room["position"]
        w, h = room["size"]
        
        # Draw toilet (more realistic)
        toilet_width = 0.6
        toilet_depth = 0.7
        toilet_x = x + 0.3
        toilet_y = y + 0.3
        
        # Toilet base (rectangle)
        toilet_base = patches.Rectangle(
            (toilet_x, toilet_y),
            toilet_width, toilet_depth * 0.6,
            facecolor='white',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(toilet_base)
        
        # Toilet seat (oval)
        seat_width = toilet_width * 0.8
        seat_height = toilet_depth * 0.4
        seat_x = toilet_x + (toilet_width - seat_width) / 2
        seat_y = toilet_y + toilet_depth * 0.2
        
        toilet_seat = patches.Ellipse(
            (seat_x + seat_width/2, seat_y + seat_height/2),
            seat_width, seat_height,
            facecolor='white',
            edgecolor='black',
            linewidth=0.5,
            zorder=2.1
        )
        ax.add_patch(toilet_seat)
        
        # Draw sink with realistic shape
        sink_width = 0.6
        sink_depth = 0.5
        sink_x = x + w - sink_width - 0.3
        sink_y = y + 0.3
        
        # Sink countertop
        counter = patches.Rectangle(
            (sink_x - 0.1, sink_y - 0.1),
            sink_width + 0.2, sink_depth + 0.1,
            facecolor='lightgray',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(counter)
        
        # Sink basin (oval)
        sink_basin = patches.Ellipse(
            (sink_x + sink_width/2, sink_y + sink_depth/2),
            sink_width * 0.7, sink_depth * 0.7,
            facecolor='white',
            edgecolor='black',
            linewidth=0.5,
            zorder=2.1
        )
        ax.add_patch(sink_basin)
        
        # Draw shower/tub if the bathroom is big enough
        if w * h > 6:
            shower_width = w * 0.4
            shower_height = h * 0.4
            shower_x = x + w - shower_width - 0.3
            shower_y = y + h - shower_height - 0.3
            
            # Shower tray
            shower = patches.Rectangle(
                (shower_x, shower_y),
                shower_width, shower_height,
                facecolor='lightblue',
                edgecolor='black',
                linewidth=1,
                zorder=2
            )
            ax.add_patch(shower)
            
            # Shower head
            shower_head_x = shower_x + shower_width * 0.85
            shower_head_y = shower_y + shower_height * 0.15
            
            shower_head = patches.Circle(
                (shower_head_x, shower_head_y),
                0.1,
                facecolor='silver',
                edgecolor='black',
                linewidth=0.5,
                zorder=2.2
            )
            ax.add_patch(shower_head)
            
            # Shower drain
            drain = patches.Circle(
                (shower_x + shower_width/2, shower_y + shower_height/2),
                0.07,
                facecolor='darkgray',
                edgecolor='black',
                linewidth=0.5,
                zorder=2.1
            )
            ax.add_patch(drain)
    
    def _draw_kitchen_furniture(self, ax, room):
        """Draw kitchen furniture and fixtures with realistic detail."""
        x, y = room["position"]
        w, h = room["size"]
        
        # Draw counters along walls
        counter_depth = 0.6
        
        # Left counter
        left_counter = patches.Rectangle(
            (x + 0.2, y + 0.2),
            counter_depth, h - 0.4,
            facecolor='lightgray',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(left_counter)
        
        # Bottom counter
        bottom_counter = patches.Rectangle(
            (x + 0.2 + counter_depth, y + 0.2),
            w - 0.4 - counter_depth, counter_depth,
            facecolor='lightgray',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(bottom_counter)
        
        # Draw sink - more realistic
        sink_size = 0.5
        sink_x = x + 0.2 + (counter_depth - sink_size) / 2
        sink_y = y + h / 2 - sink_size / 2
        
        # Sink basin (rectangle with rounded corners)
        sink = patches.FancyBboxPatch(
            (sink_x, sink_y),
            sink_size, sink_size,
            boxstyle=patches.BoxStyle("Round", pad=0.1),
            facecolor='white',
            edgecolor='black',
            linewidth=1,
            zorder=2.1
        )
        ax.add_patch(sink)
        
        # Sink faucet
        faucet_y = sink_y
        faucet_x = sink_x + sink_size/2
        
        # Faucet base
        ax.plot(
            [faucet_x, faucet_x],
            [faucet_y, faucet_y - 0.15],
            'k-', linewidth=2, zorder=2.2
        )
        
        # Draw stove with burners
        stove_width = 0.7
        stove_height = 0.6
        stove_x = x + 0.2 + counter_depth + 0.5
        stove_y = y + 0.2 + (counter_depth - stove_height) / 2
        
        # Stove base
        stove = patches.Rectangle(
            (stove_x, stove_y),
            stove_width, stove_height,
            facecolor='black',
            edgecolor='black',
            linewidth=1,
            zorder=2.1
        )
        ax.add_patch(stove)
        
        # Draw four burners in a 2x2 grid
        burner_radius = 0.08
        burner_padding = 0.12
        
        for i in range(2):
            for j in range(2):
                burner = patches.Circle(
                    (stove_x + 0.15 + i * (burner_radius*2 + burner_padding), 
                     stove_y + 0.15 + j * (burner_radius*2 + burner_padding)),
                    burner_radius,
                    facecolor='darkgray',
                    edgecolor='gray',
                    linewidth=1,
                    zorder=2.2
                )
                ax.add_patch(burner)
                
                # Add burner detail - rings
                inner_burner = patches.Circle(
                    (stove_x + 0.15 + i * (burner_radius*2 + burner_padding), 
                     stove_y + 0.15 + j * (burner_radius*2 + burner_padding)),
                    burner_radius * 0.6,
                    facecolor='none',
                    edgecolor='gray',
                    linewidth=0.5,
                    zorder=2.3
                )
                ax.add_patch(inner_burner)
        
        # Draw refrigerator
        fridge_width = 0.7
        fridge_height = 1.5
        fridge_x = x + w - fridge_width - 0.2
        fridge_y = y + h - fridge_height - 0.2
        
        # Fridge body
        fridge = patches.Rectangle(
            (fridge_x, fridge_y),
            fridge_width, fridge_height,
            facecolor='white',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(fridge)
        
        # Fridge door line
        fridge_line_y = fridge_y + fridge_height * 0.7
        ax.plot(
            [fridge_x, fridge_x + fridge_width],
            [fridge_line_y, fridge_line_y],
            'k-', linewidth=0.5, zorder=2.1
        )
        
        # Door handles
        handle_size = 0.1
        # Freezer door handle
        ax.plot(
            [fridge_x + handle_size, fridge_x + handle_size],
            [fridge_y + fridge_line_y + handle_size*2, fridge_y + fridge_line_y - handle_size*2],
            'k-', linewidth=1.5, zorder=2.2
        )
        # Fridge door handle
        ax.plot(
            [fridge_x + handle_size, fridge_x + handle_size],
            [fridge_y + handle_size*2, fridge_y + fridge_line_y - handle_size*2],
            'k-', linewidth=1.5, zorder=2.2
        )
    
    def _draw_living_room_furniture(self, ax, room):
        """Draw living room furniture with realistic detail."""
        x, y = room["position"]
        w, h = room["size"]
        
        # Draw sofa along the top wall
        sofa_width = w * 0.7
        sofa_depth = 0.8
        sofa_x = x + (w - sofa_width) / 2
        sofa_y = y + h - sofa_depth - 0.2
        
        # Main sofa body
        sofa = patches.Rectangle(
            (sofa_x, sofa_y),
            sofa_width, sofa_depth,
            facecolor='lightyellow',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(sofa)
        
        # Sofa back cushions
        back_height = 0.2
        cushion_width = sofa_width / 3
        
        for i in range(3):
            cushion = patches.Rectangle(
                (sofa_x + i * cushion_width, sofa_y + sofa_depth - back_height),
                cushion_width, back_height,
                facecolor='khaki',
                edgecolor='black',
                linewidth=0.5,
                zorder=2.1
            )
            ax.add_patch(cushion)
        
        # Sofa seat cushions
        seat_height = 0.2
        for i in range(3):
            cushion = patches.Rectangle(
                (sofa_x + i * cushion_width, sofa_y + sofa_depth - back_height - seat_height),
                cushion_width, seat_height,
                facecolor='khaki',
                edgecolor='black',
                linewidth=0.5,
                zorder=2.1
            )
            ax.add_patch(cushion)
        
        # Draw coffee table in center - glass table
        table_width = w * 0.4
        table_height = 0.6
        table_x = x + (w - table_width) / 2
        table_y = y + h * 0.4
        
        # Glass top
        table = patches.Rectangle(
            (table_x, table_y),
            table_width, table_height,
            facecolor='lightcyan',
            edgecolor='black',
            alpha=0.7,
            linewidth=1,
            zorder=2
        )
        ax.add_patch(table)
        
        # Table legs
        leg_size = 0.05
        for dx, dy in [(0, 0), (0, table_height-leg_size), 
                       (table_width-leg_size, 0), 
                       (table_width-leg_size, table_height-leg_size)]:
            leg = patches.Rectangle(
                (table_x + dx, table_y + dy),
                leg_size, leg_size,
                facecolor='black',
                edgecolor='none',
                zorder=2.1
            )
            ax.add_patch(leg)
        
        # Add side tables
        side_table_size = 0.6
        
        # Left side table
        left_table = patches.Rectangle(
            (x + 0.2, y + 0.2),
            side_table_size, side_table_size,
            facecolor='burlywood',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(left_table)
        
        # Add a lamp on left table
        lamp_base = patches.Circle(
            (x + 0.2 + side_table_size/2, y + 0.2 + side_table_size/2),
            0.1,
            facecolor='darkgray',
            edgecolor='black',
            linewidth=0.5,
            zorder=2.1
        )
        ax.add_patch(lamp_base)
        
        # Lampshade
        lampshade = patches.Polygon(
            [
                [x + 0.2 + side_table_size/2 - 0.15, y + 0.2 + side_table_size/2 + 0.1],
                [x + 0.2 + side_table_size/2 + 0.15, y + 0.2 + side_table_size/2 + 0.1],
                [x + 0.2 + side_table_size/2 + 0.12, y + 0.2 + side_table_size/2 + 0.3],
                [x + 0.2 + side_table_size/2 - 0.12, y + 0.2 + side_table_size/2 + 0.3],
            ],
            facecolor='lightyellow',
            edgecolor='black',
            linewidth=0.5,
            zorder=2.2
        )
        ax.add_patch(lampshade)
        
        # Add armchairs if room is wide enough
        if w > 5:
            chair_size = 0.8
            chair_padding = 0.3
            
            # Left chair
            left_chair = patches.Rectangle(
                (x + chair_padding, y + h * 0.5),
                chair_size, chair_size,
                facecolor='lightyellow',
                edgecolor='black',
                linewidth=1,
                zorder=2
            )
            ax.add_patch(left_chair)
            
            # Chair back
            chair_back = patches.Rectangle(
                (x + chair_padding, y + h * 0.5 + chair_size - 0.2),
                chair_size, 0.2,
                facecolor='khaki',
                edgecolor='black',
                linewidth=0.5,
                zorder=2.1
            )
            ax.add_patch(chair_back)
    
    def _draw_tv_lounge_furniture(self, ax, room):
        """Draw TV lounge furniture with realistic TV and media center."""
        x, y = room["position"]
        w, h = room["size"]
        
        # Draw TV stand and modern flat screen TV
        tv_width = w * 0.5
        tv_height = 0.1
        tv_depth = 0.5
        tv_x = x + (w - tv_width) / 2
        tv_y = y + 0.2
        
        # TV stand/media cabinet
        tv_stand = patches.Rectangle(
            (tv_x - 0.2, tv_y),
            tv_width + 0.4, tv_depth,
            facecolor='saddlebrown',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(tv_stand)
        
        # Modern flat TV
        tv_screen_width = tv_width * 0.9
        tv_screen_height = 0.05
        tv_screen_x = tv_x + (tv_width - tv_screen_width) / 2
        tv_screen_y = tv_y + tv_depth
        
        # TV base
        tv_base = patches.Rectangle(
            (tv_screen_x + tv_screen_width * 0.4, tv_screen_y),
            tv_screen_width * 0.2, 0.1,
            facecolor='dimgray',
            edgecolor='black',
            linewidth=0.5,
            zorder=2.1
        )
        ax.add_patch(tv_base)
        
        # TV screen
        tv_screen = patches.Rectangle(
            (tv_screen_x, tv_screen_y + 0.1),
            tv_screen_width, tv_screen_height * 6,  # Taller, thinner TV
            facecolor='black',
            edgecolor='darkgray',
            linewidth=1,
            zorder=2.2
        )
        ax.add_patch(tv_screen)
        
        # Draw sofa on top wall - sectional style
        sofa_width = w * 0.7
        sofa_depth = 0.8
        sofa_x = x + (w - sofa_width) / 2
        sofa_y = y + h - sofa_depth - 0.2
        
        # Main sofa body
        sofa = patches.Rectangle(
            (sofa_x, sofa_y),
            sofa_width, sofa_depth,
            facecolor='lightskyblue',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(sofa)
        
        # Draw sofa back and arms
        back_height = 0.2
        arm_width = 0.2
        
        # Sofa back cushions
        cushion_width = (sofa_width - 2*arm_width) / 3
        for i in range(3):
            cushion = patches.Rectangle(
                (sofa_x + arm_width + i * cushion_width, sofa_y + sofa_depth - back_height),
                cushion_width, back_height,
                facecolor='skyblue',
                edgecolor='black',
                linewidth=0.5,
                zorder=2.1
            )
            ax.add_patch(cushion)
        
        # Sofa arms
        left_arm = patches.Rectangle(
            (sofa_x, sofa_y),
            arm_width, sofa_depth,
            facecolor='skyblue',
            edgecolor='black',
            linewidth=1,
            zorder=2.1
        )
        ax.add_patch(left_arm)
        
        right_arm = patches.Rectangle(
            (sofa_x + sofa_width - arm_width, sofa_y),
            arm_width, sofa_depth,
            facecolor='skyblue',
            edgecolor='black',
            linewidth=1,
            zorder=2.1
        )
        ax.add_patch(right_arm)
        
        # Draw coffee table
        table_width = w * 0.4
        table_height = 0.6
        table_x = x + (w - table_width) / 2
        table_y = y + h * 0.4
        
        # Glass coffee table
        table = patches.Rectangle(
            (table_x, table_y),
            table_width, table_height,
            facecolor='lightcyan',
            edgecolor='black',
            alpha=0.7,
            linewidth=1,
            zorder=2
        )
        ax.add_patch(table)
        
        # Add some items on coffee table
        # Magazine/remote
        mag = patches.Rectangle(
            (table_x + table_width * 0.3, table_y + table_height * 0.3),
            table_width * 0.2, table_height * 0.2,
            facecolor='lightgray',
            edgecolor='gray',
            linewidth=0.5,
            zorder=2.1
        )
        ax.add_patch(mag)
        
        # Additional seating if room is wide enough
        if w > 5:
            chair_size = 0.8
            chair_padding = 0.3
            
            # Left recliner
            left_chair = patches.Rectangle(
                (x + chair_padding, y + h * 0.5),
                chair_size, chair_size,
                facecolor='lightskyblue',
                edgecolor='black',
                linewidth=1,
                zorder=2
            )
            ax.add_patch(left_chair)
            
            # Chair back
            chair_back = patches.Rectangle(
                (x + chair_padding, y + h * 0.5 + chair_size - 0.2),
                chair_size, 0.2,
                facecolor='skyblue',
                edgecolor='black',
                linewidth=0.5,
                zorder=2.1
            )
            ax.add_patch(chair_back)
    
    def _draw_garage_items(self, ax, room):
        """Draw garage with realistic car."""
        x, y = room["position"]
        w, h = room["size"]
        
        # Draw a realistic car
        car_width = min(w * 0.7, 2.2)  # Standard car width ~2m
        car_length = min(h * 0.7, 4.5)  # Standard car length ~4.5m
        
        car_x = x + (w - car_width) / 2
        car_y = y + (h - car_length) / 2
        
        # Car body - main shape with curved corners
        car_body = patches.FancyBboxPatch(
            (car_x, car_y + car_length * 0.2),
            car_width, car_length * 0.6,
            boxstyle=patches.BoxStyle("Round", pad=0.1),
            facecolor='darkred',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(car_body)
        
        # Car hood (front)
        hood_points = [
            [car_x + car_width * 0.15, car_y + car_length * 0.2],
            [car_x + car_width * 0.85, car_y + car_length * 0.2],
            [car_x + car_width * 0.9, car_y + car_length * 0.05],
            [car_x + car_width * 0.1, car_y + car_length * 0.05]
        ]
        hood = patches.Polygon(
            hood_points,
            facecolor='darkred',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(hood)
        
        # Car trunk (back)
        trunk_points = [
            [car_x + car_width * 0.15, car_y + car_length * 0.8],
            [car_x + car_width * 0.85, car_y + car_length * 0.8],
            [car_x + car_width * 0.9, car_y + car_length * 0.95],
            [car_x + car_width * 0.1, car_y + car_length * 0.95]
        ]
        trunk = patches.Polygon(
            trunk_points,
            facecolor='darkred',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(trunk)
        
        # Windshield
        windshield_points = [
            [car_x + car_width * 0.15, car_y + car_length * 0.2],
            [car_x + car_width * 0.85, car_y + car_length * 0.2],
            [car_x + car_width * 0.75, car_y + car_length * 0.35],
            [car_x + car_width * 0.25, car_y + car_length * 0.35]
        ]
        windshield = patches.Polygon(
            windshield_points,
            facecolor='lightblue',
            edgecolor='black',
            linewidth=0.5,
            alpha=0.7,
            zorder=2.1
        )
        ax.add_patch(windshield)
        
        # Back windshield
        back_windshield_points = [
            [car_x + car_width * 0.15, car_y + car_length * 0.8],
            [car_x + car_width * 0.85, car_y + car_length * 0.8],
            [car_x + car_width * 0.75, car_y + car_length * 0.65],
            [car_x + car_width * 0.25, car_y + car_length * 0.65]
        ]
        back_windshield = patches.Polygon(
            back_windshield_points,
            facecolor='lightblue',
            edgecolor='black',
            linewidth=0.5,
            alpha=0.7,
            zorder=2.1
        )
        ax.add_patch(back_windshield)
        
        # Car roof
        roof_points = [
            [car_x + car_width * 0.25, car_y + car_length * 0.35],
            [car_x + car_width * 0.75, car_y + car_length * 0.35],
            [car_x + car_width * 0.75, car_y + car_length * 0.65],
            [car_x + car_width * 0.25, car_y + car_length * 0.65]
        ]
        roof = patches.Polygon(
            roof_points,
            facecolor='darkred',
            edgecolor='black',
            linewidth=0.5,
            zorder=2.2
        )
        ax.add_patch(roof)
        
        # Car windows (side windows)
        # Left front window
        lf_window_points = [
            [car_x + car_width * 0.15, car_y + car_length * 0.35],
            [car_x + car_width * 0.25, car_y + car_length * 0.35],
            [car_x + car_width * 0.25, car_y + car_length * 0.5],
            [car_x + car_width * 0.15, car_y + car_length * 0.5]
        ]
        lf_window = patches.Polygon(
            lf_window_points,
            facecolor='lightblue',
            edgecolor='black',
            linewidth=0.5,
            alpha=0.7,
            zorder=2.1
        )
        ax.add_patch(lf_window)
        
        # Right front window
        rf_window_points = [
            [car_x + car_width * 0.75, car_y + car_length * 0.35],
            [car_x + car_width * 0.85, car_y + car_length * 0.35],
            [car_x + car_width * 0.85, car_y + car_length * 0.5],
            [car_x + car_width * 0.75, car_y + car_length * 0.5]
        ]
        rf_window = patches.Polygon(
            rf_window_points,
            facecolor='lightblue',
            edgecolor='black',
            linewidth=0.5,
            alpha=0.7,
            zorder=2.1
        )
        ax.add_patch(rf_window)
        
        # Left rear window
        lr_window_points = [
            [car_x + car_width * 0.15, car_y + car_length * 0.5],
            [car_x + car_width * 0.25, car_y + car_length * 0.5],
            [car_x + car_width * 0.25, car_y + car_length * 0.65],
            [car_x + car_width * 0.15, car_y + car_length * 0.65]
        ]
        lr_window = patches.Polygon(
            lr_window_points,
            facecolor='lightblue',
            edgecolor='black',
            linewidth=0.5,
            alpha=0.7,
            zorder=2.1
        )
        ax.add_patch(lr_window)
        
        # Right rear window
        rr_window_points = [
            [car_x + car_width * 0.75, car_y + car_length * 0.5],
            [car_x + car_width * 0.85, car_y + car_length * 0.5],
            [car_x + car_width * 0.85, car_y + car_length * 0.65],
            [car_x + car_width * 0.75, car_y + car_length * 0.65]
        ]
        rr_window = patches.Polygon(
            rr_window_points,
            facecolor='lightblue',
            edgecolor='black',
            linewidth=0.5,
            alpha=0.7,
            zorder=2.1
        )
        ax.add_patch(rr_window)
        
        # Car wheels - realistic tires with rims
        wheel_radius = car_width * 0.12
        wheel_positions = [
            (car_x + car_width * 0.2, car_y + car_length * 0.15),  # Front left
            (car_x + car_width * 0.8, car_y + car_length * 0.15),  # Front right
            (car_x + car_width * 0.2, car_y + car_length * 0.85),  # Rear left
            (car_x + car_width * 0.8, car_y + car_length * 0.85)   # Rear right
        ]
        
        for wheel_pos in wheel_positions:
            # Tire
            tire = patches.Circle(
                wheel_pos, wheel_radius,
                facecolor='black',
                edgecolor='gray',
                linewidth=1,
                zorder=2.3
            )
            ax.add_patch(tire)
            
            # Rim
            rim = patches.Circle(
                wheel_pos, wheel_radius * 0.6,
                facecolor='silver',
                edgecolor='gray',
                linewidth=0.5,
                zorder=2.4
            )
            ax.add_patch(rim)
            
            # Hub cap
            hub = patches.Circle(
                wheel_pos, wheel_radius * 0.2,
                facecolor='darkgray',
                edgecolor='black',
                linewidth=0.5,
                zorder=2.5
            )
            ax.add_patch(hub)
        
        # Add parking lines on the floor
        line_width = 0.05
        
        # Left parking line
        left_line = patches.Rectangle(
            (car_x - 0.3, car_y - 0.2),
            line_width, car_length + 0.4,
            facecolor='white',
            edgecolor='none',
            alpha=0.7,
            zorder=1.5
        )
        ax.add_patch(left_line)
        
        # Right parking line
        right_line = patches.Rectangle(
            (car_x + car_width + 0.3, car_y - 0.2),
            line_width, car_length + 0.4,
            facecolor='white',
            edgecolor='none',
            alpha=0.7,
            zorder=1.5
        )
        ax.add_patch(right_line)
        
        # Garage door outline at the front of garage
        if y < 1:  # If garage is at front of house
            door_width = min(w * 0.8, 3)
            door_x = x + (w - door_width) / 2
            
            # Garage door panels
            num_panels = 4
            panel_height = 0.3
            
            for i in range(num_panels):
                panel = patches.Rectangle(
                    (door_x, y + i * panel_height),
                    door_width, panel_height,
                    facecolor='none',
                    edgecolor='darkgray',
                    linewidth=1,
                    linestyle='--',
                    zorder=1.5
                )
                ax.add_patch(panel)
    
    def _draw_dining_room_furniture(self, ax, room):
        """Draw dining room with table and chairs."""
        x, y = room["position"]
        w, h = room["size"]
        
        # Draw dining table - improved design
        table_width = min(w * 0.6, 2.0)
        table_height = min(h * 0.6, 2.2)
        
        table_x = x + (w - table_width) / 2
        table_y = y + (h - table_height) / 2
        
        # Table top
        table = patches.FancyBboxPatch(
            (table_x, table_y),
            table_width, table_height,
            boxstyle=patches.BoxStyle("Round", pad=0.02),
            facecolor='sienna',
            edgecolor='black',
            linewidth=1,
            zorder=2
        )
        ax.add_patch(table)
        
        # Table detail - wood grain effect
        grain_spacing = 0.1
        for i in range(int(table_height / grain_spacing) - 1):
            grain_y = table_y + grain_spacing * (i + 1)
            ax.plot(
                [table_x, table_x + table_width],
                [grain_y, grain_y],
                'k-', linewidth=0.2, alpha=0.3, zorder=2.1
            )
            
        # Table centerpiece
        centerpiece_size = 0.3
        centerpiece = patches.Ellipse(
            (table_x + table_width/2, table_y + table_height/2),
            centerpiece_size, centerpiece_size * 0.7,
            facecolor='lightgray',
            edgecolor='gray',
            linewidth=0.5,
            zorder=2.1
        )
        ax.add_patch(centerpiece)
        
        # Draw chairs around the table
        chair_size = 0.5
        chair_padding = 0.05
        
        # Chair positions around table
        chair_positions = [
            # Top row
            {"x": table_x + table_width * 0.25 - chair_size/2, 
             "y": table_y + table_height + chair_padding,
             "side": "top"},
            {"x": table_x + table_width * 0.75 - chair_size/2, 
             "y": table_y + table_height + chair_padding,
             "side": "top"},
            
            # Bottom row
            {"x": table_x + table_width * 0.25 - chair_size/2, 
             "y": table_y - chair_size - chair_padding,
             "side": "bottom"},
            {"x": table_x + table_width * 0.75 - chair_size/2, 
             "y": table_y - chair_size - chair_padding,
             "side": "bottom"},
            
            # Left side
            {"x": table_x - chair_size - chair_padding, 
             "y": table_y + table_height * 0.33 - chair_size/2,
             "side": "left"},
            {"x": table_x - chair_size - chair_padding, 
             "y": table_y + table_height * 0.67 - chair_size/2,
             "side": "left"},
            
            # Right side
            {"x": table_x + table_width + chair_padding, 
             "y": table_y + table_height * 0.33 - chair_size/2,
             "side": "right"},
            {"x": table_x + table_width + chair_padding, 
             "y": table_y + table_height * 0.67 - chair_size/2,
             "side": "right"}
        ]
        
        for pos in chair_positions:
            chair_x = pos["x"]
            chair_y = pos["y"]
            side = pos["side"]
            
            # Chair base
            chair_base = patches.Rectangle(
                (chair_x, chair_y),
                chair_size, chair_size,
                facecolor='burlywood',
                edgecolor='black',
                linewidth=0.5,
                zorder=2
            )
            ax.add_patch(chair_base)
            
            # Chair back
            if side == "top":
                chair_back = patches.Rectangle(
                    (chair_x, chair_y),
                    chair_size, chair_size * 0.2,
                    facecolor='sienna',
                    edgecolor='black',
                    linewidth=0.5,
                    zorder=2.1
                )
            elif side == "bottom":
                chair_back = patches.Rectangle(
                    (chair_x, chair_y + chair_size * 0.8),
                    chair_size, chair_size * 0.2,
                    facecolor='sienna',
                    edgecolor='black',
                    linewidth=0.5,
                    zorder=2.1
                )
            elif side == "left":
                chair_back = patches.Rectangle(
                    (chair_x + chair_size * 0.8, chair_y),
                    chair_size * 0.2, chair_size,
                    facecolor='sienna',
                    edgecolor='black',
                    linewidth=0.5,
                    zorder=2.1
                )
            else:  # right
                chair_back = patches.Rectangle(
                    (chair_x, chair_y),
                    chair_size * 0.2, chair_size,
                    facecolor='sienna',
                    edgecolor='black',
                    linewidth=0.5,
                    zorder=2.1
                )
            ax.add_patch(chair_back)
        
        # Add a buffet cabinet along a wall if room is large enough
        if w * h > 25:
            cabinet_width = 1.8
            cabinet_height = 0.5
            cabinet_x = x + 0.2
            cabinet_y = y + h - 0.7
            
            cabinet = patches.Rectangle(
                (cabinet_x, cabinet_y),
                cabinet_width, cabinet_height,
                facecolor='sienna',
                edgecolor='black',
                linewidth=1,
                zorder=2
            )
            ax.add_patch(cabinet)
            
            # Add some dishes/decor on top of cabinet
            dish1 = patches.Circle(
                (cabinet_x + cabinet_width * 0.25, cabinet_y + cabinet_height * 0.5),
                0.1,
                facecolor='white',
                edgecolor='gray',
                linewidth=0.5,
                zorder=2.1
            )
            ax.add_patch(dish1)
            
            dish2 = patches.Circle(
                (cabinet_x + cabinet_width * 0.75, cabinet_y + cabinet_height * 0.5),
                0.1,
                facecolor='white',
                edgecolor='gray',
                linewidth=0.5,
                zorder=2.1
            )
            ax.add_patch(dish2)
    
    def _draw_stairs(self, ax, room):
        """Draw stairs with improved detail."""
        x, y = room["position"]
        w, h = room["size"]
        
        # Determine stair orientation based on room shape
        if w > h:
            # Horizontal stairs (wider than tall)
            stair_width = min(w * 0.8, 3.0)
            stair_height = min(h * 0.6, 2.0)
            stair_x = x + (w - stair_width) / 2
            stair_y = y + (h - stair_height) / 2
            
            # Draw the stairs rectangle outline
            stairs_outline = patches.Rectangle(
                (stair_x, stair_y),
                stair_width, stair_height,
                facecolor='none',
                edgecolor='black',
                linewidth=1,
                zorder=2
            )
            ax.add_patch(stairs_outline)
            
            # Draw stair steps with better detail
            num_steps = 8
            step_width = stair_width / num_steps
            
            for i in range(num_steps):
                # Each step
                step = patches.Rectangle(
                    (stair_x + i * step_width, stair_y),
                    step_width, stair_height,
                    facecolor='none',
                    edgecolor='black',
                    linewidth=0.5,
                    zorder=2
                )
                ax.add_patch(step)
                
                # Add step shadow/detail
                ax.plot(
                    [stair_x + i * step_width, stair_x + i * step_width],
                    [stair_y, stair_y + stair_height],
                    'k-', linewidth=0.5, zorder=2.1
                )
                
                # Add "nosing" detail to each step
                nosing = patches.Rectangle(
                    (stair_x + i * step_width, stair_y),
                    step_width, 0.05,
                    facecolor='gray',
                    edgecolor='black',
                    linewidth=0.3,
                    zorder=2.1
                )
                ax.add_patch(nosing)
                
        else:
            # Vertical stairs (taller than wide)
            stair_width = min(w * 0.6, 2.0)
            stair_height = min(h * 0.8, 3.0)
            stair_x = x + (w - stair_width) / 2
            stair_y = y + (h - stair_height) / 2
            
            # Draw the stairs rectangle outline
            stairs_outline = patches.Rectangle(
                (stair_x, stair_y),
                stair_width, stair_height,
                facecolor='none',
                edgecolor='black',
                linewidth=1,
                zorder=2
            )
            ax.add_patch(stairs_outline)
            
            # Draw stair steps with better detail
            num_steps = 8
            step_height = stair_height / num_steps
            
            for i in range(num_steps):
                # Each step
                step = patches.Rectangle(
                    (stair_x, stair_y + i * step_height),
                    stair_width, step_height,
                    facecolor='none',
                    edgecolor='black',
                    linewidth=0.5,
                    zorder=2
                )
                ax.add_patch(step)
                
                # Add step shadow/detail
                ax.plot(
                    [stair_x, stair_x + stair_width],
                    [stair_y + i * step_height, stair_y + i * step_height],
                    'k-', linewidth=0.5, zorder=2.1
                )
                
                # Add "nosing" detail to each step
                nosing = patches.Rectangle(
                    (stair_x, stair_y + i * step_height),
                    0.05, step_height,
                    facecolor='gray',
                    edgecolor='black',
                    linewidth=0.3,
                    zorder=2.1
                )
                ax.add_patch(nosing)
        
        # Add directional arrows to indicate up/down
        arrow_len = 0.4
        arrow_x = stair_x + stair_width / 2
        arrow_y = stair_y + stair_height / 2 - arrow_len/2
        
        # Up arrow
        ax.arrow(
            arrow_x, arrow_y,
            0, arrow_len,
            head_width=0.2, head_length=0.15,
            fc='black', ec='black',
            linewidth=1.5,
            zorder=2.5
        )
        
        # Add stairs text
        ax.text(
            stair_x + stair_width / 2,
            stair_y + stair_height / 2 + arrow_len/2 + 0.2,
            "STAIRS",
            ha='center', va='center',
            fontsize=8, fontweight='bold',
            zorder=2.5
        )
        
        # Add "UP" text
        ax.text(
            arrow_x + 0.25, arrow_y + arrow_len/2,
            "UP",
            ha='left', va='center',
            fontsize=6, fontweight='bold',
            zorder=2.5
        )
    
    def _draw_corridor_elements(self, ax, room):
        """Draw corridor elements to show circulation space."""
        x, y = room["position"]
        w, h = room["size"]
        
        # Draw directional arrows to indicate movement flow
        # Central arrow along corridor length
        if w > h:
            # Horizontal corridor
            arrow_x = x + w * 0.3
            arrow_y = y + h / 2
            arrow_dx = w * 0.4
            arrow_dy = 0
        else:
            # Vertical corridor
            arrow_x = x + w / 2
            arrow_y = y + h * 0.3
            arrow_dx = 0
            arrow_dy = h * 0.4
        
        # Draw movement arrow
        ax.arrow(
            arrow_x, arrow_y,
            arrow_dx, arrow_dy,
            head_width=0.15, head_length=0.2,
            fc='gray', ec='gray',
            linewidth=1.5, alpha=0.7,
            zorder=1.5
        )
        
        # Add footprint patterns to indicate walking path
        num_footprints = 5
        
        if w > h:
            # Horizontal corridor
            for i in range(num_footprints):
                fp_x = x + w * (0.2 + 0.6 * i / (num_footprints-1))
                fp_y = y + h * 0.5 + (0.1 if i % 2 == 0 else -0.1)
                
                # Simple footprint shape
                footprint = patches.Ellipse(
                    (fp_x, fp_y),
                    0.2, 0.1,
                    angle=0 if i % 2 == 0 else 0,
                    facecolor='lightgray',
                    edgecolor='gray',
                    linewidth=0.5,
                    alpha=0.5,
                    zorder=1.5
                )
                ax.add_patch(footprint)
        else:
            # Vertical corridor
            for i in range(num_footprints):
                fp_x = x + w * 0.5 + (0.1 if i % 2 == 0 else -0.1)
                fp_y = y + h * (0.2 + 0.6 * i / (num_footprints-1))
                
                # Simple footprint shape
                footprint = patches.Ellipse(
                    (fp_x, fp_y),
                    0.1, 0.2,
                    angle=90 if i % 2 == 0 else 90,
                    facecolor='lightgray',
                    edgecolor='gray',
                    linewidth=0.5,
                    alpha=0.5,
                    zorder=1.5
                )
                ax.add_patch(footprint)
    
    def _add_north_arrow(self, ax, x, y):
        """Add a north arrow to the plot."""
        arrow_len = 1
        
        # Draw the arrow with more professional styling
        ax.arrow(
            x, y,
            0, arrow_len,
            head_width=0.3, head_length=0.3,
            fc='blue', ec='blue',
            linewidth=2,
            zorder=10
        )
        
        # Add "N" label with better styling
        ax.text(
            x, y + arrow_len + 0.4,
            "N",
            ha='center', va='center',
            fontsize=12, fontweight='bold',
            color='blue',
            zorder=10
        )
        
        # Add compass circle (optional)
        compass_circle = patches.Circle(
            (x, y),
            0.2,
            facecolor='white',
            edgecolor='blue',
            linewidth=1,
            alpha=0.7,
            zorder=9.5
        )
        ax.add_patch(compass_circle)
    
    def _add_scale_bar(self, ax, x, y, length):
        """Add a scale bar to the plot."""
        # Draw the bar with better styling
        ax.plot(
            [x, x + length],
            [y, y],
            'k-',
            linewidth=3,
            solid_capstyle='butt',
            zorder=10
        )
        
        # Add tick marks
        tick_height = 0.15
        for i in range(length + 1):
            ax.plot(
                [x + i, x + i],
                [y - tick_height/2, y + tick_height/2],
                'k-',
                linewidth=1,
                zorder=10
            )
        
        # Add scale labels
        for i in range(length + 1):
            if i % 2 == 0:  # Label every second tick for cleaner look
                ax.text(
                    x + i,
                    y - tick_height - 0.1,
                    f"{i}m",
                    ha='center',
                    va='top',
                    fontsize=8,
                    zorder=10
                )
        
        # Add "SCALE" label
        ax.text(
            x + length/2,
            y - tick_height - 0.4,
            "SCALE",
            ha='center',
            va='top',
            fontsize=8,
            fontweight='bold',
            zorder=10
        )