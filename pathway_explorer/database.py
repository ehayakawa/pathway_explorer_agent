from pathlib import Path
import json
from typing import Dict, List, Set
from datetime import datetime

class PathwayDatabase:
    def __init__(self, data_file: str = "data/metabolic_pathways.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(exist_ok=True)
        self.pathways = self._load_data()

    def _load_data(self) -> Dict:
        """Load existing pathway data from file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    print(f"Loading pathways from {self.data_file}")
                    return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading JSON: {e}")
        except Exception as e:
            print(f"Error loading file: {e}")
        
        # Return empty structure if file doesn't exist or has error
        return {
            "pathways": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def save(self):
        """Save current pathways to file"""
        try:
            data = {
                "pathways": self.pathways["pathways"],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved {len(self.pathways['pathways'])} pathways to {self.data_file}")
        except Exception as e:
            print(f"Error saving database: {e}")
            raise
    
    def get_known_pathways(self) -> Set[str]:
        """Get set of known pathway names"""
        return {p["name"].lower() for p in self.pathways["pathways"]}
    
    def add_pathway(self, pathway: Dict):
        """Add a new pathway to the database"""
        if not any(p['name'] == pathway['name'] for p in self.pathways['pathways']):
            print(f"Adding new pathway: {pathway['name']}")
            self.pathways['pathways'].append(pathway)
        else:
            print(f"Pathway already exists: {pathway['name']}")
    
    def get_known_pathways(self) -> List[str]:
        """Get list of known pathway names"""
        return [p['name'] for p in self.pathways['pathways']]