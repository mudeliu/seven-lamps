"""
Seven Lamps Card Game - Batch Simulator
七灯卡牌对战系统 - 批量蒙特卡洛模拟器

核心用途:
- 验证三职业胜率是否平衡(接近50%)
- 测试不同卡组配置的强度
- 统计平均回合数、卡牌出场率等
"""
import time
from typing import Dict, List, Optional
from collections import defaultdict
from ..core.enums import ClassType
from .game_runner import AIGameRunner


class BatchSimulator:
    """
    批量对战模拟器
    
    使用示例:
        sim = BatchSimulator()
        results = sim.run_matchups([
            (ClassType.LAMPLIGHTER, ClassType.EXTINGUISHER),
            (ClassType.NIGHTWATCH, ClassType.LAMPLIGHTER),
        ], games_per_matchup=1000)
        sim.print_report(results)
    """
    
    def __init__(self, ai_type="greedy", verbose_single=False):
        """
        ai_type: "random" 或 "greedy"
        verbose_single: 是否打印每一局的详细过程(调试用,建议False)
        """
        self.ai_type = ai_type
        self.verbose_single = verbose_single
        self.results: List[Dict] = []
    
    def _create_ai(self, name: str):
        """创建AI实例"""
        if self.ai_type == "random":
            from ..ai.random_ai import RandomAI
            return RandomAI()
        else:
            from ..ai.greedy_ai import GreedyAI
            return GreedyAI(name)
    
    def run_matchup(self, class1: ClassType, class2: ClassType,
                    preset1=None, preset2=None,
                    games: int = 100, swap_sides: bool = True) -> Dict:
        """
        运行一组职业对战
        
        swap_sides: 是否交换先后手位置再打一轮(消除先手优势偏差)
        
        返回统计结果字典
        """
        results = []
        
        # 正常对局: p1=class1, p2=class2
        for i in range(games):
            ai1 = self._create_ai(f"{class1.value}_P1")
            ai2 = self._create_ai(f"{class2.value}_P2")
            runner = AIGameRunner(ai1, ai2, verbose=self.verbose_single)
            runner.setup(
                {"name": "P1", "class": class1, "preset": preset1},
                {"name": "P2", "class": class2, "preset": preset2}
            )
            result = runner.run()
            result[" matchup"] = f"{class1.value}_vs_{class2.value}"
            result["p1_is"] = class1.value
            result["p2_is"] = class2.value
            results.append(result)
        
        # 交换位置: p1=class2, p2=class1 (消除先手偏差)
        if swap_sides:
            for i in range(games):
                ai1 = self._create_ai(f"{class2.value}_P1")
                ai2 = self._create_ai(f"{class1.value}_P2")
                runner = AIGameRunner(ai1, ai2, verbose=self.verbose_single)
                runner.setup(
                    {"name": "P1", "class": class2, "preset": preset2},
                    {"name": "P2", "class": class1, "preset": preset1}
                )
                result = runner.run()
                result[" matchup"] = f"{class2.value}_vs_{class1.value}"
                result["p1_is"] = class2.value
                result["p2_is"] = class1.value
                results.append(result)
        
        return self._aggregate(results, class1, class2, games * (2 if swap_sides else 1))
    
    def run_all_matchups(self, games_per_matchup: int = 500,
                         presets: Optional[Dict] = None) -> List[Dict]:
        """
        运行所有三职业组合对战 (共3种组合)
        返回列表，每个元素是一组对战的统计结果
        """
        classes = [ClassType.LAMPLIGHTER, ClassType.NIGHTWATCH, ClassType.EXTINGUISHER]
        presets = presets or {}
        all_results = []
        
        print(f"Starting batch simulation: {games_per_matchup} games per matchup")
        print(f"AI type: {self.ai_type}, Swap sides: True")
        print("=" * 50)
        
        for i, c1 in enumerate(classes):
            for c2 in classes[i+1:]:
                p1 = presets.get(c1)
                p2 = presets.get(c2)
                print(f"\nRunning: {c1.value} vs {c2.value} ...")
                start = time.time()
                stats = self.run_matchup(c1, c2, p1, p2, games_per_matchup)
                elapsed = time.time() - start
                stats["time_sec"] = round(elapsed, 2)
                all_results.append(stats)
                print(f"  Done in {elapsed:.1f}s")
        
        self.results = all_results
        return all_results
    
    def _aggregate(self, game_results: List[Dict],
                   class1: ClassType, class2: ClassType,
                   total_games: int) -> Dict:
        """聚合统计"""
        wins_c1 = 0
        wins_c2 = 0
        draws = 0
        turn_counts = []
        
        for r in game_results:
            if not r["game_over"]:
                draws += 1
            elif r["winner_class"] == class1.value:
                wins_c1 += 1
            elif r["winner_class"] == class2.value:
                wins_c2 += 1
        
        for r in game_results:
            if r["game_over"]:
                turn_counts.append(r["turns"])
        
        avg_turns = sum(turn_counts) / len(turn_counts) if turn_counts else 0
        
        return {
            "class_a": class1.value,
            "class_b": class2.value,
            "total_games": total_games,
            "wins_a": wins_c1,
            "wins_b": wins_c2,
            "draws": draws,
            "win_rate_a": round(wins_c1 / total_games * 100, 1) if total_games > 0 else 0,
            "win_rate_b": round(wins_c2 / total_games * 100, 1) if total_games > 0 else 0,
            "avg_turns": round(avg_turns, 1),
            "turn_distribution": self._turn_distribution(turn_counts),
        }
    
    def _turn_distribution(self, turns: List[int]) -> Dict[str, int]:
        """回合数分布"""
        dist = defaultdict(int)
        for t in turns:
            bucket = f"{t}T"
            dist[bucket] += 1
        return dict(sorted(dist.items(), key=lambda x: int(x[0][:-1])))
    
    def print_report(self, results: Optional[List[Dict]] = None):
        """打印平衡性报告"""
        if results is None:
            results = self.results
        
        print("\n" + "=" * 60)
        print("SEVEN LAMPS - BALANCE REPORT (Monte Carlo)")
        print("=" * 60)
        
        for r in results:
            print(f"\n{r['class_a']} vs {r['class_b']}")
            print(f"  Total games : {r['total_games']}")
            print(f"  {r['class_a']:6s} wins : {r['wins_a']:4d} ({r['win_rate_a']:5.1f}%)")
            print(f"  {r['class_b']:6s} wins : {r['wins_b']:4d} ({r['win_rate_b']:5.1f}%)")
            print(f"  Draws       : {r['draws']:4d}")
            print(f"  Avg turns   : {r['avg_turns']:.1f}")
            print(f"  Turn dist   : {r['turn_distribution']}")
        
        # 总结
        print("\n" + "-" * 60)
        print("SUMMARY:")
        max_imbalance = 0
        for r in results:
            imbalance = abs(r['win_rate_a'] - r['win_rate_b'])
            max_imbalance = max(max_imbalance, imbalance)
            status = "OK" if imbalance <= 10 else "WARN" if imbalance <= 20 else "IMBALANCED"
            print(f"  {r['class_a']} vs {r['class_b']}: diff={imbalance:.1f}% [{status}]")
        
        print(f"\nMax imbalance: {max_imbalance:.1f}%")
        if max_imbalance <= 10:
            print("Balance status: GOOD (all matchups within 10%)")
        elif max_imbalance <= 20:
            print("Balance status: ACCEPTABLE (some matchups need tuning)")
        else:
            print("Balance status: NEEDS WORK (significant imbalance detected)")
        print("=" * 60)
