# seven-lamps
《七灯》—— 一款数值驱动的双人TCG卡牌对战游戏。Python从零实现完整对战引擎，含60张牌×3职业、灯数系统(0-7)、响应区/奥秘机制、20选10组牌。内置GreedyAI与蒙特卡洛批量模拟器，数据驱动调参验证平衡性。
# Seven Lamps (七灯)

> A data-driven, two-player Trading Card Game (TCG) engine built from scratch in Python.
> 
> 60 cards × 3 classes · Lamp system (0-7) · Response zone / Secret mechanism · 20-pick-10 deck building

## Overview

**Seven Lamps** is a two-player TCG designed and implemented as a complete, runnable game engine. The project demonstrates end-to-end game design capability: from core mechanic design → code implementation → AI simulation → data-driven balance tuning.

**Numerical Design Goal**: Every card parameter was adjusted based on Monte Carlo simulation results, not intuition.

## Key Features

- **60 cards** across 3 asymmetric classes (Lightbearer 燃灯者, Nightwatch 守夜人, Extinguisher 灭灯者)
- **Lamp system (0–7)**: central resource that powers card abilities and determines win condition
- **Response zone / Secret mechanism**: bluffing and counter-play via hidden card activation
- **20-pick-10 deck building**: ~180,000 possible deck combinations
- **GreedyAI + Monte Carlo batch simulator**: automated gameplay for balance verification
- **Data-driven tuning**: 500-game simulation reduced win-rate gap from 26% → 10.5% (Lightbearer 52.9% vs Extinguisher 42.4%)

## Tech Stack

- Python 3.6+ (standard library only, zero pip dependencies)
- CLI interface with color output
- matplotlib for balance visualization charts
- PIL for GIF demo generation
- PyInstaller for standalone executable packaging

## Project Structure
seven_lamps/
├── ai/           # GreedyAI & RandomAI opponents
├── analysis/     # Balance report generation
├── cards/        # Card registry (60 cards)
├── core/         # Game state, enums, constants
├── deck/         # Deck builder (20-pick-10)
├── mechanics/    # Lamp system, response zone, win checker
├── pve/          # Player vs Environment mode
├── simulator/    # Batch runner for Monte Carlo testing
├── ui/           # CLI and Pygame interfaces
├── main.py       # Entry point
└── README.md     # This file
plain
复制

## Running the Game

```bash
cd seven_lamps
python main.py
Follow the CLI prompts to play against AI or watch AI vs AI matches.
Balance Verification
bash
复制
python run_balance_check.py
Runs 500 automated games and outputs balance_report.json with win rates, turn distribution, and card usage frequency.
Design Philosophy
This project was built to demonstrate numerical design capability for game industry job applications. Every design decision is backed by simulation data, not gut feeling.
Author: 刘嘉骏 | Financial Engineering undergraduate | Aspiring Game Numerical Designer
