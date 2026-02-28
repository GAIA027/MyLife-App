#Fitness tracker for MyLife app
import re
import hashlib
import string
from wonderwords import random_word
import json
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable
from MyLife_Tracker import *

def MyFitness_dashboard(current_user):
    current_user = require_current_user(current_user)
    if not current_user:
        return False
    