"""
Standard Scrum Engineering Teams and OWASP Skill Profiles.
Capacity: 30 Story Points per team.
"""
from typing import List
from models import Team


def get_standard_teams(n_teams: int) -> List[Team]:
    """Tao danh sach n_teams theo chuan Scrum (30 SP / team) voi ky nang OWASP da dang."""
    all_profiles = [
        {"team_id": "t1", "name": "Team 1 (Core & Backend)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.9, "SKILL_A02": 0.7, "SKILL_A03": 0.85, "SKILL_A04": 0.6,
            "SKILL_A05": 0.65, "SKILL_A06": 0.55, "SKILL_A07": 0.9, "SKILL_A08": 0.6,
            "SKILL_A09": 0.7, "SKILL_A10": 0.65
        }},
        {"team_id": "t2", "name": "Team 2 (Business & Payment)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.6, "SKILL_A02": 0.95, "SKILL_A03": 0.65, "SKILL_A04": 0.85,
            "SKILL_A05": 0.9, "SKILL_A06": 0.6, "SKILL_A07": 0.5, "SKILL_A08": 0.7,
            "SKILL_A09": 0.6, "SKILL_A10": 0.75
        }},
        {"team_id": "t3", "name": "Team 3 (Infra & Gateway)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.55, "SKILL_A02": 0.6, "SKILL_A03": 0.7, "SKILL_A04": 0.65,
            "SKILL_A05": 0.95, "SKILL_A06": 0.9, "SKILL_A07": 0.6, "SKILL_A08": 0.65,
            "SKILL_A09": 0.9, "SKILL_A10": 0.7
        }},
        {"team_id": "t4", "name": "Team 4 (Security & Ops)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.85, "SKILL_A02": 0.8, "SKILL_A03": 0.6, "SKILL_A04": 0.7,
            "SKILL_A05": 0.8, "SKILL_A06": 0.75, "SKILL_A07": 0.65, "SKILL_A08": 0.95,
            "SKILL_A09": 0.85, "SKILL_A10": 0.95
        }},
        {"team_id": "t5", "name": "Team 5 (Data & Analytics)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.75, "SKILL_A02": 0.6, "SKILL_A03": 0.9, "SKILL_A04": 0.8,
            "SKILL_A05": 0.7, "SKILL_A06": 0.65, "SKILL_A07": 0.7, "SKILL_A08": 0.6,
            "SKILL_A09": 0.65, "SKILL_A10": 0.6
        }},
        {"team_id": "t6", "name": "Team 6 (Frontend & API)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.7, "SKILL_A02": 0.85, "SKILL_A03": 0.8, "SKILL_A04": 0.6,
            "SKILL_A05": 0.6, "SKILL_A06": 0.55, "SKILL_A07": 0.8, "SKILL_A08": 0.7,
            "SKILL_A09": 0.6, "SKILL_A10": 0.65
        }},
        {"team_id": "t7", "name": "Team 7 (Platform Eng)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.6, "SKILL_A02": 0.7, "SKILL_A03": 0.65, "SKILL_A04": 0.75,
            "SKILL_A05": 0.9, "SKILL_A06": 0.95, "SKILL_A07": 0.6, "SKILL_A08": 0.85,
            "SKILL_A09": 0.9, "SKILL_A10": 0.8
        }},
        {"team_id": "t8", "name": "Team 8 (Integration)", "capacity_sp": 30, "skills": {
            "SKILL_A01": 0.8, "SKILL_A02": 0.75, "SKILL_A03": 0.7, "SKILL_A04": 0.9,
            "SKILL_A05": 0.75, "SKILL_A06": 0.8, "SKILL_A07": 0.65, "SKILL_A08": 0.7,
            "SKILL_A09": 0.8, "SKILL_A10": 0.75
        }},
    ]
    return [
        Team(team_id=p["team_id"], name=p["name"], capacity_sp=p["capacity_sp"], skills=p["skills"])
        for p in all_profiles[:n_teams]
    ]

