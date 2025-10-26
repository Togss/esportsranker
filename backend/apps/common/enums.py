from django.db import models

class Region(models.TextChoices):
    NA = 'NA', 'North America'
    ID = 'ID', 'Indonesia'
    MY = 'MY', 'Malaysia'
    PH = 'PH', 'Philippines'
    SG = 'SG', 'Singapore'
    BR = 'BR', 'Brazil'
    VN = 'VN', 'Vietnam'
    MM = 'MM', 'Myanmar'
    TH = 'TH', 'Thailand'
    IN = 'IN', 'India'
    TR = 'TR', 'Turkey'
    EU = 'EU', 'Europe'
    JP = 'JP', 'Japan'
    CN = 'CN', 'China'
    MENA = 'MENA', 'Middle East and North Africa'
    KR = 'KR', 'Korea'
    TW = 'TW', 'Taiwan'
    HK = 'HK', 'Hong Kong'
    LATAM = 'LATAM', 'Latin America'
    INTL = 'INTL', 'International'

class PlayerRole(models.TextChoices):
    GOLD = 'GOLD', 'Gold Lane'
    MID = 'MID', 'Mid Lane'
    JUNGLE = 'JUNGLE', 'Jungle'
    EXP = 'EXP', 'Exp Lane'
    ROAM = 'ROAM', 'Roam'

class StaffRole(models.TextChoices):
    HEAD_COACH = 'HEAD_COACH', 'Head Coach'
    ASST_COACH = 'ASST_COACH', 'Assistant Coach'
    ANALYST = 'ANALYST', 'Analyst'
    MANAGER = 'MANAGER', 'Team Manager'

class HeroClass(models.TextChoices):
    TANK = 'TANK', 'Tank'
    FIGHTER = 'FIGHTER', 'Fighter'
    ASSASSIN = 'ASSASSIN', 'Assassin'
    MAGE = 'MAGE', 'Mage'
    MARKSMAN = 'MARKSMAN', 'Marksman'
    SUPPORT = 'SUPPORT', 'Support'

# ----------------------------------------------------------------------------
# Competition Model Enums
# ----------------------------------------------------------------------------

class TournamentTier(models.TextChoices):
    SS = 'SS', 'SS-tier'
    S = 'S', 'S-tier'
    A = 'A', 'A-tier'
    B = 'B', 'B-tier'
    C = 'C', 'C-tier'
    D = 'D', 'D-tier'

class TournamentStatus(models.TextChoices):
    UPCOMING = 'UPCOMING', 'Upcoming'
    ONGOING = 'ONGOING', 'Ongoing'
    COMPLETED = 'COMPLETED', 'Completed'

class StageType(models.TextChoices):
    WILD_CARD = 'WILD CARD', 'Wild card Stage'
    REGULAR_SEASON = 'REGULAR SEASON', 'Regular Season'
    KNOCKOUT = 'KNOCKOUT', 'Knockout Stage'
    GROUP = 'GROUP', 'Group Stage'
    PLAYOFFS = 'PLAYOFFS', 'Playoff Stage'
    FINALS = 'FINALS', 'Finals'

class StageStatus(models.TextChoices):
    UPCOMING = 'UPCOMING', 'Upcoming'
    ONGOING = 'ONGOING', 'Ongoing'
    COMPLETED = 'COMPLETED', 'Completed'

class StageTier(models.TextChoices):
    T1 = 'T1', 'T1-tier'
    T2 = 'T2', 'T2-tier'
    T3 = 'T3', 'T3-tier'
    T4 = 'T4', 'T4-tier'
    T5 = 'T5', 'T5-tier'
    T6 = 'T6', 'T6-tier'

class TournamentTeamKind(models.TextChoices):
    INVITED = 'INVITED', 'Invited'
    QUALIFIED = 'QUALIFIED', 'Qualified'
    WILDCARD = 'WILDCARD', 'Wild Card'
    FRANCHISE = 'FRANCHISE', 'Franchise'

class GameResultType(models.TextChoices):
    NORMAL = 'NORMAL', 'Normal Win'
    FORFEIT_TEAM1 = 'FORFEIT_TEAM1', 'Forfeit Team 1'
    FORFEIT_TEAM2 = 'FORFEIT_TEAM2', 'Forfeit Team 2'
    DRAW = 'DRAW', 'Draw'

class Side(models.TextChoices):
    BLUE = 'BLUE', 'Blue Side'
    RED = 'RED', 'Red Side'

class SeriesLength(models.IntegerChoices):
    BO1 = 1, 'Best of 1'
    BO3 = 3, 'Best of 3'
    BO5 = 5, 'Best of 5'
    BO7 = 7, 'Best of 7'