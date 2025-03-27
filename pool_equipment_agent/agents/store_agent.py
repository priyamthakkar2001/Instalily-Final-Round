from typing import Dict, Any, List, Optional
import re
from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.api.store_api import StoreAPI
from pool_equipment_agent.llm.prompt_templates import PromptTemplates
from pool_equipment_agent.agents.base_agent import BaseAgent

logger = get_logger()

class StoreAgent(BaseAgent):
    """Agent for handling store location queries"""
    
    def __init__(self):
        """Initialize the store agent"""
        super().__init__(
            name="Store Specialist",
            role="Pool equipment store location specialist",
            goal="Help customers find nearby store locations and provide relevant store information",
            backstory=PromptTemplates.store_agent_backstory(),
            prompt_template=PromptTemplates.store_agent_prompt()
        )
        self.store_api = StoreAPI()
    
    def search_stores(self, latitude: float, longitude: float, radius: int = 50) -> Dict[str, Any]:
        """Search for stores near a location using coordinates
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in miles (default: 50)
            
        Returns:
            Search results with store information
        """
        return self.store_api.search_stores(latitude, longitude, radius)
    
    def get_store_details(self, store_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific store
        
        Args:
            store_id: Store ID
            
        Returns:
            Detailed store information
        """
        return self.store_api.get_store_details(store_id)
    
    def geocode_location(self, location_query: str) -> Optional[Dict[str, float]]:
        """Convert a location string (city, zip code) to coordinates
        
        Args:
            location_query: Location string (city name, zip code, etc.)
            
        Returns:
            Dictionary with latitude and longitude if successful, None otherwise
        """
        try:
            # Check if the query looks like a US ZIP code (5 digits)
            if location_query.isdigit() and len(location_query) == 5:
                # For demonstration, we'll use a simplified approach to generate coordinates
                # This is NOT for production use - in production, use a proper geocoding API
                
                # Generate a deterministic but somewhat realistic coordinate based on the ZIP
                # This is just for demonstration - DO NOT use in production
                zip_num = int(location_query)
                # Use the first 2 digits to approximate latitude (25-50 degrees covers most of continental US)
                lat_base = 25 + ((zip_num // 1000) % 25)
                # Use the last 3 digits to approximate longitude (-65 to -125 covers continental US)
                lng_base = -65 - ((zip_num % 1000) / 10)
                
                logger.info(f"Using approximate coordinates for ZIP {location_query}: {lat_base}, {lng_base}")
                return {"latitude": lat_base, "longitude": lng_base}
            
            # Use LLM to determine if this is a city or location and extract its likely coordinates
            # This approach leverages the LLM's knowledge of geography without requiring an external API
            # In production, you would use a proper geocoding API instead
            
            prompt = f"""You are a geocoding assistant. Given a location name, provide the approximate latitude and longitude coordinates.
            
            Location: {location_query}
            
            If this is a recognizable city, town, or place in the United States, respond with ONLY a JSON object containing latitude and longitude.
            If you don't recognize this as a valid location, respond with ONLY the text 'UNKNOWN_LOCATION'.
            
            Example response for 'New York': {{"latitude": 40.7128, "longitude": -74.0060}}
            """
            
            from pool_equipment_agent.llm.gpt4o import GPT4O
            llm = GPT4O()
            response = llm.generate(prompt)
            
            # Clean and parse the response
            response = response.strip()
            if response == "UNKNOWN_LOCATION":
                logger.info(f"LLM could not recognize location: {location_query}")
                return None
                
            import json
            try:
                # Try to parse as JSON
                coordinates = json.loads(response)
                if "latitude" in coordinates and "longitude" in coordinates:
                    logger.info(f"LLM geocoded {location_query} to: {coordinates['latitude']}, {coordinates['longitude']}")
                    return coordinates
            except json.JSONDecodeError:
                logger.error(f"Could not parse LLM geocoding response as JSON: {response}")
            
            # If we can't geocode, log it and return None
            logger.info(f"Could not geocode location: {location_query}")
            logger.info(f"In production, this would use a geocoding API like Google Maps or Nominatim")
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding location: {str(e)}")
            return None

    def process_store_query(self, query: str, entities: Dict[str, Any] = None) -> str:
        """Process a store location query
        
        Args:
            query: User query text
            entities: Extracted entities from the query
            
        Returns:
            Formatted response with store information
        """
        logger.info(f"Processing store query: {query}")
        
        # Extract store parameters from entities if available
        store_id = None
        latitude = None
        longitude = None
        radius = 50
        location_query = None
        
        if entities:
            if "store_id" in entities:
                store_id = entities["store_id"]
            if "latitude" in entities and "longitude" in entities:
                latitude = entities["latitude"]
                longitude = entities["longitude"]
            if "location" in entities:
                if isinstance(entities["location"], dict) and "latitude" in entities["location"] and "longitude" in entities["location"]:
                    latitude = entities["location"]["latitude"]
                    longitude = entities["location"]["longitude"]
                elif isinstance(entities["location"], str):
                    location_query = entities["location"]
            if "radius" in entities:
                radius = entities["radius"]
        
        # Check for branch ID in the query
        branch_match = re.search(r'branch\s*(\d+)', query.lower())
        if branch_match:
            store_id = int(branch_match.group(1))
            logger.info(f"Extracted branch ID from query: {store_id}")
        
        # If no location was found in entities, try to extract it from the query
        if not location_query and not latitude and not longitude and not store_id:
            # The query itself might be a location (e.g., "02067" or "Boston")
            location_query = query.strip()
        
        # If we have a specific store ID, get store details
        if store_id:
            try:
                store_details = self.get_store_details(store_id)
                
                # If the store has location data, we can use it to find nearby stores as well
                if "location" in store_details and "latitude" in store_details["location"] and "longitude" in store_details["location"]:
                    store_lat = store_details["location"]["latitude"]
                    store_lng = store_details["location"]["longitude"]
                    
                    # Get nearby stores using the store's coordinates
                    nearby_stores = self.search_stores(store_lat, store_lng, radius)
                    
                    # Add the nearby stores to the context
                    context = {"store_details": store_details, "nearby_stores": nearby_stores}
                else:
                    context = {"store_details": store_details}
                    
                return self.process(f"Provide information about store with ID {store_id}", context)
            except Exception as e:
                logger.error(f"Error getting store details: {str(e)}")
                # Fall back to search if store details fail
        
        # If we have a location query, try to geocode it
        if location_query:
            logger.info(f"Attempting to geocode location: {location_query}")
            coordinates = self.geocode_location(location_query)
            if coordinates:
                latitude = coordinates["latitude"]
                longitude = coordinates["longitude"]
                logger.info(f"Geocoded {location_query} to coordinates: {latitude}, {longitude}")
        
        # If we have coordinates, search for stores
        if latitude is not None and longitude is not None:
            try:
                store_results = self.search_stores(latitude, longitude, radius)
                context = {"store_results": store_results, "query_location": location_query or f"{latitude}, {longitude}"}
                return self.process(f"Provide information about stores near {location_query or f'coordinates {latitude}, {longitude}'}", context)
            except Exception as e:
                logger.error(f"Error searching stores: {str(e)}")
                return f"I'm sorry, I encountered an error while searching for stores: {str(e)}"
        
        # If we don't have coordinates or store ID, return a helpful message
        return "I need your location to find stores near you. Could you please share your city or zip code? 🗺️\n\nYour information will help us provide the best options available!"
