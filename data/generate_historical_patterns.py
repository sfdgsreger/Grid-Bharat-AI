#!/usr/bin/env python3
"""
Historical Consumption Pattern Generator for Bharat-Grid AI RAG System

Generates comprehensive historical consumption patterns with:
- Seasonal variations (monsoon, summer, winter)
- Festival and holiday patterns
- Emergency scenarios and grid failures
- Different facility types with realistic load profiles
- Geographic and demographic variations
- Rich contextual descriptions for RAG training
"""

import csv
import random
import time
import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enu