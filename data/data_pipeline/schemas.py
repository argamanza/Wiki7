from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class Transfer(BaseModel):
    player_id: str
    season: str
    transfer_date: str
    from_club: str
    to_club: str
    fee: str
    loan: bool

class MarketValue(BaseModel):
    player_id: str
    value_date: str
    value: str
    team: str

class Player(BaseModel):
    id: str  # Transfermarkt ID
    name_english: str
    name_hebrew: Optional[str]
    nationality: Optional[List[str]]
    birth_date: Optional[date]
    birth_place: Optional[str]
    main_position: Optional[str]
    current_squad: bool
    current_jersey_number: Optional[int]
    homegrown: bool
    retired: bool
