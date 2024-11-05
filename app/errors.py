#!/usr/bin/env python3


from typing import List, Dict, Any, Optional


class ValidationError(Exception):
    def __init__(self, errors: List[str], details: Optional[Dict[str, Any]] = None):
        self.errors = errors
        self.details = details or {}
        super().__init__("; ".join(errors))
