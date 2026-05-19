"""
Seven Lamps Card Game - Analysis Reporter
七灯卡牌对战系统 - 分析报告生成器

生成数值策划可用的分析报告:
- 胜率矩阵 (3x3)
- 回合数分布直方图数据
- 职业强度排名
"""
from typing import Dict, List
import json


class BalanceReporter:
    """生成结构化平衡报告"""
    
    def __init__(self, results: List[Dict]):
        self.results = results
    
    def generate_matrix(self) -> Dict:
        """
        生成胜率矩阵
        返回 {class_a: {class_b: win_rate%}}
        """
        matrix = {}
        classes = set()
        
        for r in self.results:
            a, b = r["class_a"], r["class_b"]
            classes.add(a)
            classes.add(b)
            
            if a not in matrix:
                matrix[a] = {}
            if b not in matrix:
                matrix[b] = {}
            
            matrix[a][b] = r["win_rate_a"]
            matrix[b][a] = r["win_rate_b"]
        
        # 对角线50%
        for c in classes:
            matrix[c][c] = 50.0
        
        return matrix
    
    def generate_summary(self) -> Dict:
        """生成摘要统计"""
        matrix = self.generate_matrix()
        
        # 计算每个职业的平均胜率
        avg_rates = {}
        for cls, opponents in matrix.items():
            rates = [v for k, v in opponents.items() if k != cls]
            avg_rates[cls] = round(sum(rates) / len(rates), 1) if rates else 50.0
        
        # 排序
        ranked = sorted(avg_rates.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "win_matrix": matrix,
            "avg_win_rate": avg_rates,
            "ranking": [{"class": c, "avg_win_rate": r} for c, r in ranked],
            "max_imbalance": max(
                abs(r["win_rate_a"] - r["win_rate_b"]) for r in self.results
            ),
        }
    
    def to_json(self, indent: int = 2) -> str:
        """导出JSON格式报告"""
        return json.dumps(self.generate_summary(), ensure_ascii=False, indent=indent)
    
    def to_markdown(self) -> str:
        """导出Markdown格式报告"""
        s = self.generate_summary()
        lines = []
        lines.append("# 《七灯》平衡性分析报告")
        lines.append("")
        lines.append("## 胜率矩阵")
        lines.append("")
        
        # 表头
        classes = sorted(s["win_matrix"].keys())
        header = "| 职业 | " + " | ".join(classes) + " |"
        lines.append(header)
        lines.append("|" + "---|" * (len(classes) + 1))
        
        for c in classes:
            row = f"| {c} |"
            for opp in classes:
                rate = s["win_matrix"][c].get(opp, 50.0)
                row += f" {rate:.1f}% |"
            lines.append(row)
        
        lines.append("")
        lines.append("## 职业强度排名")
        lines.append("")
        lines.append("| 排名 | 职业 | 平均胜率 |")
        lines.append("|------|------|----------|")
        for i, item in enumerate(s["ranking"], 1):
            lines.append(f"| {i} | {item['class']} | {item['avg_win_rate']:.1f}% |")
        
        lines.append("")
        lines.append(f"## 平衡性评估")
        lines.append("")
        diff = s["max_imbalance"]
        if diff <= 10:
            status = "良好"
            desc = "所有对局胜率差在10%以内，平衡性优秀。"
        elif diff <= 20:
            status = "可接受"
            desc = "部分对局存在10-20%的胜率偏差，建议微调。"
        else:
            status = "需调整"
            desc = "存在显著不平衡（>20%），需要重新设计卡牌数值。"
        
        lines.append(f"- **最大胜率差**: {diff:.1f}%")
        lines.append(f"- **平衡状态**: {status}")
        lines.append(f"- **建议**: {desc}")
        
        return "\n".join(lines)
    
    def save_report(self, filepath: str, fmt: str = "markdown"):
        """保存报告到文件"""
        if fmt == "json":
            content = self.to_json()
        else:
            content = self.to_markdown()
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Report saved to {filepath}")
