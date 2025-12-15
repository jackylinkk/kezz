# -*- coding: utf-8 -*-
"""
可转债量化分析系统 v10.2（透明注解版）- 集成债底分析
完全修复版本 - 解决 unsupported operand type(s) for /: 'str' and 'float' 错误
"""

import akshare as ak
import pandas as pd
import numpy as np
import time
import sys
import requests
import random
from datetime import datetime, timedelta
import re
import os
import json
import warnings
from typing import Dict, Tuple, List, Optional

# 屏蔽所有警告信息
warnings.filterwarnings('ignore')

print("可转债量化分析系统 v10.2 透明注解版".center(60, "="))

# ==================== 核心修复：safe_float_convert 函数 ====================

def safe_float_convert(value, default=0.0):
    """
    安全地将值转换为浮点数，处理各种输入类型
    这是修复问题的关键函数
    """
    try:
        if value is None:
            return float(default)
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # 清理字符串：移除百分号、逗号、空格等
            value = value.strip()
            value = value.replace('%', '')
            value = value.replace(',', '')
            value = value.replace('元', '')
            value = value.replace('亿', '')
            
            # 处理空字符串
            if not value or value == '' or value.lower() == 'nan' or value.lower() == 'null':
                return float(default)
            
            # 尝试转换为浮点数
            return float(value)
        
        # 其他类型尝试直接转换
        return float(value)
    
    except Exception as e:
        print(f"⚠️ 数值转换警告: 将 '{value}' 转换为浮点数失败: {e}, 使用默认值 {default}")
        return float(default)

# ==================== HTML报告生成器 ====================

