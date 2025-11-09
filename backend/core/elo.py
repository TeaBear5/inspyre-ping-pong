"""
ELO Rating System for Ping Pong Tracker
Standard ELO implementation with K-factor adjustments
"""
import math


class ELOCalculator:
    """
    Calculate ELO ratings for ping pong games
    """

    # K-factors based on rating and game count
    K_FACTOR_NEW = 40      # For players with < 30 games
    K_FACTOR_MID = 32      # For players rated < 2400
    K_FACTOR_HIGH = 24     # For players rated >= 2400

    NEW_PLAYER_GAMES = 30  # Number of games before considered established
    HIGH_RATING_THRESHOLD = 2400

    @staticmethod
    def get_k_factor(rating, games_played):
        """
        Get K-factor based on rating and experience
        New players have higher K-factor for faster rating adjustment
        """
        if games_played < ELOCalculator.NEW_PLAYER_GAMES:
            return ELOCalculator.K_FACTOR_NEW
        elif rating < ELOCalculator.HIGH_RATING_THRESHOLD:
            return ELOCalculator.K_FACTOR_MID
        else:
            return ELOCalculator.K_FACTOR_HIGH

    @staticmethod
    def expected_score(rating_a, rating_b):
        """
        Calculate expected score for player A against player B
        Returns probability of player A winning (0-1)
        """
        return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))

    @staticmethod
    def calculate_new_ratings(rating_a, rating_b, score_a, games_a=None, games_b=None):
        """
        Calculate new ratings after a game

        Args:
            rating_a: Current rating of player A
            rating_b: Current rating of player B
            score_a: Actual score for player A (1 for win, 0 for loss, 0.5 for draw)
            games_a: Number of games played by player A (optional, affects K-factor)
            games_b: Number of games played by player B (optional, affects K-factor)

        Returns:
            tuple: (new_rating_a, new_rating_b, rating_change)
        """
        # Get expected scores
        expected_a = ELOCalculator.expected_score(rating_a, rating_b)
        expected_b = 1 - expected_a

        # Get actual scores
        score_b = 1 - score_a

        # Get K-factors
        k_a = ELOCalculator.get_k_factor(rating_a, games_a or 100)
        k_b = ELOCalculator.get_k_factor(rating_b, games_b or 100)

        # Calculate rating changes
        change_a = k_a * (score_a - expected_a)
        change_b = k_b * (score_b - expected_b)

        # Apply changes
        new_rating_a = round(rating_a + change_a)
        new_rating_b = round(rating_b + change_b)

        # Ensure ratings don't go below 0
        new_rating_a = max(0, new_rating_a)
        new_rating_b = max(0, new_rating_b)

        return new_rating_a, new_rating_b, abs(round(change_a))

    @staticmethod
    def calculate_doubles_ratings(team1_ratings, team2_ratings, team1_won,
                                   team1_games=None, team2_games=None):
        """
        Calculate new ratings for doubles games
        Uses average team rating for calculations

        Args:
            team1_ratings: tuple of (player1_rating, player2_rating) for team 1
            team2_ratings: tuple of (player1_rating, player2_rating) for team 2
            team1_won: boolean, True if team 1 won
            team1_games: tuple of games played for team 1 players
            team2_games: tuple of games played for team 2 players

        Returns:
            dict with new ratings for all 4 players
        """
        # Calculate average ratings for each team
        avg_team1 = sum(team1_ratings) / 2
        avg_team2 = sum(team2_ratings) / 2

        # Determine score
        score_team1 = 1 if team1_won else 0

        # Calculate expected scores
        expected_team1 = ELOCalculator.expected_score(avg_team1, avg_team2)
        expected_team2 = 1 - expected_team1

        actual_team1 = score_team1
        actual_team2 = 1 - score_team1

        # Calculate rating changes for each player
        # Each player gets 75% of the full change (to account for partner influence)
        DOUBLES_FACTOR = 0.75

        result = {}

        # Team 1 players
        for i, rating in enumerate(team1_ratings):
            games = team1_games[i] if team1_games else 100
            k_factor = ELOCalculator.get_k_factor(rating, games)
            change = k_factor * (actual_team1 - expected_team1) * DOUBLES_FACTOR
            new_rating = round(rating + change)
            result[f'team1_player{i+1}'] = max(0, new_rating)

        # Team 2 players
        for i, rating in enumerate(team2_ratings):
            games = team2_games[i] if team2_games else 100
            k_factor = ELOCalculator.get_k_factor(rating, games)
            change = k_factor * (actual_team2 - expected_team2) * DOUBLES_FACTOR
            new_rating = round(rating + change)
            result[f'team2_player{i+1}'] = max(0, new_rating)

        # Calculate average change for display
        avg_change = abs(round(ELOCalculator.get_k_factor(avg_team1, 100) *
                               (actual_team1 - expected_team1) * DOUBLES_FACTOR))

        result['elo_change'] = avg_change

        return result


class PointsCalculator:
    """
    Calculate weekly points for regular play incentives
    """

    # Point values
    POINTS_PER_GAME = 10
    POINTS_PER_WIN = 20
    POINTS_STREAK_BONUS = 5  # Per day in streak
    POINTS_UPSET_BONUS = 30  # Beating someone 200+ ELO higher

    @staticmethod
    def calculate_game_points(winner_elo, loser_elo, current_streak=0):
        """
        Calculate points earned from a single game

        Args:
            winner_elo: ELO rating of the winner
            loser_elo: ELO rating of the loser
            current_streak: Current playing streak in days

        Returns:
            tuple: (winner_points, loser_points)
        """
        # Winner gets base points
        winner_points = PointsCalculator.POINTS_PER_GAME + PointsCalculator.POINTS_PER_WIN

        # Upset bonus
        if loser_elo - winner_elo >= 200:
            winner_points += PointsCalculator.POINTS_UPSET_BONUS

        # Streak bonus
        if current_streak > 0:
            winner_points += min(current_streak * PointsCalculator.POINTS_STREAK_BONUS, 50)

        # Loser gets participation points
        loser_points = PointsCalculator.POINTS_PER_GAME

        return winner_points, loser_points

    @staticmethod
    def calculate_weekly_rank(points_list):
        """
        Calculate weekly rankings based on points

        Args:
            points_list: List of (player_id, points) tuples

        Returns:
            List of (player_id, points, rank) tuples
        """
        # Sort by points descending
        sorted_players = sorted(points_list, key=lambda x: x[1], reverse=True)

        result = []
        current_rank = 1
        prev_points = None

        for i, (player_id, points) in enumerate(sorted_players):
            # Handle ties
            if prev_points is not None and points < prev_points:
                current_rank = i + 1

            result.append((player_id, points, current_rank))
            prev_points = points

        return result