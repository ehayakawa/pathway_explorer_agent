from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Compound(BaseModel):
    """Model representing a chemical compound in a metabolic pathway."""
    id: str = Field(..., description="Unique identifier for the compound")
    name: str = Field(..., description="Common name of the compound")
    formula: Optional[str] = Field(None, description="Chemical formula of the compound")
    
class Reaction(BaseModel):
    """Model representing a reaction in a metabolic pathway."""
    reactants: List[str] = Field(..., description="List of compound IDs acting as reactants")
    products: List[str] = Field(..., description="List of compound IDs acting as products")
    enzymes: Optional[List[str]] = Field(default=[], description="List of enzyme IDs catalyzing the reaction")

class PathwayMetadata(BaseModel):
    """Model representing metadata about the pathway."""
    source: str = Field(..., description="Source of the pathway information")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the information")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    verification_status: str = Field(default="unverified", description="Verification status of the pathway")
    llm_validation_notes: Optional[str] = Field(None, description="Notes from LLM validation")

class Pathway(BaseModel):
    """Model representing a complete metabolic pathway."""
    id: str = Field(..., description="Unique identifier for the pathway")
    name: str = Field(..., description="Name of the pathway")
    description: Optional[str] = Field(None, description="Description of the pathway")
    compounds: List[Compound] = Field(default=[], description="List of compounds involved in the pathway")
    reactions: List[Reaction] = Field(default=[], description="List of reactions in the pathway")
    metadata: PathwayMetadata = Field(..., description="Metadata about the pathway")
    related_pathways: List[str] = Field(default=[], description="List of related pathway IDs")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "GLY001",
                "name": "Glycolysis",
                "description": "Metabolic pathway that breaks down glucose into pyruvate",
                "compounds": [
                    {
                        "id": "C00031",
                        "name": "Glucose",
                        "formula": "C6H12O6"
                    }
                ],
                "reactions": [
                    {
                        "reactants": ["C00031"],
                        "products": ["C00668"],
                        "enzymes": ["EC:2.7.1.1"]
                    }
                ],
                "metadata": {
                    "source": "KEGG",
                    "confidence": 0.95,
                    "verification_status": "verified",
                    "llm_validation_notes": "Validated against multiple sources"
                },
                "related_pathways": ["GLU001", "PYR001"]
            }
        }
