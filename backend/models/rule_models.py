from pydantic import BaseModel
from typing import List, Optional, Literal
from enum import Enum


class RuleType(str, Enum):
    add_prefix = "add_prefix"
    add_suffix = "add_suffix"
    insert_text = "insert_text"
    find_replace = "find_replace"
    sequence = "sequence"
    template = "template"
    case_transform = "case_transform"


class RenameRule(BaseModel):
    rule_type: RuleType
    enabled: bool = True

    # add_prefix / add_suffix
    prefix: Optional[str] = None
    suffix: Optional[str] = None

    # insert_text
    position: Optional[int] = None
    text: Optional[str] = None

    # find_replace
    search: Optional[str] = None
    replace: Optional[str] = None
    is_regex: bool = False

    # sequence
    start: int = 1
    step: int = 1
    padding: int = 2
    sequence_position: Literal["prefix", "suffix"] = "prefix"

    # template
    template: Optional[str] = None

    # case_transform
    case_type: Optional[Literal["lower", "upper", "title", "capitalize"]] = None


class RenamePreviewRequest(BaseModel):
    files: List[str]
    rules: List[RenameRule]
    regex_pattern: Optional[str] = None
