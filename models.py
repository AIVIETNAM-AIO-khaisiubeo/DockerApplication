"""Kiểu dữ liệu request của LLM API - khớp docs/CONTRACT.md   [P3]"""
from typing import Annotated

from pydantic import BaseModel, Field


class SoapRequest(BaseModel):
    symptoms: str = Field(min_length=1, max_length=2000)                
    findings: dict[str, Annotated[float, Field(ge=0, le=1)]]            
