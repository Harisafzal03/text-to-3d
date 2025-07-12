import torch
from transformers import AutoTokenizer, AutoModel
import nltk
import re
import os
import json

class TextUnderstanding:
    def __init__(self, model_name="bert-base-uncased"):
        """Initialize the text understanding module with a pre-trained language model."""
        # Download NLTK resources if not already available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger', quiet=True)
        
        # Initialize tokenizer and model
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
        except Exception as e:
            print(f"Warning: Could not load {model_name}. Using rule-based fallback. Error: {e}")
            self.tokenizer = None
            self.model = None
        
        # Load object templates
        self.object_templates = self._load_object_templates()
    
    def _load_object_templates(self):
        """Load object templates from JSON file or create default ones."""
        # Define a set of basic object types we support
        templates = {
            "house": {"type": "building", "components": ["rooms"]},
            "car": {"type": "vehicle", "components": ["body", "wheels", "windows"]},
            "apple": {"type": "fruit", "components": ["body", "stem"]},
            "chair": {"type": "furniture", "components": ["seat", "back", "legs"]},
            "table": {"type": "furniture", "components": ["top", "legs"]},
        }
        
        # In a production system, we'd load more complex templates from a file
        return templates
    
    def extract_features(self, text):
        """Extract features from the input text description."""
        # First determine what kind of object we're creating
        object_type = self._determine_object_type(text)
        
        # Extract features based on object type
        if object_type == "house":
            features = self._extract_house_features(text)
        elif object_type == "car":
            features = self._extract_car_features(text)
        elif object_type == "furniture":
            features = self._extract_furniture_features(text)
        else:
            # Generic object
            features = self._extract_generic_features(text)
        
        # Add common attributes
        features.update({
            "object_type": object_type,
            "colors": self._extract_colors(text),
            "materials": self._extract_materials(text),
            "dimensions": self._extract_dimensions(text),
            "styles": self._extract_styles(text),
            "original_text": text
        })
        
        return features
    
    def _determine_object_type(self, text):
        """Determine what kind of object we're creating from text description."""
        text = text.lower()
        
        # Check for housing/building related terms
        house_terms = ["house", "home", "apartment", "room", "bedroom", "kitchen",
                      "bathroom", "living room", "building", "office"]
        
        # Check for vehicle related terms
        car_terms = ["car", "vehicle", "bmw", "mercedes", "toyota", "honda", 
                    "ford", "truck", "suv", "van", "automobile"]
        
        # Check for furniture related terms
        furniture_terms = ["chair", "table", "desk", "sofa", "couch", "bed", 
                          "dresser", "cabinet", "shelf", "bookcase"]
        
        # Count term occurrences
        house_count = sum(1 for term in house_terms if term in text)
        car_count = sum(1 for term in car_terms if term in text)
        furniture_count = sum(1 for term in furniture_terms if term in text)
        
        # Determine most likely object type
        if house_count > car_count and house_count > furniture_count:
            return "house"
        elif car_count > house_count and car_count > furniture_count:
            return "car"
        elif furniture_count > house_count and furniture_count > car_count:
            return "furniture"
        else:
            # Default to generic object or use other heuristics
            if "apple" in text or "fruit" in text:
                return "fruit"
            return "generic"
    
    def _extract_house_features(self, text):
        """Extract features for a house model."""
        return {
            "rooms": self._extract_rooms(text),
            "relationships": self._extract_relationships(text),
        }
    
    def _extract_car_features(self, text):
        """Extract features for a car model."""
        features = {
            "car_type": self._extract_car_type(text),
            "car_brand": self._extract_car_brand(text),
            "car_parts": self._extract_car_parts(text)
        }
        return features
    
    def _extract_furniture_features(self, text):
        """Extract features for furniture."""
        features = {
            "furniture_type": self._extract_furniture_type(text),
            "furniture_parts": self._extract_furniture_parts(text)
        }
        return features
    
    def _extract_generic_features(self, text):
        """Extract features for generic objects."""
        return {
            "object_name": self._extract_object_name(text)
        }
    
    def _extract_rooms(self, text):
        """Extract room types from text description."""
        text = text.lower()
        room_types = [
            "kitchen", "bedroom", "bathroom", "living room", "dining room", 
            "office", "hallway", "corridor", "entrance", "lobby", "garage",
            "basement", "attic", "studio", "balcony", "terrace", "patio",
            "tv lounge", "tv room", "play room", "playing room", "game room"
        ]
        
        # Special case mappings (variants to standard names)
        room_mapping = {
            "tv room": "tv lounge",
            "play room": "playing room",
            "game room": "playing room"
        }
        
        found_rooms = []
        counts = {}
        
        # First check for rooms with counts (e.g., "three bedrooms")
        number_words = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
        
        for room in room_types:
            # Check for numeric counts (e.g., "3 bedrooms")
            pattern = r'(\d+)\s+' + room + 's?'
            matches = re.findall(pattern, text)
            if matches:
                count = int(matches[0])
                counts[room] = count
            
            # Check for text number counts (e.g., "three bedrooms")
            for word, num in number_words.items():
                pattern = word + r'\s+' + room + 's?'
                if re.search(pattern, text):
                    counts[room] = num
                    break
            
            # Simple presence check
            if room in text:
                if room not in counts:
                    counts[room] = 1
        
        # Special case for TV lounge
        if "tv" in text and "lounge" not in text and "tv lounge" not in counts and "tv room" not in counts:
            counts["tv lounge"] = 1
        
        # Special case for playing room
        if "play" in text and "room" in text and "playing room" not in counts and "play room" not in counts:
            counts["playing room"] = 1
        
        # Add rooms based on counts
        for room, count in counts.items():
            # Map to standard room name if needed
            standard_room = room_mapping.get(room, room)
            
            for i in range(count):
                identifier = standard_room if count == 1 else f"{standard_room}_{i+1}"
                found_rooms.append({
                    "type": standard_room,
                    "id": identifier
                })
        
        return found_rooms
    
    def _extract_car_type(self, text):
        """Extract car type from text description."""
        text = text.lower()
        car_types = [
            "sedan", "suv", "coupe", "convertible", "hatchback", 
            "wagon", "truck", "van", "sports car", "luxury car"
        ]
        
        for car_type in car_types:
            if car_type in text:
                return car_type
        
        # Default car type
        return "sedan"
    
    def _extract_car_brand(self, text):
        """Extract car brand from text description."""
        text = text.lower()
        car_brands = [
            "bmw", "mercedes", "audi", "toyota", "honda", "ford", "chevrolet",
            "tesla", "volkswagen", "nissan", "hyundai", "kia", "volvo", "porsche"
        ]
        
        for brand in car_brands:
            if brand in text:
                return brand
        
        return None
    
    def _extract_car_parts(self, text):
        """Extract mentioned car parts from text."""
        text = text.lower()
        car_parts = [
            "wheels", "tires", "doors", "roof", "hood", "trunk", "windows",
            "headlights", "taillights", "mirrors", "engine", "seats"
        ]
        
        mentioned_parts = []
        for part in car_parts:
            if part in text:
                mentioned_parts.append(part)
        
        return mentioned_parts
    
    def _extract_furniture_type(self, text):
        """Extract furniture type from text description."""
        text = text.lower()
        furniture_types = [
            "chair", "table", "desk", "sofa", "couch", "bed", "dresser",
            "cabinet", "shelf", "bookcase", "nightstand", "ottoman"
        ]
        
        for furniture_type in furniture_types:
            if furniture_type in text:
                return furniture_type
        
        return "generic furniture"
    
    def _extract_furniture_parts(self, text):
        """Extract mentioned furniture parts from text."""
        text = text.lower()
        furniture_parts = [
            "legs", "back", "seat", "cushions", "drawers", "shelves", "top",
            "frame", "arms", "headboard", "footboard"
        ]
        
        mentioned_parts = []
        for part in furniture_parts:
            if part in text:
                mentioned_parts.append(part)
        
        return mentioned_parts
    
    def _extract_object_name(self, text):
        """Extract main object name from text."""
        # Simple extraction of the first noun
        tokens = nltk.word_tokenize(text.lower())
        tagged = nltk.pos_tag(tokens)
        
        for word, tag in tagged:
            if tag.startswith('NN'):  # Noun
                return word
        
        return "object"
    
    def _extract_dimensions(self, text):
        """Extract dimension information from text."""
        dimensions = {}
        
        # Extract measurements
        meter_pattern = r'(\d+(?:\.\d+)?)\s*(?:m|meter|meters)'
        feet_pattern = r'(\d+(?:\.\d+)?)\s*(?:ft|feet|foot)'
        sqm_pattern = r'(\d+(?:\.\d+)?)\s*(?:sq\.?m|square\s+meter|square\s+meters)'
        sqft_pattern = r'(\d+(?:\.\d+)?)\s*(?:sq\.?ft|square\s+feet|square\s+foot)'
        
        # Find all matches
        meter_matches = re.findall(meter_pattern, text.lower())
        feet_matches = re.findall(feet_pattern, text.lower())
        sqm_matches = re.findall(sqm_pattern, text.lower())
        sqft_matches = re.findall(sqft_pattern, text.lower())
        
        # Store any found measurements
        if meter_matches:
            dimensions["meters"] = [float(m) for m in meter_matches]
        if feet_matches:
            dimensions["feet"] = [float(f) for f in feet_matches]
        if sqm_matches:
            dimensions["square_meters"] = [float(m) for m in sqm_matches]
        if sqft_matches:
            dimensions["square_feet"] = [float(f) for f in sqft_matches]
        
        # Check for size-related adjectives
        size_indicators = {
            "small": "small",
            "large": "large", 
            "big": "large",
            "tiny": "very_small",
            "huge": "very_large",
            "spacious": "large"
        }
        
        for word, size in size_indicators.items():
            if word in text.lower():
                if "adjectives" not in dimensions:
                    dimensions["adjectives"] = []
                dimensions["adjectives"].append(size)
        
        # Flag if we have measurements
        dimensions["has_measurements"] = bool(meter_matches or feet_matches or 
                                           sqm_matches or sqft_matches)
        
        return dimensions
    
    def _extract_relationships(self, text):
        """Extract spatial relationships between rooms/objects."""
        text = text.lower()
        relationships = []
        
        # Define relationship patterns to search for
        relationship_patterns = [
            (r'(\w+)\s+next\s+to\s+(\w+)', "next_to"),
            (r'(\w+)\s+beside\s+(\w+)', "beside"),
            (r'(\w+)\s+above\s+(\w+)', "above"),
            (r'(\w+)\s+below\s+(\w+)', "below"),
            (r'(\w+)\s+connected\s+to\s+(\w+)', "connected_to"),
            (r'(\w+)\s+adjacent\s+to\s+(\w+)', "adjacent_to"),
            (r'(\w+)\s+near\s+(\w+)', "near"),
            (r'(\w+)\s+between\s+(\w+)', "between")
        ]
        
        for pattern, rel_type in relationship_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) >= 2:
                    relationships.append({
                        "type": rel_type,
                        "source": match[0],
                        "target": match[1]
                    })
        
        return relationships
    
    def _extract_styles(self, text):
        """Extract style information from text."""
        text = text.lower()
        style_keywords = [
            "modern", "traditional", "contemporary", "minimalist", "rustic", 
            "industrial", "scandinavian", "mid-century", "vintage", "classical",
            "art deco", "bohemian", "coastal", "farmhouse", "victorian"
        ]
        
        found_styles = []
        
        for style in style_keywords:
            if style in text:
                found_styles.append(style)
        
        return found_styles
    
    def _extract_colors(self, text):
        """Extract color information from text."""
        text = text.lower()
        color_keywords = {
            "red": [1.0, 0.0, 0.0],
            "blue": [0.0, 0.0, 1.0],
            "green": [0.0, 0.8, 0.0],
            "yellow": [1.0, 1.0, 0.0],
            "orange": [1.0, 0.65, 0.0],
            "purple": [0.5, 0.0, 0.5],
            "pink": [1.0, 0.75, 0.8],
            "white": [1.0, 1.0, 1.0],
            "black": [0.0, 0.0, 0.0],
            "gray": [0.5, 0.5, 0.5],
            "grey": [0.5, 0.5, 0.5],
            "brown": [0.65, 0.16, 0.16],
            "beige": [0.96, 0.96, 0.86],
            "teal": [0.0, 0.5, 0.5],
            "turquoise": [0.25, 0.88, 0.82],
            "gold": [1.0, 0.84, 0.0],
            "silver": [0.75, 0.75, 0.75],
            "navy": [0.0, 0.0, 0.5],
            "olive": [0.5, 0.5, 0.0]
        }
        
        found_colors = {}
        
        for color_name, rgb_value in color_keywords.items():
            if color_name in text:
                found_colors[color_name] = rgb_value
        
        return found_colors
    
    def _extract_materials(self, text):
        """Extract material information from text."""
        text = text.lower()
        material_keywords = [
            "wood", "glass", "metal", "concrete", "steel", "iron", "plastic",
            "stone", "marble", "granite", "ceramic", "brick", "leather", 
            "fabric", "wool", "cotton", "aluminum", "copper"
        ]
        
        found_materials = []
        
        for material in material_keywords:
            if material in text:
                found_materials.append(material)
        
        return found_materials