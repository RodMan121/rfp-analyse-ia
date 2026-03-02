from pydantic import BaseModel, Field
from typing import List, Optional

class FragmentMetadata(BaseModel):
    source_file: str
    section: str
    page: int
    raw_text: str
    char_count: int

class FragmentClassification(BaseModel):
    domaine: str
    type_babok: str
    tags: List[str] = Field(default_factory=list)
    priorite_esn: str
    score_complexite: int

class AtomicFragment(BaseModel):
    metadata: FragmentMetadata
    classification: FragmentClassification
