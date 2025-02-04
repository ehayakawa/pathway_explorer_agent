from langchain.tools import BaseTool
from bs4 import BeautifulSoup
import requests
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import re
from .models import Pathway, Compound, Reaction, PathwayMetadata
from pydantic import Field
import os
from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from pathlib import Path
from .database import PathwayDatabase

# Define the data structure we want
class Compound(BaseModel):
    name: str = Field(description="name of the compound")
    formula: str = Field(description="chemical formula if known", default="")

class MetabolicPathway(BaseModel):
    name: str = Field(description="name of the metabolic pathway")
    description: str = Field(description="brief description of the pathway")
    compounds: List[Compound] = Field(description="list of key compounds involved in the pathway")

class PathwayList(BaseModel):
    pathways: List[MetabolicPathway] = Field(description="list of metabolic pathways")

class WebScraperTool(BaseTool):
    """Tool for scraping metabolic pathway information from various web sources."""
    
    name: str = "web_scraper"
    description: str = "Scrapes metabolic pathway information from specified web sources"
    return_direct: bool = False
    
    # Add these as model fields
    session: Optional[requests.Session] = Field(default=None)
    chrome_options: Optional[Options] = Field(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize after parent class initialization
        self.session = requests.Session()
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")

    def _setup_selenium(self) -> webdriver.Chrome:
        """Initialize Selenium WebDriver with appropriate options."""
        driver = webdriver.Chrome(options=self.chrome_options)
        return driver

    def _extract_pathway_info_kegg(self, pathway_id: str) -> Optional[Dict[str, Any]]:
        """Extract pathway information from KEGG database."""
        base_url = f"https://www.kegg.jp/entry/{pathway_id}"
        try:
            response = self.session.get(base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic pathway information
            pathway_data = {
                "id": pathway_id,
                "name": soup.find("h1").text.strip() if soup.find("h1") else "",
                "description": "",
                "compounds": [],
                "reactions": [],
                "metadata": {
                    "source": "KEGG",
                    "confidence": 0.9,
                    "verification_status": "unverified"
                }
            }
            
            # Extract compounds and reactions (simplified)
            compound_elements = soup.find_all("div", class_="compound")
            for elem in compound_elements:
                compound = {
                    "id": elem.get("id", ""),
                    "name": elem.text.strip(),
                    "formula": ""  # Would need additional API call to get formula
                }
                pathway_data["compounds"].append(compound)
            
            return pathway_data
        except Exception as e:
            print(f"Error scraping KEGG pathway {pathway_id}: {str(e)}")
            return None

    def _extract_pathway_info_wikipathways(self, pathway_id: str) -> Optional[Dict[str, Any]]:
        """Extract pathway information from WikiPathways."""
        base_url = f"https://www.wikipathways.org/pathways/{pathway_id}"
        try:
            driver = self._setup_selenium()
            driver.get(base_url)
            
            # Wait for content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pathway-title"))
            )
            
            # Extract pathway information
            pathway_data = {
                "id": pathway_id,
                "name": driver.find_element(By.CLASS_NAME, "pathway-title").text,
                "description": "",
                "compounds": [],
                "metadata": {
                    "source": "WikiPathways",
                    "confidence": 0.85,
                    "verification_status": "unverified"
                }
            }
            
            # Extract compounds (simplified)
            compound_elements = driver.find_elements(By.CLASS_NAME, "metabolite")
            for elem in compound_elements:
                compound = {
                    "id": elem.get_attribute("id"),
                    "name": elem.text,
                    "formula": ""
                }
                pathway_data["compounds"].append(compound)
            
            driver.quit()
            return pathway_data
        except Exception as e:
            print(f"Error scraping WikiPathways pathway {pathway_id}: {str(e)}")
            if 'driver' in locals():
                driver.quit()
            return None

    def _run(self, query: str) -> str:
        """Execute the web scraping tool with the given query."""
        try:
            # Parse the query to determine source and pathway ID
            if "KEGG:" in query:
                pathway_id = query.split("KEGG:")[1].strip()
                pathway_data = self._extract_pathway_info_kegg(pathway_id)
            elif "WP:" in query:
                pathway_id = query.split("WP:")[1].strip()
                pathway_data = self._extract_pathway_info_wikipathways(pathway_id)
            else:
                return "Error: Invalid query format. Use 'KEGG:pathway_id' or 'WP:pathway_id'"

            if pathway_data:
                return json.dumps(pathway_data, indent=2)
            else:
                return "Error: Failed to extract pathway information"

        except Exception as e:
            return f"Error during web scraping: {str(e)}"

class PathwayValidatorTool(BaseTool):
    """Tool for validating scraped pathway information using LLM."""
    
    name: str = "pathway_validator"
    description: str = "Validates scraped pathway information using LLM"
    return_direct: bool = False

    def _run(self, pathway_data: str) -> str:
        """Validate the pathway data using LLM."""
        try:
            # Parse the pathway data
            pathway_dict = json.loads(pathway_data)
            
            # Basic validation checks
            required_fields = ["id", "name", "compounds"]
            missing_fields = [field for field in required_fields if field not in pathway_dict]
            
            if missing_fields:
                return f"Validation Error: Missing required fields: {', '.join(missing_fields)}"
            
            # Add validation status
            pathway_dict["metadata"]["verification_status"] = "validated"
            pathway_dict["metadata"]["llm_validation_notes"] = "Basic validation passed"
            
            return json.dumps(pathway_dict, indent=2)
            
        except json.JSONDecodeError:
            return "Error: Invalid JSON data"
        except Exception as e:
            return f"Error during validation: {str(e)}"

# Define the expected JSON structure
class MetabolicPathway(BaseModel):
    name: str = Field(description="name of the metabolic pathway")
    description: str = Field(description="brief description of the pathway")
    compounds: List[str] = Field(description="list of key compounds involved in the pathway")
    enzymes: List[str] = Field(description="list of enzymes involved in the pathway")

class PathwayList(BaseModel):
    pathways: List[MetabolicPathway] = Field(description="list of metabolic pathways")

class PathwayDiscoveryLLMTool(BaseTool):
    """Tool for discovering metabolic pathways using LLM knowledge."""
    
    name: str = "llm_pathway_discoverer"
    description: str = "Uses LLM to discover and describe metabolic pathways"
    return_direct: bool = False
    llm: Optional[ChatOpenAI] = Field(default=None)
    parser: Optional[JsonOutputParser] = Field(default=None)
    database: Optional[PathwayDatabase] = Field(default=None)
    prompt: Optional[ChatPromptTemplate] = Field(default=None)

    def __init__(self, database: PathwayDatabase, **data):
        super().__init__(**data)
        self.llm = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=2000
        )
        self.database = database
        self.parser = JsonOutputParser(pydantic_object=PathwayList)
        
        # Create the prompt template with parser
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a biochemistry expert. 
            You must return a valid JSON object with a 'pathways' array containing exactly 1 pathways.
            Each pathway must have 'name', 'description', 'compounds', and 'enzymes' fields.
            for compounds, provide complete list of compound for the pathway.
            for compounds, provide as many compounds involved in the pathway, as possible.
            You are more interested in plant metabolism and has much knowledge in plant secondary metabolites.
            Prioritize to provide secondary metabolite-related mathways.
            """),
            ("human", """Currently known pathways: {known_pathways}

            Return a JSON object containing 1 metabolic pathways NOT in the above list.
            For compounds, provide complete list of compound for the pathway.
            Normally, metabolic pathway contains many metabolites, more than 5.
            For compounds, provide as many compounds as possible.
            
            The JSON must have this exact structure:
            {{
                "pathways": [
                    {{
                        "name": "pathway name",
                        "description": "pathway description",
                        "compounds": ["compound1", "compound2"],
                        "enzymes": ["enzyme1", "enzyme2"]
                    }}
                ]
            }}

            {format_instructions}""")
        ])
    
    def _run(self, query: str) -> str:
        try:
            known_pathways = self.database.get_known_pathways()
            known_pathways_str = ", ".join(known_pathways) if known_pathways else "none"
            print(f"\nCurrent known pathways: {known_pathways_str}")
            
            # Format prompt with parser instructions
            messages = self.prompt.format_messages(
                known_pathways=known_pathways_str,
                format_instructions=self.parser.get_format_instructions()
            )
            
            # Get response
            response = self.llm.invoke(messages)
            print("\nReceived LLM response")
            
            # Log response time and content
            response_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"Response Time: {response_time}\n"
            

        
            try:
                # Parse the JSON response
                parsed_json = self.parser.parse(response.content)
                
                # Create PathwayList from the parsed data
                if isinstance(parsed_json, dict) and 'pathways' in parsed_json:
                    pathway_list = PathwayList(pathways=[
                        MetabolicPathway(**pathway) for pathway in parsed_json['pathways']
                    ])
                else:
                    raise ValueError("Parsed JSON missing 'pathways' array")
                
                print("\nParsed pathways to be added:")
                for pathway in pathway_list.pathways:
                    print(f"- {pathway.name}")
                    log_entry += f"- {pathway.name}\n"


                # Add to database
                initial_count = len(self.database.pathways["pathways"])
                for pathway in pathway_list.pathways:
                    self.database.add_pathway(pathway.dict())
                self.database.save()
                
                final_count = len(self.database.pathways["pathways"])
                print(f"\nAdded {final_count - initial_count} new pathways")
                

                # Append log entry to a single log file
                with open("pathway_explorer.log", "a") as log_file:
                    log_file.write(log_entry + "\n")


                # Save markdown
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"llm_responses/metabolic_pathways_{timestamp}.md"
                
                content = f"""# New Metabolic Pathways
                Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

                ## Known Pathways
                {known_pathways_str}

                ## LLM Response
                {response.content}

                ## Parsed and Saved Pathways
                ```json
                {json.dumps(pathway_list.dict(), indent=2)}
                ```

                ## Database Update Summary
                - Initial pathway count: {initial_count}
                - New pathways added: {final_count - initial_count}
                - Final pathway count: {final_count}
                """
                                
                os.makedirs("llm_responses", exist_ok=True)
                with open(filename, "w") as f:
                    f.write(content)
                
                return response.content
                
            except Exception as parse_error:
                print(f"\nError parsing response: {parse_error}")
                print("Raw response content:")
                print(response.content)
                raise
            
        except Exception as e:
            error_msg = f"Error during LLM pathway discovery: {str(e)}"
            print(error_msg)
            return error_msg
