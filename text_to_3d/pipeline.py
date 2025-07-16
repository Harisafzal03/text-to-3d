#!/usr/bin/env python3
"""
Text to 3D Pipeline
------------------
Provides the main pipeline for converting text to 3D models.
"""

import os
import time
import numpy as np
import matplotlib.pyplot as plt
import random
import re
from datetime import datetime
from pathlib import Path
from text_to_3d.model_generator.model_builder import ModelBuilder
from text_to_3d.floor_plan_renderer import FloorPlanRenderer
from text_to_3d.layout_generator.layout_model import ImprovedLayoutGenerator

class TextTo3DPipeline:
    def __init__(self):
        """Initialize the Text to 3D Pipeline."""
        print("Initializing pipeline components...")
        
        # Load room type definitions
        self.room_types = {
            "bedroom": {"color": [1.0, 0.6, 0.8], "min_area": 12},      # Pink, min 12 sq meters
            "kitchen": {"color": [0.4, 0.6, 1.0], "min_area": 9},       # Blue, min 9 sq meters
            "bathroom": {"color": [0.6, 1.0, 0.6], "min_area": 4.5},    # Green, min 4.5 sq meters
            "washroom": {"color": [0.5, 0.9, 0.6], "min_area": 4.5},    # Light green, min 4.5 sq meters
            "living room": {"color": [1.0, 0.9, 0.5], "min_area": 15},  # Yellow, min 15 sq meters
            "tv lounge": {"color": [1.0, 0.7, 0.4], "min_area": 15},    # Orange, min 15 sq meters
            "dining room": {"color": [1.0, 0.5, 0.5], "min_area": 10},  # Coral, min 10 sq meters
            "garage": {"color": [0.6, 0.6, 0.7], "min_area": 16},       # Gray-blue, min 16 sq meters
            "car parking": {"color": [0.7, 0.7, 0.8], "min_area": 16},  # Light purple-gray, min 16 sq meters
            "lobby": {"color": [0.9, 0.8, 0.5], "min_area": 8},         # Light orange/tan, min 8 sq meters
            "hallway": {"color": [0.9, 0.8, 0.7], "min_area": 6},       # Beige, min 6 sq meters
            "entrance": {"color": [0.8, 0.8, 0.6], "min_area": 5},      # Light brown, min 5 sq meters
            "main entrance": {"color": [0.8, 0.7, 0.5], "min_area": 6}, # Tan, min 6 sq meters
            "terrace": {"color": [0.7, 0.9, 0.8], "min_area": 10},      # Mint green, min 10 sq meters
            "study": {"color": [0.8, 0.7, 1.0], "min_area": 8},         # Lavender, min 8 sq meters
            "office": {"color": [0.7, 0.9, 1.0], "min_area": 8},        # Light blue, min 8 sq meters
            "corridor": {"color": [0.9, 0.9, 0.7], "min_area": 4}       # Light yellow for corridors
        }
        
        # Initialize the 3D model builder
        self.model_builder = ModelBuilder()
        
        # Standard door width (meters)
        self.door_width = 0.9
        
        print("Pipeline ready!")
    
    def generate(self, text, output_file=None):
        """Generate a 3D model from text description and save it to the output file."""
        print("\n" + "=" * 60)
        print(f"Processing text: '{text}'")
        print("=" * 60 + "\n")
        
        start_time = time.time()
        
        # Step 1: Process text input
        print("📝 Step 1: Processing text...")
        features = self._process_text(text)
        
        # Step 2: Generate 2D layout
        print("🏠 Step 2: Generating 2D layout...")
        layout = self._generate_layout(features)
        
        # Generate an image of the layout
        layout["visualization_path"] = self._visualize_layout(layout)
        
        # Step 3: Build 3D model
        print("🏗️ Step 3: Building 3D model...")
        model = self.model_builder.generate_3d_model(layout)
        print(f"✓ Created 3D model with {len(model['vertices'])} vertices")
        print(f"✓ Generated {len(model['faces'])} faces")
        
        # Set default output file if none provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/model_{timestamp}.obj"
        
        # Step 4: Export the model
        print("\n💾 Exporting model...")
        self.model_builder.export_obj(model, output_file)
        print(f"✓ Model exported to: {output_file}")
        
        # Print visualization paths
        print("\n🖼️ Visualizations:")
        print(f"✓ 2D Layout: {layout['visualization_path']}")
        print(f"✓ 3D Model preview: {model['visualization_path']}")
        
        elapsed_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("Generation complete!")
        print("=" * 60 + "\n")
        
        return features, layout, model
    
    def _process_text(self, text):
        """Process text input to extract features."""
        # Extract room information
        rooms = self._extract_rooms(text)
        print(f"✓ Detected {len(rooms)} rooms")
        
        # Extract style information
        styles = self._extract_styles(text)
        print(f"✓ Identified styles: {styles}")
        
        # Extract plot size information
        plot_size = self._extract_plot_size(text)
        
        # Extract number of stories
        stories = self._extract_stories(text)
        
        return {
            "rooms": rooms,
            "styles": styles,
            "plot_size": plot_size,
            "stories": stories
        }
    
    def _extract_rooms(self, text):
        """Extract room information from text."""
        rooms = []
        
        # Look for room count + room type patterns
        room_patterns = [
            r'(\d+)\s+(bedroom|kitchen|bathroom|washroom|living room|tv lounge|dining room|garage|lobby|hallway|entrance|terrace)',
            r'(one|two|three|four|five|six|seven|eight|nine|ten)\s+(bedroom|kitchen|bathroom|washroom|living room|tv lounge|dining room|garage|lobby|hallway|entrance|terrace)'
        ]
        
        # Also look for single mentions of rooms
        single_room_pattern = r'\b(bedroom|kitchen|bathroom|washroom|living room|tv lounge|dining room|garage|car parking|lobby|hallway|entrance|main entrance|terrace)\b'
        
        # Extract rooms with counts
        for pattern in room_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                count = match[0]
                room_type = match[1]
                
                # Convert text numbers to integers
                if count in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']:
                    count_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 
                                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}
                    count = count_map[count]
                else:
                    count = int(count)
                
                # Add the specified number of rooms
                for i in range(count):
                    rooms.append(room_type)
        
        # Extract single room mentions not already counted
        single_matches = re.findall(single_room_pattern, text.lower())
        for room_type in single_matches:
            if room_type not in [r for r in rooms]:
                rooms.append(room_type)
        
        # Check for attached washrooms with bedrooms
        if "bedroom" in text.lower() and "attach" in text.lower() and "washroom" in text.lower():
            # For each bedroom, add an attached washroom if not already accounted for
            bedroom_count = rooms.count("bedroom")
            washroom_count = rooms.count("washroom") + rooms.count("bathroom")
            
            if washroom_count < bedroom_count:
                # Add attached washrooms
                for i in range(bedroom_count - washroom_count):
                    rooms.append("washroom")
        
        # Ensure at least some basic rooms if none detected
        if not rooms:
            rooms = ["bedroom", "kitchen", "living room"]
        
        # Convert to list of dict with types
        return [{"type": room_type} for room_type in rooms]
    
    def _extract_styles(self, text):
        """Extract architectural style information from text."""
        styles = []
        
        # Common architectural styles
        style_patterns = [
            "modern", "contemporary", "traditional", "minimalist", "classic",
            "colonial", "victorian", "farmhouse", "rustic", "industrial",
            "mediterranean", "scandinavian", "mid-century", "gothic", "art deco"
        ]
        
        # Look for style mentions in the text
        for style in style_patterns:
            if style in text.lower():
                styles.append(style)
        
        # Default to modern if no style detected
        if not styles:
            styles = ["modern"]
            
        return styles
    
    def _extract_plot_size(self, text):
        """Extract plot size information in Marla/Kanal units."""
        plot_size = {}
        
        # Look for Marla mentions
        marla_pattern = r'(\d+(?:\.\d+)?)\s*(?:marla|Marla)'
        marla_match = re.search(marla_pattern, text)
        
        if marla_match:
            marla = float(marla_match.group(1))
            plot_size["marla"] = marla
            plot_size["kanal"] = marla / 20.0  # 1 Kanal = 20 Marla
            
            # Calculate approximate dimensions (assuming 1 Marla = 25.2929 sqm)
            area_sqm = marla * 25.2929
            # Create a bit more rectangular shape rather than square
            width = np.sqrt(area_sqm * 0.8)  # Slightly narrower
            length = area_sqm / width  # Slightly longer
            
            plot_size["width_meters"] = width
            plot_size["length_meters"] = length
        
        # Look for Kanal mentions
        kanal_pattern = r'(\d+(?:\.\d+)?)\s*(?:kanal|Kanal)'
        kanal_match = re.search(kanal_pattern, text)
        
        if kanal_match:
            kanal = float(kanal_match.group(1))
            plot_size["kanal"] = kanal
            plot_size["marla"] = kanal * 20.0  # 1 Kanal = 20 Marla
            
            # Calculate approximate dimensions
            area_sqm = kanal * 20 * 25.2929
            # Create a bit more rectangular shape rather than square
            width = np.sqrt(area_sqm * 0.8)  # Slightly narrower
            length = area_sqm / width  # Slightly longer
            
            plot_size["width_meters"] = width
            plot_size["length_meters"] = length
        
        return plot_size
    
    def _extract_stories(self, text):
        """Extract number of stories/floors from text."""
        # Default to 1 story
        stories = 1
        
        # Look for mentions of stories/floors
        story_patterns = [
            r'(\d+)\s*(?:stor(?:ies|ys|y)|floors?)',
            r'(one|two|three|four|five)\s*(?:stor(?:ies|ys|y)|floors?)'
        ]
        
        for pattern in story_patterns:
            match = re.search(pattern, text.lower())
            if match:
                count = match.group(1)
                
                # Convert text numbers to integers
                if count in ['one', 'two', 'three', 'four', 'five']:
                    count_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}
                    stories = count_map[count]
                else:
                    stories = int(count)
                    
                # Cap at reasonable number
                stories = min(stories, 5)
                break
        
        return stories
    
    def _generate_layout(self, features):
        """Generate a 2D layout using the improved layout generator."""
        rooms = features["rooms"]
        styles = features["styles"]
        plot_size = features["plot_size"]
        stories = features["stories"]
        
        # Initialize the improved layout generator
        layout_generator = ImprovedLayoutGenerator()
        
        # Generate the layout
        layout = layout_generator.generate_layout(rooms, plot_size, stories)
        
        # Add additional metadata
        layout["object_type"] = "house"
        layout["styles"] = styles
        layout["plot_size"] = plot_size
        layout["stories"] = stories
        
        print(f"✓ Created layout with {len(layout['rooms'])} rooms")
        print(f"✓ Generated {len(layout['connections'])} connections between rooms")
        print(f"✓ Added {len(layout['doors'])} door openings")
        
        return layout
    
    def _visualize_layout(self, layout):
        """Create a professional architectural floor plan visualization."""
        renderer = FloorPlanRenderer()
        return renderer.render(layout, output_path="output/floor_plan.png")