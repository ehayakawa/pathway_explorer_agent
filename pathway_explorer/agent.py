from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from typing import List, Optional, Dict, Any
import json
import os
from dotenv import load_dotenv

from .tools import WebScraperTool, PathwayValidatorTool, PathwayDiscoveryLLMTool
from .models import Pathway, PathwayMetadata
from .database import PathwayDatabase

class PathwayExplorerAgent:
    """Agent for exploring and collecting metabolic pathway information."""

    def __init__(self, database: Optional[PathwayDatabase] = None, **kwargs):
        """Initialize the PathwayExplorerAgent.
        
        Args:
            database: PathwayDatabase object. If not provided, will create a new one.
        """
        # Load environment variables
        load_dotenv()
        
        # Set up API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in environment as OPENAI_API_KEY")

        # Initialize tools
        self.scraper = WebScraperTool()
        self.validator = PathwayValidatorTool()
        if database is None:
            database = PathwayDatabase()
        self.database = database
        self.discoverer = PathwayDiscoveryLLMTool(database=self.database)

        # Set up LLM
        self.llm = OpenAI(temperature=0.7, openai_api_key=self.api_key)

        # Set up memory
        self.memory = ConversationBufferMemory(memory_key="chat_history")

        # Initialize tools list
        self.tools = [
            Tool(
                name="web_scraper",
                func=self.scraper._run,
                description="Scrapes metabolic pathway information from specified web sources"
            ),
            Tool(
                name="pathway_validator",
                func=self.validator._run,
                description="Validates scraped pathway information using LLM"
            ),
            Tool(
                name="llm_pathway_discoverer",
                func=self.discoverer._run,
                description="Uses LLM to discover and describe new metabolic pathways"
            )
        ]

        # Initialize agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )

        # Initialize storage for collected pathways
        self.collected_pathways: Dict[str, Pathway] = {}

    def explore_pathway(self, pathway_id: str, source: str = "KEGG") -> Optional[Pathway]:
        """Explore a specific metabolic pathway.
        
        Args:
            pathway_id: ID of the pathway to explore
            source: Source database ("KEGG" or "WP" for WikiPathways)
            
        Returns:
            Pathway object if successful, None otherwise
        """
        try:
            # Format query based on source
            query = f"{source}:{pathway_id}"
            
            # Execute agent to scrape pathway data
            scrape_result = self.agent.run(f"Use web_scraper to get information about {query}")
            
            if "Error" in scrape_result:
                print(f"Error scraping pathway: {scrape_result}")
                return None

            # Validate the scraped data
            validate_result = self.agent.run(f"Use pathway_validator to validate this data: {scrape_result}")
            
            if "Error" in validate_result:
                print(f"Error validating pathway: {validate_result}")
                return None

            # Parse validated data into Pathway object
            pathway_dict = json.loads(validate_result)
            pathway = Pathway(**pathway_dict)
            
            # Store the pathway
            self.collected_pathways[pathway.id] = pathway
            
            return pathway

        except Exception as e:
            print(f"Error exploring pathway: {str(e)}")
            return None

    def explore_related_pathways(self, pathway: Pathway, max_depth: int = 2) -> List[Pathway]:
        """Recursively explore related pathways up to a specified depth.
        
        Args:
            pathway: Initial pathway to explore from
            max_depth: Maximum depth of recursive exploration
            
        Returns:
            List of discovered related pathways
        """
        if max_depth <= 0:
            return []

        related_pathways = []
        for related_id in pathway.related_pathways:
            if related_id not in self.collected_pathways:
                related_pathway = self.explore_pathway(related_id)
                if related_pathway:
                    related_pathways.append(related_pathway)
                    # Recursively explore deeper
                    deeper_pathways = self.explore_related_pathways(
                        related_pathway, 
                        max_depth - 1
                    )
                    related_pathways.extend(deeper_pathways)

        return related_pathways

    def save_pathways(self, filepath: str):
        """Save collected pathways to a JSON file.
        
        Args:
            filepath: Path to save the JSON file
        """
        try:
            # Convert pathways to dictionary
            pathways_dict = {
                id: pathway.dict() 
                for id, pathway in self.collected_pathways.items()
            }
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(pathways_dict, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error saving pathways: {str(e)}")

    def load_pathways(self, filepath: str):
        """Load pathways from a JSON file.
        
        Args:
            filepath: Path to the JSON file
        """
        try:
            with open(filepath, 'r') as f:
                pathways_dict = json.load(f)
            
            # Convert dictionary to Pathway objects
            self.collected_pathways = {
                id: Pathway(**pathway_data)
                for id, pathway_data in pathways_dict.items()
            }
            
        except Exception as e:
            print(f"Error loading pathways: {str(e)}")

    def discover_pathways_with_llm(self) -> List[Pathway]:
        """
        Use LLM to discover and describe metabolic pathways from its knowledge.
        Returns a list of newly discovered pathways.
        """
        try:
            # Query LLM for pathway suggestions
            discovery_result = self.agent.run(
                "Use llm_pathway_discoverer to suggest metabolic pathways that you know about"
            )
            
            if "Error" in discovery_result:
                print(f"Error in LLM pathway discovery: {discovery_result}")
                return []
            
            # Validate the suggested pathway
            validate_result = self.agent.run(
                f"Use pathway_validator to validate this pathway data: {discovery_result}"
            )
            
            if "Error" in validate_result:
                print(f"Error validating LLM pathway: {validate_result}")
                return []
            
            # Parse and store the pathway
            pathway_dict = json.loads(validate_result)
            pathway = Pathway(**pathway_dict)
            
            # Generate unique ID for LLM-discovered pathway
            pathway.id = f"LLM_PATH_{len(self.collected_pathways)}"
            
            # Store the pathway
            self.collected_pathways[pathway.id] = pathway
            
            return [pathway]
            
        except Exception as e:
            print(f"Error during LLM pathway discovery: {str(e)}")
            return []
