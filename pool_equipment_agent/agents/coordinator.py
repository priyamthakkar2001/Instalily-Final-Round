from typing import Dict, Any, List, Optional
from crewai import Crew, Task, Agent
from pool_equipment_agent.utils.model_context import ModelContext

from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.llm.gpt4o import GPT4O
from pool_equipment_agent.llm.query_classifier import QueryClassifier, QueryIntent
from pool_equipment_agent.llm.prompt_templates import PromptTemplates

from pool_equipment_agent.agents.product_agent import ProductAgent
from pool_equipment_agent.agents.store_agent import StoreAgent
from pool_equipment_agent.agents.pricing_agent import PricingAgent
from pool_equipment_agent.agents.advisor_agent import AdvisorAgent

logger = get_logger()

class CoordinatorAgent:
    """Coordinator agent that orchestrates specialized agents"""
    
    def __init__(self):
        """Initialize the coordinator agent"""
        self.llm = GPT4O()
        self.query_classifier = QueryClassifier()
        
        # Initialize specialized agents
        self.product_agent = ProductAgent()
        self.store_agent = StoreAgent()
        self.pricing_agent = PricingAgent()
        self.advisor_agent = AdvisorAgent()
        
        # Create CrewAI agent
        self.agent = Agent(
            name="Coordinator",
            role="Pool equipment chat agent coordinator",
            goal="Analyze customer queries, determine which specialized agents to invoke, and synthesize their responses",
            backstory=PromptTemplates.coordinator_agent_backstory(),
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
    
    def process_query(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Process a user query by coordinating specialized agents
        
        Args:
            query: User query text
            conversation_history: Optional conversation history for context
            
        Returns:
            Synthesized response from specialized agents
        """
        logger.info(f"Coordinator processing query: {query}")
        
        # Check if the query is within scope
        if not self._is_query_in_scope(query):
            return self._out_of_scope_response()
        
        # Classify the query intent
        intent = self.query_classifier.classify(query, conversation_history)
        logger.info(f"Query classified as: {intent.primary_intent} (confidence: {intent.confidence})")
        
        # Collect responses from relevant agents based on intent
        responses = {}
        entities = intent.entities
        
        # Process with primary intent agent
        primary_response = self._process_with_intent_agent(intent.primary_intent, query, entities)
        responses[intent.primary_intent] = primary_response
        
        # Process with secondary intent agent if applicable
        if intent.secondary_intent and intent.secondary_intent != intent.primary_intent:
            secondary_response = self._process_with_intent_agent(intent.secondary_intent, query, entities)
            responses[intent.secondary_intent] = secondary_response
        
        # Synthesize responses
        return self._synthesize_responses(query, intent, responses)
    
    def _process_with_intent_agent(self, intent: str, query: str, entities: Dict[str, Any]) -> str:
        """Process a query with the appropriate agent based on intent
        
        Args:
            intent: Query intent (product_search, store_location, pricing, technical_advice, general)
            query: User query text
            entities: Extracted entities from the query
            
        Returns:
            Response from the specialized agent
        """
        if intent == "product_search":
            return self.product_agent.process_product_query(query, entities)
        elif intent == "store_location":
            return self.store_agent.process_store_query(query, entities)
        elif intent == "pricing":
            return self.pricing_agent.process_pricing_query(query, entities)
        elif intent == "technical_advice":
            return self.advisor_agent.process_advice_query(query, entities)
        else:  # general
            # For general queries, use the coordinator agent directly
            return self._process_general_query(query)
    
    def _process_general_query(self, query: str) -> str:
        """Process a general query directly with the coordinator agent
        
        Args:
            query: User query text
            
        Returns:
            Response from the coordinator agent
        """
        # Create messages for the model context
        messages = [
            {"role": "system", "content": PromptTemplates.coordinator_agent_prompt().messages[0].content},
            {"role": "user", "content": query}
        ]
        
        # Create model context
        model_context = ModelContext.from_messages(
            messages=messages,
            parameters={"temperature": 0.7}
        )
        
        # Generate response
        try:
            response = self.llm.generate(model_context)
            logger.info("Coordinator generated general response")
            return response
        except Exception as e:
            logger.error(f"Error processing general query: {str(e)}")
            return f"I'm sorry, I encountered an error while processing your request: {str(e)}"
    
    def _synthesize_responses(self, query: str, intent: QueryIntent, responses: Dict[str, str]) -> str:
        """Synthesize responses from multiple agents into a cohesive reply
        
        Args:
            query: Original user query
            intent: Query intent classification
            responses: Responses from specialized agents
            
        Returns:
            Synthesized response
        """
        logger.info("Synthesizing responses from specialized agents")
        
        # If we only have one response, return it directly
        if len(responses) == 1:
            return list(responses.values())[0]
        
        # Create messages for the model context
        system_content = PromptTemplates.coordinator_agent_prompt().messages[0].content
        
        # Create user message with the query and agent responses
        user_content = f"Original query: {query}\n\n"
        for intent_type, response in responses.items():
            user_content += f"{intent_type.replace('_', ' ').title()} Agent Response:\n{response}\n\n"
        
        user_content += "Please synthesize these responses into a cohesive, helpful reply that addresses all aspects of the user's query."
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
        
        # Create model context
        model_context = ModelContext.from_messages(
            messages=messages,
            parameters={"temperature": 0.7}
        )
        
        # Generate synthesized response
        try:
            response = self.llm.generate(model_context)
            logger.info("Coordinator generated synthesized response")
            return response
        except Exception as e:
            logger.error(f"Error synthesizing responses: {str(e)}")
            # Fall back to primary response if synthesis fails
            primary_intent = intent.primary_intent
            if primary_intent in responses:
                return responses[primary_intent]
            return f"I'm sorry, I encountered an error while processing your request: {str(e)}"

    def _is_query_in_scope(self, query: str) -> bool:
        """Check if a query is within the scope of the pool equipment chat agent
        
        Args:
            query: User query text
            
        Returns:
            True if the query is in scope, False otherwise
        """
        # Pool equipment related terms that should always be allowed
        pool_terms = [
            "pool", "pump", "filter", "chlorine", "chemical", "cleaner", "heater", "motor",
            "hayward", "pentair", "jandy", "zodiac", "polaris", "aqua", "intex", "bestway",
            "salt", "ph", "alkalinity", "acid", "shock", "algae", "valve", "skimmer", "drain",
            "plumbing", "pipe", "liner", "cover", "maintenance", "repair", "install", "price", 
            "cost", "store", "location", "warranty", "manual", "part", "replacement", "component",
            "equipment", "accessory", "image", "picture", "photo", "diagram", "schematic"
        ]
        
        # Check for product codes/part numbers (alphanumeric patterns like LZA406103A)
        import re
        product_code_pattern = r'\b[A-Z0-9]{5,}\b'
        if re.search(product_code_pattern, query):
            logger.info(f"Query contains product code, considering in-scope: {query}")
            return True
        
        # If query contains pool-related terms, it's in scope
        if any(term in query.lower() for term in pool_terms):
            return True
        
        # Check for specific patterns that indicate out-of-scope queries
        out_of_scope_patterns = [
            # Political patterns
            r"who is (the )?([a-z]+ )?(president|prime minister|pm|leader|king|queen|ruler|dictator)( of)?\b",
            r"\b(trump|biden|obama|bush|clinton|putin|modi|xi|merkel|macron)\b",
            r"\b(democrat|republican|liberal|conservative|election|vote|ballot|campaign)\b",
            r"\b(war|conflict|treaty|sanction|military|army|weapon|missile|nuclear)\b",
            r"\b(india|china|russia|ukraine|israel|palestine|iran|iraq|north korea|south korea)\b",
            
            # Entertainment patterns
            r"\b(movie|film|actor|actress|director|hollywood|bollywood|netflix|amazon prime|disney\+)\b",
            r"\b(tv show|series|episode|season|channel|streaming|youtube|tiktok|instagram)\b",
            r"\b(music|song|album|artist|band|concert|festival|spotify|apple music)\b",
            r"\b(game|gaming|playstation|xbox|nintendo|pc game|mobile game|fortnite|minecraft)\b",
            
            # Technology patterns
            r"\b(iphone|android|samsung|apple|google|microsoft|facebook|twitter|snapchat)\b",
            r"\b(computer|laptop|tablet|smartphone|gadget|tech|technology|software|hardware)\b",
            r"\b(ai|artificial intelligence|machine learning|deep learning|algorithm|neural network)\b",
            r"\b(internet|wifi|broadband|5g|4g|network|router|modem|fiber|ethernet)\b",
            
            # Sports patterns
            r"\b(football|soccer|basketball|baseball|cricket|tennis|golf|hockey|rugby|volleyball)\b",
            r"\b(nfl|nba|mlb|nhl|premier league|la liga|serie a|bundesliga|champions league)\b",
            r"\b(team|player|coach|manager|referee|umpire|stadium|arena|field|court|match|game|tournament)\b",
            r"\b(olympics|world cup|championship|medal|trophy|title|record|score|goal|point|win|lose|draw)\b",
            
            # Finance patterns
            r"\b(stock|market|invest|bitcoin|crypto|blockchain|nft|token|coin|wallet|exchange)\b",
            r"\b(economy|inflation|recession|gdp|unemployment|interest rate|fed|federal reserve)\b",
            r"\b(bank|loan|mortgage|credit|debit|card|payment|transaction|transfer|deposit|withdraw)\b",
            r"\b(tax|income|revenue|profit|loss|dividend|yield|return|asset|liability|equity)\b",
            
            # Education patterns
            r"\b(school|college|university|degree|diploma|certificate|education|academic|student)\b",
            r"\b(course|class|lecture|professor|teacher|instructor|tutor|mentor|curriculum)\b",
            r"\b(homework|assignment|exam|test|quiz|grade|score|gpa|sat|act|gre|gmat|lsat|mcat)\b",
            r"\b(subject|topic|discipline|field|major|minor|study|research|thesis|dissertation)\b",
            
            # Health patterns
            r"\b(doctor|hospital|clinic|medicine|drug|prescription|symptom|disease|condition|illness)\b",
            r"\b(covid|coronavirus|pandemic|vaccine|vaccination|booster|mask|quarantine|isolation)\b",
            r"\b(diet|nutrition|exercise|workout|fitness|gym|weight loss|calorie|protein|vitamin)\b",
            
            # General knowledge patterns
            r"\b(what is the (capital|population|area|currency|language|religion) of)\b",
            r"\b(how (tall|old|big|long|far|deep|high|wide) is)\b",
            r"\b(when (was|did|will))\b",
            r"\b(why (is|are|do|does|did))\b"
        ]
        
        # Check if query matches any out-of-scope pattern
        for pattern in out_of_scope_patterns:
            if re.search(pattern, query.lower()):
                # Only consider it out of scope if it doesn't contain pool terms
                if not any(term in query.lower() for term in pool_terms):
                    logger.info(f"Query matches out-of-scope pattern: {query}")
                    return False
        
        # Check for out-of-scope topics - use whole words to avoid false positives
        out_of_scope_topics = [
            # Politics and countries
            "politics", "news", "government", "policy", "law", "court", "justice",
            "president", "minister", "election", "vote", "campaign", "democracy",
            "country", "nation", "state", "province", "city", "town", "village",
            "india", "china", "usa", "america", "russia", "ukraine", "europe", "asia", "africa",
            
            # Entertainment
            "celebrity", "movie", "film", "actor", "actress", "director", "producer",
            "tv", "television", "show", "series", "episode", "season", "channel",
            "music", "song", "album", "artist", "band", "concert", "festival",
            "game", "gaming", "player", "console", "playstation", "xbox", "nintendo",
            
            # Sports
            "sport", "team", "player", "coach", "match", "game", "tournament", "championship",
            "football", "soccer", "basketball", "baseball", "cricket", "tennis", "golf",
            
            # Technology
            "computer", "laptop", "phone", "smartphone", "tablet", "device", "gadget",
            "software", "hardware", "app", "application", "website", "internet", "web",
            "social media", "facebook", "twitter", "instagram", "tiktok", "youtube",
            
            # Finance
            "money", "finance", "bank", "loan", "mortgage", "credit", "debit", "card",
            "stock", "market", "invest", "bitcoin", "crypto", "blockchain", "nft",
            "economy", "inflation", "recession", "gdp", "unemployment",
            
            # Education
            "school", "college", "university", "degree", "diploma", "certificate",
            "course", "class", "lecture", "professor", "teacher", "student", "pupil",
            "homework", "assignment", "exam", "test", "quiz", "grade", "score",
            
            # Health
            "health", "doctor", "hospital", "clinic", "medicine", "drug", "prescription",
            "symptom", "disease", "condition", "illness", "virus", "bacteria", "infection",
            "covid", "coronavirus", "pandemic", "vaccine", "vaccination", "booster",
            "diet", "nutrition", "exercise", "workout", "fitness", "gym"
        ]
        
        # Check if any out-of-scope topic is in the query as a whole word
        for topic in out_of_scope_topics:
            # Use word boundary to match whole words only
            if re.search(r'\b' + re.escape(topic) + r'\b', query.lower()):
                # Only consider it out of scope if it doesn't contain pool terms
                if not any(term in query.lower() for term in pool_terms):
                    logger.info(f"Query contains out-of-scope topic: {query}")
                    return False
            
        # Use the query classifier to check if the query is related to pool equipment
        try:
            intent = self.query_classifier.classify(query, None)
            # If confidence is very low, it might be out of scope
            if intent.confidence < 0.3 and intent.primary_intent == "general":
                logger.info(f"Query classified with low confidence: {query}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error classifying query scope: {str(e)}")
            # Default to in-scope if we can't classify
            return True

    def _out_of_scope_response(self) -> str:
        """Generate a response for out-of-scope queries
        
        Returns:
            Response indicating the query is out of scope
        """
        responses = [
            "I'm sorry, but I'm a specialized pool equipment assistant and can only answer questions related to pool equipment, products, pricing, store locations, and technical advice for pools. Please ask me something about pool equipment or maintenance.",
            "As a pool equipment specialist, I can only help with questions about pool products, maintenance, store locations, and technical advice. I don't have information on other topics. How can I assist you with your pool needs?",
            "I'm designed specifically to help with pool equipment queries. I can't answer questions outside that scope. Is there something about pool equipment, maintenance, or our stores that I can help you with?"
        ]
        
        import random
        return random.choice(responses)
