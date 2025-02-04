"""
This script demonstrates the LLM-based metabolic pathway discovery functionality.

How it works:
1. Database Initialization:
   - Loads existing pathways from data/metabolic_pathways.json
   - If no database exists, creates a new empty one

2. LLM Pathway Discovery:
   - Uses PathwayExplorerAgent with OpenAI's GPT model
   - Prompts LLM to generate new metabolic pathway information
   - LLM is instructed to focus on plant metabolism and secondary metabolites

3. Output Generation:
   - Creates timestamped files in llm_responses/ directory
     Format: metabolic_pathways_YYYYMMDD_HHMMSS.md
   - Each response file contains:
     * List of currently known pathways
     * New pathway suggestions from LLM
     * Database update summary

4. Database Update:
   - New pathways are automatically added to data/metabolic_pathways.json
   - Maintains a growing database of metabolic pathways

Usage:
    python test_llm_discovery.py

Requirements:
    - OpenAI API key in .env file
    - Existing data/metabolic_pathways.json (will be created if not exists)
"""

from pathway_explorer import PathwayExplorerAgent
from pathway_explorer.database import PathwayDatabase
from dotenv import load_dotenv

def test_llm_pathways():
    # Load environment variables
    load_dotenv()
    
    # Initialize database
    db = PathwayDatabase()
    print("\nCurrent pathways in database:")
    for pathway in db.pathways["pathways"]:
        print(f"- {pathway['name']}")
    
    print("\nInitializing PathwayExplorerAgent...")
    agent = PathwayExplorerAgent(database=db)
    
    try:
        print("\n=== Requesting New Metabolic Pathways from LLM ===")
        response = agent.discoverer._run("List metabolic pathways")
        
        print("\nCheck the 'llm_responses' directory for the full response")
        print("\nUpdated pathways in database:")
        for pathway in db.pathways["pathways"]:
            print(f"- {pathway['name']}")
        
        # Save final results
        agent.save_pathways("discovered_pathways.json")
        print("\nResults saved to discovered_pathways.json")
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")

if __name__ == "__main__":
    test_llm_pathways()