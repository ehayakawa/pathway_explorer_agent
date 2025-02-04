# Metabolic Pathway Explorer Agent

A sophisticated autonomous agent system that discovers, validates, and maintains metabolic pathway information using LLM (Large Language Model) technology and web scraping capabilities.

## Overview

The Metabolic Pathway Explorer Agent combines LangChain's agent framework with LLM capabilities to:
- Discover new metabolic pathways using LLM knowledge
- Validate pathway information through LLM reasoning
- Store and maintain a growing database of pathway information
- Focus on plant metabolism and secondary metabolites

### Key Features

#### 1. LLM-based Pathway Discovery
- Autonomous discovery of metabolic pathways
- Focus on plant secondary metabolism
- Validation of pathway information
- Comprehensive compound and enzyme tracking

#### 2. Data Management
- Structured JSON storage
- Pathway information includes:
  ```json
  {
    "pathway": {
      "id": "string",
      "name": "string",
      "description": "string",
      "compounds": [
        {
          "id": "string",
          "name": "string",
          "formula": "string"
        }
      ],
      "reactions": [
        {
          "reactants": ["compound_ids"],
          "products": ["compound_ids"],
          "enzymes": ["enzyme_ids"]
        }
      ],
      "metadata": {
        "source": "string",
        "confidence": "float",
        "last_updated": "timestamp",
        "verification_status": "string",
        "llm_validation_notes": "string"
      }
    }
  }
  ```

#### 3. Web Scraping Capabilities (Future)
- KEGG database integration
- WikiPathways support
- MetaCyc database access
- Reactome pathway data
- HMDB integration
- Brenda database support

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd pathway-explorer
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY="your-api-key"
```

## Usage

Basic pathway discovery:
```python
from pathway_explorer import PathwayExplorerAgent
from pathway_explorer.database import PathwayDatabase

# Initialize database and agent
db = PathwayDatabase()
agent = PathwayExplorerAgent(database=db)

# Discover new pathways
response = agent.discoverer._run("List metabolic pathways")
```

## Test Code

The repository includes a test script `test_llm_discovery.py` that demonstrates the LLM-based pathway discovery functionality:

```python
# test_llm_discovery.py
from pathway_explorer import PathwayExplorerAgent
from pathway_explorer.database import PathwayDatabase

def test_llm_pathways():
    # Initialize database and agent
    db = PathwayDatabase()
    agent = PathwayExplorerAgent(database=db)
    
    # Use LLM to discover new pathways
    response = agent.discoverer._run("List metabolic pathways")
```

This test script:
1. Loads or creates a pathway database
2. Uses LLM to discover new metabolic pathways
3. Generates output in two locations:
   - `llm_responses/`: Markdown files with timestamped LLM responses
   - `data/`: JSON database of discovered pathways

To run the test:
```bash
python test_llm_discovery.py
```

Requirements:
- OpenAI API key in `.env` file
- Required packages installed from `requirements.txt`

## Project Structure

```
pathway_explorer/
├── agent.py          # Main agent implementation
├── models.py         # Data models
├── tools.py          # LLM and scraping tools
├── database.py       # Database management
├── data/            # Pathway database storage
└── llm_responses/   # LLM output logs
```

## Technical Implementation

### Core Components
1. **LangChain Integration**
   - Zero-shot-react-description agent
   - Custom tools for pathway discovery
   - Memory management for context

2. **LLM Tools**
   - PathwayDiscoveryLLMTool
   - PathwayValidatorTool
   - Content summarization
   - Relationship identification

3. **Data Storage**
   - JSON-based database
   - Structured pathway information
   - Metadata and confidence scoring

### Dependencies
- langchain: Core agent framework
- openai: LLM API integration
- pydantic: Data validation
- python-dotenv: Environment management
- beautifulsoup4: HTML parsing (future)
- selenium: Dynamic web scraping (future)

## Development Phases

### Current: Phase 1 - LLM Discovery
- LLM-based pathway discovery
- Basic data storage
- Pathway validation
- Knowledge base building

### Future: Phase 2 - Web Integration
- Web scraping implementation
- Multiple database sources
- Enhanced validation
- Relationship mapping

### Planned: Phase 3 - Scale
- Performance optimization
- Error handling
- Rate limiting
- Data verification

## Success Metrics
- Number of discovered pathways
- Data accuracy (LLM validated)
- Source diversity
- System performance
- Resource utilization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[License Information]