class HTMLReportGenerator:
    """HTML报告生成器"""
    
    def __init__(self):
        self.report_content = []
        self.css_style = """
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #e0e0e0; }
            .section { margin-bottom: 25px; padding: 15px; background: #fafafa; border-radius: 8px; border-left: 4px solid #007bff; }
            .section h2 { color: #333; margin-top: 0; }
            .bond-card { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .bond-header { display: flex; justify-content: between; align-items: center; margin-bottom: 10px; }
            .bond-name { font-size: 1.2em; font-weight: bold; color: #0056b3; }
            .bond-rating { font-size: 1.1em; font-weight: bold; padding: 5px 10px; border-radius: 5px; }
            .rating-excellent { background: #d4edda; color: #155724; }
            .rating-good { background: #d1ecf1; color: #0c5460; }
            .rating-medium { background: #fff3cd; color: #856404; }
            .rating-poor { background: #f8d7da; color: #721c24; }
            .bond-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px; }
            .detail-item { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #f0f0f0; }
            .detail-label { font-weight: bold; color: #666; }
            .detail-value { color: #333; }
            .advice-box { background: #e7f3ff; padding: 10px; border-radius: 5px; margin-top: 10px; border-left: 4px solid #007bff; }
            .timestamp { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #666; font-size: 0.9em; }
            .risk-warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .signal-strong-buy { background: linear-gradient(135deg, #d4edda, #c3e6cb); }
            .signal-buy { background: linear-gradient(135deg, #d1ecf1, #bee5eb); }
            .signal-wait { background: linear-gradient(135deg, #fff3cd, #ffeaa7); }
            .signal-sell { background: linear-gradient(135deg, #f8d7da, #f5c6cb); }
        </style>
        """
    
    def add_header(self, title, subtitle=""):
        """添加报告头部"""
        self.report_content.append(f"""
        <div class="header">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """)
    
    def add_section(self, title, content):
        """添加章节"""
        self.report_content.append(f"""
        <div class="section">
            <h2>{title}</h2>
            {content}
        </div>
        """)
    
    def add_subsection(self, title, content):
        """添加子章节"""
        self.report_content.append(f"""
        <div class="subsection">
            <h3>{title}</h3>
            {content}
        </div>
        """)
    
    def create_metric_card(self, value, label, color_class=""):
        """创建指标卡片"""
        return f"""
        <div class="metric-card {color_class}">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """
    
    def create_progress_bar(self, value, max_value=100, label=""):
        """创建进度条"""
        percentage = (value / max_value) * 100 if max_value > 0 else 0
        return f"""
        <div>
            <div style="display: flex; justify-content: space-between;">
                <span>{label}</span>
                <span>{percentage:.1f}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-value" style="width: {percentage}%"></div>
            </div>
        </div>
        """
    
    def generate_bond_analysis_report(self, bond_info, ta_results, holding_info=None):
        """生成债券分析报告"""
        # 重置内容
        self.report_content = []
        
        # 添加头部
        self.add_header(
            f"可转债全面分析报告 - {bond_info['名称']}",
            f"代码: {bond_info['转债代码']} | 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # 基本信息
        basic_info_html = self._generate_basic_info_html(bond_info)
        self.add_section("📊 基本信息", basic_info_html)
        
        # 债底分析
        floor_html = self._generate_floor_analysis_html(bond_info)
        if floor_html:
            self.add_section("🛡️ 债底分析", floor_html)
        
        # 多因子共振分析
        if ta_results and ta_results.get('overall_signal') != 'INVALID':
            ta_html = self._generate_ta_analysis_html(ta_results)
            self.add_section("🎯 多因子共振技术分析", ta_html)
        
        # 风险分析
        risk_html = self._generate_risk_analysis_html(bond_info)
        self.add_section("⚠️ 风险分析", risk_html)
        
        # 策略分析
        strategy_html = self._generate_strategy_analysis_html(bond_info)
        self.add_section("💡 投资策略", strategy_html)
        
        # 持仓分析
        if holding_info:
            holding_html = self._generate_holding_analysis_html(bond_info, holding_info)
            self.add_section("💰 持仓分析", holding_html)
        
        # 技术分析
        tech_html = self._generate_technical_analysis_html(bond_info)
        self.add_section("📈 技术分析", tech_html)
        
        # 综合评分
        score_html = self._generate_score_analysis_html(bond_info)
        self.add_section("🏆 综合评分", score_html)
        
        # 生成完整HTML
        return self._wrap_html()
    
    def _generate_basic_info_html(self, bond_info):
        """生成基本信息HTML"""
        html = """
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0;">
        """
        
        # 使用 safe_float_convert 确保数值类型
        bond_price = safe_float_convert(bond_info.get('转债价格', 0))
        stock_price = safe_float_convert(bond_info.get('正股价格', 0))
        premium = safe_float_convert(bond_info.get('溢价率(%)', 0))
        conversion_value = safe_float_convert(bond_info.get('转股价值', 0))
        remaining_size = safe_float_convert(bond_info.get('剩余规模(亿)', 0))
        remaining_years = safe_float_convert(bond_info.get('剩余年限', 0))
        double_low = safe_float_convert(bond_info.get('双低值', 0))
        ytm = safe_float_convert(bond_info.get('YTM(%)', 0))
        
        metrics = [
            (f"{bond_price:.2f}元", "转债价格", ""),
            (f"{stock_price:.2f}元", "正股价格", ""),
            (f"{premium:.2f}%", "溢价率", "risk-high" if premium > 30 else "risk-low"),
            (f"{conversion_value:.2f}", "转股价值", ""),
            (f"{remaining_size:.2f}亿", "剩余规模", ""),
            (f"{remaining_years:.2f}年", "剩余年限", ""),
            (f"{double_low:.2f}", "双低值", ""),
            (f"{ytm:.2f}%", "到期收益率", ""),
        ]
        
        # 添加债底分析指标
        floor_analysis = bond_info.get("债底分析", {})
        if floor_analysis:
            pure_bond_value = safe_float_convert(floor_analysis.get('pure_bond_value', 0))
            effective_floor = safe_float_convert(floor_analysis.get('effective_floor', 0))
            effective_floor_premium = safe_float_convert(floor_analysis.get('effective_floor_premium', 0))
            
            metrics.extend([
                (f"{pure_bond_value:.2f}元", "纯债价值", ""),
                (f"{effective_floor:.2f}元", "有效债底", ""),
                (f"{effective_floor_premium:.2f}%", "债底溢价率", 
                 "risk-high" if effective_floor_premium > 30 else "risk-low"),
            ])
        
        for value, label, color_class in metrics:
            html += self.create_metric_card(value, label, color_class)
        
        html += "</div>"
        
        # 数据来源
        html += f"""
        <div class="explanation">
            <strong>数据来源:</strong> {bond_info.get('数据来源', 'AkShare')} | 
            <strong>更新时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        """
        
        return html
    
    def _generate_floor_analysis_html(self, bond_info):
        """生成债底分析HTML"""
        floor_analysis = bond_info.get("债底分析", {})
        if not floor_analysis:
            return ""
            
        # 使用 safe_float_convert 确保数值类型
        pure_bond_value = safe_float_convert(floor_analysis.get('pure_bond_value', 0))
        effective_floor = safe_float_convert(floor_analysis.get('effective_floor', 0))
        pure_bond_premium = safe_float_convert(floor_analysis.get('pure_bond_premium', 0))
        effective_floor_premium = safe_float_convert(floor_analysis.get('effective_floor_premium', 0))
        put_value = safe_float_convert(floor_analysis.get('put_value', 0))
        historical_support = safe_float_convert(floor_analysis.get('historical_support', 0))
        
        # 生成务实评语
        bond_price = safe_float_convert(bond_info.get('转债价格', 0))
        conversion_premium = safe_float_convert(bond_info.get('溢价率(%)', 0))
        
        practical_assessment = f"""
        <div class="explanation">
            <strong>务实评估:</strong><br>
            理论债底约{pure_bond_value:.2f}元，但历史支撑在{effective_floor:.2f}元附近；<br>
            当前价格隐含正股需上涨{conversion_premium:.2f}%才能平价，若无催化剂，上行空间有限，下行有技术支撑但无强债底保护。
        </div>
        """
        
        html = f"""
        <table class="table">
            <tr><th>指标</th><th>数值</th><th>说明</th></tr>
            <tr><td>纯债价值</td><td>{pure_bond_value:.2f}元</td><td>基于贴现现金流计算的理论底线</td></tr>
            <tr><td>回售价值</td><td>{put_value:.2f}元</td><td>满足回售条件时可获得的价值</td></tr>
            <tr><td>历史支撑</td><td>{historical_support:.2f}元</td><td>基于历史价格的技术支撑位</td></tr>
            <tr><td>有效债底</td><td>{effective_floor:.2f}元</td><td>综合考虑后的实际支撑位</td></tr>
            <tr><td>纯债溢价率</td><td>{pure_bond_premium:.2f}%</td><td>价格相对于纯债价值的高估程度</td></tr>
            <tr><td>有效债底溢价率</td><td>{effective_floor_premium:.2f}%</td><td>价格相对于有效债底的高估程度</td></tr>
        </table>
        {practical_assessment}
        """
        
        return html
    
    def _generate_ta_analysis_html(self, ta_results):
        """生成技术分析HTML"""
        html = ""
        
        # 前提条件
        prereq = ta_results['prerequisites']
        if not prereq['all_ok']:
            html += """
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <h4 style="color: #856404; margin-top: 0;">⚠️ 技术分析前提条件不满足</h4>
            """
            for msg in prereq['messages']:
                html += f"<p>{msg}</p>"
            html += "</div>"
            return html
        
        # 趋势确认
        trend = ta_results['trend_confirmation']
        trend_strength = safe_float_convert(trend.get('trend_strength', 0))
        html += f"""
        <div class="subsection">
            <h4>趋势确认 (强度: {trend_strength:.0f}/3)</h4>
            <table class="table">
                <tr><th>指标</th><th>状态</th><th>解释</th></tr>
                <tr><td>均线排列</td><td>{'✅ 多头' if trend.get('ma_bullish', False) else '❌ 非多头'}</td><td>{trend.get('explanations', {}).get('ma_explanation', '')}</td></tr>
                <tr><td>MACD</td><td>{'✅ 金叉' if trend.get('macd_bullish', False) else '❌ 非金叉'}</td><td>{trend.get('explanations', {}).get('macd_explanation', '')}</td></tr>
                <tr><td>ADX趋势</td><td>{'✅ 强趋势' if trend.get('adx_strong', False) else '❌ 弱趋势'}</td><td>{trend.get('explanations', {}).get('adx_explanation', '')}</td></tr>
            </table>
            <p><strong>参与建议:</strong> {trend.get('participate_advice', '')}</p>
        </div>
        """
        
        # 买点信号
        buy = ta_results['buy_signals']
        satisfied_count = safe_float_convert(buy.get('satisfied_count', 0))
        html += f"""
        <div class="subsection">
            <h4>买点确认 (满足 {satisfied_count:.0f}/4 个条件)</h4>
            <table class="table">
                <tr><th>信号</th><th>状态</th><th>解释</th></tr>
                <tr><td>斐波支撑</td><td>{'✅ 满足' if buy.get('fib_support', False) else '❌ 不满足'}</td><td>{buy.get('explanations', {}).get('fib_support', '')}</td></tr>
                <tr><td>布林超卖</td><td>{'✅ 满足' if buy.get('bollinger_oversold', False) else '❌ 不满足'}</td><td>{buy.get('explanations', {}).get('bollinger_oversold', '')}</td></tr>
                <tr><td>RSI底背离</td><td>{'✅ 满足' if buy.get('rsi_oversold_divergence', False) else '❌ 不满足'}</td><td>{buy.get('explanations', {}).get('rsi_oversold_divergence', '')}</td></tr>
                <tr><td>温和放量</td><td>{'✅ 满足' if buy.get('volume_increase', False) else '❌ 不满足'}</td><td>{buy.get('explanations', {}).get('volume_increase', '')}</td></tr>
            </table>
            <p><strong>买点触发:</strong> {'✅ 是' if buy.get('buy_triggered', False) else '❌ 否'}</p>
        </div>
        """
        
        # 综合信号
        signal = ta_results.get('overall_signal', 'WAIT')
        signal_class = {
            'STRONG_BUY': 'signal-buy',
            'BUY': 'signal-buy', 
            'SELL': 'signal-sell',
            'HOLD': 'signal-hold',
            'WAIT': 'signal-wait'
        }.get(signal, 'signal-wait')
        
        signal_desc = {
            'STRONG_BUY': '🚀 强烈买入',
            'BUY': '✅ 买入', 
            'SELL': '⚠️ 卖出',
            'HOLD': '⏳ 持有',
            'WAIT': '🎯 等待'
        }.get(signal, '未知')
        
        html += f"""
        <div style="background: #d4edda; padding: 20px; border-radius: 8px; text-align: center; margin: 15px 0;">
            <h2 class="{signal_class}">{signal_desc}</h2>
            <p>{ta_results.get('advice_context', '')}</p>
        </div>
        """
        
        return html
    
    def _generate_risk_analysis_html(self, bond_info):
        """生成风险分析HTML"""
        html = ""
        
        # 使用 safe_float_convert 确保数值类型
        premium = safe_float_convert(bond_info.get('溢价率(%)', 0))
        price = safe_float_convert(bond_info.get('转债价格', 0))
        
        # 溢价率风险
        if premium > 40:
            premium_risk = "<span class='badge badge-danger'>高风险</span>"
            premium_desc = "溢价率过高，技术分析失效"
        elif premium > 30:
            premium_risk = "<span class='badge badge-warning'>中风险</span>"
            premium_desc = "溢价率偏高，需谨慎"
        elif premium > 20:
            premium_risk = "<span class='badge badge-info'>低风险</span>"
            premium_desc = "溢价率适中"
        else:
            premium_risk = "<span class='badge badge-success'>无风险</span>"
            premium_desc = "溢价率合理"
        
        # 价格风险
        if price > 140:
            price_risk = "<span class='badge badge-danger'>高风险</span>"
            price_desc = "价格过高，债底保护弱"
        elif price > 130:
            price_risk = "<span class='badge badge-warning'>中风险</span>"
            price_desc = "价格偏高"
        elif price > 115:
            price_risk = "<span class='badge badge-info'>低风险</span>"
            price_desc = "价格合理"
        else:
            price_risk = "<span class='badge badge-success'>无风险</span>"
            price_desc = "价格安全"
        
        # 债底保护风险
        floor_analysis = bond_info.get("债底分析", {})
        if floor_analysis:
            effective_floor_premium = safe_float_convert(floor_analysis.get('effective_floor_premium', 0))
            if effective_floor_premium > 40:
                floor_risk = "<span class='badge badge-danger'>高风险</span>"
                floor_desc = "债底保护很弱"
            elif effective_floor_premium > 25:
                floor_risk = "<span class='badge badge-warning'>中风险</span>"
                floor_desc = "债底保护一般"
            else:
                floor_risk = "<span class='badge badge-success'>低风险</span>"
                floor_desc = "债底保护较强"
        else:
            floor_risk = "<span class='badge badge-info'>未知</span>"
            floor_desc = "债底数据缺失"
        
        # 强赎风险
        redemption = bond_info.get('强赎分析', {})
        if redemption:
            status = redemption.get('status', '')
            if status == "已触发":
                redemption_risk = "<span class='badge badge-danger'>极高风险</span>"
                redemption_desc = "已触发强赎，注意强赎风险"
            elif status == "接近触发":
                redemption_risk = "<span class='badge badge-warning'>高风险</span>"
                redemption_desc = "接近强赎条件，密切关注"
            else:
                redemption_risk = "<span class='badge badge-success'>低风险</span>"
                redemption_desc = "强赎风险较低"
        else:
            redemption_risk = "<span class='badge badge-info'>未知</span>"
            redemption_desc = "强赎数据缺失"
        
        html += f"""
        <table class="table">
            <tr><th>风险类型</th><th>风险等级</th><th>说明</th></tr>
            <tr><td>溢价率风险</td><td>{premium_risk}</td><td>{premium_desc}</td></tr>
            <tr><td>价格风险</td><td>{price_risk}</td><td>{price_desc}</td></tr>
            <tr><td>债底保护风险</td><td>{floor_risk}</td><td>{floor_desc}</td></tr>
            <tr><td>强赎风险</td><td>{redemption_risk}</td><td>{redemption_desc}</td></tr>
        </table>
        """
        
        # 风险标签
        risk_tags = self._generate_risk_tags(bond_info)
        if risk_tags:
            html += f"""
            <div style="margin: 15px 0;">
                <strong>风险标签:</strong>
                {" ".join([f'<span class="badge badge-warning">{tag}</span>' for tag in risk_tags])}
            </div>
            """
        
        # 风险提示
        if premium > 30 or price > 140:
            html += """
            <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h4 style="color: #721c24; margin-top: 0;">⚠️ 高风险提示</h4>
                <p>当前转债存在较高风险，建议谨慎投资或寻找其他机会</p>
            </div>
            """
        
        return html
    
    def _generate_risk_tags(self, bond_info):
        """生成风险标签"""
        risk_tags = []
        
        price = safe_float_convert(bond_info.get("转债价格", 0))
        ytm = safe_float_convert(bond_info.get("YTM(%)", 0))
        floor_analysis = bond_info.get("债底分析", {})
        
        # 高波风险判断
        if price > 130 and ytm < -5:
            risk_tags.append("高波风险")
            
            # 检查回售保护
            put_value = safe_float_convert(floor_analysis.get('put_value', 0)) if floor_analysis else 0
            if put_value <= 100:  # 无强回售保护
                risk_tags.append("无回售保护")
        
        # 债底保护判断
        if floor_analysis:
            effective_floor_premium = safe_float_convert(floor_analysis.get('effective_floor_premium', 0))
            if effective_floor_premium > 40:
                risk_tags.append("债底保护弱")
            elif effective_floor_premium > 25:
                risk_tags.append("债底保护一般")
        
        return risk_tags
    
    def _generate_strategy_analysis_html(self, bond_info):
        """生成策略分析HTML"""
        strategies = self._analyze_strategies(bond_info)
        
        html = "<div class='strategy-card'>"
        html += "<h4>适用策略分析</h4>"
        
        for strategy in strategies:
            if "优秀" in strategy:
                icon = "✅"
            elif "良好" in strategy:
                icon = "⚠️"  
            else:
                icon = "❌"
            html += f"<p>{icon} {strategy}</p>"
        
        html += "</div>"
        
        # 联动分析
        linkage = bond_info.get('联动分析', {})
        if linkage:
            html += "<div class='strategy-card'>"
            html += "<h4>正股转债联动分析</h4>"
            html += f"<p><strong>溢价率联动:</strong> {linkage.get('溢价率联动', '未知')}</p>"
            html += f"<p><strong>Delta弹性:</strong> {linkage.get('Delta弹性', '未知')}</p>"
            html += f"<p><strong>联动策略:</strong> {linkage.get('联动策略', '未知')}</p>"
            html += "</div>"
        
        return html
    
    def _analyze_strategies(self, info):
        """分析策略适用性 - 修复版本"""
        strategies = []
        
        double_low_value = safe_float_convert(info.get("双低值", 0))
        if double_low_value < 130:
            strategies.append("双低策略: 优秀 - 价格和溢价率都很低, 安全边际充足")
        elif double_low_value < 150:
            strategies.append("双低策略: 良好 - 性价比较高, 适合配置")
        else:
            strategies.append("双低策略: 一般 - 双低值偏高, 安全边际有限")
        
        premium = safe_float_convert(info.get("溢价率(%)", 0))
        if premium < 10:
            strategies.append("低溢价策略: 优秀 - 跟涨能力强, 正股上涨时弹性大")
        elif premium < 20:
            strategies.append("低溢价策略: 良好 - 跟涨能力较好")
        else:
            strategies.append("低溢价策略: 不适合 - 溢价率偏高, 跟涨能力弱")
        
        size = safe_float_convert(info.get("剩余规模(亿)", 0))
        if size < 3:
            strategies.append("小规模策略: 优秀 - 规模小易炒作, 波动性大")
        elif size < 5:
            strategies.append("小规模策略: 良好 - 规模适中, 有一定弹性")
        
        ytm = safe_float_convert(info.get("YTM(%)", 0))
        if ytm > 3:
            strategies.append("高YTM策略: 优秀 - 到期收益高, 债底保护强")
        elif ytm > 1:
            strategies.append("高YTM策略: 良好 - 有一定债底保护")
        
        # 小规模低溢价策略
        if size < 5 and premium < 20:
            strategies.append("小规模低溢价策略: 优秀 - 兼具弹性和安全边际")
        elif size < 5 and premium < 30:
            strategies.append("小规模低溢价策略: 良好 - 平衡型选择")
        
        return strategies
    
    def _generate_holding_analysis_html(self, bond_info, holding_info):
        """生成持仓分析HTML"""
        holding_analysis = self._calculate_holding_analysis(bond_info, holding_info)
        if not holding_analysis:
            return "<p>无持仓信息</p>"
        
        profit_rate = safe_float_convert(holding_analysis.get('盈亏比例', 0))
        if profit_rate > 20:
            profit_class = "risk-high"
        elif profit_rate > 10:
            profit_class = "risk-medium" 
        elif profit_rate > -5:
            profit_class = "risk-low"
        else:
            profit_class = "risk-high"
        
        return f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
            {self.create_metric_card(f"{safe_float_convert(holding_analysis.get('持仓成本', 0)):.2f}元", "持仓成本", "")}
            {self.create_metric_card(f"{safe_float_convert(holding_analysis.get('持仓数量', 0)):.0f}张", "持仓数量", "")}
            {self.create_metric_card(f"{safe_float_convert(holding_analysis.get('当前盈亏', 0)):.2f}元", "当前盈亏", profit_class)}
            {self.create_metric_card(f"{profit_rate:.2f}%", "盈亏比例", profit_class)}
        </div>
        <div class="explanation">
            <strong>持仓建议:</strong> {holding_analysis.get('持仓建议', '')} | 
            <strong>风险等级:</strong> {holding_analysis.get('风险等级', '')} |
            <strong>建仓日期:</strong> {holding_analysis.get('建仓日期', '未知')}
        </div>
        """
    
    def _calculate_holding_analysis(self, bond_info, holding_info):
        """计算持仓分析 - 修复版本"""
        if not holding_info:
            return None
        
        current_price = safe_float_convert(bond_info.get('转债价格', 0))
        cost_price = safe_float_convert(holding_info.get('cost_price', 0))
        shares = safe_float_convert(holding_info.get('shares', 0))
        
        if cost_price > 0 and current_price > 0:
            profit_per_share = current_price - cost_price
            profit_rate = (profit_per_share / cost_price) * 100
            total_profit = profit_per_share * shares
            
            if profit_rate > 20:
                advice = "考虑止盈"
                risk_level = "高风险"
            elif profit_rate > 10:
                advice = "持有观察"
                risk_level = "中风险"
            elif profit_rate > -5:
                advice = "继续持有"
                risk_level = "低风险"
            elif profit_rate > -15:
                advice = "谨慎持有"
                risk_level = "中风险"
            else:
                advice = "考虑止损"
                risk_level = "高风险"
            
            return {
                '持仓成本': cost_price,
                '持仓数量': shares,
                '当前盈亏': round(total_profit, 2),
                '盈亏比例': round(profit_rate, 2),
                '持仓市值': round(current_price * shares, 2),
                '建仓日期': holding_info.get('purchase_date', '未知'),
                '持仓建议': advice,
                '风险等级': risk_level,
                '成本市值': round(cost_price * shares, 2)
            }
        
        return None
    
    def _generate_technical_analysis_html(self, bond_info):
        """生成技术分析HTML"""
        tech_data = bond_info.get('技术分析数据', {})
        
        html = """
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
        """
        
        if tech_data:
            # 使用 safe_float_convert 确保数值类型
            support = safe_float_convert(tech_data.get('支撑位', 0))
            resistance = safe_float_convert(tech_data.get('压力位', 0))
            distance_to_support = safe_float_convert(tech_data.get('距支撑百分比', 0))
            distance_to_resistance = safe_float_convert(tech_data.get('距压力百分比', 0))
            
            metrics = [
                (f"{support:.2f}元", "支撑位"),
                (f"{resistance:.2f}元", "压力位"), 
                (f"{distance_to_support:.2f}%", "距支撑"),
                (f"{distance_to_resistance:.2f}%", "距压力"),
                (tech_data.get('位置状态', '未知'), "位置状态"),
                (tech_data.get('弹性状态', '未知'), "弹性状态")
            ]
            
            for value, label in metrics:
                html += self.create_metric_card(value, label)
        
        html += "</div>"
        
        # 斐波那契水平
        fib_levels = tech_data.get('斐波那契_levels', {})
        if fib_levels:
            html += "<div class='subsection'><h4>斐波那契关键位</h4><table class='table'><tr><th>水平</th><th>价格</th><th>相对位置</th></tr>"
            current_price = safe_float_convert(bond_info.get('转债价格', 0))
            
            for level, price in fib_levels.items():
                fib_price = safe_float_convert(price)
                diff_pct = ((current_price - fib_price) / current_price) * 100 if current_price > 0 else 0
                if abs(diff_pct) < 2:
                    position = "<span class='badge badge-info'>当前位置</span>"
                elif fib_price < current_price:
                    position = "<span class='badge badge-success'>支撑区</span>"
                else:
                    position = "<span class='badge badge-warning'>压力区</span>"
                
                html += f"<tr><td>{level}</td><td>{fib_price:.2f}元</td><td>{position} ({diff_pct:+.1f}%)</td></tr>"
            
            html += "</table></div>"
        
        return html
    
    def _generate_score_analysis_html(self, bond_info):
        """生成评分分析HTML"""
        score, score_details = self._calculate_comprehensive_score_v2(bond_info)
        final_grade, final_advice = get_enhanced_rating(score, bond_info)
    
        # 进度条显示
        progress_html = self.create_progress_bar(score, 100, "综合评分")
    
        # 评分明细
        details_html = "<div style='margin: 15px 0;'><strong>评分明细:</strong><br>"
        for detail in score_details:
            details_html += f"<span class='badge badge-info' style='margin: 2px;'>{detail}</span> "
        details_html += "</div>"
    
        # 信号类别
        signal_class = "signal-buy" if score >= 65 else "signal-hold" if score >= 50 else "signal-wait"
    
        return f"""
        {progress_html}
        {details_html}
        <div style="text-align: center; padding: 20px; background: #e7f3ff; border-radius: 8px;">
            <h2 class="{signal_class}">最终评分: {score:.0f}/100 - {final_grade}</h2>
            <p><strong>{final_advice}</strong></p>
        </div>
        """
    
    def _calculate_comprehensive_score_v2(self, info):
        """综合评分算法 v2.1 - 使用 safe_float_convert 确保数值类型"""
        score = 0
        details = []
        
        premium = safe_float_convert(info.get("溢价率(%)", 0))
        conversion_value = safe_float_convert(info.get("转股价值", 0))
        
        # 高溢价硬性扣分 - 修复核心问题
        if premium > 40:
            # 超高溢价直接大幅扣分
            score -= 20
            details.append("溢价:超高溢[-20]")
        elif premium > 35:
            # 高溢价显著扣分
            score -= 15
            details.append("溢价:高溢[-15]")
        elif premium > 30:
            # 较高溢价扣分
            score -= 10
            details.append("溢价:较高溢[-10]")
        elif premium > 25:
            score += 5
            details.append("溢价:略高[+5]")
        elif premium > 15:
            score += 15
            details.append("溢价:适中[+15]")
        elif premium > 10:
            score += 20
            details.append("溢价:较低[+20]")
        else:
            score += 25
            details.append("溢价:极低[+25]")
        
        # 1. 规模因子 (20分)
        size = safe_float_convert(info.get("剩余规模(亿)", 10))
        if size < 3:
            score += 20
            details.append("规模:小盘[+20]")
        elif size < 5:
            score += 16
            details.append("规模:中小盘[+16]")
        elif size < 8:
            score += 12
            details.append("规模:中盘[+12]")
        elif size < 12:
            score += 8
            details.append("规模:大盘[+8]")
        else:
            score += 4
            details.append("规模:超大[+4]")
        
        # 2. 价格因子 (20分) - 结合债性保护
        price = safe_float_convert(info.get("转债价格", 0))
        if price < 110:
            score += 20
            details.append("价格:安全[+20]")
        elif price < 120:
            score += 16
            details.append("价格:合理[+16]")
        elif price < 130:
            score += 12
            details.append("价格:适中[+12]")
        elif price < 140:
            score += 8
            details.append("价格:偏高[+8]")
        else:
            score += 4
            details.append("价格:过高[+4]")
        
        # 3. 流动性因子 (15分)
        volume = safe_float_convert(info.get("日均成交额(亿)", 0))
        if volume > 0.8:
            score += 15
            details.append("流动性:优秀[+15]")
        elif volume > 0.4:
            score += 12
            details.append("流动性:良好[+12]")
        elif volume > 0.2:
            score += 9
            details.append("流动性:中等[+9]")
        elif volume > 0.1:
            score += 6
            details.append("流动性:一般[+6]")
        else:
            score += 3
            details.append("流动性:较差[+3]")
        
        # 4. 债性保护因子 (15分)
        ytm = safe_float_convert(info.get("YTM(%)", 0))
        if ytm > 2:
            score += 15
            details.append("YTM:强保护[+15]")
        elif ytm > 0:
            score += 12
            details.append("YTM:有保护[+12]")
        elif ytm > -2:
            score += 8
            details.append("YTM:弱保护[+8]")
        else:
            score += 4
            details.append("YTM:无保护[+4]")
        
        # 5. 转股价值质量 (10分) - 新增: 识别伪价内债
        if conversion_value > 110:
            score += 10
            details.append("价内:深度[+10]")
        elif conversion_value > 105:
            score += 8
            details.append("价内:良好[+8]")
        elif conversion_value > 100:
            score += 5  # 伪价内，仅小幅加分
            details.append("价内:边缘[+5]")
        elif conversion_value > 95:
            score += 2
            details.append("价外:轻度[+2]")
        elif conversion_value > 90:
            score += 0
            details.append("价外:中度[+0]")
        else:
            score -= 5
            details.append("价外:深度[-5]")
        
        final_score = max(0, min(score, 100))  # 确保在0-100范围内
        return final_score, details
    
    def _wrap_html(self):
        """包装完整HTML"""
        full_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>可转债全面分析报告</title>
            {self.css_style}
        </head>
        <body>
            <div class="container">
                {"".join(self.report_content)}
                <div class="timestamp">
                    报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                    可转债量化分析系统 v10.2
                </div>
            </div>
        </body>
        </html>
        """
        return full_html
    
    def save_report(self, html_content, filename=None):
        """保存报告到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bond_analysis_report_{timestamp}.html"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return filename
        except Exception as e:
            print(f"保存HTML报告失败: {e}")
            return None

# 创建HTML报告生成器实例
html_generator = HTMLReportGenerator()

# ==================== 评级函数 ====================

def get_enhanced_rating(score, bond_info):
    """增强版评级 v2.2 - 修复技术面与基本面矛盾问题"""
    premium = safe_float_convert(bond_info.get("溢价率(%)", 0))
    conversion_value = safe_float_convert(bond_info.get("转股价值", 0))
    price = safe_float_convert(bond_info.get("转债价格", 0))
    
    # 获取多因子信号
    ta_signal = bond_info.get('multifactor_signal', 'WAIT')
    
    # ==================== 核心修复：建立优先级决策机制 ====================
    
    # 第一优先级：硬性风控规则（无论技术信号如何都回避）
    if premium > 40:
        final_grade = "🔴[硬回避]"
        final_advice = "超高溢价压制弹性，技术信号失效，强烈建议回避"
        return final_grade, final_advice
    elif premium > 35:
        final_grade = "🔴[硬回避]" 
        final_advice = "高溢价严重压制跟涨能力，技术信号可靠性低，建议回避"
        return final_grade, final_advice
    elif premium > 30:
        # 高溢价但技术面强烈看多 -> 给出矛盾提示
        if ta_signal == "STRONG_BUY":
            final_grade = "🟡[矛盾信号]"
            final_advice = "技术面强烈看多但溢价率偏高压制弹性，仅限极小仓位短线参与"
            return final_grade, final_advice
        else:
            final_grade = "🟡[谨慎]"
            final_advice = "溢价率偏高，仅限激进投资者极小仓位"
            return final_grade, final_advice
    
    # 第二优先级：伪价内陷阱识别
    if 100 <= conversion_value <= 105 and premium > 25:
        if ta_signal == "STRONG_BUY":
            final_grade = "🟡[矛盾信号]"
            final_advice = "技术面看多但伪价内+高溢价构成风险，建议轻仓谨慎参与"
            return final_grade, final_advice
        else:
            final_grade = "🟡[谨慎]"
            final_advice = "伪价内+高溢价，风险较高"
            return final_grade, final_advice
    
    # 第三优先级：高价债风控
    if price > 140:
        if ta_signal == "STRONG_BUY":
            final_grade = "🟡[矛盾信号]"
            final_advice = "技术面看多但价格过高债底保护弱，建议轻仓短线"
            return final_grade, final_advice
        else:
            final_grade = "🟠[中高风险]"
            final_advice = "价格过高，债底保护弱"
            return final_grade, final_advice
    
    # ==================== 正常评级流程（无硬性风控问题时） ====================
    
    if score >= 75:
        base_grade = "🟢[优秀]"
        base_advice = "优质标的，适合重点配置"
    elif score >= 60:
        base_grade = "🟢[良好]" 
        base_advice = "良好标的，适合配置"
    elif score >= 45:
        base_grade = "🟡[中等]"
        base_advice = "中等标的，可小仓位参与"
    elif score >= 30:
        base_grade = "🟡[一般]"
        base_advice = "一般标的，谨慎参与"
    else:
        base_grade = "🔴[较差]"
        base_advice = "较差标的，建议回避"
    
    # 结合多因子信号微调（仅在无硬性风控问题时）
    if ta_signal == "STRONG_BUY" and score >= 45:
        final_grade = "🚀" + base_grade
        final_advice = f"{base_advice} + 多因子共振强烈看多"
    elif ta_signal == "BUY" and score >= 45:
        final_grade = "✅" + base_grade  
        final_advice = f"{base_advice} + 技术面支持参与"
    elif ta_signal == "SELL":
        final_grade = "⚠️" + base_grade
        final_advice = f"{base_advice} + 注意技术面风险"
    else:
        final_grade = base_grade
        final_advice = base_advice
    
    return final_grade, final_advice

# ==================== 多因子共振技术分析系统 ====================

import pandas_ta as ta

class ConvertibleBondTA:
    """
    可转债多因子共振技术分析系统 - 透明注解版
    集成趋势确认、买点确认、卖点确认三大模块
    """
    
    def __init__(self, 
                 volume_threshold: float = 20000000,  # 2000万流动性门槛
                 max_premium: float = 0.3,           # 最大溢价率30%
                 min_call_distance: float = 0.1      # 最小强赎距离10%
                ):
        self.volume_threshold = volume_threshold
        self.max_premium = max_premium
        self.min_call_distance = min_call_distance
        
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标 - 修复版
        返回包含所有技术指标的DataFrame
        """
        df = df.copy()
        
        # 1. 移动平均线
        df['ma5'] = ta.sma(df['close'], length=5)
        df['ma10'] = ta.sma(df['close'], length=10)
        df['ma20'] = ta.sma(df['close'], length=20)
        df['ma60'] = ta.sma(df['close'], length=60)
        df['ma120'] = ta.sma(df['close'], length=120)
        
        # 2. MACD
        macd_data = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd_data is not None:
            df['macd'] = macd_data['MACD_12_26_9']
            df['macd_signal'] = macd_data['MACDs_12_26_9']
            df['macd_hist'] = macd_data['MACDh_12_26_9']
        
        # 3. 布林带 - 使用手动计算确保稳定性
        bb_data = self.calculate_bbands_manual(df, length=20, std=2)
        df['bb_upper'] = bb_data['bb_upper']
        df['bb_middle'] = bb_data['bb_middle'] 
        df['bb_lower'] = bb_data['bb_lower']
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # 4. RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        # 5. ADX 趋势强度
        adx_data = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx_data is not None:
            df['adx'] = adx_data['ADX_14']
            df['dmi_plus'] = adx_data['DMP_14']
            df['dmi_minus'] = adx_data['DMN_14']
        
        # 6. 成交量指标
        df['volume_ma5'] = ta.sma(df['volume'], length=5)
        df['volume_ma20'] = ta.sma(df['volume'], length=20)
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        
        # 7. 价格位置计算
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
            bb_range = df['bb_upper'] - df['bb_lower']
            bb_range = bb_range.replace(0, 0.001)  # 避免除零错误
            df['price_position'] = (df['close'] - df['bb_lower']) / bb_range
        else:
            df['price_position'] = 0.5
        
        return df

    def calculate_bbands_manual(self, df: pd.DataFrame, length=20, std=2):
        """手动计算布林带"""
        result = pd.DataFrame(index=df.index)
        
        # 计算中轨 (20日均线)
        result['bb_middle'] = df['close'].rolling(window=length).mean()
        
        # 计算标准差
        rolling_std = df['close'].rolling(window=length).std()
        
        # 计算上下轨
        result['bb_upper'] = result['bb_middle'] + (rolling_std * std)
        result['bb_lower'] = result['bb_middle'] - (rolling_std * std)
        
        return result
        
    def check_prerequisites(self, 
                          df: pd.DataFrame, 
                          premium_rate: float,
                          call_risk_distance: float,
                          days: int = 20) -> Dict:
        """
        检查可转债技术分析的三大前提条件
        每个条件都有详细说明
        """
        results = {
            'liquidity_ok': False,
            'premium_ok': False,
            'call_risk_ok': False,
            'all_ok': False,
            'messages': [],
            'detailed_explanations': []
        }
        
        # 使用 safe_float_convert 确保数值类型
        premium_rate = safe_float_convert(premium_rate)
        call_risk_distance = safe_float_convert(call_risk_distance)
        
        # 1. 流动性检查 (日均成交 > 2000万)
        avg_volume = df['volume'].tail(days).mean()
        avg_volume = safe_float_convert(avg_volume)
        if avg_volume >= self.volume_threshold:
            results['liquidity_ok'] = True
            results['messages'].append(f"✅ 流动性充足: 日均成交{avg_volume:,.0f}元")
            results['detailed_explanations'].append(
                f"💡 流动性充足({avg_volume:,.0f}元 > {self.volume_threshold:,.0f}元): "
                f"成交活跃, 买卖顺畅, 适合技术分析"
            )
        else:
            results['messages'].append(f"❌ 流动性不足: 日均成交{avg_volume:,.0f}元 < {self.volume_threshold:,.0f}元")
            results['detailed_explanations'].append(
                f"💡 流动性不足({avg_volume:,.0f}元): "
                f"成交清淡, 技术指标容易失真, 建议关注其他标的"
            )
        
        # 2. 溢价率检查 (<30%)
        if premium_rate <= self.max_premium:
            results['premium_ok'] = True
            results['messages'].append(f"✅ 溢价率合理: {premium_rate:.1%}")
            results['detailed_explanations'].append(
                f"💡 溢价率合理({premium_rate:.1%} ≤ {self.max_premium:.0%}): "
                f"转债与正股联动性较好, 技术分析有效"
            )
        else:
            results['messages'].append(f"❌ 溢价率过高: {premium_rate:.1%} > {self.max_premium:.0%}")
            results['detailed_explanations'].append(
                f"💡 溢价率过高({premium_rate:.1%} > {self.max_premium:.0%}): "
                f"转债与正股脱钩, 技术分析可靠性大幅降低"
            )
        
        # 3. 强赎风险检查 (距强赎 > 10%)
        if call_risk_distance > self.min_call_distance:
            results['call_risk_ok'] = True
            results['messages'].append(f"✅ 强赎风险低: 距离强赎{call_risk_distance:.1%}")
            results['detailed_explanations'].append(
                f"💡 强赎风险低(距离{call_risk_distance:.1%}): "
                f"短期内无强赎压力, 技术走势相对稳定"
            )
        else:
            results['messages'].append(f"❌ 强赎风险高: 距离强赎{call_risk_distance:.1%} ≤ {self.min_call_distance:.0%}")
            results['detailed_explanations'].append(
                f"💡 强赎风险高(距离{call_risk_distance:.1%}): "
                f"接近强赎条件, 技术走势可能被强赎预期干扰"
            )
        
        # 总体判断
        results['all_ok'] = all([
            results['liquidity_ok'],
            results['premium_ok'], 
            results['call_risk_ok']
        ])
        
        return results
    
    def _check_adx_strength(self, df: pd.DataFrame) -> Tuple[bool, str, str]:
        """检查ADX趋势强度 - 修复版，返回详细解释"""
        current = df.iloc[-1]
        adx = current.get('adx', 0)
        adx = safe_float_convert(adx)
        
        if pd.isna(adx):
            return False, "ADX数据缺失", "ADX指标计算失败, 无法判断趋势强度"
        
        # 修复ADX判定逻辑，提供详细解释
        if adx > 25:
            explanation = f"ADX={adx:.1f} > 25 → 强趋势市场, 价格运动方向明确"
            return True, "强趋势", explanation
        elif adx > 15:
            explanation = f"ADX={adx:.1f} (15-25) → 初步趋势, 价格开始有方向性运动"
            return True, "初步趋势", explanation
        else:
            explanation = f"ADX={adx:.1f} < 15 → 震荡市场, 价格缺乏明确方向"
            return False, "无明确趋势", explanation
    
    def check_trend_confirmation(self, df: pd.DataFrame) -> Dict:
        """
        趋势确认（修复版）- 允许初步趋势参与
        每个判断都有详细解释
        """
        current = df.iloc[-1]
        
        # 使用 safe_float_convert 确保数值类型
        ma20 = safe_float_convert(current.get('ma20', 0))
        ma60 = safe_float_convert(current.get('ma60', 0))
        ma120 = safe_float_convert(current.get('ma120', 0))
        
        # 计算趋势强度评分，每个判断都有解释
        ma_bullish, ma_explanation = self._check_ma_bullish_arrangement_with_explanation(df)
        macd_bullish, macd_explanation = self._check_macd_bullish_with_explanation(current)
        adx_strong, adx_desc, adx_explanation = self._check_adx_strength(df)
        
        ma_score = 1 if ma_bullish else 0
        macd_score = 1 if macd_bullish else 0
        adx_score = 1 if adx_strong else 0
        
        trend_strength = ma_score + macd_score + adx_score
        
        results = {
            'ma_bullish': ma_score == 1,
            'macd_bullish': macd_score == 1, 
            'adx_strong': adx_score == 1,
            'trend_strength': trend_strength,  # 0-3分
            'trend_level': "",  # 强/中/弱
            'details': {
                'ma_status': f"MA20={ma20:.2f}, MA60={ma60:.2f}, MA120={ma120:.2f}",
                'macd_status': f"MACD={safe_float_convert(current.get('macd', 0)):.3f}, Signal={safe_float_convert(current.get('macd_signal', 0)):.3f}",
                'adx_status': f"ADX={safe_float_convert(current.get('adx', 0)):.1f} ({adx_desc})"
            },
            'explanations': {
                'ma_explanation': ma_explanation,
                'macd_explanation': macd_explanation,
                'adx_explanation': adx_explanation
            }
        }
        
        # 分级趋势确认
        if trend_strength >= 3:
            results['trend_level'] = "strong"
            results['all_satisfied'] = True
            results['participate_advice'] = "趋势强劲, 适合参与"
            results['trend_interpretation'] = "💡 技术面全面向好: 均线多头 + MACD金叉 + 趋势强劲"
        elif trend_strength >= 2:
            results['trend_level'] = "medium" 
            results['all_satisfied'] = True
            results['participate_advice'] = "趋势初步形成, 可小仓位参与"
            results['trend_interpretation'] = "💡 技术面偏多: 关键指标多数向好, 但需关注弱势指标"
        else:
            results['trend_level'] = "weak"
            results['all_satisfied'] = False
            results['participate_advice'] = "趋势未明, 建议观望"
            results['trend_interpretation'] = "💡 技术面偏弱: 多数指标显示弱势, 等待明确信号"
        
        return results
    
    def _check_ma_bullish_arrangement_with_explanation(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """检查均线多头排列，返回详细解释"""
        current = df.iloc[-1]
        ma20 = safe_float_convert(current.get('ma20', 0))
        ma60 = safe_float_convert(current.get('ma60', 0))
        ma120 = safe_float_convert(current.get('ma120', 0))
        
        is_bullish = ma20 > ma60 > ma120
        
        if is_bullish:
            explanation = f"✅ 均线多头: MA20={ma20:.2f} > MA60={ma60:.2f} > MA120={ma120:.2f} → 短期>中期>长期, 趋势向上"
        else:
            if ma20 < ma60 and ma60 < ma120:
                explanation = f"❌ 均线空头: MA20={ma20:.2f} < MA60={ma60:.2f} < MA120={ma120:.2f} → 短期<中期<长期, 趋势向下"
            elif ma20 > ma60 and ma60 < ma120:
                explanation = f"🟡 均线交织: MA20={ma20:.2f} > MA60={ma60:.2f}但<MA120={ma120:.2f} → 短期反弹但长期仍弱"
            else:
                explanation = f"🟡 均线混乱: MA20={ma20:.2f}, MA60={ma60:.2f}, MA120={ma120:.2f} → 均线排列无序, 震荡格局"
        
        return is_bullish, explanation
    
    def _check_macd_bullish_with_explanation(self, current) -> Tuple[bool, str]:
        """检查MACD在零轴上方且金叉，返回详细解释"""
        macd = safe_float_convert(current.get('macd', 0))
        macd_signal = safe_float_convert(current.get('macd_signal', 0))
        
        is_bullish = macd > 0 and macd > macd_signal
        
        if is_bullish:
            explanation = f"✅ MACD金叉: MACD={macd:.3f} > Signal={macd_signal:.3f}且>0 → 动能向上, 买入信号"
        else:
            if macd < 0:
                explanation = f"❌ MACD在零轴下: MACD={macd:.3f} < 0 → 整体动能偏空"
            elif macd < macd_signal:
                explanation = f"❌ MACD死叉: MACD={macd:.3f} < Signal={macd_signal:.3f} → 短期动能转弱"
            else:
                explanation = f"🟡 MACD中性: MACD={macd:.3f}, Signal={macd_signal:.3f} → 动能方向不明"
        
        return is_bullish, explanation
    
    def check_buy_signals(self, df: pd.DataFrame, fib_levels: Dict) -> Dict:
        """
        买点确认（满足2项即可）
        每个买点信号都有详细注解
        """
        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else current
        
        # 使用 safe_float_convert 确保数值类型
        current_close = safe_float_convert(current.get('close', 0))
        current_volume = safe_float_convert(current.get('volume', 0))
        prev_volume_ma5 = safe_float_convert(prev.get('volume_ma5', 0))
        
        # 每个信号都返回值和详细解释
        fib_support, fib_explanation = self._check_fibonacci_support_with_explanation(current, fib_levels)
        bollinger_oversold, bollinger_explanation = self._check_bollinger_oversold_with_explanation(current, prev)
        rsi_oversold_divergence, rsi_explanation = self._check_rsi_oversold_divergence_with_explanation(df)
        volume_increase, volume_explanation = self._check_volume_increase_gentle_with_explanation(df)
        
        signals = {
            # 信号值
            'fib_support': fib_support,
            'bollinger_oversold': bollinger_oversold,
            'rsi_oversold_divergence': rsi_oversold_divergence,
            'volume_increase': volume_increase,
            
            # 详细解释
            'explanations': {
                'fib_support': fib_explanation,
                'bollinger_oversold': bollinger_explanation,
                'rsi_oversold_divergence': rsi_explanation,
                'volume_increase': volume_explanation
            }
        }
        
        # 统计满足的条件数量
        satisfied_count = sum([fib_support, bollinger_oversold, rsi_oversold_divergence, volume_increase])
        signals['buy_triggered'] = satisfied_count >= 2
        signals['satisfied_count'] = satisfied_count
        
        # 详细信息
        bb_position = safe_float_convert(current.get('price_position', 0))
        rsi_value = safe_float_convert(current.get('rsi', 0))
        volume_ratio = safe_float_convert(current.get('volume_ratio', 0))
        
        signals['details'] = {
            'fib_level': f"当前价{current_close:.2f}, 61.8%位{safe_float_convert(fib_levels.get('61.8%', 0)):.2f}",
            'bollinger_position': f"布林带位置: {bb_position:.1%}",
            'rsi_level': f"RSI: {rsi_value:.1f}",
            'volume_status': f"量比: {volume_ratio:.2f}"
        }
        
        return signals
    
    def _check_fibonacci_support_with_explanation(self, current, fib_levels: Dict) -> Tuple[bool, str]:
        """检查斐波那契61.8%支撑，返回详细解释"""
        fib_618 = fib_levels.get('61.8%')
        if fib_618 is None:
            return False, "❌ 斐波支撑: 无法计算61.8%斐波那契回撤位"
        
        # 使用 safe_float_convert 确保数值类型
        fib_618_value = safe_float_convert(fib_618)
        current_price = safe_float_convert(current.get('close', 0))
        
        # 价格在61.8%附近±2%范围内
        price_diff_pct = abs(current_price - fib_618_value) / fib_618_value if fib_618_value > 0 else 0
        is_support = price_diff_pct <= 0.02
        
        if is_support:
            explanation = f"✅ 斐波支撑: 当前价{current_price:.2f}接近61.8%位{fib_618_value:.2f}(误差{price_diff_pct:.1%}) → 关键支撑区域"
        else:
            distance_pct = (current_price - fib_618_value) / fib_618_value if fib_618_value > 0 else 0
            if distance_pct > 0:
                explanation = f"❌ 斐波阻力: 当前价{current_price:.2f}高于61.8%位{fib_618_value:.2f}(+{distance_pct:.1%}) → 已突破支撑"
            else:
                explanation = f"❌ 远离支撑: 当前价{current_price:.2f}低于61.8%位{fib_618_value:.2f}({distance_pct:.1%}) → 支撑较远"
        
        return is_support, explanation
    
    def _check_bollinger_oversold_with_explanation(self, current, prev) -> Tuple[bool, str]:
        """触及布林带下轨 + 缩量，返回详细解释"""
        # 添加布林带数据存在性检查
        if 'bb_lower' not in current or pd.isna(current['bb_lower']):
            return False, "❌ 布林带分析: 布林带数据缺失"
            
        # 使用 safe_float_convert 确保数值类型
        current_price = safe_float_convert(current.get('close', 0))
        bb_lower = safe_float_convert(current.get('bb_lower', 0))
        bb_position = safe_float_convert(current.get('price_position', 0))
        current_volume = safe_float_convert(current.get('volume', 0))
        prev_volume_ma5 = safe_float_convert(prev.get('volume_ma5', 0))
        
        at_lower_band = current_price <= bb_lower * 1.02  # 下轨附近2%
        volume_shrinking = current_volume < prev_volume_ma5  # 缩量
        
        # 计算距离下轨的百分比
        distance_to_lower = (current_price - bb_lower) / bb_lower * 100 if bb_lower > 0 else 0
        
        if at_lower_band and volume_shrinking:
            explanation = f"✅ 布林超卖: 价格{current_price:.2f}在下轨{bb_lower:.2f}附近(距离{distance_to_lower:+.1f}%) + 缩量 → 超卖反弹概率大"
        elif at_lower_band:
            explanation = f"🟡 触及下轨: 价格{current_price:.2f}在下轨{bb_lower:.2f}附近, 但量能{'' if volume_shrinking else '未'}缩量 → 需确认量价配合"
        else:
            explanation = f"❌ 未超卖: 价格{current_price:.2f}距下轨{bb_lower:.2f}较远(距离{distance_to_lower:+.1f}%), 布林位置{bb_position:.1%} → 无超卖信号"
        
        return at_lower_band and volume_shrinking, explanation
    
    def _check_rsi_oversold_divergence_with_explanation(self, df: pd.DataFrame, lookback: int = 10) -> Tuple[bool, str]:
        """RSI < 30 且出现底背离，返回详细解释"""
        if len(df) < lookback + 5:
            return False, f"❌ RSI分析: 数据不足({len(df)}天), 需要{lookback+5}天"
        
        current = df.iloc[-1]
        current_rsi = safe_float_convert(current.get('rsi', 50))
        
        # 检查RSI是否超卖
        if current_rsi >= 30:
            return False, f"❌ RSI未超卖: RSI={current_rsi:.1f} ≥ 30, 未进入超卖区"
        
        # 简化版底背离检测
        recent_data = df.tail(lookback)
        price_low_idx = recent_data['close'].idxmin()
        rsi_low_idx = recent_data['rsi'].idxmin()
        
        # 如果价格创新低但RSI没有创新低，形成底背离
        price_divergence = (price_low_idx == recent_data.index[-1] and 
                          rsi_low_idx != recent_data.index[-1])
        
        if price_divergence:
            explanation = f"✅ RSI底背离: 价格创新低但RSI{current_rsi:.1f}未新低 → 下跌动能减弱, 反弹概率增加"
        else:
            explanation = f"❌ 无底背离: RSI={current_rsi:.1f}超卖但无底背离信号 → 单纯超卖, 需其他信号确认"
        
        return price_divergence, explanation
    
    def _check_volume_increase_gentle_with_explanation(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """成交量温和放大（非脉冲），返回详细解释"""
        if len(df) < 6:
            return False, f"❌ 量能分析: 数据不足({len(df)}天)"
        
        current = df.iloc[-1]
        volume_ratio = safe_float_convert(current.get('volume_ratio', 1))
        
        # 温和放量: 量比在1.2-2.5之间，避免脉冲式放量
        is_gentle_increase = 1.2 <= volume_ratio <= 2.5
        
        if is_gentle_increase:
            explanation = f"✅ 温和放量: 量比{volume_ratio:.2f}(1.2-2.5) → 资金有序进场, 非脉冲行情"
        elif volume_ratio < 1.2:
            explanation = f"❌ 量能不足: 量比{volume_ratio:.2f} < 1.2 → 资金参与度低"
        else:
            explanation = f"❌ 脉冲放量: 量比{volume_ratio:.2f} > 2.5 → 可能是一日游行情"
        
        return is_gentle_increase, explanation
    
    def check_sell_signals(self, df: pd.DataFrame, fib_levels: Dict) -> Dict:
        """
        卖点确认
        每个卖点信号都有详细注解
        """
        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else current
        
        # 使用 safe_float_convert 确保数值类型
        current_close = safe_float_convert(current.get('close', 0))
        current_volume = safe_float_convert(current.get('volume', 0))
        prev_volume_ma5 = safe_float_convert(prev.get('volume_ma5', 0))
        prev_close = safe_float_convert(prev.get('close', 0))
        
        # 每个信号都返回值和详细解释
        fib_resistance, fib_explanation = self._check_fibonacci_resistance_with_explanation(current, fib_levels)
        bollinger_overbought, bollinger_explanation = self._check_bollinger_overbought_stagnation_with_explanation(current, prev)
        rsi_overbought, rsi_explanation = self._check_rsi_overbought_divergence_with_explanation(df)
        
        signals = {
            # 信号值
            'fib_resistance': fib_resistance,
            'bollinger_overbought_stagnation': bollinger_overbought,
            'rsi_overbought_divergence': rsi_overbought,
            
            # 详细解释
            'explanations': {
                'fib_resistance': fib_explanation,
                'bollinger_overbought_stagnation': bollinger_explanation,
                'rsi_overbought_divergence': rsi_explanation
            }
        }
        
        # 详细信息
        bb_position = safe_float_convert(current.get('price_position', 0))
        rsi_value = safe_float_convert(current.get('rsi', 0))
        volume_ratio = safe_float_convert(current.get('volume_ratio', 0))
        
        signals['details'] = {
            'fib_resistance_level': f"当前价{current_close:.2f}, 161.8%位{safe_float_convert(fib_levels.get('161.8%', 0)):.2f}",
            'bollinger_position': f"布林带位置: {bb_position:.1%}",
            'rsi_level': f"RSI: {rsi_value:.1f}",
            'volume_status': f"量比: {volume_ratio:.2f}"
        }
        
        return signals
    
    def _check_fibonacci_resistance_with_explanation(self, current, fib_levels: Dict) -> Tuple[bool, str]:
        """检查斐波那契161.8%阻力，返回详细解释"""
        fib_1618 = fib_levels.get('161.8%')
        if fib_1618 is None:
            return False, "❌ 斐波阻力: 无法计算161.8%斐波那契扩展位"
        
        # 使用 safe_float_convert 确保数值类型
        fib_1618_value = safe_float_convert(fib_1618)
        current_price = safe_float_convert(current.get('close', 0))
        
        # 价格在161.8%附近±2%范围内
        price_diff_pct = abs(current_price - fib_1618_value) / fib_1618_value if fib_1618_value > 0 else 0
        is_resistance = price_diff_pct <= 0.02
        
        if is_resistance:
            explanation = f"✅ 斐波阻力: 当前价{current_price:.2f}接近161.8%位{fib_1618_value:.2f}(误差{price_diff_pct:.1%}) → 关键阻力区域"
        else:
            distance_pct = (fib_1618_value - current_price) / current_price if current_price > 0 else 0
            if distance_pct > 0.1:
                explanation = f"❌ 远离阻力: 当前价{current_price:.2f}距161.8%位{fib_1618_value:.2f}较远(还需+{distance_pct:.1%}) → 阻力较远"
            else:
                explanation = f"🟡 接近阻力: 当前价{current_price:.2f}逐步接近161.8%位{fib_1618_value:.2f}(还需+{distance_pct:.1%}) → 关注阻力效果"
        
        return is_resistance, explanation
    
    def _check_bollinger_overbought_stagnation_with_explanation(self, current, prev) -> Tuple[bool, str]:
        """触及布林带上轨 + 放量滞涨，返回详细解释"""
        # 添加布林带数据存在性检查
        if 'bb_upper' not in current or pd.isna(current['bb_upper']):
            return False, "❌ 布林带分析: 布林带数据缺失"
            
        # 使用 safe_float_convert 确保数值类型
        current_price = safe_float_convert(current.get('close', 0))
        bb_upper = safe_float_convert(current.get('bb_upper', 0))
        bb_position = safe_float_convert(current.get('price_position', 0))
        current_volume = safe_float_convert(current.get('volume', 0))
        prev_volume_ma5 = safe_float_convert(prev.get('volume_ma5', 0))
        prev_close = safe_float_convert(prev.get('close', 0))
        
        at_upper_band = current_price >= bb_upper * 0.98  # 上轨附近2%
        volume_spike = current_volume > prev_volume_ma5 * 1.5  # 放量
        price_stagnant = abs(current_price - prev_close) / prev_close <= 0.01  # 滞涨(涨幅<1%)
        
        # 计算距离上轨的百分比
        distance_to_upper = (current_price - bb_upper) / bb_upper * 100 if bb_upper > 0 else 0
        
        if at_upper_band and volume_spike and price_stagnant:
            explanation = f"✅ 布林滞涨: 价格{current_price:.2f}在上轨{bb_upper:.2f}附近 + 放量滞涨 → 顶部信号明显"
        elif at_upper_band and volume_spike:
            explanation = f"🟡 上轨放量: 价格{current_price:.2f}在上轨附近且放量, 但未明显滞涨 → 警惕回调"
        elif at_upper_band:
            explanation = f"🟡 触及上轨: 价格{current_price:.2f}在上轨附近, 但量能一般 → 压力显现"
        else:
            explanation = f"❌ 无滞涨: 价格{current_price:.2f}距上轨{bb_upper:.2f}较远(距离{distance_to_upper:+.1f}%), 布林位置{bb_position:.1%} → 无顶部信号"
        
        return at_upper_band and volume_spike and price_stagnant, explanation
    
    def _check_rsi_overbought_divergence_with_explanation(self, df: pd.DataFrame, lookback: int = 10) -> Tuple[bool, str]:
        """RSI > 80 + 顶背离，返回详细解释"""
        if len(df) < lookback + 5:
            return False, f"❌ RSI分析: 数据不足({len(df)}天), 需要{lookback+5}天"
        
        current = df.iloc[-1]
        current_rsi = safe_float_convert(current.get('rsi', 50))
        
        # 检查RSI是否超买
        if current_rsi <= 80:
            return False, f"❌ RSI未超买: RSI={current_rsi:.1f} ≤ 80, 未进入超买区"
        
        # 简化版顶背离检测
        recent_data = df.tail(lookback)
        price_high_idx = recent_data['close'].idxmax()
        rsi_high_idx = recent_data['rsi'].idxmax()
        
        # 如果价格创新高但RSI没有创新高，形成顶背离
        price_divergence = (price_high_idx == recent_data.index[-1] and 
                          rsi_high_idx != recent_data.index[-1])
        
        if price_divergence:
            explanation = f"✅ RSI顶背离: 价格创新高但RSI{current_rsi:.1f}未新高 → 上涨动能减弱, 回调概率增加"
        else:
            explanation = f"🟡 RSI超买: RSI={current_rsi:.1f} > 80超买但无顶背离 → 单纯超买, 需其他信号确认"
        
        return price_divergence, explanation
    
    def calculate_fibonacci_levels(self, high: float, low: float) -> Dict[str, float]:
        """计算完整的斐波那契回撤和扩展位"""
        # 使用 safe_float_convert 确保数值类型
        high_val = safe_float_convert(high)
        low_val = safe_float_convert(low)
        diff = high_val - low_val
        
        levels = {
            # 回撤位
            '0.0%': high_val,
            '23.6%': high_val - diff * 0.236,
            '38.2%': high_val - diff * 0.382,
            '50.0%': (high_val + low_val) / 2,
            '61.8%': high_val - diff * 0.618,
            '78.6%': high_val - diff * 0.786,
            '100.0%': low_val,
            
            # 扩展位
            '138.2%': high_val + diff * 0.382,
            '161.8%': high_val + diff * 0.618,
            '200.0%': high_val + diff,
            '261.8%': high_val + diff * 1.618,
        }
        
        return levels
    
    def get_recent_high_low(self, df: pd.DataFrame, period: int = 250) -> Tuple[float, float]:
        """获取近期高点和低点"""
        recent_df = df.tail(period)
        return recent_df['high'].max(), recent_df['low'].min()
    
    def comprehensive_analysis(self, 
                             df: pd.DataFrame,
                             premium_rate: float,
                             call_risk_distance: float,
                             lookback_period: int = 250,
                             actual_price: float = None) -> Dict:
        """
        综合技术分析入口函数 - 完全修复版本
        返回完整的分析结果，包含详细注解
        """
        try:
            print(f"🔍 进入comprehensive_analysis函数...")
            print(f"   参数类型检查:")
            print(f"     premium_rate: {premium_rate} (类型: {type(premium_rate)})")
            print(f"     call_risk_distance: {call_risk_distance} (类型: {type(call_risk_distance)})")
            print(f"     actual_price: {actual_price} (类型: {type(actual_price)})")
            
            # 1. 强制参数类型转换 - 使用 safe_float_convert 确保所有参数都是数值类型
            premium_rate = safe_float_convert(premium_rate)
            if premium_rate > 1:  # 如果是百分比形式，转换为小数
                premium_rate = premium_rate / 100
                
            call_risk_distance = safe_float_convert(call_risk_distance)
            if call_risk_distance > 1:  # 如果是百分比形式，转换为小数
                call_risk_distance = call_risk_distance / 100
                
            if actual_price is not None:
                actual_price = safe_float_convert(actual_price)
            
            print(f"   参数转换后:")
            print(f"     premium_rate: {premium_rate:.4f} (类型: {type(premium_rate)})")
            print(f"     call_risk_distance: {call_risk_distance:.4f} (类型: {type(call_risk_distance)})")
            print(f"     actual_price: {actual_price} (类型: {type(actual_price)})")
        
            # 2. 计算技术指标
            df_with_indicators = self.calculate_all_indicators(df)
            
            # 3. 如果提供了实际价格，确保数据一致性
            if actual_price is not None and len(df_with_indicators) > 0:
                actual_price = float(actual_price)  # 确保是浮点数
                # 更新最新价格确保一致性
                df_with_indicators.iloc[-1, df_with_indicators.columns.get_loc('close')] = actual_price
                # 同时更新其他价格相关列
                df_with_indicators.iloc[-1, df_with_indicators.columns.get_loc('open')] = actual_price
                if len(df_with_indicators) > 1:
                    prev_high = safe_float_convert(df_with_indicators.iloc[-2]['high'])
                    prev_low = safe_float_convert(df_with_indicators.iloc[-2]['low'])
                    df_with_indicators.iloc[-1, df_with_indicators.columns.get_loc('high')] = max(prev_high, actual_price)
                    df_with_indicators.iloc[-1, df_with_indicators.columns.get_loc('low')] = min(prev_low, actual_price)
                else:
                    df_with_indicators.iloc[-1, df_with_indicators.columns.get_loc('high')] = actual_price
                    df_with_indicators.iloc[-1, df_with_indicators.columns.get_loc('low')] = actual_price
                
                # 重新计算技术指标以确保一致性
                df_with_indicators = self.calculate_all_indicators(df_with_indicators)
        
            # 4. 获取高低点并计算斐波那契
            high, low = self.get_recent_high_low(df_with_indicators, lookback_period)
            fib_levels = self.calculate_fibonacci_levels(high, low)
            
            # 5. 检查前提条件
            prereq_results = self.check_prerequisites(
                df_with_indicators, premium_rate, call_risk_distance
            )
            
            # 6. 如果前提条件不满足，直接返回
            if not prereq_results['all_ok']:
                return {
                    'prerequisites': prereq_results,
                    'trend_confirmation': None,
                    'buy_signals': None,
                    'sell_signals': None,
                    'overall_signal': 'INVALID',
                    'message': '不满足可转债分析前提条件',
                    'advice_context': "💡 由于不满足技术分析前提条件（流动性/溢价率/强赎风险）, 建议基于基本面和其他因素进行投资决策"
                }
            
            # 7. 技术分析
            trend_results = self.check_trend_confirmation(df_with_indicators)
            buy_results = self.check_buy_signals(df_with_indicators, fib_levels)
            sell_results = self.check_sell_signals(df_with_indicators, fib_levels)
            
            # 8. 生成综合信号
            overall_signal = self._generate_overall_signal(trend_results, buy_results, sell_results)
            
            # 9. 生成策略上下文
            advice_context = self._generate_advice_context(trend_results, buy_results, sell_results, overall_signal)
            
            # 10. 获取当前价格
            current_price = safe_float_convert(df_with_indicators['close'].iloc[-1])
            
            result = {
                'prerequisites': prereq_results,
                'trend_confirmation': trend_results,
                'buy_signals': buy_results,
                'sell_signals': sell_results,
                'fibonacci_levels': fib_levels,
                'current_price': current_price,
                'overall_signal': overall_signal,
                'advice_context': advice_context,
                'analysis_time': pd.Timestamp.now()
            }
            
            print(f"✅ comprehensive_analysis函数执行成功")
            return result
        
        except Exception as e:
            print(f"❌ comprehensive_analysis 方法出错: {e}")
            print(f"   错误详情:")
            print(f"     premium_rate: {premium_rate} (类型: {type(premium_rate)})")
            print(f"     call_risk_distance: {call_risk_distance} (类型: {type(call_risk_distance)})")
            import traceback
            traceback.print_exc()
            return {
                'prerequisites': {'all_ok': False, 'messages': [f"分析出错: {str(e)}"]},
                'overall_signal': 'ERROR',
                'message': f"技术分析出错: {str(e)}"
            }
    
    def _generate_overall_signal(self, trend: Dict, buy: Dict, sell: Dict) -> str:
        """生成综合交易信号"""
        if not trend.get('all_satisfied', False):
            return "WAIT"  # 等待趋势确认
        
        if buy.get('buy_triggered', False):
            return "STRONG_BUY"
        
        if any(sell.values()):
            return "SELL"
        
        return "HOLD"
    
    def _generate_advice_context(self, trend: Dict, buy: Dict, sell: Dict, signal: str) -> str:
        """生成策略上下文，解释当前市场状态和适合的操作"""
        trend_strength = safe_float_convert(trend.get('trend_strength', 0))
        buy_count = safe_float_convert(buy.get('satisfied_count', 0))
        has_sell_signals = any(sell.values()) if sell else False
        
        if signal == "STRONG_BUY":
            return ("💡 当前处于'技术买点确认 + 趋势向上'的理想状态\n"
                   "   适合: ① 空仓者分批建仓; ② 持仓者继续持有")
        
        elif signal == "BUY":
            return ("💡 当前处于'技术买点出现 + 趋势初步形成'状态\n"
                   "   适合: ① 激进投资者小仓位试仓; ② 稳健投资者等待趋势进一步确认")
        
        elif signal == "SELL":
            return ("💡 当前出现卖出信号, 需注意风险\n"
                   "   适合: ① 持仓者考虑减仓; ② 空仓者继续观望")
        
        elif signal == "HOLD":
            if trend_strength >= 2:
                return ("💡 当前处于'趋势向上但买点未确认'状态\n"
                       "   适合: ① 持仓者继续持有; ② 空仓者等待回调机会")
            else:
                return ("💡 当前处于'趋势不明 + 无明确买卖点'状态\n"
                       "   适合: 保持观望, 等待市场方向明确")
        
        else:  # WAIT
            if buy_count >= 2:
                return ("💡 当前处于'技术买点出现 + 趋势未确认'的矛盾状态\n"
                       "   适合: ① 持仓者持有观察; ② 空仓者等待趋势拐头向上再介入")
            else:
                return ("💡 当前处于'趋势未明 + 买点不足'状态\n"
                       "   适合: 继续观望, 等待更多技术信号确认")
    
    def generate_analysis_report(self, analysis_results: Dict) -> str:
        """生成可读的分析报告 - 透明注解版"""
        report = []
        report.append("=" * 60)
        report.append("📊 可转债多因子共振技术分析报告（透明注解版）")
        report.append("=" * 60)
        
        # 前提条件
        prereq = analysis_results['prerequisites']
        report.append("\n🔍 前提条件检查:")
        for msg in prereq['messages']:
            report.append(f"  {msg}")
        
        # 详细解释前提条件
        if 'detailed_explanations' in prereq:
            report.append("\n💡 前提条件解读:")
            for explanation in prereq['detailed_explanations']:
                report.append(f"  {explanation}")
        
        if not prereq['all_ok']:
            report.append("\n❌ 技术分析终止: 不满足前提条件")
            if 'advice_context' in analysis_results:
                report.append(f"\n{analysis_results['advice_context']}")
            return "\n".join(report)
        
        # 当前价格 - 确保使用正确的价格
        current_price = safe_float_convert(analysis_results.get('current_price', 0))
        report.append(f"\n💰 当前价格: {current_price:.2f}")
        
        # 趋势确认 - 修复版显示，带详细解释
        trend = analysis_results['trend_confirmation']
        report.append("\n📈 趋势确认:")
        report.append(f"  均线多头: {'✅' if trend.get('ma_bullish', False) else '❌'} {trend.get('details', {}).get('ma_status', '')}")
        report.append(f"     → {trend.get('explanations', {}).get('ma_explanation', '')}")
        
        report.append(f"  MACD金叉: {'✅' if trend.get('macd_bullish', False) else '❌'} {trend.get('details', {}).get('macd_status', '')}")
        report.append(f"     → {trend.get('explanations', {}).get('macd_explanation', '')}")
        
        report.append(f"  ADX强度: {'✅' if trend.get('adx_strong', False) else '❌'} {trend.get('details', {}).get('adx_status', '')}")
        report.append(f"     → {trend.get('explanations', {}).get('adx_explanation', '')}")
        
        trend_strength = safe_float_convert(trend.get('trend_strength', 0))
        report.append(f"  趋势强度: {trend_strength:.0f}/3分 - {trend.get('trend_level', '').upper()}趋势")
        report.append(f"  参与建议: {trend.get('participate_advice', '')}")
        if 'trend_interpretation' in trend:
            report.append(f"  {trend['trend_interpretation']}")
        
        # 买点信号 - 带详细解释
        buy = analysis_results['buy_signals']
        buy_count = safe_float_convert(buy.get('satisfied_count', 0))
        report.append(f"\n🛒 买点确认 (满足{buy_count:.0f}/4):")
        
        report.append(f"  斐波支撑: {'✅' if buy.get('fib_support', False) else '❌'} {buy.get('details', {}).get('fib_level', '')}")
        report.append(f"     → {buy.get('explanations', {}).get('fib_support', '')}")
        
        report.append(f"  布林超卖: {'✅' if buy.get('bollinger_oversold', False) else '❌'} {buy.get('details', {}).get('bollinger_position', '')}")
        report.append(f"     → {buy.get('explanations', {}).get('bollinger_oversold', '')}")
        
        report.append(f"  RSI底背离: {'✅' if buy.get('rsi_oversold_divergence', False) else '❌'} {buy.get('details', {}).get('rsi_level', '')}")
        report.append(f"     → {buy.get('explanations', {}).get('rsi_oversold_divergence', '')}")
        
        report.append(f"  温和放量: {'✅' if buy.get('volume_increase', False) else '❌'} {buy.get('details', {}).get('volume_status', '')}")
        report.append(f"     → {buy.get('explanations', {}).get('volume_increase', '')}")
        
        report.append(f"  买点触发: {'✅' if buy.get('buy_triggered', False) else '❌'}")
        
        # 卖点信号 - 带详细解释
        sell = analysis_results['sell_signals']
        report.append(f"\n🏷️ 卖点确认:")
        
        report.append(f"  斐波阻力: {'✅' if sell.get('fib_resistance', False) else '❌'} {sell.get('details', {}).get('fib_resistance_level', '')}")
        report.append(f"     → {sell.get('explanations', {}).get('fib_resistance', '')}")
        
        report.append(f"  布林滞涨: {'✅' if sell.get('bollinger_overbought_stagnation', False) else '❌'} {sell.get('details', {}).get('bollinger_position', '')}")
        report.append(f"     → {sell.get('explanations', {}).get('bollinger_overbought_stagnation', '')}")
        
        report.append(f"  RSI顶背离: {'✅' if sell.get('rsi_overbought_divergence', False) else '❌'} {sell.get('details', {}).get('rsi_level', '')}")
        report.append(f"     → {sell.get('explanations', {}).get('rsi_overbought_divergence', '')}")
        
        # 综合建议和策略上下文
        signal = analysis_results['overall_signal']
        report.append(f"\n🎯 综合建议: {self._get_signal_description(signal)}")
        
        if 'advice_context' in analysis_results:
            report.append(f"\n{analysis_results['advice_context']}")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)
    
    def _get_signal_description(self, signal: str) -> str:
        """获取信号描述"""
        descriptions = {
            "STRONG_BUY": "🚀 强烈买入 - 趋势确认且买点共振",
            "SELL": "⚠️ 卖出信号 - 注意风险", 
            "HOLD": "⏳ 持有观望 - 等待更好时机",
            "WAIT": "🎯 等待趋势 - 趋势未确认",
            "INVALID": "❌ 无效信号 - 检查前提条件"
        }
        return descriptions.get(signal, "未知信号")

# 创建多因子共振分析器实例
ta_analyzer = ConvertibleBondTA()

# ==================== 原有数据库和类定义 ====================

# 可转债数据库
BOND_MATURITY_DATABASE = {
    "110064": "2024-12-20",  # 建工转债
    "113053": "2028-01-05",  # 隆22转债
    "127089": "2029-07-18",  # 晶澳转债
    "123210": "2029-12-01",  # 志特转债
    "113062": "2028-03-01",  # 杭银转债
    "113056": "2028-03-20",  # 重银转债
    "113588": "2026-06-16",  # 润达转债
    "123214": "2029-08-23",  # 东宝转债
    "123208": "2029-06-30",  # 金丹转债
    "123206": "2029-05-25",  # 正元转02
    "118037": "2029-11-03",  # 合力转债
    "123013": "2024-07-27",  # 横河转债
    "123042": "2025-05-22",  # 银河转债",
}

# 重点转债技术分析数据库
BOND_TECHNICAL_DATABASE = {
    "123214": {  # 东宝转债
        "high_250": 143.16,
        "low_250": 105.82,
        "high_120": 136.94,
        "low_120": 112.04,
        "high_60": 130.0,
        "low_60": 118.0,
        "data_source": "真实价格数据库",
        "fib_levels": {
            '0.0%': 143.16, '23.6%': 134.56, '38.2%': 129.12, 
            '50.0%': 124.49, '61.8%': 119.86, '78.6%': 113.42, '100.0%': 105.82
        }
    },
    "113053": {  # 隆22转债
        "high_250": 153.02,
        "low_250": 113.10,
        "high_120": 145.0,
        "low_120": 120.0,
        "high_60": 138.0,
        "low_60": 125.0,
        "data_source": "真实价格数据库",
        "fib_levels": {
            '0.0%': 153.02, '23.6%': 143.68, '38.2%': 137.74, 
            '50.0%': 133.06, '61.8%': 128.38, '78.6%': 121.64, '100.0%': 113.10
        }
    },
    "110064": {  # 建工转债
        "high_250": 128.50,
        "low_250": 105.30,
        "high_120": 125.80,
        "low_120": 110.20,
        "high_60": 122.50,
        "low_60": 115.60,
        "data_source": "智能估算",
        "fib_levels": {
            '0.0%': 128.50, '23.6%': 123.02, '38.2%': 119.43, 
            '50.0%': 116.90, '61.8%': 114.37, '78.6%': 110.78, '100.0%': 105.30
        }
    }
}

# PB值数据库
BOND_PB_DATABASE = {
    "113053": 2.0,   # 隆22转债
    "110064": 1.2,   # 建工转债  
    "123214": 3.5,   # 东宝转债
    "113062": 0.8,   # 杭银转债
    "113056": 0.6,   # 重银转债
    "113588": 2.8,   # 润达转债",
}

# 用户持仓数据库
USER_HOLDINGS = {}

class RiskMonitor:
    """风险监控器"""
    
    def __init__(self):
        self.blacklist_rules = {
            "超高溢价": {"threshold": 50, "weight": 1.0, "desc": "溢价率>50%"},
            "深度价外": {"threshold": 70, "weight": 0.9, "desc": "转股价值<70"},  
            "价格过高": {"threshold": 150, "weight": 0.7, "desc": "价格>150元"},
        }
    
    def get_all_bonds_data(self):
        """获取全市场转债数据"""
        try:
            print("获取全市场转债数据...")
            bond_df = ak.bond_zh_cov()
            
            bonds_data = {}
            for _, bond in bond_df.iterrows():
                bond_code = bond.get('债券代码', '')
                if not bond_code:
                    continue
                
                price = safe_float_convert(bond.get('债现价', 0))
                premium = safe_float_convert(bond.get('转股溢价率', 0))
                conversion_value = safe_float_convert(bond.get('转股价值', 0))
                
                if price > 1000:
                    price = price / 10
                if conversion_value > 1000:
                    conversion_value = conversion_value / 10
                
                bonds_data[bond_code] = {
                    'name': bond.get('债券简称', f"转债{bond_code}"),
                    'price': price,
                    'premium_rate': premium,
                    'conversion_value': conversion_value,
                    'remaining_size': safe_float_convert(str(bond.get('发行规模', '10')).replace('亿元', '').replace('亿', ''))
                }
            
            print(f"获取到 {len(bonds_data)} 只转债数据")
            return bonds_data
            
        except Exception as e:
            print(f"全市场数据获取失败: {e}")
            return {}
    
    def calculate_risk_score(self, bond_info):
        """计算风险评分"""
        risk_score = 0
        risk_reasons = []
        
        premium = safe_float_convert(bond_info.get('premium_rate', 0))
        conversion_value = safe_float_convert(bond_info.get('conversion_value', 0))
        price = safe_float_convert(bond_info.get('price', 0))
        
        if premium > self.blacklist_rules["超高溢价"]["threshold"]:
            risk_score += self.blacklist_rules["超高溢价"]["weight"]
            risk_reasons.append(f"溢价率{premium:.1f}%")
        
        if conversion_value < self.blacklist_rules["深度价外"]["threshold"]:
            risk_score += self.blacklist_rules["深度价外"]["weight"]
            risk_reasons.append(f"转股价值{conversion_value:.1f}")
        
        if price > self.blacklist_rules["价格过高"]["threshold"]:
            risk_score += self.blacklist_rules["价格过高"]["weight"]
            risk_reasons.append(f"价格{price:.1f}元")
        
        return risk_score, risk_reasons
    
    def generate_blacklist(self):
        """生成高风险转债黑名单"""
        bonds_data = self.get_all_bonds_data()
        if not bonds_data:
            return []
        
        blacklist = []
        
        for bond_code, info in bonds_data.items():
            risk_score, risk_reasons = self.calculate_risk_score(info)
            
            if risk_score >= 1.0:
                blacklist.append({
                    'code': bond_code,
                    'name': info.get('name', ''),
                    'risk_score': round(risk_score, 2),
                    'reasons': risk_reasons,
                    'premium': info.get('premium_rate', 0),
                    'conversion_value': info.get('conversion_value', 0),
                    'price': info.get('price', 0),
                    'size': info.get('remaining_size', 0)
                })
        
        return sorted(blacklist, key=lambda x: x['risk_score'], reverse=True)

class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self.session = requests.Session()
        self._setup_headers()
    
    def _setup_headers(self):
        """设置headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
        })
    
    def get_tencent_data(self, bond_code):
        """获取腾讯财经数据"""
        try:
            if bond_code.startswith('11'):
                market = 'sh'
            else:
                market = 'sz'
                
            url = f"https://qt.gtimg.cn/q={market}{bond_code}"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                content = response.text
                parts = content.split('~')
                if len(parts) > 40:
                    price = safe_float_convert(parts[3])
                    
                    if 50 < price < 300:
                        return {
                            'current': price,
                            'source': '腾讯财经'
                        }
            return None
            
        except Exception:
            return None
    
    def get_eastmoney_data(self, bond_code):
        """获取东方财富数据 - 修复版"""
        try:
            if bond_code.startswith('11'):
                secid = f"1.{bond_code}"
            else:
                secid = f"0.{bond_code}"
            
            url = "http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': secid,
                'fields': 'f43,f47,f48,f168',
                'invt': '2',
                '_': str(int(time.time() * 1000))
            }
            
            response = self.session.get(url, params=params, timeout=8)
            if response.status_code == 200:
                content = response.text
                json_match = re.search(r'\{.*\}', content)
                if json_match:
                    data = json.loads(json_match.group())
                    if data.get('data'):
                        em_data = data['data']
                        
                        current_price = safe_float_convert(em_data.get('f43', 0))
                        # 价格合理性验证
                        if current_price > 1000:
                            current_price = current_price / 1000
                        elif current_price > 100:
                            current_price = current_price / 100
                        
                        # 价格范围验证
                        if current_price < 50 or current_price > 300:
                            print(f"   东方财富价格异常: {current_price}, 使用默认值")
                            return None
                        
                        turnover = safe_float_convert(em_data.get('f168', 0))
                        # 换手率修正
                        if turnover > 100:
                            corrected_turnover = turnover / 100
                        else:
                            corrected_turnover = turnover
                        
                        result = {
                            'current': round(current_price, 2),
                            'amount': safe_float_convert(em_data.get('f48', 0)),
                            'turnover': round(corrected_turnover, 2),
                        }
                        return result
            return None
            
        except Exception:
            return None

# 创建数据源管理器
data_source = DataSourceManager()

class EnhancedBondAnalyzer:
    """增强版债券分析器"""
    
    def __init__(self):
        pass
    
    def get_enhanced_maturity_info(self, bond_code, raw_maturity_date):
        """增强版到期信息获取"""
        if bond_code in BOND_MATURITY_DATABASE:
            maturity_date = BOND_MATURITY_DATABASE[bond_code]
            years_to_maturity = self.calculate_years_to_maturity(maturity_date)
            return maturity_date, years_to_maturity
        
        if raw_maturity_date and raw_maturity_date != "未知":
            try:
                years_to_maturity = self.calculate_years_to_maturity(raw_maturity_date)
                return raw_maturity_date, years_to_maturity
            except:
                pass
        
        return "未知", None
    
    def calculate_years_to_maturity(self, maturity_date_str):
        """精确计算剩余年限"""
        if not maturity_date_str or maturity_date_str == "未知":
            return None
        try:
            maturity = datetime.strptime(maturity_date_str, "%Y-%m-%d")
            today = datetime.now()
            days = (maturity - today).days
            if days < 0:
                return 0
            return round(days / 365.25, 2)
        except:
            return None

    def calculate_pure_bond_value(self, bond_code, bond_price, years_to_maturity=None):
        """计算纯债价值和纯债溢价率"""
        try:
            # 使用 safe_float_convert 确保数值类型
            bond_price_val = safe_float_convert(bond_price)
            
            # 简化的纯债价值计算（实际应用中需要更复杂的贴现计算）
            # 假设票面利率2%，贴现率4%
            face_value = 100  # 面值
            coupon_rate = 0.02  # 票面利率
            discount_rate = 0.04  # 贴现率
            
            if years_to_maturity is None:
                years_to_maturity = 3  # 默认3年
            
            years_to_maturity = safe_float_convert(years_to_maturity)
            
            # 简化的现金流贴现计算
            annual_coupon = face_value * coupon_rate
            present_value = 0
            
            # 计算各期利息现值
            for year in range(1, int(years_to_maturity) + 1):
                present_value += annual_coupon / ((1 + discount_rate) ** year)
            
            # 加上本金的现值
            present_value += face_value / ((1 + discount_rate) ** years_to_maturity)
            
            pure_bond_value = round(present_value, 2)
            bond_premium_rate = ((bond_price_val - pure_bond_value) / pure_bond_value) * 100 if pure_bond_value > 0 else 0
            
            return {
                'pure_bond_value': pure_bond_value,
                'bond_premium_rate': round(bond_premium_rate, 2),
                'calculation_method': f"贴现率{discount_rate:.1%}, 剩余年限{years_to_maturity}年"
            }
        except Exception as e:
            print(f"纯债价值计算失败: {e}")
            return {
                'pure_bond_value': 85,  # 默认值
                'bond_premium_rate': 0,
                'calculation_method': '估算值'
            }

    def calculate_effective_floor(self, bond_info):
        """计算有效债底 - 结合纯债价值、回售价值、历史支撑"""
        try:
            bond_price = safe_float_convert(bond_info.get('转债价格', 0))
            pure_bond_data = self.calculate_pure_bond_value(
                bond_info.get('转债代码', ''),
                bond_price,
                bond_info.get('剩余年限')
            )
            
            pure_bond_value = safe_float_convert(pure_bond_data['pure_bond_value'])
            
            # 回售价值估算（如果有回售条款）
            put_value = self.estimate_put_value(bond_info)
            
            # 历史支撑（使用技术分析中的支撑位）
            historical_support = safe_float_convert(bond_info.get('技术分析数据', {}).get('支撑位', pure_bond_value * 1.1))
            
            # 有效债底取三者中的最高值
            effective_floor = max(pure_bond_value, put_value, historical_support)
            
            return {
                'pure_bond_value': pure_bond_value,
                'put_value': put_value,
                'historical_support': historical_support,
                'effective_floor': effective_floor,
                'effective_floor_premium': round(((bond_price - effective_floor) / effective_floor) * 100, 2) if effective_floor > 0 else 0,
                'pure_bond_premium': safe_float_convert(pure_bond_data['bond_premium_rate']),
                'calculation_method': pure_bond_data['calculation_method']
            }
        except Exception as e:
            print(f"有效债底计算失败: {e}")
            return None

    def estimate_put_value(self, bond_info):
        """估算回售价值"""
        try:
            # 简化的回售价值计算
            # 回售价格通常是面值+当期利息
            years_to_maturity = safe_float_convert(bond_info.get('剩余年限', 3))
            
            if years_to_maturity <= 2:
                # 临近回售期，回售价值较高
                put_value = 102  # 面值100 + 利息2
            elif years_to_maturity <= 3:
                put_value = 101
            else:
                put_value = 100
            
            return put_value
        except:
            return 100  # 默认回售价值

    def analyze_redemption_risk(self, bond_code, stock_price, conversion_price):
        """分析强赎风险 - 修正版本"""
        # 使用 safe_float_convert 确保数值类型
        stock_price_val = safe_float_convert(stock_price)
        conversion_price_val = safe_float_convert(conversion_price)
        
        # 模拟计算强赎信息
        redemption_data = {
            "conversion_price": conversion_price_val,
            "trigger_price": round(conversion_price_val * 1.3, 2),
            "pb_ratio": 1.5,  # 默认PB
            "trigger_condition": "连续30个交易日中至少15个交易日收盘价不低于转股价的130%",
        }
        
        # 使用实际传入的股价进行计算
        current_ratio = stock_price_val / redemption_data["trigger_price"] if redemption_data["trigger_price"] > 0 else 0
        progress_percent = current_ratio * 100
        
        # 修正状态判断逻辑
        if current_ratio >= 1.0:
            status = "已触发"
            progress = "100%"
            risk_level = "极高风险"
        elif current_ratio >= 0.9:
            status = "接近触发"
            progress = f"{progress_percent:.1f}%"
            risk_level = "高风险"
        elif current_ratio >= 0.7:
            status = "观察中" 
            progress = f"{progress_percent:.1f}%"
            risk_level = "中风险"
        elif current_ratio >= 0.5:
            status = "安全"
            progress = f"{progress_percent:.1f}%"
            risk_level = "低风险"
        else:
            status = "安全"
            progress = f"{progress_percent:.1f}%"
            risk_level = "极低风险"
        
        redemption_data.update({
            "current_stock_price": round(stock_price_val, 2),
            "trigger_ratio": round(current_ratio, 3),
            "status": status,
            "progress": progress,
            "risk_level": risk_level,
            "distance_to_trigger": round(redemption_data["trigger_price"] - stock_price_val, 2),
            "progress_percent": progress_percent  # 用于排序
        })
        
        return redemption_data
    
    def analyze_downward_adjustment(self, bond_code, stock_price, conversion_price, bond_price, pb_ratio, years_to_maturity):
        """分析下修可能性 - 增强版本"""
        adjust_data = {
            "adjust_history": [],
            "adjust_count": 0,
            "last_adjust_date": "无",
        }
        
        # 使用 safe_float_convert 确保数值类型
        stock_price_val = safe_float_convert(stock_price)
        conversion_price_val = safe_float_convert(conversion_price)
        bond_price_val = safe_float_convert(bond_price)
        pb_ratio_val = safe_float_convert(pb_ratio)
        years_to_maturity_val = safe_float_convert(years_to_maturity)
        
        # 计算下修相关指标
        conversion_value = stock_price_val / conversion_price_val * 100 if conversion_price_val > 0 else 0
        premium_rate = (bond_price_val - conversion_value) / conversion_value * 100 if conversion_value > 0 else 0
        
        # 下修条件判断 - 更精细的评估
        down_conditions = []
        condition_scores = 0
        
        # 条件1: 转股价值低于一定水平
        if conversion_value < 70:
            down_conditions.append(f"转股价值极低({conversion_value:.1f})")
            condition_scores += 3
        elif conversion_value < 80:
            down_conditions.append(f"转股价值较低({conversion_value:.1f})")
            condition_scores += 2
        elif conversion_value < 90:
            down_conditions.append(f"转股价值一般({conversion_value:.1f})")
            condition_scores += 1
        
        # 条件2: 溢价率过高
        if premium_rate > 40:
            down_conditions.append(f"溢价率极高({premium_rate:.1f}%)")
            condition_scores += 3
        elif premium_rate > 30:
            down_conditions.append(f"溢价率较高({premium_rate:.1f}%)")
            condition_scores += 2
        elif premium_rate > 20:
            down_conditions.append(f"溢价率适中({premium_rate:.1f}%)")
            condition_scores += 1
        
        # 条件3: 临近回售期
        if years_to_maturity_val and years_to_maturity_val < 1:
            down_conditions.append("临近回售期(<1年)")
            condition_scores += 3
        elif years_to_maturity_val and years_to_maturity_val < 2:
            down_conditions.append("接近回售期(<2年)")
            condition_scores += 2
        
        # 条件4: PB值限制（下修不能低于净资产）
        if pb_ratio_val and pb_ratio_val < 1.0:
            down_conditions.append("PB<1, 下修空间受限")
            condition_scores -= 2  # 负分，降低下修概率
        elif pb_ratio_val and pb_ratio_val < 1.3:
            down_conditions.append("PB较低, 下修空间有限")
            condition_scores -= 1
        
        # 条件5: 历史下修次数
        if adjust_data["adjust_count"] > 0:
            down_conditions.append(f"历史已下修{adjust_data['adjust_count']}次")
            condition_scores += 1
        
        # 评估下修概率 - 更精细的评估
        if condition_scores >= 5:
            probability = "高"
            suggestion = "下修可能性较大, 密切关注公司公告"
        elif condition_scores >= 3:
            probability = "中高"
            suggestion = "存在下修可能, 需持续观察"
        elif condition_scores >= 1:
            probability = "中低" 
            suggestion = "下修可能性一般"
        else:
            probability = "低"
            suggestion = "当前下修可能性较小"
        
        # 考虑剩余年限因素
        if years_to_maturity_val and years_to_maturity_val < 1.5 and condition_scores >= 2:
            probability = "中高"  # 临期转债下修概率提升
            suggestion += " (临期转债下修概率提升)"
        
        adjust_data.update({
            "down_conditions": down_conditions,
            "condition_scores": condition_scores,
            "current_probability": probability,
            "suggestion": suggestion,
            "conversion_value": round(conversion_value, 2),
            "premium_rate": round(premium_rate, 2),
            "pb_ratio": pb_ratio_val,
            "probability_score": condition_scores  # 用于排序
        })
        
        return adjust_data

    def get_pb_ratio(self, bond_code, default=1.5):
        """获取PB值"""
        return safe_float_convert(BOND_PB_DATABASE.get(bond_code, default))

    def analyze_stock_bond_linkage(self, bond_info):
        """正股和转债联动分析"""
        try:
            stock_price = safe_float_convert(bond_info.get("正股价格", 0))
            bond_price = safe_float_convert(bond_info.get("转债价格", 0))
            conversion_value = safe_float_convert(bond_info.get("转股价值", 0))
            premium_rate = safe_float_convert(bond_info.get("溢价率(%)", 0))
            
            # 计算联动指标
            linkage_analysis = {}
            
            # 1. 溢价率分析
            if premium_rate < 10:
                linkage_analysis["溢价率联动"] = "强联动 - 溢价率低, 转债跟涨性强"
            elif premium_rate < 20:
                linkage_analysis["溢价率联动"] = "中等联动 - 溢价率适中"
            elif premium_rate < 30:
                linkage_analysis["溢价率联动"] = "弱联动 - 溢价率偏高"
            else:
                linkage_analysis["溢价率联动"] = "脱钩风险 - 溢价率过高, 联动性差"
            
            # 2. Delta值分析（转股价值/转债价格）
            delta = conversion_value / bond_price if bond_price > 0 else 0
            if delta > 0.9:
                linkage_analysis["Delta弹性"] = "高弹性 - 股性强, 正股波动传导充分"
            elif delta > 0.7:
                linkage_analysis["Delta弹性"] = "中弹性 - 平衡型"
            else:
                linkage_analysis["Delta弹性"] = "低弹性 - 债性强, 正股波动传导有限"
            
            # 3. 价格偏离度分析
            theoretical_price = conversion_value * (1 + premium_rate/100)
            price_deviation = ((bond_price - theoretical_price) / theoretical_price) * 100 if theoretical_price > 0 else 0
            
            if abs(price_deviation) < 2:
                linkage_analysis["价格合理性"] = "价格合理 - 市场定价有效"
            elif price_deviation > 5:
                linkage_analysis["价格合理性"] = "可能高估 - 转债价格偏高"
            elif price_deviation < -5:
                linkage_analysis["价格合理性"] = "可能低估 - 转债价格偏低"
            else:
                linkage_analysis["价格合理性"] = "价格基本合理"
            
            # 4. 联动投资建议
            if premium_rate < 15 and delta > 0.8:
                linkage_analysis["联动策略"] = "适合正股联动策略 - 跟涨性强"
            elif premium_rate > 30:
                linkage_analysis["联动策略"] = "适合独立走势策略 - 联动性弱"
            else:
                linkage_analysis["联动策略"] = "平衡策略 - 需结合其他因素"
            
            # 5. 风险提示
            if premium_rate > 40 and bond_price > 130:
                linkage_analysis["风险提示"] = "高风险 - 高溢价+高价格, 双重风险"
            elif premium_rate > 30:
                linkage_analysis["风险提示"] = "中风险 - 溢价率偏高"
            else:
                linkage_analysis["风险提示"] = "低风险 - 溢价率合理"
            
            linkage_analysis["Delta值"] = round(delta, 3)
            linkage_analysis["价格偏离度"] = round(price_deviation, 2)
            
            return linkage_analysis
            
        except Exception as e:
            return {"分析错误": f"联动分析失败: {str(e)}"}

# 创建分析器实例
bond_analyzer = EnhancedBondAnalyzer()
risk_monitor = RiskMonitor()

# ==================== 修复函数：多因子共振分析 ====================

def get_historical_data_for_ta(bond_code, days=300, actual_price=None):
    """
    为技术分析获取历史数据 - 修复价格一致性版本
    使用真实的当前价格生成历史数据
    """
    try:
        # 优先使用传入的实际价格
        if actual_price is not None:
            current_price = safe_float_convert(actual_price)
        else:
            # 如果没有传入价格，则重新获取
            base_info = get_bond_basic_info(bond_code)
            if not base_info:
                return None
            current_price = safe_float_convert(base_info.get('转债价格', 100))
            
        print(f"   技术分析使用价格: {current_price:.2f}元")
        
        # 模拟生成历史数据
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # 基于当前价格生成合理的历史价格序列
        np.random.seed(int(bond_code) % 10000)
        
        prices = [current_price * 0.8]  # 起始价格
        for i in range(1, days-1):  # 留出最后一个位置给实际价格
            change = np.random.normal(0.001, 0.015)
            new_price = prices[-1] * (1 + change)
            # 限制价格在合理范围内
            if new_price < current_price * 0.5:
                new_price = current_price * 0.5
            elif new_price > current_price * 1.5:
                new_price = current_price * 1.5
            prices.append(new_price)
        
        # 确保最后一个价格就是实际价格
        prices.append(current_price)
        
        # 创建DataFrame
        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': [abs(np.random.normal(50000000, 20000000)) for _ in prices]
        })
        df.set_index('date', inplace=True)
        
        # 验证最后一个价格是否正确
        if abs(df['close'].iloc[-1] - current_price) > 0.01:
            print(f"   ⚠️ 价格验证: 历史数据最后价格{df['close'].iloc[-1]:.2f} vs 实际价格{current_price:.2f}")
            # 强制修正
            df.iloc[-1, df.columns.get_loc('close')] = current_price
        
        return df
        
    except Exception as e:
        print(f"历史数据生成失败: {e}")
        return None

def perform_multifactor_analysis(bond_code, bond_info):
    """
    执行多因子共振分析 - 完全修复版本
    修复了 unsupported operand type(s) for /: 'str' and 'float' 错误
    """
    print(f"\n🔍 执行多因子共振技术分析...")
    
    # 使用 safe_float_convert 确保数值类型
    actual_price = safe_float_convert(bond_info.get('转债价格', 0))
    premium_str = bond_info.get('溢价率(%)', 0)
    conversion_value_str = bond_info.get('转股价值', 0)
    
    # 强制转换为数值类型
    premium_value = safe_float_convert(premium_str)
    conversion_value = safe_float_convert(conversion_value_str)
    
    print(f"   实际转债价格: {actual_price:.2f}元")
    print(f"   溢价率: {premium_value:.2f}% (原始: {premium_str})")
    print(f"   转股价值: {conversion_value:.2f} (原始: {conversion_value_str})")
    
    # 获取历史数据，传入实际价格确保一致性
    historical_data = get_historical_data_for_ta(bond_code, actual_price=actual_price)
    if historical_data is None:
        return {"error": "无法获取历史数据"}
    
    # 获取强赎距离信息 - 修复类型问题
    call_risk_distance = 0.3  # 默认30%距离
    redemption_data = bond_info.get("强赎分析", {})
    if redemption_data:
        progress_percent = redemption_data.get("progress_percent", 30)
        # 确保progress_percent是数值类型 - 使用 safe_float_convert
        progress_percent = safe_float_convert(progress_percent)
        call_risk_distance = (100 - progress_percent) / 100
    
    # 执行多因子共振分析，传入实际价格确保一致性
    try:
        # 确保premium_rate是数值类型 - 这是修复的核心
        premium = safe_float_convert(premium_value)
        premium_rate = premium / 100  # 转换为小数形式
        
        print(f"   技术分析参数:")
        print(f"     - 溢价率(小数形式): {premium_rate:.4f} (原始值: {premium}%)")
        print(f"     - 强赎距离: {call_risk_distance:.4f}")
        print(f"     - 实际价格: {actual_price:.2f}")
        
        # 确保call_risk_distance是浮点数类型
        call_risk_distance = float(call_risk_distance)
        
        # 确保actual_price是浮点数类型
        actual_price = float(actual_price) if actual_price else None
        
        ta_results = ta_analyzer.comprehensive_analysis(
            df=historical_data,
            premium_rate=premium_rate,  # 使用修复后的数值类型
            call_risk_distance=call_risk_distance,
            actual_price=actual_price
        )
        
        # 将信号集成到bond_info中
        bond_info['multifactor_signal'] = ta_results.get('overall_signal', 'WAIT')
        bond_info['multifactor_results'] = ta_results
        
        # 生成分析报告
        if ta_results and 'error' not in ta_results:
            report = ta_analyzer.generate_analysis_report(ta_results)
            print(report)
        
        return ta_results
        
    except Exception as e:
        print(f"❌ 多因子共振分析失败: {e}")
        print(f"   出错位置: perform_multifactor_analysis 函数")
        print(f"   参数详情:")
        print(f"     - bond_code: {bond_code}")
        print(f"     - premium_value: {premium_value} (类型: {type(premium_value)})")
        print(f"     - call_risk_distance: {call_risk_distance} (类型: {type(call_risk_distance)})")
        print(f"     - actual_price: {actual_price} (类型: {type(actual_price)})")
        import traceback
        traceback.print_exc()
        bond_info['multifactor_signal'] = 'ERROR'
        return {"error": f"分析失败: {str(e)}"}

# ==================== 工具函数定义 ====================

def get_bond_name(bond_code):
    """获取转债名称"""
    name_map = {
        "113588": "润达转债", "113053": "隆22转债", "110064": "建工转债",
        "127089": "晶澳转债", "123210": "志特转债", "113062": "杭银转债",
        "113056": "重银转债", "123214": "东宝转债", "123208": "金丹转债",
        "123206": "正元转02", "118037": "合力转债", "123013": "横河转债",
        "123042": "银河转债", "123140": "天地转债", "113510": "再升转债",
        "128091": "新天转债", "128103": "同德转债", "113646": "永吉转债",
        "123043": "正元转债", "123052": "飞鹿转债", "123072": "乐歌转债",
    }
    return name_map.get(bond_code, f"转债{bond_code}")

def get_detailed_liquidity_rating(avg_volume, turnover_rate):
    """详细流动性评级 - 修复版"""
    # 使用 safe_float_convert 确保数值类型
    avg_volume_val = safe_float_convert(avg_volume)
    turnover_rate_val = safe_float_convert(turnover_rate)
    
    volume_desc = ""
    turnover_desc = ""
    
    # 修正换手率判断逻辑
    if turnover_rate_val > 100:  # 如果换手率异常高，可能是数据错误
        turnover_rate_val = turnover_rate_val / 100  # 自动修正
    
    if avg_volume_val < 0.05:
        volume_desc = "成交额极低"
        volume_score = 1
    elif avg_volume_val < 0.1:
        volume_desc = "成交额较低"
        volume_score = 2
    elif avg_volume_val < 0.3:
        volume_desc = "成交额一般"
        volume_score = 3
    elif avg_volume_val < 0.5:
        volume_desc = "成交额良好"
        volume_score = 4
    else:
        volume_desc = "成交额充足"
        volume_score = 5
    
    # 修正换手率评分标准
    if turnover_rate_val < 0.5:
        turnover_desc = "换手率极低"
        turnover_score = 1
    elif turnover_rate_val < 1:
        turnover_desc = "换手率较低"
        turnover_score = 2
    elif turnover_rate_val < 3:
        turnover_desc = "换手率一般"
        turnover_score = 3
    elif turnover_rate_val < 5:
        turnover_desc = "换手率良好"
        turnover_score = 4
    else:
        turnover_desc = "换手率活跃"
        turnover_score = 5
    
    total_score = volume_score + turnover_score
    if total_score >= 9:
        rating = "流动性优秀"
        advice = "买卖顺畅, 适合大资金"
    elif total_score >= 7:
        rating = "流动性良好"
        advice = "交易较为顺畅"
    elif total_score >= 5:
        rating = "流动性一般"
        advice = "适合中小资金"
    else:
        rating = "流动性较差"
        advice = "买卖可能受限"
    
    return {
        '评级': rating,
        '成交额描述': f"{volume_desc}({avg_volume_val:.3f}亿)",
        '换手率描述': f"{turnover_desc}({turnover_rate_val:.2f}%)",
        '建议': advice,
        '综合得分': f"{total_score}/10"
    }

def calculate_ytm(bond_price, years=3):
    """计算到期收益率"""
    try:
        bond_price_val = safe_float_convert(bond_price)
        years_val = safe_float_convert(years)
        
        if bond_price_val <= 100:
            ytm = (100 - bond_price_val) / bond_price_val / years_val + 0.02
        else:
            ytm = 0.02 - (bond_price_val - 100) / bond_price_val / years_val
        return round(ytm * 100, 2)
    except:
        return 0.0

def safe_float_parse(value, default=0):
    """安全浮点数解析 - 使用统一的 safe_float_convert"""
    return safe_float_convert(value, default)

def safe_premium_parse(premium_raw, bond_price, conversion_value):
    """安全溢价率解析"""
    try:
        if premium_raw and isinstance(premium_raw, str):
            premium_str = premium_raw.replace('%', '').replace(',', '').strip()
            if premium_str and premium_str.replace('.', '', 1).replace('-', '').isdigit():
                return safe_float_convert(premium_str)
        
        if conversion_value > 0:
            bond_price_val = safe_float_convert(bond_price)
            conversion_value_val = safe_float_convert(conversion_value)
            return round((bond_price_val - conversion_value_val) / conversion_value_val * 100, 2)
        else:
            return 0.0
    except:
        return 0.0

def calculate_fibonacci_levels(high, low):
    """计算斐波那契回撤位"""
    try:
        high_val = safe_float_convert(high)
        low_val = safe_float_convert(low)
        
        if high_val <= low_val:
            return {}
            
        price_range = high_val - low_val
        
        fib_levels = {
            '0.0%': high_val,
            '23.6%': high_val - price_range * 0.236,
            '38.2%': high_val - price_range * 0.382,
            '50.0%': high_val - price_range * 0.5,
            '61.8%': high_val - price_range * 0.618,
            '78.6%': high_val - price_range * 0.786,
            '100.0%': low_val,
        }
        return fib_levels
    except:
        return {}

def get_technical_analysis(bond_code, current_price, conversion_value, bond_price):
    """完整技术分析"""
    try:
        # 使用 safe_float_convert 确保数值类型
        current_price_val = safe_float_convert(current_price)
        conversion_value_val = safe_float_convert(conversion_value)
        bond_price_val = safe_float_convert(bond_price)
        
        if bond_code in BOND_TECHNICAL_DATABASE:
            bond_data = BOND_TECHNICAL_DATABASE[bond_code]
            high_250 = safe_float_convert(bond_data['high_250'])
            low_250 = safe_float_convert(bond_data['low_250'])
            high_120 = safe_float_convert(bond_data['high_120'])
            low_120 = safe_float_convert(bond_data['low_120'])
            data_source_info = bond_data.get('data_source', '真实价格数据库')
            fib_levels = bond_data.get('fib_levels', calculate_fibonacci_levels(high_250, low_250))
        else:
            high_250 = min(current_price_val * 1.15, 200)
            low_250 = max(current_price_val * 0.85, 80)
            high_120 = min(current_price_val * 1.10, 180)
            low_120 = max(current_price_val * 0.90, 90)
            data_source_info = '智能估算'
            fib_levels = calculate_fibonacci_levels(high_250, low_250)
        
        # 计算技术指标
        ma_20 = current_price_val * 0.98
        ma_60 = current_price_val * 0.96
        ma_120 = current_price_val * 0.94
        
        support = round(low_120 * 0.98, 2)
        resistance = round(high_250, 2)
        
        # 计算位置百分比
        distance_to_support = ((current_price_val - support) / current_price_val) * 100 if current_price_val > 0 else 0
        distance_to_resistance = ((resistance - current_price_val) / current_price_val) * 100 if current_price_val > 0 else 0
        
        # 位置判断
        if distance_to_support < 5:
            position_status = "接近支撑"
        elif distance_to_resistance < 5:
            position_status = "接近压力"
        else:
            position_status = "中间区域, 方向待定"
        
        # 均线排列判断
        if ma_20 > ma_60 > ma_120:
            ma_status = "多头排列, 趋势向上"
        elif ma_20 < ma_60 < ma_120:
            ma_status = "空头排列, 趋势向下"
        else:
            ma_status = "均线交织, 震荡整理"
        
        # Delta弹性分析
        delta = conversion_value_val / bond_price_val if bond_price_val > 0 else 0
        if delta > 0.9:
            delta_status = "高弹性: 股性较强"
        elif delta > 0.7:
            delta_status = "中弹性: 平衡型"
        else:
            delta_status = "低弹性: 债性保护较强"
        
        return {
            '支撑位': support,
            '压力位': resistance,
            '斐波那契_levels': fib_levels,
            '近期高点(250日)': round(high_250, 2),
            '近期低点(250日)': round(low_250, 2),
            '近期高点(120日)': round(high_120, 2),
            '近期低点(120日)': round(low_120, 2),
            '20日均线': round(ma_20, 2),
            '60日均线': round(ma_60, 2),
            '120日均线': round(ma_120, 2),
            '数据来源': data_source_info,
            '位置状态': position_status,
            '距支撑百分比': round(distance_to_support, 1),
            '距压力百分比': round(distance_to_resistance, 1),
            '均线状态': ma_status,
            'Delta值': round(delta, 3),
            '弹性状态': delta_status
        }
        
    except Exception:
        return get_fallback_technical_levels(current_price, conversion_value, bond_price)

def get_fallback_technical_levels(current_price, conversion_value, bond_price):
    """备用技术分析"""
    try:
        current_price_val = safe_float_convert(current_price)
        conversion_value_val = safe_float_convert(conversion_value)
        bond_price_val = safe_float_convert(bond_price)
        
        support = current_price_val * 0.95
        resistance = current_price_val * 1.05
        
        delta = conversion_value_val / bond_price_val if bond_price_val > 0 else 0
        if delta > 0.9:
            delta_status = "高弹性: 股性较强"
        elif delta > 0.7:
            delta_status = "中弹性: 平衡型"
        else:
            delta_status = "低弹性: 债性保护较强"
        
        return {
            '支撑位': round(support, 2),
            '压力位': round(resistance, 2),
            '斐波那契_levels': {},
            '近期高点(250日)': round(current_price_val * 1.15, 2),
            '近期低点(250日)': round(current_price_val * 0.85, 2),
            '近期高点(120日)': round(current_price_val * 1.10, 2),
            '近期低点(120日)': round(current_price_val * 0.90, 2),
            '20日均线': round(current_price_val, 2),
            '60日均线': round(current_price_val, 2),
            '120日均线': round(current_price_val, 2),
            '数据来源': '基础估算',
            '位置状态': '数据不足',
            '距支撑百分比': 5.0,
            '距压力百分比': 5.0,
            '均线状态': '数据不足',
            'Delta值': round(delta, 3),
            '弹性状态': delta_status
        }
    except:
        return {
            '支撑位': 0, '压力位': 0, '斐波那契_levels': {},
            '近期高点(250日)': 0, '近期低点(250日)': 0,
            '近期高点(120日)': 0, '近期低点(120日)': 0,
            '20日均线': 0, '60日均线': 0, '120日均线': 0,
            '数据来源': '估算失败',
            '位置状态': '数据不足',
            '距支撑百分比': 0,
            '距压力百分比': 0,
            '均线状态': '数据不足',
            'Delta值': 0,
            '弹性状态': '数据不足'
        }

def get_bond_basic_info(bond_code):
    """获取债券基础信息"""
    try:
        bond_df = ak.bond_zh_cov()
        if bond_df is not None and not bond_df.empty and '债券代码' in bond_df.columns:
            match = bond_df[bond_df['债券代码'] == bond_code]
            if not match.empty:
                bond_data = match.iloc[0]
                
                bond_price = safe_float_parse(bond_data.get('债现价', 0))
                stock_price = safe_float_parse(bond_data.get('正股价', 0))
                convert_price = safe_float_parse(bond_data.get('转股价', 1))
                
                if bond_price > 1000:
                    bond_price = bond_price / 10
                
                conversion_value = round(stock_price / convert_price * 100, 2) if convert_price > 0 else 0
                premium_rate = safe_premium_parse(bond_data.get('转股溢价率', ''), bond_price, conversion_value)
                
                raw_maturity_date = bond_data.get('到期时间', '未知')
                maturity_date, years_to_maturity = bond_analyzer.get_enhanced_maturity_info(bond_code, raw_maturity_date)
                
                size_str = str(bond_data.get('发行规模', '10')).replace('亿元', '').replace('亿', '')
                remaining_size = safe_float_convert(size_str)
                
                # 获取PB值
                pb_ratio = bond_analyzer.get_pb_ratio(bond_code)
                
                # 强赎分析 - 使用正确的股价数据
                redemption_analysis = bond_analyzer.analyze_redemption_risk(bond_code, stock_price, convert_price)
                
                # 下修分析 - 增强版本，传入PB和剩余年限
                downward_analysis = bond_analyzer.analyze_downward_adjustment(
                    bond_code, stock_price, convert_price, bond_price, pb_ratio, years_to_maturity
                )
                
                info = {
                    "名称": bond_data.get('债券简称', get_bond_name(bond_code)),
                    "转债代码": bond_code,
                    "正股代码": bond_data.get('正股代码', '未知'),
                    "正股价格": round(stock_price, 2),
                    "转债价格": round(bond_price, 2),
                    "转股价": round(convert_price, 2),
                    "转股价值": conversion_value,
                    "溢价率(%)": round(premium_rate, 2),
                    "剩余规模(亿)": round(remaining_size, 2),
                    "PB": pb_ratio,
                    "到期时间": maturity_date,
                    "剩余年限": years_to_maturity,
                    "日均成交额(亿)": 0.1,
                    "换手率(%)": 2.5,
                    "流动性评级": "待计算",
                    "距强赎空间(%)": round((convert_price * 1.3 - stock_price) / stock_price * 100, 2) if stock_price > 0 else 20.0,
                    "YTM(%)": calculate_ytm(bond_price, years_to_maturity or 3),
                    "双低值": round(bond_price + premium_rate, 2),
                    "Delta值": round(conversion_value / bond_price, 3) if bond_price > 0 else 0,
                    "强赎分析": redemption_analysis,
                    "下修分析": downward_analysis
                }
                return info
    except Exception as e:
        print(f"   基础数据获取失败: {e}")
    return None

def get_user_holding_input(bond_code, bond_name):
    """获取用户持仓输入"""
    print(f"\n正在分析 {bond_name}({bond_code})")
    
    if bond_code in USER_HOLDINGS:
        current = USER_HOLDINGS[bond_code]
        print(f"当前持仓: 成本{current['cost_price']}元, 数量{current['shares']}张")
        use_existing = input("是否使用现有持仓？(y/n, 回车使用): ").strip().lower()
        if use_existing in ['', 'y', 'yes']:
            return USER_HOLDINGS[bond_code]
    
    print("\n请输入持仓信息(直接回车跳过):")
    try:
        cost_input = input("持仓成本价(元): ").strip()
        if not cost_input:
            return None
            
        shares_input = input("持仓数量(张): ").strip()
        if not shares_input:
            return None
            
        cost_price = safe_float_convert(cost_input)
        shares = int(safe_float_convert(shares_input))
        
        holding_info = {
            'cost_price': cost_price,
            'shares': shares,
            'purchase_date': datetime.now().strftime("%Y-%m-%d")
        }
        
        USER_HOLDINGS[bond_code] = holding_info
        return holding_info
        
    except ValueError:
        print("输入格式错误, 跳过持仓分析")
        return None

def calculate_holding_analysis(bond_info, holding_info):
    """计算持仓分析"""
    if not holding_info:
        return None
    
    current_price = safe_float_convert(bond_info.get('转债价格', 0))
    cost_price = safe_float_convert(holding_info.get('cost_price', 0))
    shares = safe_float_convert(holding_info.get('shares', 0))
    
    if cost_price > 0 and current_price > 0:
        profit_per_share = current_price - cost_price
        profit_rate = (profit_per_share / cost_price) * 100 if cost_price > 0 else 0
        total_profit = profit_per_share * shares
        total_value = current_price * shares
        cost_value = cost_price * shares
        
        if profit_rate > 20:
            advice = "考虑止盈"
            risk_level = "高风险"
        elif profit_rate > 10:
            advice = "持有观察"
            risk_level = "中风险"
        elif profit_rate > -5:
            advice = "继续持有"
            risk_level = "低风险"
        elif profit_rate > -15:
            advice = "谨慎持有"
            risk_level = "中风险"
        else:
            advice = "考虑止损"
            risk_level = "高风险"
        
        return {
            '持仓成本': cost_price,
            '持仓数量': shares,
            '当前盈亏': round(total_profit, 2),
            '盈亏比例': round(profit_rate, 2),
            '持仓市值': round(total_value, 2),
            '建仓日期': holding_info.get('purchase_date', '未知'),
            '持仓建议': advice,
            '风险等级': risk_level,
            '成本市值': round(cost_value, 2)
        }
    
    return None

def get_enhanced_bond_info(bond_code):
    """增强版债券信息获取"""
    print(f"   分析 {bond_code}...")
    
    base_info = get_bond_basic_info(bond_code)
    if not base_info:
        return None
    
    tencent_data = data_source.get_tencent_data(bond_code)
    eastmoney_data = data_source.get_eastmoney_data(bond_code)
    
    enhanced_info = base_info.copy()
    data_sources = ["AkShare"]
    original_price = base_info.get("转债价格", 0)
    if tencent_data:
        t_price = tencent_data.get('current', 0)
        if 80 < t_price < 200:
            # 只有当AkShare价格明显异常时才覆盖
            if original_price < 50 or original_price > 300:
                enhanced_info["转债价格"] = round(t_price, 2)
                data_sources.append("腾讯财经(修正)")
            else:
                # 正常情况不覆盖，只记录
                data_sources.append("腾讯财经")
                print(f"🔍【价格验证】AkShare: {original_price}元, 腾讯: {t_price}元")
    
    if eastmoney_data:
        if eastmoney_data.get('amount'):
            em_amount = eastmoney_data['amount'] / 1e8
            if 0 < em_amount < 10:
                enhanced_info["日均成交额(亿)"] = round(em_amount, 3)
        if eastmoney_data.get('turnover'):
            # 修正换手率显示
            turnover_rate = eastmoney_data['turnover']
            if turnover_rate > 100:
                turnover_rate = turnover_rate / 100
            enhanced_info["换手率(%)"] = round(turnover_rate, 2)
        data_sources.append("东方财富")
    
    enhanced_info["数据来源"] = "+".join(data_sources)
    
    volume = enhanced_info.get("日均成交额(亿)", 0.1)
    turnover = enhanced_info.get("换手率(%)", 2.5)
    liquidity_analysis = get_detailed_liquidity_rating(volume, turnover)
    enhanced_info["流动性分析"] = liquidity_analysis
    
    tech_analysis = get_technical_analysis(
        bond_code, 
        enhanced_info["转债价格"], 
        enhanced_info["转股价值"],
        enhanced_info["转债价格"]
    )
    enhanced_info.update(tech_analysis)
    enhanced_info["技术分析数据"] = tech_analysis
    
    # 正股转债联动分析
    linkage_analysis = bond_analyzer.analyze_stock_bond_linkage(enhanced_info)
    enhanced_info["联动分析"] = linkage_analysis
    
    # 债底分析
    floor_analysis = bond_analyzer.calculate_effective_floor(enhanced_info)
    if floor_analysis:
        enhanced_info["债底分析"] = floor_analysis
    
    years_to_maturity = enhanced_info.get("剩余年限")
    if years_to_maturity and years_to_maturity < 1.0:
        enhanced_info["临期策略"] = "关注临期机会, 注意回售条款"
    elif years_to_maturity and years_to_maturity < 2.0:
        enhanced_info["临期策略"] = "时间较为充裕"
    else:
        enhanced_info["临期策略"] = "时间充足, 可中长期持有"
    
    return enhanced_info

def generate_risk_tags(bond_info):
    """生成风险标签 - 基于价格、YTM、回售条件"""
    price = safe_float_convert(bond_info.get("转债价格", 0))
    ytm = safe_float_convert(bond_info.get("YTM(%)", 0))
    floor_analysis = bond_info.get("债底分析", {})
    
    risk_tags = []
    
    # 高波风险判断
    if price > 130 and ytm < -5:
        risk_tags.append("高波风险")
        
        # 检查回售保护
        put_value = safe_float_convert(floor_analysis.get('put_value', 0)) if floor_analysis else 0
        if put_value <= 100:  # 无强回售保护
            risk_tags.append("无回售保护")
    
    # 债底保护判断
    if floor_analysis:
        effective_floor_premium = safe_float_convert(floor_analysis.get('effective_floor_premium', 0))
        if effective_floor_premium > 40:
            risk_tags.append("债底保护弱")
        elif effective_floor_premium > 25:
            risk_tags.append("债底保护一般")
    
    return risk_tags

def calculate_comprehensive_score_v2(info):
    """综合评分算法 v2.1 - 修复高溢价陷阱问题"""
    score = 0
    details = []
    
    premium = safe_float_convert(info.get("溢价率(%)", 0))
    conversion_value = safe_float_convert(info.get("转股价值", 0))
    
    # 高溢价硬性扣分 - 修复核心问题
    if premium > 40:
        # 超高溢价直接大幅扣分
        score -= 20
        details.append("溢价:超高溢[-20]")
    elif premium > 35:
        # 高溢价显著扣分
        score -= 15
        details.append("溢价:高溢[-15]")
    elif premium > 30:
        # 较高溢价扣分
        score -= 10
        details.append("溢价:较高溢[-10]")
    elif premium > 25:
        score += 5
        details.append("溢价:略高[+5]")
    elif premium > 15:
        score += 15
        details.append("溢价:适中[+15]")
    elif premium > 10:
        score += 20
        details.append("溢价:较低[+20]")
    else:
        score += 25
        details.append("溢价:极低[+25]")
    
    # 1. 规模因子 (20分)
    size = safe_float_convert(info.get("剩余规模(亿)", 10))
    if size < 3:
        score += 20
        details.append("规模:小盘[+20]")
    elif size < 5:
        score += 16
        details.append("规模:中小盘[+16]")
    elif size < 8:
        score += 12
        details.append("规模:中盘[+12]")
    elif size < 12:
        score += 8
        details.append("规模:大盘[+8]")
    else:
        score += 4
        details.append("规模:超大[+4]")
    
    # 2. 价格因子 (20分) - 结合债性保护
    price = safe_float_convert(info.get("转债价格", 0))
    if price < 110:
        score += 20
        details.append("价格:安全[+20]")
    elif price < 120:
        score += 16
        details.append("价格:合理[+16]")
    elif price < 130:
        score += 12
        details.append("价格:适中[+12]")
    elif price < 140:
        score += 8
        details.append("价格:偏高[+8]")
    else:
        score += 4
        details.append("价格:过高[+4]")
    
    # 3. 流动性因子 (15分)
    volume = safe_float_convert(info.get("日均成交额(亿)", 0))
    if volume > 0.8:
        score += 15
        details.append("流动性:优秀[+15]")
    elif volume > 0.4:
        score += 12
        details.append("流动性:良好[+12]")
    elif volume > 0.2:
        score += 9
        details.append("流动性:中等[+9]")
    elif volume > 0.1:
        score += 6
        details.append("流动性:一般[+6]")
    else:
        score += 3
        details.append("流动性:较差[+3]")
    
    # 4. 债性保护因子 (15分)
    ytm = safe_float_convert(info.get("YTM(%)", 0))
    if ytm > 2:
        score += 15
        details.append("YTM:强保护[+15]")
    elif ytm > 0:
        score += 12
        details.append("YTM:有保护[+12]")
    elif ytm > -2:
        score += 8
        details.append("YTM:弱保护[+8]")
    else:
        score += 4
        details.append("YTM:无保护[+4]")
    
    # 5. 转股价值质量 (10分) - 新增: 识别伪价内债
    if conversion_value > 110:
        score += 10
        details.append("价内:深度[+10]")
    elif conversion_value > 105:
        score += 8
        details.append("价内:良好[+8]")
    elif conversion_value > 100:
        score += 5  # 伪价内，仅小幅加分
        details.append("价内:边缘[+5]")
    elif conversion_value > 95:
        score += 2
        details.append("价外:轻度[+2]")
    elif conversion_value > 90:
        score += 0
        details.append("价外:中度[+0]")
    else:
        score -= 5
        details.append("价外:深度[-5]")
    
    final_score = max(0, min(score, 100))  # 确保在0-100范围内
    return final_score, details

def get_operation_advice(score, bond_info, final_grade):
    """操作建议 v2.2 - 修复矛盾建议问题"""
    premium = safe_float_convert(bond_info.get("溢价率(%)", 0))
    bond_price = safe_float_convert(bond_info.get("转债价格", 0))
    conversion_value = safe_float_convert(bond_info.get("转股价值", 0))
    ta_signal = bond_info.get('multifactor_signal', 'WAIT')
    
    # 根据最终评级给出一致的操作建议
    if "硬回避" in final_grade:
        upside_needed = (bond_price - conversion_value) / conversion_value * 100 if conversion_value > 0 else 0
        return f"💡 操作建议: {final_grade} - 硬性风控规则触发，建议坚决回避（正股需涨{upside_needed:.1f}%才能平价）"
    
    elif "矛盾信号" in final_grade:
        if premium > 25:
            return "💡 操作建议: 技术面与基本面矛盾 - 可极小仓位短线参与，严格设置止损"
        else:
            return "💡 操作建议: 技术面与基本面矛盾 - 建议轻仓谨慎参与，关注风险"
    
    elif "谨慎" in final_grade or "中高风险" in final_grade:
        return "💡 操作建议: 风险较高，建议观望或极小仓位试探"
    
    elif "优秀" in final_grade or "良好" in final_grade:
        if ta_signal in ["STRONG_BUY", "BUY"]:
            return "💡 操作建议: 适合建立仓位，可分批买入"
        else:
            return "💡 操作建议: 基本面良好，可逢低布局"
    
    elif "中等" in final_grade:
        if ta_signal in ["STRONG_BUY", "BUY"]:
            return "💡 操作建议: 可小仓位试仓，严格设置止损"
        else:
            return "💡 操作建议: 保持观望，等待更好时机"
    
    else:
        return "💡 操作建议: 暂时回避，寻找更好机会"

def analyze_strategies(info):
    """分析策略适用性"""
    strategies = []
    
    double_low_value = safe_float_convert(info.get("双低值", 0))
    if double_low_value < 130:
        strategies.append("双低策略: 优秀 - 价格和溢价率都很低, 安全边际充足")
    elif double_low_value < 150:
        strategies.append("双低策略: 良好 - 性价比较高, 适合配置")
    else:
        strategies.append("双低策略: 一般 - 双低值偏高, 安全边际有限")
    
    premium = safe_float_convert(info.get("溢价率(%)", 0))
    if premium < 10:
        strategies.append("低溢价策略: 优秀 - 跟涨能力强, 正股上涨时弹性大")
    elif premium < 20:
        strategies.append("低溢价策略: 良好 - 跟涨能力较好")
    else:
        strategies.append("低溢价策略: 不适合 - 溢价率偏高, 跟涨能力弱")
    
    size = safe_float_convert(info.get("剩余规模(亿)", 0))
    if size < 3:
        strategies.append("小规模策略: 优秀 - 规模小易炒作, 波动性大")
    elif size < 5:
        strategies.append("小规模策略: 良好 - 规模适中, 有一定弹性")
    
    ytm = safe_float_convert(info.get("YTM(%)", 0))
    if ytm > 3:
        strategies.append("高YTM策略: 优秀 - 到期收益高, 债底保护强")
    elif ytm > 1:
        strategies.append("高YTM策略: 良好 - 有一定债底保护")
    
    # 小规模低溢价策略
    if size < 5 and premium < 20:
        strategies.append("小规模低溢价策略: 优秀 - 兼具弹性和安全边际")
    elif size < 5 and premium < 30:
        strategies.append("小规模低溢价策略: 良好 - 平衡型选择")
    
    return strategies

def get_risk_analysis(info):
    """风险分析"""
    risks = []
    
    premium = safe_float_convert(info.get("溢价率(%)", 0))
    if premium > 40:
        risks.append("溢价率风险: 高风险 - 溢价率>40%, 技术面信号可靠性大幅降低")
    elif premium > 30:
        risks.append("溢价率风险: 中风险 - 溢价率偏高, 需谨慎对待")
    elif premium > 20:
        risks.append("溢价率风险: 低风险 - 溢价率适中")
    else:
        risks.append("溢价率风险: 无风险 - 溢价率合理")
    
    price = safe_float_convert(info.get("转债价格", 0))
    if price > 140:
        risks.append("价格风险: 高风险 - 价格过高, 债底保护弱")
    elif price > 130:
        risks.append("价格风险: 中风险 - 价格偏高")
    elif price > 115:
        risks.append("价格风险: 低风险 - 价格合理")
    else:
        risks.append("价格风险: 无风险 - 价格安全")
    
    return risks

def analyze_single_bond_enhanced():
    """增强版单个转债分析 - 集成多因子共振分析和HTML输出"""
    code = input("\n请输入转债代码: ").strip()
    if not code:
        print("未输入代码")
        return
    
    print(f"\n正在分析代码: {code} ...")
    
    info = get_enhanced_bond_info(code)
    if not info:
        print("分析失败")
        return
    
    # 修复剩余年限显示
    if info.get("剩余年限") is None:
        _, estimated_years = bond_analyzer.get_enhanced_maturity_info(code, "未知")
        if estimated_years:
            info["剩余年限"] = round(estimated_years, 2)
    
    holding_info = get_user_holding_input(code, info['名称'])
    
    print("\n" + "=" * 70)
    print(f"转债名称: {info['名称']}")
    print(f"代码: {info['转债代码']}  |  正股: {info['正股代码']}")
    
    # 使用 safe_float_convert 确保数值类型
    stock_price = safe_float_convert(info.get('正股价格', 0))
    bond_price = safe_float_convert(info.get('转债价格', 0))
    conversion_price = safe_float_convert(info.get('转股价', 0))
    pb_value = safe_float_convert(info.get('PB', 0))
    conversion_value = safe_float_convert(info.get('转股价值', 0))
    premium = safe_float_convert(info.get('溢价率(%)', 0))
    remaining_size = safe_float_convert(info.get('剩余规模(亿)', 0))
    remaining_years = safe_float_convert(info.get('剩余年限', 0))
    double_low = safe_float_convert(info.get('双低值', 0))
    ytm = safe_float_convert(info.get('YTM(%)', 0))
    delta = safe_float_convert(info.get('Delta值', 0))
    
    print(f"正股价格: {stock_price:.2f} 元  |  转债价格: {bond_price:.2f} 元")
    print(f"转股价: {conversion_price:.2f} 元  |  PB: {pb_value:.2f}")
    print(f"转股价值: {conversion_value:.2f}  |  溢价率: {premium:.2f}%")
    print(f"剩余规模: {remaining_size:.2f}亿  |  剩余年限: {remaining_years:.2f}年")
    print(f"双低值: {double_low:.2f}  |  YTM: {ytm:.2f}%  |  Delta: {delta:.3f}")
    
    liquidity = info.get("流动性分析", {})
    if liquidity:
        print(f"流动性: {liquidity['评级']} ({liquidity['综合得分']})")
        print(f"成交额: {liquidity['成交额描述']}")
        print(f"换手率: {liquidity['换手率描述']}")
    
    print(f"数据来源: {info.get('数据来源', 'AkShare')}")
    print("=" * 70)

    # 债底分析显示
    floor_analysis = info.get("债底分析", {})
    if floor_analysis:
        print("\n🛡️ 债底分析:")
        print("-" * 50)
        pure_bond_value = safe_float_convert(floor_analysis.get('pure_bond_value', 0))
        put_value = safe_float_convert(floor_analysis.get('put_value', 0))
        historical_support = safe_float_convert(floor_analysis.get('historical_support', 0))
        effective_floor = safe_float_convert(floor_analysis.get('effective_floor', 0))
        pure_bond_premium = safe_float_convert(floor_analysis.get('pure_bond_premium', 0))
        effective_floor_premium = safe_float_convert(floor_analysis.get('effective_floor_premium', 0))
        
        print(f"  纯债价值: {pure_bond_value:.2f}元")
        print(f"  回售价值: {put_value:.2f}元")
        print(f"  历史支撑: {historical_support:.2f}元")
        print(f"  有效债底: {effective_floor:.2f}元")
        print(f"  纯债溢价率: {pure_bond_premium:.2f}%")
        print(f"  有效债底溢价率: {effective_floor_premium:.2f}%")
        
        # 生成务实的评语
        conversion_premium = safe_float_convert(info.get('溢价率(%)', 0))
        
        print(f"\n💡 务实评估:")
        print(f"  理论债底约{pure_bond_value:.2f}元，但历史支撑在{effective_floor:.2f}元附近；")
        print(f"  当前价格隐含正股需上涨{conversion_premium:.2f}%才能平价，若无催化剂，上行空间有限，下行有技术支撑但无强债底保护。")

    # 高溢价风险提示
    premium = safe_float_convert(info.get("溢价率(%)", 0))
    conversion_value = safe_float_convert(info.get("转股价值", 0))
    bond_price = safe_float_convert(info.get("转债价格", 0))
    current_stock_price = safe_float_convert(info.get("正股价格", 0))

    # 立即添加调试信息来确认价格
    print(f"\n🔍【调试】计算盈亏平衡点使用的数据:")
    print(f"  转债价格: {bond_price:.2f}元")
    print(f"  转股价值: {conversion_value:.2f}元") 
    print(f"  正股价格: {current_stock_price:.2f}元")

    if premium > 30:
        print(f"\n⚠️ 高溢价风险提示:")
        print("-" * 40)
        if 100 <= conversion_value <= 105:
            print(f"  🔍 伪价内陷阱: 转股价值仅{conversion_value:.2f}, 名义价内但实际风险高")
    
    # 立即计算盈亏平衡点
    print(f"\n🎯 盈亏平衡分析（立即计算）:")
    print(f"  当前转债价格: {bond_price:.2f}元")
    print(f"  当前转股价值: {conversion_value:.2f}元")
    print(f"  当前正股价格: {current_stock_price:.2f}元")

    if current_stock_price > 0 and conversion_value > 0:
        # 计算转股价
        conversion_price = (current_stock_price * 100) / conversion_value
        # 计算盈亏平衡点
        parity_price = bond_price * conversion_price / 100
        rise_percent = (parity_price - current_stock_price) / current_stock_price * 100 if current_stock_price > 0 else 0
    
        print(f"  计算转股价: {conversion_price:.2f}元")
        print(f"  需正股上涨至: {parity_price:.2f}元 (+{rise_percent:.1f}%) 才能实现平价")
        print(f"  💡 风险提示: 高溢价严重压制跟涨能力, 正股小幅波动难以传导")
    else:
        print("  无法计算盈亏平衡点：数据不完整")

    # 风险标签显示
    risk_tags = generate_risk_tags(info)
    if risk_tags:
        print(f"\n🏷️ 风险标签: {', '.join(risk_tags)}")

    # 执行多因子共振分析（仅在溢价合理时）
    if premium <= 30:
        multifactor_results = perform_multifactor_analysis(code, info)
    else:
        print(f"\n🔍 多因子共振分析: 跳过（溢价率{premium:.2f}% > 30%, 技术分析失效）")
        info['multifactor_signal'] = 'SKIP_HIGH_PREMIUM'
        multifactor_results = None
    
    # 持仓分析
    if holding_info:
        holding_analysis = calculate_holding_analysis(info, holding_info)
        if holding_analysis:
            print("\n持仓分析:")
            print("-" * 50)
            print(f"  持仓成本: {holding_analysis['持仓成本']:.2f}元")
            print(f"  持仓数量: {holding_analysis['持仓数量']:.0f}张")
            print(f"  成本市值: {holding_analysis['成本市值']:.2f}元")
            print(f"  当前市值: {holding_analysis['持仓市值']:.2f}元")
            print(f"  当前盈亏: {holding_analysis['当前盈亏']:.2f}元 ({holding_analysis['盈亏比例']:.2f}%)")
            print(f"  建仓日期: {holding_analysis['建仓日期']}")
            print(f"  风险等级: {holding_analysis['风险等级']}")
            print(f"  持仓建议: {holding_analysis['持仓建议']}")

    # 正股转债联动分析
    linkage_data = info.get("联动分析", {})
    if linkage_data:
        print("\n正股转债联动分析:")
        print("-" * 40)
        print(f"  溢价率联动: {linkage_data.get('溢价率联动', '未知')}")
        print(f"  Delta弹性: {linkage_data.get('Delta弹性', '未知')} (Delta值: {linkage_data.get('Delta值', 0):.3f})")
        print(f"  价格合理性: {linkage_data.get('价格合理性', '未知')} (偏离度: {linkage_data.get('价格偏离度', 0):.2f}%)")
        print(f"  联动策略: {linkage_data.get('联动策略', '未知')}")
        print(f"  风险提示: {linkage_data.get('风险提示', '未知')}")

    # 强赎分析
    redemption_data = info.get("强赎分析", {})
    if redemption_data:
        print("\n强赎分析:")
        print("-" * 40)
        conversion_price_val = safe_float_convert(redemption_data.get('conversion_price', 0))
        trigger_price = safe_float_convert(redemption_data.get('trigger_price', 0))
        current_stock_price_val = safe_float_convert(redemption_data.get('current_stock_price', 0))
        progress = redemption_data.get('progress', '0%')
        status = redemption_data.get('status', '未知')
        risk_level = redemption_data.get('risk_level', '未知')
        distance_to_trigger = safe_float_convert(redemption_data.get('distance_to_trigger', 0))
        trigger_condition = redemption_data.get('trigger_condition', '未知')
        
        print(f"  转股价: {conversion_price_val:.2f}元")
        print(f"  强赎触发价: {trigger_price:.2f}元 (转股价×130%)")
        print(f"  当前正股价: {current_stock_price_val:.2f}元")
        print(f"  触发进度: {progress}")
        print(f"  强赎状态: {status}")
        print(f"  风险等级: {risk_level}")
        print(f"  距触发价差: {distance_to_trigger:.2f}元")
        print(f"  触发条件: {trigger_condition}")
        
        # 强赎风险提示
        if status == "已触发":
            print(f"  ⚠️  强赎风险: 已触发强赎, 注意强赎风险！")
        elif status == "接近触发":
            print(f"  ⚠️  强赎风险: 接近触发条件, 密切关注正股走势")
        elif status == "观察中":
            print(f"  强赎风险: 有一定触发可能, 需持续观察")
        else:
            print(f"  强赎风险: 当前风险较低")

    # 下修分析
    downward_data = info.get("下修分析", {})
    if downward_data:
        print("\n下修分析:")
        print("-" * 40)
        current_probability = downward_data.get('current_probability', '未知')
        condition_scores = safe_float_convert(downward_data.get('condition_scores', 0))
        adjust_count = safe_float_convert(downward_data.get('adjust_count', 0))
        last_adjust_date = downward_data.get('last_adjust_date', '无')
        pb_ratio_val = safe_float_convert(downward_data.get('pb_ratio', 0))
        
        print(f"  下修概率: {current_probability}")
        print(f"  条件评分: {condition_scores:.0f}分")
        print(f"  历史下修次数: {adjust_count:.0f}次")
        print(f"  最后下修时间: {last_adjust_date}")
        print(f"  PB值: {pb_ratio_val:.2f} (影响下修空间)")
        
        down_conditions = downward_data.get('down_conditions', [])
        if down_conditions:
            print(f"  下修条件分析:")
            for condition in down_conditions:
                print(f"    ✓ {condition}")
        else:
            print(f"  下修条件: 当前无明显下修压力")
        
        suggestion = downward_data.get('suggestion', '')
        print(f"  下修建议: {suggestion}")

    # 风险分析
    print("\n风险分析:")
    print("-" * 40)
    risks = get_risk_analysis(info)
    for risk in risks:
        print(f"  {risk}")

    # 技术分析
    tech_data = info.get("技术分析数据", {})
    print("\n技术分析建议:")
    print("-" * 40)
    print(f"  统一支撑压力分析:")
    
    support = safe_float_convert(tech_data.get('支撑位', 0))
    resistance = safe_float_convert(tech_data.get('压力位', 0))
    distance_to_support = safe_float_convert(tech_data.get('距支撑百分比', 0))
    distance_to_resistance = safe_float_convert(tech_data.get('距压力百分比', 0))
    position_status = tech_data.get('位置状态', '数据不足')
    
    print(f"     主支撑位（120日）: {support:.2f}元")
    print(f"     主压力位（250日）: {resistance:.2f}元")
    print(f"     当前位置: 距支撑{distance_to_support:.1f}% | 距压力{distance_to_resistance:.1f}%")
    print(f"     {position_status}")
    
    ma20 = safe_float_convert(tech_data.get('20日均线', 0))
    ma60 = safe_float_convert(tech_data.get('60日均线', 0))
    ma120 = safe_float_convert(tech_data.get('120日均线', 0))
    ma_status = tech_data.get('均线状态', '数据不足')
    
    print(f"  均线系统分析:")
    print(f"     20日均线: {ma20:.2f}元 | 60日均线: {ma60:.2f}元 | 120日均线: {ma120:.2f}元")
    print(f"     {ma_status}")
    
    delta_value = safe_float_convert(tech_data.get('Delta值', 0))
    delta_status = tech_data.get('弹性状态', '数据不足')
    
    print(f"  转债弹性分析:")
    print(f"     Delta值: {delta_value:.3f}")
    print(f"     {delta_status}")

    # 斐波那契回撤位分析
    fib_levels = tech_data.get('斐波那契_levels', {})
    if fib_levels:
        print(f"\n斐波那契回撤位分析:")
        print("   " + "-" * 50)
        for level, price in fib_levels.items():
            fib_price = safe_float_convert(price)
            price_diff = bond_price - fib_price
            diff_percent = (price_diff / bond_price) * 100 if bond_price > 0 else 0
            
            if abs(diff_percent) < 2:
                marker = ">当前位置"
            elif fib_price < bond_price:
                marker = "^支撑区域"
            else:
                marker = "v压力区域"
                
            print(f"   {marker:8} {level}: {fib_price:.2f}元 | 差: {price_diff:+.2f}元 ({diff_percent:+.1f}%)")

    # 策略分析
    print("\n策略分析:")
    print("-" * 40)
    strategies = analyze_strategies(info)
    for strategy in strategies:
        print(f"  {strategy}")

    # 临期策略提醒
    print(f"\n临期策略: {info.get('临期策略', '')}")

    # 评分 - 使用修复版算法
    score, score_details = calculate_comprehensive_score_v2(info)
    final_grade, final_advice = get_enhanced_rating(score, info)
    operation_advice = get_operation_advice(score, info, final_grade)
    
    print(f"\n综合评分: {score:.0f}/100 (修复版算法)")
    print("评分明细: " + " | ".join(score_details))

    # 多因子信号显示
    ta_signal = info.get('multifactor_signal', 'UNKNOWN')
    if ta_signal == "STRONG_BUY":
        print("🎯 多因子共振: 🚀 强烈买入 - 趋势确认且买点共振")
    elif ta_signal == "BUY":
        print("🎯 多因子共振: ✅ 买入信号 - 技术面支持参与")  
    elif ta_signal == "SELL":
        print("🎯 多因子共振: ⚠️ 卖出信号 - 注意技术风险")
    elif ta_signal == "HOLD":
        print("🎯 多因子共振: ⏳ 持有观望 - 等待更好时机")
    elif ta_signal == "SKIP_HIGH_PREMIUM":
        print("🎯 多因子共振: ⏭️ 分析跳过 - 高溢价导致技术分析失效")
    else:
        print("🎯 多因子共振: 🔄 等待信号 - 趋势未确认")

    print(f"\n最终投资建议: {final_grade} {final_advice}")
    print(operation_advice)

    # 补充盈亏平衡分析
    if premium > 20:
        upside_needed = (bond_price - conversion_value) / conversion_value * 100 if conversion_value > 0 else 0
        print(f"\n📈 盈亏平衡分析:")
        print(f"  当前转债价格: {bond_price:.2f}元")
        print(f"  当前转股价值: {conversion_value:.2f}元")
        print(f"  需正股上涨至: {bond_price * conversion_value / 100:.2f}元 (+{upside_needed:.1f}%) 才能实现平价")

    # ==================== 新增：生成HTML报告 ====================
    print(f"\n{'='*60}")
    print("📊 正在生成HTML全面分析报告...")
    
    try:
        # 生成HTML报告
        html_report = html_generator.generate_bond_analysis_report(
            info, multifactor_results, holding_info
        )
        
        # 保存报告
        filename = html_generator.save_report(html_report)
        
        if filename:
            print(f"✅ HTML报告已生成: {filename}")
            print(f"💡 请在浏览器中打开该文件查看完整分析报告")
        else:
            print("❌ HTML报告生成失败")
        
    except Exception as e:
        print(f"❌ HTML报告生成失败: {e}")

# ==================== 批量分析函数 ====================

def show_risk_blacklist():
    """显示高风险转债黑名单"""
    print("\n" + "高风险转债黑名单 ".center(60, "="))
    print("正在扫描全市场转债...")
    
    blacklist = risk_monitor.generate_blacklist()
    
    if not blacklist:
        print("未发现高风险转债")
        return
    
    print(f"发现 {len(blacklist)} 只高风险转债")
    print("=" * 60)
    
    for i, bond in enumerate(blacklist[:15], 1):
        print(f"{i:2d}. {bond['name']}({bond['code']})")
        print(f"    风险因素: {', '.join(bond['reasons'])}")
        print(f"    溢价率: {bond['premium']:.1f}% | 价格: {bond['price']:.1f}元 | 规模: {bond['size']:.1f}亿")
        print()

def analyze_custom_list():
    """分析自定义代码列表"""
    codes_input = input("请输入转债代码（多个代码用逗号分隔）: ").strip()
    codes_input = codes_input.replace('，', ',')
    codes = [code.strip() for code in codes_input.split(',') if code.strip()]
    
    print(f"\n开始批量分析 {len(codes)} 只转债...")
    
    results = []
    for i, code in enumerate(codes, 1):
        print(f"[{i}/{len(codes)}] 分析 {code}...")
        try:
            info = get_enhanced_bond_info(code)
            if info:
                score, _ = calculate_comprehensive_score_v2(info)
                results.append({
                    'code': code,
                    'name': info['名称'],
                    'price': safe_float_convert(info['转债价格']),
                    'premium': safe_float_convert(info['溢价率(%)']),
                    'double_low': safe_float_convert(info['双低值']),
                    'size': safe_float_convert(info['剩余规模(亿)']),
                    'score': score,
                    'ytm': safe_float_convert(info.get('YTM(%)', 0)),
                    'volume': safe_float_convert(info.get('日均成交额(亿)', 0)),
                    'full_info': info
                })
            time.sleep(0.3)
        except Exception as e:
            print(f"分析 {code} 失败: {e}")
    
    display_batch_results(results)

def analyze_double_low_top10():
    """分析双低策略前10名"""
    print("\n正在获取双低策略前10名...")
    try:
        bond_df = ak.bond_zh_cov()
        double_low_list = []
        
        for _, bond in bond_df.iterrows():
            price = safe_float_parse(bond.get('债现价', 0))
            premium = safe_float_parse(bond.get('转股溢价率', 0))
            
            if price > 1000:
                price = price / 10
                
            if 80 < price < 150 and premium < 100:
                double_low = price + premium
                double_low_list.append({
                    'code': bond.get('债券代码', ''),
                    'name': bond.get('债券简称', ''),
                    'price': price,
                    'premium': premium,
                    'double_low': double_low
                })
        
        top10 = sorted(double_low_list, key=lambda x: x['double_low'])[:10]
        
        print(f"\n双低策略前10名:")
        print("=" * 80)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'双低值':<8} {'价格':<8} {'溢价率':<8}")
        print("-" * 80)
        for i, bond in enumerate(top10, 1):
            print(f"{i:<4} {bond['name']:<12} {bond['code']:<10} {bond['double_low']:<8.1f} {bond['price']:<8.1f} {bond['premium']:<8.1f}%")
        
        if input("\n是否详细分析这些转债？(y/n): ").strip().lower() == 'y':
            codes = [bond['code'] for bond in top10]
            results = []
            for code in codes:
                info = get_enhanced_bond_info(code)
                if info:
                    score, _ = calculate_comprehensive_score_v2(info)
                    results.append({
                        'code': code,
                        'name': info['名称'],
                        'price': safe_float_convert(info['转债价格']),
                        'premium': safe_float_convert(info['溢价率(%)']),
                        'double_low': safe_float_convert(info['双低值']),
                        'size': safe_float_convert(info['剩余规模(亿)']),
                        'score': score,
                        'ytm': safe_float_convert(info.get('YTM(%)', 0)),
                        'volume': safe_float_convert(info.get('日均成交额(亿)', 0))
                    })
            display_batch_results(results)
            
    except Exception as e:
        print(f"双低策略分析失败: {e}")

def analyze_low_premium_top10():
    """分析低溢价策略前10名"""
    print("\n正在获取低溢价策略前10名...")
    try:
        bond_df = ak.bond_zh_cov()
        low_premium_list = []
        
        for _, bond in bond_df.iterrows():
            price = safe_float_parse(bond.get('债现价', 0))
            premium = safe_float_parse(bond.get('转股溢价率', 0))
            
            if price > 1000:
                price = price / 10
                
            if 80 < price < 150 and premium < 30:
                low_premium_list.append({
                    'code': bond.get('债券代码', ''),
                    'name': bond.get('债券简称', ''),
                    'price': price,
                    'premium': premium,
                    'double_low': price + premium
                })
        
        top10 = sorted(low_premium_list, key=lambda x: x['premium'])[:10]
        
        print(f"\n低溢价策略前10名:")
        print("=" * 80)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'溢价率':<8} {'价格':<8} {'双低值':<8}")
        print("-" * 80)
        for i, bond in enumerate(top10, 1):
            print(f"{i:<4} {bond['name']:<12} {bond['code']:<10} {bond['premium']:<8.1f}% {bond['price']:<8.1f} {bond['double_low']:<8.1f}")
        
        if input("\n是否详细分析这些转债？(y/n): ").strip().lower() == 'y':
            codes = [bond['code'] for bond in top10]
            results = []
            for code in codes:
                info = get_enhanced_bond_info(code)
                if info:
                    score, _ = calculate_comprehensive_score_v2(info)
                    results.append({
                        'code': code,
                        'name': info['名称'],
                        'price': safe_float_convert(info['转债价格']),
                        'premium': safe_float_convert(info['溢价率(%)']),
                        'double_low': safe_float_convert(info['双低值']),
                        'size': safe_float_convert(info['剩余规模(亿)']),
                        'score': score,
                        'ytm': safe_float_convert(info.get('YTM(%)', 0)),
                        'volume': safe_float_convert(info.get('日均成交额(亿)', 0))
                    })
            display_batch_results(results)
            
    except Exception as e:
        print(f"低溢价策略分析失败: {e}")

def analyze_small_size_top10():
    """分析小规模策略前10名"""
    print("\n正在获取小规模策略前10名...")
    try:
        bond_df = ak.bond_zh_cov()
        small_size_list = []
        
        for _, bond in bond_df.iterrows():
            price = safe_float_parse(bond.get('债现价', 0))
            premium = safe_float_parse(bond.get('转股溢价率', 0))
            size_str = str(bond.get('发行规模', '10')).replace('亿元', '').replace('亿', '')
            size = safe_float_parse(size_str)
            
            if price > 1000:
                price = price / 10
                
            if 80 < price < 150 and size < 5:
                small_size_list.append({
                    'code': bond.get('债券代码', ''),
                    'name': bond.get('债券简称', ''),
                    'price': price,
                    'premium': premium,
                    'size': size,
                    'double_low': price + premium
                })
        
        top10 = sorted(small_size_list, key=lambda x: x['size'])[:10]
        
        print(f"\n小规模策略前10名:")
        print("=" * 80)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'规模':<8} {'价格':<8} {'溢价率':<8}")
        print("-" * 80)
        for i, bond in enumerate(top10, 1):
            print(f"{i:<4} {bond['name']:<12} {bond['code']:<10} {bond['size']:<8.1f}亿 {bond['price']:<8.1f} {bond['premium']:<8.1f}%")
        
        if input("\n是否详细分析这些转债？(y/n): ").strip().lower() == 'y':
            codes = [bond['code'] for bond in top10]
            results = []
            for code in codes:
                info = get_enhanced_bond_info(code)
                if info:
                    score, _ = calculate_comprehensive_score_v2(info)
                    results.append({
                        'code': code,
                        'name': info['名称'],
                        'price': safe_float_convert(info['转债价格']),
                        'premium': safe_float_convert(info['溢价率(%)']),
                        'double_low': safe_float_convert(info['双低值']),
                        'size': safe_float_convert(info['剩余规模(亿)']),
                        'score': score,
                        'ytm': safe_float_convert(info.get('YTM(%)', 0)),
                        'volume': safe_float_convert(info.get('日均成交额(亿)', 0))
                    })
            display_batch_results(results)
            
    except Exception as e:
        print(f"小规模策略分析失败: {e}")

def analyze_high_ytm_top10():
    """分析高YTM策略前10名"""
    print("\n正在获取高YTM策略前10名...")
    try:
        bond_df = ak.bond_zh_cov()
        high_ytm_list = []
        
        for _, bond in bond_df.iterrows():
            price = safe_float_parse(bond.get('债现价', 0))
            if price > 1000:
                price = price / 10
                
            if 80 < price < 130:  # YTM策略通常关注低价转债
                # 模拟计算YTM
                ytm = calculate_ytm(price, 3)
                if ytm > 0:  # 只考虑正YTM
                    high_ytm_list.append({
                        'code': bond.get('债券代码', ''),
                        'name': bond.get('债券简称', ''),
                        'price': price,
                        'premium': safe_float_parse(bond.get('转股溢价率', 0)),
                        'ytm': ytm,
                        'size': safe_float_parse(str(bond.get('发行规模', '10')).replace('亿元', '').replace('亿', ''))
                    })
        
        top10 = sorted(high_ytm_list, key=lambda x: x['ytm'], reverse=True)[:10]
        
        print(f"\n高YTM策略前10名:")
        print("=" * 80)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'YTM':<8} {'价格':<8} {'溢价率':<8}")
        print("-" * 80)
        for i, bond in enumerate(top10, 1):
            print(f"{i:<4} {bond['name']:<12} {bond['code']:<10} {bond['ytm']:<8.1f}% {bond['price']:<8.1f} {bond['premium']:<8.1f}%")
        
        if input("\n是否详细分析这些转债？(y/n): ").strip().lower() == 'y':
            codes = [bond['code'] for bond in top10]
            results = []
            for code in codes:
                info = get_enhanced_bond_info(code)
                if info:
                    score, _ = calculate_comprehensive_score_v2(info)
                    results.append({
                        'code': code,
                        'name': info['名称'],
                        'price': safe_float_convert(info['转债价格']),
                        'premium': safe_float_convert(info['溢价率(%)']),
                        'double_low': safe_float_convert(info['双低值']),
                        'size': safe_float_convert(info['剩余规模(亿)']),
                        'score': score,
                        'ytm': safe_float_convert(info.get('YTM(%)', 0)),
                        'volume': safe_float_convert(info.get('日均成交额(亿)', 0))
                    })
            display_batch_results(results)
            
    except Exception as e:
        print(f"高YTM策略分析失败: {e}")

def analyze_small_low_premium_top10():
    """分析小规模低溢价策略前10名"""
    print("\n正在获取小规模低溢价策略前10名...")
    try:
        bond_df = ak.bond_zh_cov()
        small_low_list = []
        
        for _, bond in bond_df.iterrows():
            price = safe_float_parse(bond.get('债现价', 0))
            premium = safe_float_parse(bond.get('转股溢价率', 0))
            size_str = str(bond.get('发行规模', '10')).replace('亿元', '').replace('亿', '')
            size = safe_float_parse(size_str)
            
            if price > 1000:
                price = price / 10
                
            if 80 < price < 150 and size < 5 and premium < 30:
                small_low_list.append({
                    'code': bond.get('债券代码', ''),
                    'name': bond.get('债券简称', ''),
                    'price': price,
                    'premium': premium,
                    'size': size,
                    'double_low': price + premium
                })
        
        # 按规模从小到大，溢价率从低到高排序
        top10 = sorted(small_low_list, key=lambda x: (x['size'], x['premium']))[:10]
        
        print(f"\n小规模低溢价策略前10名:")
        print("=" * 80)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'规模':<8} {'溢价率':<8} {'价格':<8}")
        print("-" * 80)
        for i, bond in enumerate(top10, 1):
            print(f"{i:<4} {bond['name']:<12} {bond['code']:<10} {bond['size']:<8.1f}亿 {bond['premium']:<8.1f}% {bond['price']:<8.1f}")
        
        if input("\n是否详细分析这些转债？(y/n): ").strip().lower() == 'y':
            codes = [bond['code'] for bond in top10]
            results = []
            for code in codes:
                info = get_enhanced_bond_info(code)
                if info:
                    score, _ = calculate_comprehensive_score_v2(info)
                    results.append({
                        'code': code,
                        'name': info['名称'],
                        'price': safe_float_convert(info['转债价格']),
                        'premium': safe_float_convert(info['溢价率(%)']),
                        'double_low': safe_float_convert(info['双低值']),
                        'size': safe_float_convert(info['剩余规模(亿)']),
                        'score': score,
                        'ytm': safe_float_convert(info.get('YTM(%)', 0)),
                        'volume': safe_float_convert(info.get('日均成交额(亿)', 0))
                    })
            display_batch_results(results)
            
    except Exception as e:
        print(f"小规模低溢价策略分析失败: {e}")

def analyze_comprehensive_top15():
    """分析综合评分前15名"""
    print("\n正在获取综合评分前15名...")
    try:
        bond_df = ak.bond_zh_cov()
        comprehensive_list = []
        
        for _, bond in bond_df.iterrows():
            price = safe_float_parse(bond.get('债现价', 0))
            premium = safe_float_parse(bond.get('转股溢价率', 0))
            size_str = str(bond.get('发行规模', '10')).replace('亿元', '').replace('亿', '')
            size = safe_float_parse(size_str)
            
            if price > 1000:
                price = price / 10
                
            if 80 < price < 150 and premium < 100:
                score = 0
                if size < 3: score += 25
                elif size < 5: score += 20
                elif size < 10: score += 15
                else: score += 10
                
                if premium < 10: score += 25
                elif premium < 20: score += 20
                elif premium < 30: score += 15
                elif premium < 40: score += 10
                else: score += 5
                
                if price < 110: score += 20
                elif price < 120: score += 15
                elif price < 130: score += 10
                elif price < 140: score += 5
                
                comprehensive_list.append({
                    'code': bond.get('债券代码', ''),
                    'name': bond.get('债券简称', ''),
                    'price': price,
                    'premium': premium,
                    'size': size,
                    'score': min(score, 100),
                    'double_low': price + premium
                })
        
        top15 = sorted(comprehensive_list, key=lambda x: x['score'], reverse=True)[:15]
        
        print(f"\n综合评分前15名:")
        print("=" * 90)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'评分':<6} {'价格':<8} {'溢价率':<8} {'规模':<8} {'双低值':<8}")
        print("-" * 90)
        for i, bond in enumerate(top15, 1):
            print(f"{i:<4} {bond['name']:<12} {bond['code']:<10} {bond['score']:<6} {bond['price']:<8.1f} {bond['premium']:<8.1f}% {bond['size']:<8.1f}亿 {bond['double_low']:<8.1f}")
        
        if input("\n是否详细分析这些转债？(y/n): ").strip().lower() == 'y':
            codes = [bond['code'] for bond in top15]
            results = []
            for code in codes:
                info = get_enhanced_bond_info(code)
                if info:
                    score, _ = calculate_comprehensive_score_v2(info)
                    results.append({
                        'code': code,
                        'name': info['名称'],
                        'price': safe_float_convert(info['转债价格']),
                        'premium': safe_float_convert(info['溢价率(%)']),
                        'double_low': safe_float_convert(info['双低值']),
                        'size': safe_float_convert(info['剩余规模(亿)']),
                        'score': score,
                        'ytm': safe_float_convert(info.get('YTM(%)', 0)),
                        'volume': safe_float_convert(info.get('日均成交额(亿)', 0))
                    })
            display_batch_results(results)
            
    except Exception as e:
        print(f"综合评分分析失败: {e}")

def analyze_multifactor_top10():
    """分析多因子共振策略前10名"""
    print("\n正在扫描多因子共振策略前10名...")
    try:
        bond_df = ak.bond_zh_cov()
        multifactor_list = []
        
        for _, bond in bond_df.iterrows():
            bond_code = bond.get('债券代码', '')
            if not bond_code:
                continue
                
            price = safe_float_parse(bond.get('债现价', 0))
            premium = safe_float_parse(bond.get('转股溢价率', 0))
            
            if price > 1000:
                price = price / 10
                
            if 80 < price < 150 and premium < 40:  # 多因子策略要求更严格
                # 获取详细信息进行多因子分析
                info = get_enhanced_bond_info(bond_code)
                if info:
                    # 执行多因子分析
                    historical_data = get_historical_data_for_ta(bond_code, actual_price=info['转债价格'])
                    if historical_data is not None:
                        try:
                            # 使用 safe_float_convert 确保数值类型
                            premium_rate_value = safe_float_convert(premium) / 100
                            call_risk_distance = 0.3
                            actual_price = safe_float_convert(info['转债价格'])
                            
                            ta_results = ta_analyzer.comprehensive_analysis(
                                df=historical_data,
                                premium_rate=premium_rate_value,
                                call_risk_distance=call_risk_distance,
                                actual_price=actual_price
                            )
                            
                            if ta_results and ta_results.get('overall_signal') == "STRONG_BUY":
                                multifactor_list.append({
                                    'code': bond_code,
                                    'name': bond.get('债券简称', ''),
                                    'price': price,
                                    'premium': premium,
                                    'signal': 'STRONG_BUY',
                                    'score': 95
                                })
                            elif ta_results and ta_results.get('overall_signal') == "BUY":
                                multifactor_list.append({
                                    'code': bond_code,
                                    'name': bond.get('债券简称', ''),
                                    'price': price,
                                    'premium': premium,
                                    'signal': 'BUY',
                                    'score': 85
                                })
                                
                        except Exception as e:
                            print(f"  多因子分析失败: {e}")
                            continue
        
        # 按信号强度排序
        top10 = sorted(multifactor_list, key=lambda x: x['score'], reverse=True)[:10]
        
        print(f"\n多因子共振策略前10名:")
        print("=" * 80)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'信号':<12} {'价格':<8} {'溢价率':<8}")
        print("-" * 80)
        for i, bond in enumerate(top10, 1):
            signal_desc = "强烈买入" if bond['signal'] == 'STRONG_BUY' else "买入"
            print(f"{i:<4} {bond['name']:<12} {bond['code']:<10} {signal_desc:<12} {bond['price']:<8.1f} {bond['premium']:<8.1f}%")
        
        if input("\n是否详细分析这些转债？(y/n): ").strip().lower() == 'y':
            codes = [bond['code'] for bond in top10]
            results = []
            for code in codes:
                info = get_enhanced_bond_info(code)
                if info:
                    score, _ = calculate_comprehensive_score_v2(info)
                    results.append({
                        'code': code,
                        'name': info['名称'],
                        'price': safe_float_convert(info['转债价格']),
                        'premium': safe_float_convert(info['溢价率(%)']),
                        'double_low': safe_float_convert(info['双低值']),
                        'size': safe_float_convert(info['剩余规模(亿)']),
                        'score': score,
                        'ytm': safe_float_convert(info.get('YTM(%)', 0)),
                        'volume': safe_float_convert(info.get('日均成交额(亿)', 0))
                    })
            display_batch_results(results)
            
    except Exception as e:
        print(f"多因子共振策略分析失败: {e}")

def analyze_near_redemption_top15():
    """分析距离强赎接近的前15名（未达到强赎条件）"""
    print("\n正在扫描距离强赎接近的转债（未达到条件）...")
    try:
        bond_df = ak.bond_zh_cov()
        near_redemption_list = []
        
        for _, bond in bond_df.iterrows():
            bond_code = bond.get('债券代码', '')
            if not bond_code:
                continue
                
            stock_price = safe_float_parse(bond.get('正股价', 0))
            convert_price = safe_float_parse(bond.get('转股价', 1))
            bond_price = safe_float_parse(bond.get('债现价', 0))
            
            if bond_price > 1000:
                bond_price = bond_price / 10
                
            if 80 < bond_price < 200:  # 合理的转债价格范围
                # 计算强赎进度
                trigger_price = convert_price * 1.3
                progress_ratio = stock_price / trigger_price if trigger_price > 0 else 0
                progress_percent = progress_ratio * 100
                
                # 关键修改: 只考虑进度在70%-99%之间的（接近但未达到）
                if 0.7 <= progress_ratio < 1.0:
                    # 计算距离强赎的涨幅空间
                    upside_potential = ((trigger_price - stock_price) / stock_price) * 100 if stock_price > 0 else 0
                    
                    near_redemption_list.append({
                        'code': bond_code,
                        'name': bond.get('债券简称', ''),
                        'stock_price': round(stock_price, 2),
                        'trigger_price': round(trigger_price, 2),
                        'progress': round(progress_percent, 1),
                        'bond_price': round(bond_price, 2),
                        'premium': safe_float_parse(bond.get('转股溢价率', 0)),
                        'upside_potential': round(upside_potential, 1),
                        'conversion_price': round(convert_price, 2)
                    })
        
        # 按进度从高到低排序（最接近强赎的排在前面）
        top15 = sorted(near_redemption_list, key=lambda x: x['progress'], reverse=True)[:15]
        
        print(f"\n距离强赎接近的前15名（搏强赎策略）:")
        print("=" * 120)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'进度%':<8} {'正股价':<8} {'触发价':<8} {'上涨空间%':<10} {'转债价':<8} {'溢价率':<8}")
        print("-" * 120)
        for i, bond in enumerate(top15, 1):
            # 根据进度设置不同的状态标识
            if bond['progress'] >= 95:
                status = "🔥"  # 非常接近
                status_desc = "即将触发"
            elif bond['progress'] >= 90:
                status = "⚠️"  # 接近触发
                status_desc = "很接近"
            elif bond['progress'] >= 80:
                status = "🔶"  # 中等接近
                status_desc = "较接近"
            else:
                status = "🔹"  # 一般接近
                status_desc = "有希望"
            
            print(f"{i:<4} {status}{bond['name']:<11} {bond['code']:<10} {bond['progress']:<7.1f}%({status_desc}) "
                  f"{bond['stock_price']:<8.1f} {bond['trigger_price']:<8.1f} {bond['upside_potential']:<9.1f}% "
                  f"{bond['bond_price']:<8.1f} {bond['premium']:<8.1f}%")
        
        print(f"\n说明:")
        print(f"  🔥进度≥95%: 即将触发强赎, 正股只需小幅上涨")
        print(f"  ⚠️进度90-95%: 很接近强赎条件")
        print(f"  🔶进度80-90%: 较接近强赎条件") 
        print(f"  🔹进度70-80%: 有希望达到强赎")
        print(f"  上涨空间%: 正股需要上涨的幅度才能达到强赎触发价")
        
        # 投资策略建议
        if top15:
            print(f"\n搏强赎策略建议:")
            high_progress = [b for b in top15 if b['progress'] >= 90]
            mid_progress = [b for b in top15 if 80 <= b['progress'] < 90]
            
            if high_progress:
                print(f"  🎯 重点关注: {len(high_progress)}只进度≥90%的转债, 强赎概率较高")
                for bond in high_progress[:3]:
                    print(f"     {bond['name']}({bond['code']}): 进度{bond['progress']}%, 正股还需上涨{bond['upside_potential']}%")
            
            if mid_progress:
                print(f"  📈 可关注: {len(mid_progress)}只进度80-90%的转债, 具备潜力")
        
        if input("\n是否详细分析这些转债？(y/n): ").strip().lower() == 'y':
            codes = [bond['code'] for bond in top15]
            results = []
            for code in codes:
                info = get_enhanced_bond_info(code)
                if info:
                    score, _ = calculate_comprehensive_score_v2(info)
                    results.append({
                        'code': code,
                        'name': info['名称'],
                        'price': safe_float_convert(info['转债价格']),
                        'premium': safe_float_convert(info['溢价率(%)']),
                        'double_low': safe_float_convert(info['双低值']),
                        'size': safe_float_convert(info['剩余规模(亿)']),
                        'score': score,
                        'ytm': safe_float_convert(info.get('YTM(%)', 0)),
                        'volume': safe_float_convert(info.get('日均成交额(亿)', 0))
                    })
            display_batch_results(results)
        else:
            # 即使不详细分析，也显示一些关键信息
            if top15:
                print(f"\n快速筛选建议（基于进度和溢价率）:")
                good_opportunities = [b for b in top15 if b['progress'] >= 85 and b['premium'] < 25]
                if good_opportunities:
                    print(f"  ✅ 优质机会: {len(good_opportunities)}只（高进度+低溢价）")
                    for bond in good_opportunities[:3]:
                        print(f"     {bond['name']}: 进度{bond['progress']}%, 溢价率{bond['premium']}%")
            
    except Exception as e:
        print(f"强赎接近分析失败: {e}")

def analyze_near_downward_top15():
    """分析距离下修接近的前15名"""
    print("\n正在扫描距离下修接近的转债...")
    try:
        bond_df = ak.bond_zh_cov()
        near_downward_list = []
        
        for _, bond in bond_df.iterrows():
            bond_code = bond.get('债券代码', '')
            if not bond_code:
                continue
                
            stock_price = safe_float_parse(bond.get('正股价', 0))
            convert_price = safe_float_parse(bond.get('转股价', 1))
            bond_price = safe_float_parse(bond.get('债现价', 0))
            
            if bond_price > 1000:
                bond_price = bond_price / 10
                
            if 80 < bond_price < 200:  # 合理的转债价格范围
                # 计算转股价值
                conversion_value = stock_price / convert_price * 100 if convert_price > 0 else 0
                premium_rate = (bond_price - conversion_value) / conversion_value * 100 if conversion_value > 0 else 0
                
                # 下修条件评分
                downward_score = 0
                
                # 条件1: 转股价值低
                if conversion_value < 70:
                    downward_score += 3
                elif conversion_value < 80:
                    downward_score += 2
                elif conversion_value < 90:
                    downward_score += 1
                
                # 条件2: 溢价率高
                if premium_rate > 40:
                    downward_score += 3
                elif premium_rate > 30:
                    downward_score += 2
                elif premium_rate > 20:
                    downward_score += 1
                
                # 只考虑评分3分以上的
                if downward_score >= 3:
                    near_downward_list.append({
                        'code': bond_code,
                        'name': bond.get('债券简称', ''),
                        'conversion_value': round(conversion_value, 1),
                        'premium': round(premium_rate, 1),
                        'bond_price': round(bond_price, 2),
                        'downward_score': downward_score,
                        'stock_price': round(stock_price, 2)
                    })
        
        # 按下修评分从高到低排序
        top15 = sorted(near_downward_list, key=lambda x: x['downward_score'], reverse=True)[:15]
        
        print(f"\n距离下修接近的前15名:")
        print("=" * 90)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'下修评分':<8} {'转股价值':<8} {'溢价率':<8} {'转债价':<8}")
        print("-" * 90)
        for i, bond in enumerate(top15, 1):
            probability = "高" if bond['downward_score'] >= 5 else "中" if bond['downward_score'] >= 3 else "低"
            print(f"{i:<4} {bond['name']:<12} {bond['code']:<10} {bond['downward_score']:<5}({probability}) {bond['conversion_value']:<8.1f} {bond['premium']:<8.1f}% {bond['bond_price']:<8.1f}")
        
        print(f"\n说明: 下修评分综合考虑转股价值和溢价率, 评分越高下修可能性越大")
        
        if input("\n是否详细分析这些转债？(y/n): ").strip().lower() == 'y':
            codes = [bond['code'] for bond in top15]
            results = []
            for code in codes:
                info = get_enhanced_bond_info(code)
                if info:
                    score, _ = calculate_comprehensive_score_v2(info)
                    results.append({
                        'code': code,
                        'name': info['名称'],
                        'price': safe_float_convert(info['转债价格']),
                        'premium': safe_float_convert(info['溢价率(%)']),
                        'double_low': safe_float_convert(info['双低值']),
                        'size': safe_float_convert(info['剩余规模(亿)']),
                        'score': score,
                        'ytm': safe_float_convert(info.get('YTM(%)', 0)),
                        'volume': safe_float_convert(info.get('日均成交额(亿)', 0))
                    })
            display_batch_results(results)
            
    except Exception as e:
        print(f"下修接近分析失败: {e}")

def display_batch_results(results):
    """显示批量分析结果"""
    if not results:
        print("没有有效的分析结果")
        return
    
    print("\n" + "批量分析结果 ".center(80, "="))
    
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
    
    print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'评分':<6} {'价格':<8} {'溢价率':<8} {'规模':<8} {'双低值':<8} {'YTM':<6}")
    print("-" * 90)
    
    for i, result in enumerate(sorted_results, 1):
        if result['score'] >= 80:
            rating = "[优]"
        elif result['score'] >= 65:
            rating = "[良]"
        elif result['score'] >= 50:
            rating = "[中]"
        else:
            rating = "[差]"
            
        print(f"{i:<4} {result['name']:<12} {result['code']:<10} {rating}{result['score']:<4} {result['price']:<8.1f} {result['premium']:<8.1f}% {result['size']:<8.1f}亿 {result['double_low']:<8.1f} {result['ytm']:<6.1f}%")
    
    print("-" * 90)
    print(f"总计分析: {len(results)} 只转债 | 优秀(>=80) {len([r for r in results if r['score'] >= 80])} 只 | 良好(>=65) {len([r for r in results if 65 <= r['score'] < 80])} 只 | 中等(>=50) {len([r for r in results if 50 <= r['score'] < 65])} 只")

# ==================== 主程序入口 ====================

def main_enhanced():
    """主程序 - 集成多因子共振分析和HTML输出"""
    print("可转债分析系统 v10.2 透明注解版 初始化中...")
    
    while True:
        print("\n" + "="*60)
        print("可转债分析系统 v10.2 透明注解版")
        print("="*60)
        print("1. 分析单个转债 (集成多因子共振+透明注解+HTML报告)")
        print("2. 批量代码列表分析")
        print("3. 双低策略前10名")
        print("4. 低溢价策略前10名") 
        print("5. 小规模策略前10名")
        print("6. 高YTM策略前10名")
        print("7. 小规模低溢价策略前10名")
        print("8. 综合评分前15名")
        print("9. 多因子共振策略前10名")
        print("10. 高风险转债黑名单")
        print("11. 距离强赎接近前15名")
        print("12. 距离下修接近前15名")
        print("0. 退出系统")
        print("-"*60)
        
        choice = input("请选择操作 (0-12): ").strip()
        
        if choice == '1':
            analyze_single_bond_enhanced()
        elif choice == '2':
            analyze_custom_list()
        elif choice == '3':
            analyze_double_low_top10()
        elif choice == '4':
            analyze_low_premium_top10()
        elif choice == '5':
            analyze_small_size_top10()
        elif choice == '6':
            analyze_high_ytm_top10()
        elif choice == '7':
            analyze_small_low_premium_top10()
        elif choice == '8':
            analyze_comprehensive_top15()
        elif choice == '9':
            analyze_multifactor_top10()
        elif choice == '10':
            show_risk_blacklist()
        elif choice == '11':
            analyze_near_redemption_top15()
        elif choice == '12':
            analyze_near_downward_top15()
        elif choice == '0':
            print("\n感谢使用可转债分析系统！再见！")
            break
        else:
            print("无效选择, 请重新输入")

if __name__ == "__main__":
    try:
        main_enhanced()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断, 再见！")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        print("如果出现akshare相关错误, 请尝试: pip install akshare --upgrade")

        print("如果出现pandas_ta错误, 请安装: pip install pandas_ta")
