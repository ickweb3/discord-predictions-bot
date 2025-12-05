import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class DataManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        self.tournaments_file = os.path.join(data_dir, "tournaments.json")
        self.predictions_file = os.path.join(data_dir, "predictions.json")

        self._init_files()

    def _init_files(self):
        """Initialize data files if they don't exist"""
        if not os.path.exists(self.tournaments_file):
            self._save_json(self.tournaments_file, {"tournaments": {}, "rounds": {}})
        if not os.path.exists(self.predictions_file):
            self._save_json(self.predictions_file, {})

    def _load_json(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_json(self, filepath, data):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # Tournament management
    def create_tournament(self, tournament_id: str, name: str, guild_id: int) -> Dict:
        """Create a new tournament"""
        data = self._load_json(self.tournaments_file)
        data["tournaments"][tournament_id] = {
            "id": tournament_id,
            "name": name,
            "guild_id": guild_id,
            "created_at": datetime.now().isoformat(),
            "rounds": [],
            "active": True
        }
        self._save_json(self.tournaments_file, data)
        return data["tournaments"][tournament_id]

    def create_round(self, round_id: str, name: str, guild_id: int, tournament_id: Optional[str] = None) -> Dict:
        """Create a new round (can be part of tournament or standalone)"""
        data = self._load_json(self.tournaments_file)
        data["rounds"][round_id] = {
            "id": round_id,
            "name": name,
            "guild_id": guild_id,
            "tournament_id": tournament_id,
            "created_at": datetime.now().isoformat(),
            "matches": [],
            "active": True,
            "predictions_open": True
        }

        if tournament_id and tournament_id in data["tournaments"]:
            data["tournaments"][tournament_id]["rounds"].append(round_id)

        self._save_json(self.tournaments_file, data)
        return data["rounds"][round_id]

    def add_match(self, round_id: str, team1: str, team2: str) -> Dict:
        """Add a match to a round"""
        data = self._load_json(self.tournaments_file)

        if round_id not in data["rounds"]:
            raise ValueError(f"Round {round_id} not found")

        match_id = f"{round_id}_match_{len(data['rounds'][round_id]['matches'])}"
        match = {
            "id": match_id,
            "team1": team1,
            "team2": team2,
            "result": None,  # None, "team1", "team2"
            "message_id": None
        }

        data["rounds"][round_id]["matches"].append(match)
        self._save_json(self.tournaments_file, data)
        return match

    def set_match_message_id(self, round_id: str, match_index: int, message_id: int):
        """Set the Discord message ID for a match"""
        data = self._load_json(self.tournaments_file)
        data["rounds"][round_id]["matches"][match_index]["message_id"] = message_id
        self._save_json(self.tournaments_file, data)

    def close_predictions(self, round_id: str):
        """Close predictions for a round"""
        data = self._load_json(self.tournaments_file)
        if round_id in data["rounds"]:
            data["rounds"][round_id]["predictions_open"] = False
            self._save_json(self.tournaments_file, data)

    def set_match_result(self, round_id: str, match_index: int, winner: str):
        """Set the result of a match"""
        data = self._load_json(self.tournaments_file)
        data["rounds"][round_id]["matches"][match_index]["result"] = winner
        self._save_json(self.tournaments_file, data)

    def get_round(self, round_id: str) -> Optional[Dict]:
        """Get round data"""
        data = self._load_json(self.tournaments_file)
        return data["rounds"].get(round_id)

    def get_tournament(self, tournament_id: str) -> Optional[Dict]:
        """Get tournament data"""
        data = self._load_json(self.tournaments_file)
        return data["tournaments"].get(tournament_id)

    def get_all_rounds(self, guild_id: int) -> List[Dict]:
        """Get all rounds for a guild"""
        data = self._load_json(self.tournaments_file)
        return [r for r in data["rounds"].values() if r["guild_id"] == guild_id]

    def get_active_round(self, guild_id: int) -> Optional[Dict]:
        """Get the active round for a guild"""
        rounds = self.get_all_rounds(guild_id)
        active = [r for r in rounds if r["active"] and r["predictions_open"]]
        return active[0] if active else None

    # Prediction management
    def save_prediction(self, round_id: str, match_id: str, user_id: int, prediction: str):
        """Save a user's prediction"""
        data = self._load_json(self.predictions_file)

        if round_id not in data:
            data[round_id] = {}
        if str(user_id) not in data[round_id]:
            data[round_id][str(user_id)] = {}

        data[round_id][str(user_id)][match_id] = prediction
        self._save_json(self.predictions_file, data)

    def get_user_predictions(self, round_id: str, user_id: int) -> Dict:
        """Get all predictions for a user in a round"""
        data = self._load_json(self.predictions_file)
        return data.get(round_id, {}).get(str(user_id), {})

    def get_all_predictions(self, round_id: str) -> Dict:
        """Get all predictions for a round"""
        data = self._load_json(self.predictions_file)
        return data.get(round_id, {})

    def calculate_round_leaderboard(self, round_id: str) -> List[Dict]:
        """Calculate leaderboard for a specific round"""
        round_data = self.get_round(round_id)
        if not round_data:
            return []

        predictions = self.get_all_predictions(round_id)
        scores = {}

        for user_id, user_predictions in predictions.items():
            correct = 0
            total = 0

            for match in round_data["matches"]:
                match_id = match["id"]
                if match["result"] and match_id in user_predictions:
                    total += 1
                    if user_predictions[match_id] == match["result"]:
                        correct += 1

            if total > 0:
                scores[user_id] = {
                    "user_id": int(user_id),
                    "correct": correct,
                    "total": total,
                    "percentage": round(correct / total * 100, 1) if total > 0 else 0
                }

        leaderboard = sorted(scores.values(), key=lambda x: (x["correct"], x["percentage"]), reverse=True)
        return leaderboard

    def calculate_tournament_leaderboard(self, tournament_id: str) -> List[Dict]:
        """Calculate overall leaderboard for a tournament"""
        tournament = self.get_tournament(tournament_id)
        if not tournament:
            return []

        user_totals = {}

        for round_id in tournament["rounds"]:
            round_scores = self.calculate_round_leaderboard(round_id)
            for score in round_scores:
                user_id = str(score["user_id"])
                if user_id not in user_totals:
                    user_totals[user_id] = {"user_id": score["user_id"], "correct": 0, "total": 0}
                user_totals[user_id]["correct"] += score["correct"]
                user_totals[user_id]["total"] += score["total"]

        for user_id in user_totals:
            total = user_totals[user_id]["total"]
            user_totals[user_id]["percentage"] = round(
                user_totals[user_id]["correct"] / total * 100, 1
            ) if total > 0 else 0

        leaderboard = sorted(user_totals.values(), key=lambda x: (x["correct"], x["percentage"]), reverse=True)
        return leaderboard
