# Complete ELO Rating System Documentation

## Table of Contents
1. [Quick Start Guide](#quick-start-guide)
2. [What is ELO?](#what-is-elo)
3. [How ELO Works - The Basics](#how-elo-works---the-basics)
4. [Mathematical Foundation](#mathematical-foundation)
5. [Our Implementation Details](#our-implementation-details)
6. [Detailed Examples with Real Numbers](#detailed-examples-with-real-numbers)
7. [Rating Milestones and Skill Levels](#rating-milestones-and-skill-levels)
8. [Singles vs Doubles](#singles-vs-doubles)
9. [Common Questions Answered](#common-questions-answered)
10. [Strategy and Tips](#strategy-and-tips)
11. [Advanced Concepts](#advanced-concepts)

---

## Quick Start Guide

**New to ELO? Here's what you need to know:**
- You start at **1000 ELO** (average)
- Win = rating goes up, Loss = rating goes down
- Beat stronger players = gain more points
- Lose to weaker players = lose more points
- Your first 30 games adjust quickly to find your true level

---

## What is ELO?

The ELO rating system is a method for calculating the relative skill levels of players in competitive games. Originally created by Arpad Elo for chess, it's now used in many competitive activities including table tennis, online gaming, and sports analytics.

### Core Concept
- Every player has a numerical rating (ELO score)
- When you win, your rating goes up
- When you lose, your rating goes down
- The amount of change depends on the relative strength of your opponent

### Why Use ELO?
1. **Fair Matchmaking**: Helps identify players of similar skill
2. **Progress Tracking**: Shows improvement over time
3. **Competitive Integrity**: Rewards beating stronger opponents more than weaker ones
4. **Self-Balancing**: Ratings naturally adjust to reflect true skill over time

---

## How ELO Works - The Basics

### Starting Point
- **New Players**: Everyone starts at 1000 ELO
- This is considered "average" skill level
- Your true rating emerges after ~30 games

### Zero-Sum System
- Points lost by one player = Points gained by the other
- Total ELO in the system remains constant
- No rating inflation or deflation

### Key Principles

1. **Beating a Higher-Rated Player**
   - You gain MORE points
   - They lose the same amount you gain
   - Bigger upset = Bigger point swing

2. **Beating a Lower-Rated Player**
   - You gain FEWER points
   - They lose the same small amount
   - Expected results = Small changes

3. **Losing to a Higher-Rated Player**
   - You lose FEWER points
   - Expected result = Small penalty

4. **Losing to a Lower-Rated Player**
   - You lose MORE points
   - Upset result = Large penalty

---

## Mathematical Foundation

### The Core Formula

#### Step 1: Calculate Expected Score
```
Expected_Score = 1 / (1 + 10^((Opponent_Rating - Your_Rating) / 400))
```

This gives a probability between 0 and 1 of winning.

#### Step 2: Calculate Rating Change
```
Rating_Change = K × (Actual_Score - Expected_Score)
```

Where:
- K = K-factor (volatility constant)
- Actual_Score = 1 for win, 0 for loss
- Expected_Score = probability from Step 1

#### Step 3: Apply New Rating
```
New_Rating = Old_Rating + Rating_Change
```

### Understanding the 400-Point Rule

The number 400 in the formula is significant:
- **400-point difference** = 10:1 odds (91% vs 9%)
- **200-point difference** = 3:1 odds (76% vs 24%)
- **100-point difference** = 1.6:1 odds (64% vs 36%)
- **0-point difference** = 1:1 odds (50% vs 50%)

---

## Our Implementation Details

### K-Factor System (Dynamic Volatility)

We use different K-factors based on experience and rating:

| Category | Condition | K-Factor | Purpose |
|----------|-----------|----------|---------|
| **New Player** | < 30 games played | 40 | Quick adjustment to true skill level |
| **Regular Player** | ≥ 30 games AND < 2400 rating | 32 | Balanced stability vs responsiveness |
| **Elite Player** | ≥ 30 games AND ≥ 2400 rating | 24 | Prevents wild swings at high levels |

### Why Variable K-Factors?

1. **New Players (K=40)**
   - Need rapid adjustment
   - Initial rating is just a guess
   - Helps find true level quickly
   - Reduces frustration from mismatches

2. **Regular Players (K=32)**
   - Established baseline skill
   - Still room for improvement
   - Responsive to genuine skill changes

3. **Elite Players (K=24)**
   - Proven consistent skill
   - Prevents rating manipulation
   - Maintains leaderboard stability

### Additional Features

- **Peak Ratings**: System tracks your highest-ever rating in both singles and doubles
- **Rating Floors**: Ratings cannot drop below 0
- **Initial Provisional Period**: First 30 games use higher K-factor

---

## Detailed Examples with Real Numbers

### Example 1: Even Match (Both 1000 ELO)
**Players**: Alice (1000) vs Bob (1000)
**K-factors**: Both 32 (regular players)

**Calculation**:
- Expected score for each: 0.50 (50% chance)
- If Alice wins:
  - Alice: 1000 + 32 × (1 - 0.50) = 1000 + 16 = **1016**
  - Bob: 1000 + 32 × (0 - 0.50) = 1000 - 16 = **984**

### Example 2: Favorite Wins (1200 vs 1000)
**Players**: Charlie (1200) vs Dana (1000)
**K-factors**: Both 32

**Calculation**:
- Charlie's expected score: 0.76 (76% chance)
- Dana's expected score: 0.24 (24% chance)
- If Charlie wins (expected):
  - Charlie: 1200 + 32 × (1 - 0.76) = 1200 + 8 = **1208**
  - Dana: 1000 + 32 × (0 - 0.24) = 1000 - 8 = **992**

### Example 3: Major Upset (1400 vs 1000)
**Players**: Expert Eve (1400) vs Novice Nick (1000)
**K-factors**: Eve = 32, Nick = 40 (new player)

**Calculation**:
- Eve's expected score: 0.91 (91% chance)
- Nick's expected score: 0.09 (9% chance)
- If Nick wins (huge upset!):
  - Nick: 1000 + 40 × (1 - 0.09) = 1000 + 36 = **1036**
  - Eve: 1400 + 32 × (0 - 0.91) = 1400 - 29 = **1371**

### Example 4: New Player's First Games
**Player**: Fresh Frank (1000, 0 games) vs Veteran Vicky (1150)
**K-factors**: Frank = 40 (new), Vicky = 32 (regular)

**Game 1 - Frank loses (expected)**:
- Frank's expected: 0.30
- Frank: 1000 + 40 × (0 - 0.30) = 1000 - 12 = **988**
- Vicky: 1150 + 32 × (1 - 0.70) = 1150 + 10 = **1160**

**Game 2 - Frank beats 1050-rated player (mild upset)**:
- Frank's expected: 0.43
- Frank: 988 + 40 × (1 - 0.43) = 988 + 23 = **1011**

### Example 5: Rating Progression Over 10 Games

**New Player Journey** (Starting at 1000):

| Game | Opponent | Result | Expected Win% | Rating Change | New Rating |
|------|----------|--------|---------------|---------------|------------|
| 1 | 950 | Win | 57% | +17 | 1017 |
| 2 | 1100 | Loss | 37% | -15 | 1002 |
| 3 | 1000 | Win | 50% | +20 | 1022 |
| 4 | 1150 | Loss | 32% | -13 | 1009 |
| 5 | 1000 | Win | 51% | +20 | 1029 |
| 6 | 1050 | Win | 47% | +21 | 1050 |
| 7 | 1200 | Loss | 29% | -12 | 1038 |
| 8 | 1100 | Win | 42% | +23 | 1061 |
| 9 | 1000 | Win | 59% | +16 | 1077 |
| 10 | 1150 | Win | 38% | +25 | **1102** |

**Result**: After 10 games (7-3 record), settled around true skill level of 1100.

### Common Scenarios

#### The Upset
- Player A (800 rating, new player) beats Player B (1200 rating)
- A gains: 40 × (1 - 0.09) = +36 points
- B loses: 32 × (0 - 0.91) = -29 points
- Note: Different K-factors mean different magnitudes!

#### The Expected Result
- Player A (1200) beats Player B (1000)
- A gains: 32 × (1 - 0.76) = +8 points
- B loses: 32 × (0 - 0.24) = -8 points

#### The Even Match
- Player A (1000) beats Player B (1000)
- A gains: 32 × (1 - 0.50) = +16 points
- B loses: 32 × (0 - 0.50) = -16 points

---

## Rating Milestones and Skill Levels

### Detailed Rating Brackets

| Rating Range | Skill Level | Percentile | Description | Typical Characteristics |
|--------------|-------------|------------|-------------|------------------------|
| **< 600** | Absolute Beginner | Bottom 1% | Just learning the game | Learning basic rules, can't serve consistently |
| **600-800** | Beginner | 1-10% | Knows rules, lacks consistency | Can rally occasionally, weak serves |
| **800-900** | Advanced Beginner | 10-25% | Developing fundamentals | Basic serves work, starting to use spin |
| **900-1000** | Novice | 25-40% | Casual player level | Consistent serves, can maintain rallies |
| **1000-1100** | Average | 40-60% | Regular recreational player | Good consistency, basic strategy |
| **1100-1200** | Above Average | 60-75% | Strong recreational player | Multiple serve types, good placement |
| **1200-1300** | Competitive | 75-85% | Club level player | Strong spin game, tactical awareness |
| **1300-1400** | Advanced | 85-92% | Tournament competitor | Excellent consistency, multiple strategies |
| **1400-1500** | Expert | 92-96% | Top club player | Near-professional technique |
| **1500-1600** | Master | 96-98% | Regional competitor | Could compete professionally |
| **1600-1800** | Elite | 98-99.5% | National level | Professional or semi-pro |
| **1800-2000** | Champion | 99.5-99.9% | International competitor | World-class player |
| **2000+** | Legendary | Top 0.1% | World elite | Olympic/World Championship level |

### Real-World Comparisons

- **800 ELO**: Can play recreationally with friends
- **1000 ELO**: Average office tournament player
- **1200 ELO**: Wins most casual games, competitive in club
- **1400 ELO**: Dominates local club, enters regional tournaments
- **1600 ELO**: Could coach professionally
- **1800 ELO**: Could compete nationally
- **2000+ ELO**: World-class athlete

---

## Singles vs Doubles

### Singles Games

In singles matches, the calculation is straightforward:
- Winner gains rating points
- Loser loses the same amount
- Both players experience the same magnitude of change (one positive, one negative)

**Example**:
- Player A (1200) beats Player B (1000)
- Expected: A has 76% chance to win
- K-factor: Both use K=32 (assuming regular players)
- A gains: 32 × (1 - 0.76) = +8 points → New rating: 1208
- B loses: 32 × (0 - 0.24) = -8 points → New rating: 992

### Doubles Games (Currently Disabled in UI)

For doubles matches, the system:

1. **Calculates Team Ratings**: Averages the ratings of both players on each team
2. **Applies Team Results**: Calculates expected vs actual outcomes for teams
3. **Individual Adjustments**: Each player receives 75% of the calculated change

The 75% factor (DOUBLES_FACTOR = 0.75) accounts for:
- Partner influence on the outcome
- Reduced individual responsibility for wins/losses
- Prevents rating inflation from team games

**Example**:
- Team 1: Player A (1200) + Player B (1100) = Average 1150
- Team 2: Player C (1000) + Player D (900) = Average 950
- Team 1 wins (expected, given 200-point advantage)
- Each Team 1 player gains ~6 points (75% of calculated 8)
- Each Team 2 player loses ~6 points

---

## Common Questions Answered

### Q: Why did I lose more points than my opponent gained?
**A**: Different K-factors. If you have different numbers of games played, your K-factors differ.

**Example**:
- You (1100, 50 games, K=32) beat newcomer (1000, 5 games, K=40)
- You gain: 32 × 0.36 = 12 points
- They lose: 40 × 0.36 = 14 points

### Q: How many games until my rating is accurate?
**A**:
- After 10 games: ±100 points of true skill
- After 20 games: ±50 points of true skill
- After 30 games: Generally accurate (K-factor drops)
- After 50 games: Very accurate representation

### Q: Can I lose rating by winning?
**A**: No, never. Winners always gain rating and losers always lose rating.

### Q: What's the fastest way to gain rating?
**A**: Beat players rated higher than you. One upset victory against someone 200+ points higher is worth 3-4 wins against equal opponents.

### Q: Why do I gain fewer points for each win in a winning streak?
**A**: As your rating rises, you become the favorite. Favorites gain less for expected wins.

### Q: Is 1500 ELO twice as good as 750?
**A**: No! ELO is not linear. The difference between 1000→1100 represents the same skill improvement as 1400→1500.

### Q: What happens if I don't play for months?
**A**: Nothing. Your rating remains unchanged. There's no rating decay for inactivity.

### Q: Can the system be gamed?
**A**: Difficult. Intentionally losing drops your rating but doesn't help long-term. The system self-corrects manipulation attempts.

### Q: Do singles and doubles affect each other?
**A**: No, singles and doubles ratings are tracked separately. Playing doubles doesn't affect your singles rating.

---

## Strategy and Tips

### For New Players (< 30 games)
1. **Play lots of games**: Your K-factor is high, use it to find your level
2. **Don't fear losses**: Early losses barely matter long-term
3. **Challenge variety**: Play different skill levels to calibrate faster
4. **Focus on learning**: Rating will follow skill improvement

### For Improving Players
1. **Challenge up**: Playing slightly better players (50-150 points higher) optimizes learning
2. **Analyze losses**: Losses to lower-rated players highlight weaknesses
3. **Track trends**: Monitor your rating graph for improvement patterns
4. **Consistency matters**: Regular play maintains and improves rating

### For High-Level Players
1. **Protect your rating**: With lower K-factor, recovery from upsets is slower
2. **Select opponents carefully**: Risk/reward changes at high levels
3. **Consistency matters**: Avoiding bad losses is as important as big wins
4. **Mentor others**: Teaching reinforces your own skills

### Understanding Matchup Math

| Rating Difference | Favorite's Win % | Underdog's Win % | Favorite Gains | Underdog Gains |
|-------------------|------------------|------------------|----------------|----------------|
| 0 | 50% | 50% | 16 | 16 |
| 50 | 57% | 43% | 14 | 18 |
| 100 | 64% | 36% | 12 | 20 |
| 150 | 70% | 30% | 10 | 22 |
| 200 | 76% | 24% | 8 | 24 |
| 300 | 85% | 15% | 5 | 27 |
| 400 | 91% | 9% | 3 | 29 |
| 500 | 95% | 5% | 2 | 30 |

### Psychological Factors

1. **Rating Anxiety**: Don't obsess over every point. Focus on improvement.
2. **Tilt Protection**: After a bad loss, take a break. Emotional play leads to rating spirals.
3. **Plateau Breaking**: Stuck at a rating? Focus on defeating players 50-100 points higher.
4. **Long-term View**: Daily fluctuations of ±50 points are normal. Judge progress monthly.

---

## Advanced Concepts

### Rating Inflation/Deflation Prevention
Our system prevents this by:
- Zero-sum exchanges (no points created/destroyed)
- Fixed starting rating (1000)
- No bonus points or artificial adjustments
- Consistent K-factor rules

### Provisional vs Established Ratings
- **Provisional** (< 30 games): High volatility, rapid adjustments
- **Established** (≥ 30 games): Stable rating, eligible for all leaderboards

### Peak Rating Tracking
- System records your highest-ever rating
- Shown on profile as "Peak: XXXX"
- Date of achievement recorded
- Separate peaks for singles and doubles

### Win Probability Quick Reference

```
Your_Rating - Opponent_Rating = Win_Probability
+400 = 91%
+300 = 85%
+200 = 76%
+150 = 70%
+100 = 64%
+50 = 57%
0 = 50%
-50 = 43%
-100 = 36%
-150 = 30%
-200 = 24%
-300 = 15%
-400 = 9%
```

### Weekly Points System

In addition to ELO, players earn weekly points for:
- Playing games: 10 points
- Winning games: 20 points
- Win streaks: 5 points per day
- Upset victories: 30 bonus points (beating someone 200+ ELO higher)

---

## Conclusion

The ELO system provides a fair, mathematical approach to ranking players. Key takeaways:

1. **Patience**: Your true rating emerges over time
2. **Challenge yourself**: Playing stronger opponents accelerates improvement
3. **Embrace variance**: Short-term fluctuations are normal
4. **Focus on improvement**: Rating follows skill, not vice versa
5. **Understand the math**: Knowing the system helps set realistic expectations

Remember: ELO measures relative performance, not absolute skill. A 1200 player today might be stronger than a 1200 player last year if the overall player pool improved.

### Quick Formulas Reference

**Expected Score**: `E = 1 / (1 + 10^((OpponentELO - YourELO) / 400))`

**Rating Change**: `Change = K × (ActualResult - ExpectedScore)`

**New Rating**: `NewELO = OldELO + Change`

**K-Factors**:
- New (< 30 games): K = 40
- Regular (≥ 30 games, < 2400 ELO): K = 32
- Elite (≥ 30 games, ≥ 2400 ELO): K = 24

Good luck, and may your rating always trend upward! 🏓