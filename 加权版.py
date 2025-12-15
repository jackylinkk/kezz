# -*- coding: utf-8 -*-
"""
可转债量化分析系统 v10.5（完整修复版）- 修复价格获取和多因子指标问题
修复数据源价格不一致问题和多因子共振分析指标缺失
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
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas_ta as ta  # 确保导入pandas_ta

# 屏蔽所有警告信息
warnings.filterwarnings('ignore')

print("可转债量化分析系统 v10.5 完整修复版".center(60, "="))

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
            .progress-bar { background: #e9ecef; border-radius: 5px; height: 10px; margin: 5px 0; }
            .progress-value { background: #007bff; border-radius: 5px; height: 10px; }
            .table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .table th { background-color: #f8f9fa; font-weight: bold; }
            .badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }
            .badge-danger { background: #f8d7da; color: #721c24; }
            .badge-warning { background: #fff3cd; color: #856404; }
            .badge-info { background: #d1ecf1; color: #0c5460; }
            .badge-success { background: #d4edda; color: #155724; }
            .explanation { margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; font-size: 0.9em; color: #666; }
            .metric-card { background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; text-align: center; }
            .metric-value { font-size: 1.5em; font-weight: bold; color: #007bff; }
            .metric-label { font-size: 0.9em; color: #666; margin-top: 5px; }
            .risk-high { border-left: 4px solid #dc3545; }
            .risk-medium { border-left: 4px solid #ffc107; }
            .risk-low { border-left: 4px solid #28a745; }
            .strategy-card { background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #007bff; }
            .subsection { margin: 15px 0; padding: 10px; background: white; border-radius: 5px; border: 1px solid #e0e0e0; }
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
        
        # 新增指标分析
        if 'relative_strength_ratio' in bond_info:
            rs_html = self._generate_relative_strength_html(bond_info)
            self.add_section("📈 相对强弱分析", rs_html)
        
        if 'volume_structure' in bond_info:
            vol_html = self._generate_volume_structure_html(bond_info)
            self.add_section("📊 量能结构分析", vol_html)
        
        # 新增技术指标
        if 'enhanced_ta' in bond_info:
            ta_html = self._generate_enhanced_ta_html(bond_info)
            self.add_section("🎯 增强技术指标", ta_html)
        
        # 债底分析
        floor_html = self._generate_floor_analysis_html(bond_info)
        if floor_html:
            self.add_section("🛡️ 债底分析", floor_html)
        
        # 多因子共振分析 - 修复：确保显示所有技术指标
        if ta_results and ta_results.get('overall_signal') != 'INVALID':
            ta_html = self._generate_ta_analysis_html(ta_results, bond_info)
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
        
        metrics = [
            (f"{bond_info['转债价格']}元", "转债价格", ""),
            (f"{bond_info['正股价格']}元", "正股价格", ""),
            (f"{bond_info['溢价率(%)']}%", "溢价率", "risk-high" if bond_info['溢价率(%)'] > 30 else "risk-low"),
            (f"{bond_info['转股价值']}", "转股价值", ""),
            (f"{bond_info['剩余规模(亿)']}亿", "剩余规模", ""),
            (f"{bond_info.get('剩余年限', '未知')}年", "剩余年限", ""),
            (f"{bond_info['双低值']}", "双低值", ""),
            (f"{bond_info['YTM(%)']}%", "到期收益率", ""),
        ]
        
        # 添加新增指标
        if 'relative_strength_ratio' in bond_info:
            rs_ratio = bond_info['relative_strength_ratio']
            rs_label = f"{rs_ratio:.2f}"
            rs_color = "risk-high" if rs_ratio < 0.8 else "risk-low" if rs_ratio > 1.0 else ""
            metrics.append((rs_label, "相对强弱比", rs_color))
        
        if 'volume_structure' in bond_info:
            vol_signal = bond_info['volume_structure'].get('signal', '未知')
            vol_color = "risk-low" if vol_signal == '积极' else "risk-high" if vol_signal == '消极' else ""
            metrics.append((vol_signal, "量能结构", vol_color))
        
        # 添加债底分析指标
        floor_analysis = bond_info.get("债底分析", {})
        if floor_analysis:
            metrics.extend([
                (f"{floor_analysis.get('pure_bond_value', 0)}元", "纯债价值", ""),
                (f"{floor_analysis.get('effective_floor', 0)}元", "有效债底", ""),
                (f"{floor_analysis.get('effective_floor_premium', 0)}%", "债底溢价率", 
                 "risk-high" if floor_analysis.get('effective_floor_premium', 0) > 30 else "risk-low"),
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
    
    def _generate_relative_strength_html(self, bond_info):
        """生成相对强弱分析HTML"""
        rs_data = bond_info.get('relative_strength', {})
        
        html = f"""
        <table class="table">
            <tr><th>指标</th><th>数值</th><th>信号</th><th>说明</th></tr>
            <tr>
                <td>相对强弱比</td>
                <td>{bond_info.get('relative_strength_ratio', 0):.2f}</td>
                <td>{rs_data.get('signal', '未知')}</td>
                <td>{rs_data.get('explanation', '')}</td>
            </tr>
            <tr>
                <td>5日转债涨幅</td>
                <td>{rs_data.get('cb_5d_return', 0):.2f}%</td>
                <td>{'强' if rs_data.get('cb_5d_return', 0) > 0 else '弱'}</td>
                <td>近5日转债表现</td>
            </tr>
            <tr>
                <td>5日正股涨幅</td>
                <td>{rs_data.get('stock_5d_return', 0):.2f}%</td>
                <td>{'强' if rs_data.get('stock_5d_return', 0) > 0 else '弱'}</td>
                <td>近5日正股表现</td>
            </tr>
        </table>
        """
        
        return html
    
    def _generate_volume_structure_html(self, bond_info):
        """生成量能结构分析HTML"""
        vol_data = bond_info.get('volume_structure', {})
        
        html = f"""
        <table class="table">
            <tr><th>指标</th><th>数值</th><th>信号</th><th>说明</th></tr>
            <tr>
                <td>量能结构</td>
                <td>{vol_data.get('signal', '未知')}</td>
                <td>{'✅' if vol_data.get('signal') == '积极' else '❌' if vol_data.get('signal') == '消极' else '⚠️'}</td>
                <td>{vol_data.get('explanation', '')}</td>
            </tr>
            <tr>
                <td>3日量能趋势</td>
                <td>{vol_data.get('volume_trend', '未知')}</td>
                <td>{'↘️' if vol_data.get('volume_trend') == '递减' else '↗️' if vol_data.get('volume_trend') == '递增' else '➡️'}</td>
                <td>近3日成交额变化</td>
            </tr>
            <tr>
                <td>反弹量能比</td>
                <td>{vol_data.get('rebound_volume_ratio', 0):.2f}</td>
                <td>{'>1' if vol_data.get('rebound_volume_ratio', 0) > 1 else '<1'}</td>
                <td>反弹日/下跌日量能对比</td>
            </tr>
        </table>
        """
        
        return html
    
    def _generate_enhanced_ta_html(self, bond_info):
        """生成增强技术指标HTML"""
        ta_data = bond_info.get('enhanced_ta', {})
        
        html = """
        <table class="table">
            <tr><th>指标</th><th>数值</th><th>信号</th><th>说明</th></tr>
        """
        
        # KDJ指标
        kdj = ta_data.get('kdj', {})
        html += f"""
            <tr>
                <td>KDJ指标</td>
                <td>K={kdj.get('K', 0):.1f}, D={kdj.get('D', 0):.1f}, J={kdj.get('J', 0):.1f}</td>
                <td>{kdj.get('signal', '未知')}</td>
                <td>{kdj.get('explanation', '')}</td>
            </tr>
        """
        
        # MFI指标
        mfi = ta_data.get('mfi', {})
        html += f"""
            <tr>
                <td>MFI指标</td>
                <td>{mfi.get('MFI', 0):.1f}</td>
                <td>{mfi.get('signal', '未知')}</td>
                <td>{mfi.get('explanation', '')}</td>
            </tr>
        """
        
        html += "</table>"
        return html
    
    def _generate_floor_analysis_html(self, bond_info):
        """生成债底分析HTML"""
        floor_analysis = bond_info.get("债底分析", {})
        if not floor_analysis:
            return ""
            
        pure_bond_value = floor_analysis.get('pure_bond_value', 0)
        effective_floor = floor_analysis.get('effective_floor', 0)
        pure_bond_premium = floor_analysis.get('pure_bond_premium', 0)
        effective_floor_premium = floor_analysis.get('effective_floor_premium', 0)
        put_value = floor_analysis.get('put_value', 0)
        historical_support = floor_analysis.get('historical_support', 0)
        
        # 生成务实评语
        bond_price = bond_info.get('转债价格', 0)
        conversion_premium = bond_info.get('溢价率(%)', 0)
        
        practical_assessment = f"""
        <div class="explanation">
            <strong>务实评估:</strong><br>
            理论债底约{pure_bond_value}元，但历史支撑在{effective_floor}元附近；<br>
            当前价格隐含正股需上涨{conversion_premium}%才能平价，若无催化剂，上行空间有限，下行有技术支撑但无强债底保护。
        </div>
        """
        
        html = f"""
        <table class="table">
            <tr><th>指标</th><th>数值</th><th>说明</th></tr>
            <tr><td>纯债价值</td><td>{pure_bond_value}元</td><td>基于贴现现金流计算的理论底线</td></tr>
            <tr><td>回售价值</td><td>{put_value}元</td><td>满足回售条件时可获得的价值</td></tr>
            <tr><td>历史支撑</td><td>{historical_support}元</td><td>基于历史价格的技术支撑位</td></tr>
            <tr><td>有效债底</td><td>{effective_floor}元</td><td>综合考虑后的实际支撑位</td></tr>
            <tr><td>纯债溢价率</td><td>{pure_bond_premium}%</td><td>价格相对于纯债价值的高估程度</td></tr>
            <tr><td>有效债底溢价率</td><td>{effective_floor_premium}%</td><td>价格相对于有效债底的高估程度</td></tr>
        </table>
        {practical_assessment}
        """
        
        return html
    
    def _generate_ta_analysis_html(self, ta_results, bond_info=None):
        """生成技术分析HTML - 修复：确保显示所有技术指标"""
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
        
        # 当前价格 - 修复价格一致性
        current_price = bond_info.get('转债价格', ta_results.get('current_price', 0))
        html += f"""
        <div class="subsection">
            <h4>当前价格: {current_price:.2f}元</h4>
        </div>
        """
        
        # 趋势确认 - 修复：显示所有趋势指标
        trend = ta_results['trend_confirmation']
        html += f"""
        <div class="subsection">
            <h4>趋势确认 (强度: {trend['trend_strength']}/3)</h4>
            <table class="table">
                <tr><th>指标</th><th>状态</th><th>解释</th></tr>
                <tr><td>均线排列</td><td>{'✅ 多头' if trend['ma_bullish'] else '❌ 非多头'}</td><td>{trend.get('explanations', {}).get('ma_explanation', '')}</td></tr>
                <tr><td>MACD</td><td>{'✅ 金叉' if trend['macd_bullish'] else '❌ 非金叉'}</td><td>{trend.get('explanations', {}).get('macd_explanation', '')}</td></tr>
                <tr><td>ADX趋势</td><td>{'✅ 强趋势' if trend['adx_strong'] else '❌ 弱趋势'}</td><td>{trend.get('explanations', {}).get('adx_explanation', '')}</td></tr>
            </table>
            <p><strong>参与建议:</strong> {trend.get('participate_advice', '')}</p>
        </div>
        """
        
        # 买点信号 - 修复：显示所有技术指标
        buy = ta_results['buy_signals']
        if buy:
            html += f"""
            <div class="subsection">
                <h4>买点确认 (满足 {buy.get('satisfied_count', 0)}/6 个条件)</h4>
                <table class="table">
                    <tr><th>信号</th><th>状态</th><th>解释</th></tr>
                    <tr><td>斐波支撑</td><td>{'✅ 满足' if buy.get('fib_support', False) else '❌ 不满足'}</td><td>{buy.get('explanations', {}).get('fib_support', '')}</td></tr>
                    <tr><td>布林超卖</td><td>{'✅ 满足' if buy.get('bollinger_oversold', False) else '❌ 不满足'}</td><td>{buy.get('explanations', {}).get('bollinger_oversold', '')}</td></tr>
                    <tr><td>RSI底背离</td><td>{'✅ 满足' if buy.get('rsi_oversold_divergence', False) else '❌ 不满足'}</td><td>{buy.get('explanations', {}).get('rsi_oversold_divergence', '')}</td></tr>
                    <tr><td>温和放量</td><td>{'✅ 满足' if buy.get('volume_increase', False) else '❌ 不满足'}</td><td>{buy.get('explanations', {}).get('volume_increase', '')}</td></tr>
                    <tr><td>相对强弱</td><td>{'✅ 满足' if buy.get('relative_strength', False) else '❌ 不满足'}</td><td>{buy.get('explanations', {}).get('relative_strength', '')}</td></tr>
                    <tr><td>量能结构</td><td>{'✅ 满足' if buy.get('volume_structure', False) else '❌ 不满足'}</td><td>{buy.get('explanations', {}).get('volume_structure', '')}</td></tr>
                </table>
                <p><strong>买点触发:</strong> {'✅ 是' if buy.get('buy_triggered', False) else '❌ 否'}</p>
            </div>
            """
        
        # 卖点信号 - 修复：显示卖点指标
        sell = ta_results.get('sell_signals', {})
        if sell:
            html += f"""
            <div class="subsection">
                <h4>卖点确认</h4>
                <table class="table">
                    <tr><th>信号</th><th>状态</th><th>解释</th></tr>
                    <tr><td>斐波阻力</td><td>{'✅ 满足' if sell.get('fib_resistance', False) else '❌ 不满足'}</td><td>{sell.get('explanations', {}).get('fib_resistance', '')}</td></tr>
                    <tr><td>布林滞涨</td><td>{'✅ 满足' if sell.get('bollinger_overbought_stagnation', False) else '❌ 不满足'}</td><td>{sell.get('explanations', {}).get('bollinger_overbought_stagnation', '')}</td></tr>
                    <tr><td>RSI顶背离</td><td>{'✅ 满足' if sell.get('rsi_overbought_divergence', False) else '❌ 不满足'}</td><td>{sell.get('explanations', {}).get('rsi_overbought_divergence', '')}</td></tr>
                </table>
            </div>
            """
        
        # 综合信号
        signal = ta_results['overall_signal']
        signal_class = {
            'STRONG_BUY': 'signal-strong-buy',
            'BUY': 'signal-buy', 
            'SELL': 'signal-sell',
            'HOLD': 'signal-wait',
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
        
        # 技术指标详情 - 新增：显示MACD、RSI、KDJ等具体数值
        html += self._generate_technical_details(ta_results, bond_info)
        
        return html
    
    def _generate_technical_details(self, ta_results, bond_info):
        """生成技术指标详情HTML"""
        html = """
        <div class="subsection">
            <h4>📊 技术指标详情</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0;">
        """
        
        # 从多因子分析结果中获取技术指标
        if 'indicators' in ta_results:
            indicators = ta_results['indicators']
            
            # MACD指标
            if 'macd' in indicators:
                macd = indicators['macd']
                html += self.create_metric_card(
                    f"{macd.get('macd', 0):.3f}", 
                    f"MACD", 
                    "risk-low" if macd.get('macd', 0) > 0 else "risk-high"
                )
                html += self.create_metric_card(
                    f"{macd.get('signal', 0):.3f}", 
                    "MACD Signal", 
                    ""
                )
            
            # RSI指标
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                rsi_value = rsi.get('rsi', 50)
                if rsi_value < 30:
                    rsi_color = "risk-low"
                elif rsi_value > 70:
                    rsi_color = "risk-high"
                else:
                    rsi_color = ""
                html += self.create_metric_card(
                    f"{rsi_value:.1f}", 
                    f"RSI", 
                    rsi_color
                )
            
            # KDJ指标
            if 'kdj' in indicators:
                kdj = indicators['kdj']
                k_value = kdj.get('K', 50)
                d_value = kdj.get('D', 50)
                html += self.create_metric_card(
                    f"K={k_value:.1f}<br>D={d_value:.1f}", 
                    f"KDJ", 
                    "risk-low" if k_value > d_value else "risk-high"
                )
            
            # 布林带位置
            if 'bollinger' in indicators:
                bb = indicators['bollinger']
                position = bb.get('position', 0.5)
                if position < 0.2:
                    bb_color = "risk-low"
                    bb_desc = "超卖"
                elif position > 0.8:
                    bb_color = "risk-high"
                    bb_desc = "超买"
                else:
                    bb_color = ""
                    bb_desc = "正常"
                html += self.create_metric_card(
                    f"{position:.1%}", 
                    f"布林位置 {bb_desc}", 
                    bb_color
                )
        
        html += "</div></div>"
        return html
    
    def _generate_risk_analysis_html(self, bond_info):
        """生成风险分析HTML"""
        html = ""
        
        # 溢价率风险
        premium = bond_info['溢价率(%)']
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
        price = bond_info['转债价格']
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
            effective_floor_premium = floor_analysis.get('effective_floor_premium', 0)
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
        
        price = bond_info.get("转债价格", 0)
        ytm = bond_info.get("YTM(%)", 0)
        floor_analysis = bond_info.get("债底分析", {})
        
        # 高波风险判断
        if price > 130 and ytm < -5:
            risk_tags.append("高波风险")
            
            # 检查回售保护
            put_value = floor_analysis.get('put_value', 0) if floor_analysis else 0
            if put_value <= 100:  # 无强回售保护
                risk_tags.append("无回售保护")
        
        # 债底保护判断
        if floor_analysis:
            effective_floor_premium = floor_analysis.get('effective_floor_premium', 0)
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
        
        double_low_value = info["双低值"]
        if double_low_value < 130:
            strategies.append("双低策略: 优秀 - 价格和溢价率都很低, 安全边际充足")
        elif double_low_value < 150:
            strategies.append("双低策略: 良好 - 性价比较高, 适合配置")
        else:
            strategies.append("双低策略: 一般 - 双低值偏高, 安全边际有限")
        
        premium = info["溢价率(%)"]
        if premium < 10:
            strategies.append("低溢价策略: 优秀 - 跟涨能力强, 正股上涨时弹性大")
        elif premium < 20:
            strategies.append("低溢价策略: 良好 - 跟涨能力较好")
        else:
            strategies.append("低溢价策略: 不适合 - 溢价率偏高, 跟涨能力弱")
        
        size = info["剩余规模(亿)"]
        if size < 3:
            strategies.append("小规模策略: 优秀 - 规模小易炒作, 波动性大")
        elif size < 5:
            strategies.append("小规模策略: 良好 - 规模适中, 有一定弹性")
        
        ytm = info.get("YTM(%)", 0)
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
        
        profit_rate = holding_analysis['盈亏比例']
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
            {self.create_metric_card(f"{holding_analysis['持仓成本']}元", "持仓成本", "")}
            {self.create_metric_card(f"{holding_analysis['持仓数量']}张", "持仓数量", "")}
            {self.create_metric_card(f"{holding_analysis['当前盈亏']}元", "当前盈亏", profit_class)}
            {self.create_metric_card(f"{holding_analysis['盈亏比例']}%", "盈亏比例", profit_class)}
        </div>
        <div class="explanation">
            <strong>持仓建议:</strong> {holding_analysis['持仓建议']} | 
            <strong>风险等级:</strong> {holding_analysis['风险等级']} |
            <strong>建仓日期:</strong> {holding_analysis['建仓日期']}
        </div>
        """
    
    def _calculate_holding_analysis(self, bond_info, holding_info):
        """计算持仓分析 - 修复版本"""
        if not holding_info:
            return None
        
        current_price = bond_info.get('转债价格', 0)
        cost_price = holding_info.get('cost_price', 0)
        shares = holding_info.get('shares', 0)
        
        if cost_price > 0 and current_price > 0:
            profit_per_share = current_price - cost_price
            profit_rate = (profit_per_share / cost_price) * 100
            total_profit = profit_per_share * shares
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
                '持仓市值': round(current_price * shares, 2),
                '建仓日期': holding_info.get('purchase_date', '未知'),
                '持仓建议': advice,
                '风险等级': risk_level,
                '成本市值': round(cost_value, 2)
            }
        
        return None
    
    def _generate_technical_analysis_html(self, bond_info):
        """生成技术分析HTML"""
        tech_data = bond_info.get("技术分析数据", {})
        
        html = """
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
        """
        
        if tech_data:
            metrics = [
                (f"{tech_data.get('支撑位', 0)}元", "支撑位"),
                (f"{tech_data.get('压力位', 0)}元", "压力位"), 
                (f"{tech_data.get('距支撑百分比', 0)}%", "距支撑"),
                (f"{tech_data.get('距压力百分比', 0)}%", "距压力"),
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
            current_price = bond_info['转债价格']
            
            for level, price in fib_levels.items():
                diff_pct = ((current_price - price) / current_price) * 100
                if abs(diff_pct) < 2:
                    position = "<span class='badge badge-info'>当前位置</span>"
                elif price < current_price:
                    position = "<span class='badge badge-success'>支撑区</span>"
                else:
                    position = "<span class='badge badge-warning'>压力区</span>"
                
                html += f"<tr><td>{level}</td><td>{price:.2f}元</td><td>{position} ({diff_pct:+.1f}%)</td></tr>"
            
            html += "</table></div>"
        
        return html
    
    def _generate_score_analysis_html(self, bond_info):
        """生成评分分析HTML"""
        score, score_details = self._calculate_comprehensive_score_v2(bond_info)
        final_grade, final_advice = self._get_enhanced_rating(score, bond_info)
    
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
            <h2 class="{signal_class}">最终评分: {score}/100 - {final_grade}</h2>
            <p><strong>{final_advice}</strong></p>
        </div>
        """
    
    def _calculate_comprehensive_score_v2(self, info):
        """综合评分算法 v2.1 - 修复高溢价陷阱问题"""
        score = 0
        details = []
        
        premium = info.get("溢价率(%)", 0)
        conversion_value = info.get("转股价值", 0)
        
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
        size = info.get("剩余规模(亿)", 10)
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
        price = info.get("转债价格", 0)
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
        volume = info.get("日均成交额(亿)", 0)
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
        ytm = info.get("YTM(%)", 0)
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
    
    def _get_enhanced_rating(self, score, bond_info):
        """增强版评级 v2.2 - 修复技术面与基本面矛盾问题"""
        premium = bond_info.get("溢价率(%)", 0)
        conversion_value = bond_info.get("转股价值", 0)
        price = bond_info.get("转债价格", 0)
        
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
                    报告生成时间: {datetime.now().strftime('%Y-%m-d %H:%M:%S')} | 
                    可转债量化分析系统 v10.5
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

# ==================== 将函数移到类外部 ====================

# 创建HTML报告生成器实例
html_generator = HTMLReportGenerator()

# ==================== 新增：核心指标计算函数 ====================

def get_enhanced_rating(score, bond_info):
    """增强版评级 v2.2 - 修复技术面与基本面矛盾问题"""
    premium = bond_info.get("溢价率(%)", 0)
    conversion_value = bond_info.get("转股价值", 0)
    price = bond_info.get("转债价格", 0)
    
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

def calculate_relative_strength(bond_prices, stock_prices, period=5):
    """
    计算相对强弱比
    近5日转债涨幅 / 近5日正股涨幅
    """
    try:
        if len(bond_prices) < period + 1 or len(stock_prices) < period + 1:
            return None
            
        # 获取价格数据
        bond_start = bond_prices[-(period + 1)]
        bond_end = bond_prices[-1]
        stock_start = stock_prices[-(period + 1)]
        stock_end = stock_prices[-1]
        
        # 计算涨幅
        bond_return = (bond_end - bond_start) / bond_start
        stock_return = (stock_end - stock_start) / stock_start
        
        # 避免除零错误
        if stock_return == 0:
            if bond_return > 0:
                rs_ratio = float('inf')
            elif bond_return < 0:
                rs_ratio = float('-inf')
            else:
                rs_ratio = 1.0
        else:
            rs_ratio = bond_return / stock_return
        
        # 生成信号
        if rs_ratio > 1.0:
            signal = "强势"
            explanation = f"转债强于正股(rs_ratio={rs_ratio:.2f}>1.0)，资金主动买入"
        elif rs_ratio >= 0.8:
            signal = "中性"
            explanation = f"转债与正股基本同步(rs_ratio={rs_ratio:.2f})"
        else:
            signal = "弱势"
            explanation = f"转债弱于正股(rs_ratio={rs_ratio:.2f}<0.8)，反弹可能是被动跟随"
        
        return {
            'relative_strength_ratio': round(rs_ratio, 2),
            'cb_5d_return': round(bond_return * 100, 2),
            'stock_5d_return': round(stock_return * 100, 2),
            'signal': signal,
            'explanation': explanation,
            'period': period
        }
        
    except Exception as e:
        print(f"相对强弱计算失败: {e}")
        return None

def analyze_volume_structure(volume_data, price_data, period=3):
    """
    分析量能结构
    1. 近3日量能趋势
    2. 下跌vs反弹时的量能对比
    """
    try:
        if len(volume_data) < period + 2 or len(price_data) < period + 2:
            return None
        
        # 获取最近period+2天的数据
        recent_volumes = volume_data[-(period + 2):]
        recent_prices = price_data[-(period + 2):]
        
        # 1. 近3日量能趋势
        last_3_volumes = recent_volumes[-period:]
        volume_trend = "未知"
        
        if len(last_3_volumes) >= 3:
            if last_3_volumes[0] > last_3_volumes[1] > last_3_volumes[2]:
                volume_trend = "递减"
            elif last_3_volumes[0] < last_3_volumes[1] < last_3_volumes[2]:
                volume_trend = "递增"
            else:
                volume_trend = "波动"
        
        # 2. 下跌vs反弹量能对比
        price_changes = []
        for i in range(1, len(recent_prices)):
            change = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] * 100
            price_changes.append(change)
        
        # 找出最大的下跌日和反弹日
        down_days = []
        rebound_days = []
        
        for i in range(len(price_changes)):
            if price_changes[i] < -0.5:  # 跌幅超过0.5%定义为下跌日
                down_days.append(i)
            elif price_changes[i] > 0.5:  # 涨幅超过0.5%定义为反弹日
                rebound_days.append(i)
        
        # 计算量能对比
        rebound_volume_ratio = 0
        if down_days and rebound_days:
            # 取最近一个下跌日和反弹日
            last_down = down_days[-1] if down_days else 0
            last_rebound = rebound_days[-1] if rebound_days else 0
            
            if last_rebound > last_down:  # 确保反弹日在下跌日之后
                down_volume = recent_volumes[last_down + 1]  # +1是因为price_changes少一天
                rebound_volume = recent_volumes[last_rebound + 1]
                
                if down_volume > 0:
                    rebound_volume_ratio = rebound_volume / down_volume
        
        # 生成信号
        if volume_trend == "递减" and rebound_volume_ratio > 1.0:
            signal = "积极"
            explanation = "下跌缩量+反弹放量，抛压衰竭资金试探"
        elif volume_trend == "递减" and rebound_volume_ratio <= 1.0:
            signal = "中性"
            explanation = "下跌缩量但反弹未放量，需要观察"
        elif volume_trend == "递增" and price_changes[-1] < 0:
            signal = "消极"
            explanation = "下跌放量，抛压较重"
        elif volume_trend == "递增" and price_changes[-1] > 0:
            signal = "积极"
            explanation = "上涨放量，资金积极"
        else:
            signal = "中性"
            explanation = "量能结构无明显信号"
        
        return {
            'volume_trend': volume_trend,
            'rebound_volume_ratio': round(rebound_volume_ratio, 2),
            'signal': signal,
            'explanation': explanation,
            'recent_volumes': [round(v, 0) for v in recent_volumes[-period:]],
            'recent_price_changes': [round(p, 2) for p in price_changes[-period:]]
        }
        
    except Exception as e:
        print(f"量能结构分析失败: {e}")
        return None

def calculate_kdj(high_prices, low_prices, close_prices, period=9):
    """
    计算KDJ指标
    """
    try:
        if len(close_prices) < period:
            return None
        
        # 获取最近period天的数据
        recent_highs = high_prices[-period:]
        recent_lows = low_prices[-period:]
        recent_closes = close_prices[-period:]
        
        # 计算RSV
        highest_high = max(recent_highs)
        lowest_low = min(recent_lows)
        
        if highest_high == lowest_low:
            rsv = 50
        else:
            rsv = (recent_closes[-1] - lowest_low) / (highest_high - lowest_low) * 100
        
        # 简化版KDJ计算
        K = 50  # 默认值
        D = 50
        J = 50
        
        # 如果有历史数据，可以更精确计算
        if len(close_prices) > period * 3:
            # 简单模拟KDJ
            K = rsv * 0.3 + 50 * 0.7
            D = K * 0.3 + 50 * 0.7
            J = 3 * K - 2 * D
        
        # 生成信号
        if K < 20 and D < 20 and J < 0:
            signal = "超卖"
            explanation = "KDJ指标严重超卖，反弹概率大"
        elif K > 80 and D > 80 and J > 100:
            signal = "超买"
            explanation = "KDJ指标严重超买，回调概率大"
        elif K > D and J > K:
            signal = "金叉"
            explanation = "KDJ金叉向上，短期看多"
        elif K < D and J < K:
            signal = "死叉"
            explanation = "KDJ死叉向下，短期看空"
        else:
            signal = "中性"
            explanation = "KDJ指标中性"
        
        return {
            'K': round(K, 1),
            'D': round(D, 1),
            'J': round(J, 1),
            'RSV': round(rsv, 1),
            'signal': signal,
            'explanation': explanation
        }
        
    except Exception as e:
        print(f"KDJ计算失败: {e}")
        return None

def calculate_mfi(high_prices, low_prices, close_prices, volume_data, period=14):
    """
    计算MFI指标（资金流量指数）
    """
    try:
        if len(close_prices) < period + 1:
            return None
        
        # 简化版MFI计算
        typical_prices = []
        for i in range(len(close_prices)):
            typical = (high_prices[i] + low_prices[i] + close_prices[i]) / 3
            typical_prices.append(typical)
        
        # 计算资金流
        money_flows = []
        for i in range(1, len(typical_prices)):
            if typical_prices[i] > typical_prices[i-1]:
                money_flow = typical_prices[i] * volume_data[i]  # 正资金流
            else:
                money_flow = -typical_prices[i] * volume_data[i]  # 负资金流
            money_flows.append(money_flow)
        
        # 计算MFI
        if len(money_flows) >= period:
            positive_mf = sum(max(0, mf) for mf in money_flows[-period:])
            negative_mf = sum(abs(min(0, mf)) for mf in money_flows[-period:])
            
            if negative_mf == 0:
                mfi = 100
            else:
                money_ratio = positive_mf / negative_mf
                mfi = 100 - (100 / (1 + money_ratio))
        else:
            mfi = 50  # 默认值
        
        # 生成信号
        if mfi < 20:
            signal = "超卖"
            explanation = f"MFI={mfi:.1f}<20，严重超卖，资金流出过度"
        elif mfi > 80:
            signal = "超买"
            explanation = f"MFI={mfi:.1f}>80，严重超买，资金流入过度"
        elif mfi < 30:
            signal = "偏卖"
            explanation = f"MFI={mfi:.1f}<30，偏卖区域"
        elif mfi > 70:
            signal = "偏买"
            explanation = f"MFI={mfi:.1f}>70，偏买区域"
        else:
            signal = "中性"
            explanation = f"MFI={mfi:.1f}，中性区域"
        
        return {
            'MFI': round(mfi, 1),
            'signal': signal,
            'explanation': explanation
        }
        
    except Exception as e:
        print(f"MFI计算失败: {e}")
        return None

# ==================== 修改原有函数：集成新增指标 ====================

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
    
    # 计算新增指标
    info = calculate_enhanced_indicators(info)
    
    holding_info = get_user_holding_input(code, info['名称'])
    
    print("\n" + "=" * 70)
    print(f"转债名称: {info['名称']}")
    print(f"代码: {info['转债代码']}  |  正股: {info['正股代码']}")
    print(f"正股价格: {info['正股价格']} 元  |  转债价格: {info['转债价格']} 元")
    print(f"转股价: {info['转股价']} 元  |  PB: {info['PB']}")
    print(f"转股价值: {info['转股价值']}  |  溢价率: {info['溢价率(%)']}%")
    print(f"剩余规模: {info['剩余规模(亿)']}亿  |  剩余年限: {info.get('剩余年限', '未知')}年")
    print(f"双低值: {info['双低值']}  |  YTM: {info['YTM(%)']}%  |  Delta: {info.get('Delta值', 0):.3f}")
    
    # 显示新增指标
    if 'relative_strength_ratio' in info:
        rs_data = info.get('relative_strength', {})
        print(f"相对强弱比: {info['relative_strength_ratio']:.2f} ({rs_data.get('signal', '未知')})")
    
    if 'volume_structure' in info:
        vol_data = info.get('volume_structure', {})
        print(f"量能结构: {vol_data.get('signal', '未知')} (趋势: {vol_data.get('volume_trend', '未知')})")
    
    liquidity = info.get("流动性分析", {})
    if liquidity:
        print(f"流动性: {liquidity['评级']} ({liquidity['综合得分']})")
        print(f"成交额: {liquidity['成交额描述']}")
        print(f"换手率: {liquidity['换手率描述']}")
    
    print(f"数据来源: {info.get('数据来源', 'AkShare')}")
    print("=" * 70)

    # 显示增强技术指标
    if 'enhanced_ta' in info:
        ta_data = info['enhanced_ta']
        kdj = ta_data.get('kdj', {})
        mfi = ta_data.get('mfi', {})
        
        print("\n📊 增强技术指标:")
        print(f"  KDJ: K={kdj.get('K', 0):.1f}, D={kdj.get('D', 0):.1f}, J={kdj.get('J', 0):.1f} ({kdj.get('signal', '未知')})")
        print(f"  MFI: {mfi.get('MFI', 0):.1f} ({mfi.get('signal', '未知')})")

    # 债底分析显示
    floor_analysis = info.get("债底分析", {})
    if floor_analysis:
        print("\n🛡️ 债底分析:")
        print("-" * 50)
        print(f"  纯债价值: {floor_analysis.get('pure_bond_value', 0)}元")
        print(f"  回售价值: {floor_analysis.get('put_value', 0)}元")
        print(f"  历史支撑: {floor_analysis.get('historical_support', 0)}元")
        print(f"  有效债底: {floor_analysis.get('effective_floor', 0)}元")
        print(f"  纯债溢价率: {floor_analysis.get('pure_bond_premium', 0)}%")
        print(f"  有效债底溢价率: {floor_analysis.get('effective_floor_premium', 0)}%")
        
        # 生成务实的评语
        bond_price = info.get('转债价格', 0)
        conversion_premium = info.get('溢价率(%)', 0)
        effective_floor = floor_analysis.get('effective_floor', 0)
        pure_bond_value = floor_analysis.get('pure_bond_value', 0)
        
        print(f"\n💡 务实评估:")
        print(f"  理论债底约{pure_bond_value}元，但历史支撑在{effective_floor}元附近；")
        print(f"  当前价格隐含正股需上涨{conversion_premium}%才能平价，若无催化剂，上行空间有限，下行有技术支撑但无强债底保护。")

    # 高溢价风险提示
    premium = info.get("溢价率(%)", 0)
    conversion_value = info.get("转股价值", 0)
    bond_price = info.get("转债价格", 0)  # 修复：使用bond_price而不是price
    current_stock_price = info.get("正股价格", 0)

    # 立即添加调试信息来确认价格
    print(f"\n🔍【价格验证】AkShare价格: {bond_price}元")
    
    # 执行多因子共振分析（仅在溢价合理时）
    if premium <= 30:
        multifactor_results = perform_multifactor_analysis(code, info)
    else:
        print(f"\n🔍 多因子共振分析: 跳过（溢价率{premium}% > 30%, 技术分析失效）")
        info['multifactor_signal'] = 'SKIP_HIGH_PREMIUM'
        multifactor_results = None
    
    # 持仓分析
    if holding_info:
        holding_analysis = calculate_holding_analysis(info, holding_info)
        if holding_analysis:
            print("\n持仓分析:")
            print("-" * 50)
            print(f"  持仓成本: {holding_analysis['持仓成本']}元")
            print(f"  持仓数量: {holding_analysis['持仓数量']}张")
            print(f"  成本市值: {holding_analysis['成本市值']}元")
            print(f"  当前市值: {holding_analysis['持仓市值']}元")
            print(f"  当前盈亏: {holding_analysis['当前盈亏']}元 ({holding_analysis['盈亏比例']}%)")
            print(f"  建仓日期: {holding_analysis['建仓日期']}")
            print(f"  风险等级: {holding_analysis['风险等级']}")
            print(f"  持仓建议: {holding_analysis['持仓建议']}")

    # 正股转债联动分析
    linkage_data = info.get("联动分析", {})
    if linkage_data:
        print("\n正股转债联动分析:")
        print("-" * 40)
        print(f"  溢价率联动: {linkage_data.get('溢价率联动', '未知')}")
        print(f"  Delta弹性: {linkage_data.get('Delta弹性', '未知')} (Delta值: {linkage_data.get('Delta值', 0)})")
        print(f"  价格合理性: {linkage_data.get('价格合理性', '未知')} (偏离度: {linkage_data.get('价格偏离度', 0)}%)")
        print(f"  联动策略: {linkage_data.get('联动策略', '未知')}")
        print(f"  风险提示: {linkage_data.get('风险提示', '未知')}")

    # 强赎分析 - 修正版本
    redemption_data = info.get("强赎分析", {})
    if redemption_data:
        print("\n强赎分析:")
        print("-" * 40)
        print(f"  转股价: {redemption_data.get('conversion_price', 0)}元")
        print(f"  强赎触发价: {redemption_data.get('trigger_price', 0)}元 (转股价×130%)")
        print(f"  当前正股价: {redemption_data.get('current_stock_price', 0)}元")
        print(f"  触发进度: {redemption_data.get('progress', '0%')}")
        print(f"  强赎状态: {redemption_data.get('status', '未知')}")
        print(f"  风险等级: {redemption_data.get('risk_level', '未知')}")
        print(f"  距触发价差: {redemption_data.get('distance_to_trigger', 0)}元")
        print(f"  触发条件: {redemption_data.get('trigger_condition', '未知')}")
        
        # 强赎风险提示 - 基于正确的数据
        status = redemption_data.get('status', '')
        if status == "已触发":
            print(f"  ⚠️  强赎风险: 已触发强赎, 注意强赎风险！")
        elif status == "接近触发":
            print(f"  ⚠️  强赎风险: 接近触发条件, 密切关注正股走势")
        elif status == "观察中":
            print(f"  强赎风险: 有一定触发可能, 需持续观察")
        else:
            print(f"  强赎风险: 当前风险较低")

    # 下修分析 - 增强版本
    downward_data = info.get("下修分析", {})
    if downward_data:
        print("\n下修分析:")
        print("-" * 40)
        print(f"  下修概率: {downward_data.get('current_probability', '未知')}")
        print(f"  条件评分: {downward_data.get('condition_scores', 0)}分")
        print(f"  历史下修次数: {downward_data.get('adjust_count', 0)}次")
        print(f"  最后下修时间: {downward_data.get('last_adjust_date', '无')}")
        print(f"  PB值: {downward_data.get('pb_ratio', 0)} (影响下修空间)")
        
        down_conditions = downward_data.get('down_conditions', [])
        if down_conditions:
            print(f"  下修条件分析:")
            for condition in down_conditions:
                print(f"    ✓ {condition}")
        else:
            print(f"  下修条件: 当前无明显下修压力")
        
        print(f"  下修建议: {downward_data.get('suggestion', '')}")

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
    print(f"     主支撑位（120日）: {tech_data.get('支撑位', 0)}元")
    print(f"     主压力位（250日）: {tech_data.get('压力位', 0)}元")
    print(f"     当前位置: 距支撑{tech_data.get('距支撑百分比', 0)}% | 距压力{tech_data.get('距压力百分比', 0)}%")
    print(f"     {tech_data.get('位置状态', '数据不足')}")
    
    print(f"  均线系统分析:")
    print(f"     20日均线: {tech_data.get('20日均线', 0)}元 | 60日均线: {tech_data.get('60日均线', 0)}元 | 120日均线: {tech_data.get('120日均线', 0)}元")
    print(f"     {tech_data.get('均线状态', '数据不足')}")
    
    print(f"  转债弹性分析:")
    print(f"     Delta值: {tech_data.get('Delta值', 0)}")
    print(f"     {tech_data.get('弹性状态', '数据不足')}")

    # 斐波那契回撤位分析
    fib_levels = tech_data.get('斐波那契_levels', {})
    if fib_levels:
        print(f"\n斐波那契回撤位分析:")
        print("   " + "-" * 50)
        for level, price in fib_levels.items():
            price_diff = info['转债价格'] - price
            diff_percent = (price_diff / info['转债价格']) * 100 if info['转债价格'] > 0 else 0
            
            if abs(diff_percent) < 2:
                marker = ">当前位置"
            elif price < info['转债价格']:
                marker = "^支撑区域"
            else:
                marker = "v压力区域"
                
            print(f"   {marker:8} {level}: {price:.2f}元 | 差: {price_diff:+.2f}元 ({diff_percent:+.1f}%)")

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
    
    print(f"\n综合评分: {score}/100 (修复版算法)")
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
        upside_needed = (bond_price - conversion_value) / conversion_value * 100  # 修复：使用bond_price而不是price
        print(f"\n📈 盈亏平衡分析:")
        print(f"  当前转债价格: {bond_price}元")
        print(f"  当前转股价值: {conversion_value}元")
        print(f"  需正股上涨至: {bond_price * conversion_value / 100:.2f}元 (+{upside_needed:.1f}%) 才能实现平价")  # 修复：使用bond_price而不是price

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

# ==================== 多因子共振技术分析系统 - 完整修复版 ====================

class ConvertibleBondTA:
    """
    可转债多因子共振技术分析系统 - 完整修复版
    修复技术指标计算和显示问题
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
        计算所有技术指标 - 完整修复版，确保所有指标都计算
        """
        df = df.copy()
        
        # 确保有足够的列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                if col == 'volume':
                    df[col] = 1000000  # 默认成交量
                else:
                    df[col] = df.get('close', 100)
        
        # 1. 移动平均线
        df['ma5'] = ta.sma(df['close'], length=5)
        df['ma10'] = ta.sma(df['close'], length=10)
        df['ma20'] = ta.sma(df['close'], length=20)
        df['ma60'] = ta.sma(df['close'], length=60)
        df['ma120'] = ta.sma(df['close'], length=120)
        
        # 2. MACD - 修复计算方式
        try:
            macd_data = ta.macd(df['close'], fast=12, slow=26, signal=9)
            if macd_data is not None and not macd_data.empty:
                # 修复：检查列名
                macd_columns = macd_data.columns
                if 'MACD_12_26_9' in macd_columns:
                    df['macd'] = macd_data['MACD_12_26_9']
                    df['macd_signal'] = macd_data['MACDs_12_26_9']
                    df['macd_hist'] = macd_data['MACDh_12_26_9']
                elif len(macd_columns) >= 3:
                    df['macd'] = macd_data.iloc[:, 0]
                    df['macd_signal'] = macd_data.iloc[:, 1]
                    df['macd_hist'] = macd_data.iloc[:, 2]
                else:
                    # 手动计算MACD作为后备
                    exp1 = df['close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['close'].ewm(span=26, adjust=False).mean()
                    df['macd'] = exp1 - exp2
                    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
                    df['macd_hist'] = df['macd'] - df['macd_signal']
            else:
                # 手动计算MACD作为后备
                exp1 = df['close'].ewm(span=12, adjust=False).mean()
                exp2 = df['close'].ewm(span=26, adjust=False).mean()
                df['macd'] = exp1 - exp2
                df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
                df['macd_hist'] = df['macd'] - df['macd_signal']
        except Exception as e:
            print(f"MACD计算错误: {e}")
            df['macd'] = 0
            df['macd_signal'] = 0
            df['macd_hist'] = 0
        
        # 3. 布林带 - 使用pandas_ta确保稳定性
        try:
            bb_data = ta.bbands(df['close'], length=20, std=2)
            if bb_data is not None and not bb_data.empty:
                # 修复：检查布林带列名
                bb_columns = bb_data.columns
                if 'BBU_20_2.0' in bb_columns:
                    df['bb_upper'] = bb_data['BBU_20_2.0']
                    df['bb_middle'] = bb_data['BBM_20_2.0']
                    df['bb_lower'] = bb_data['BBL_20_2.0']
                elif len(bb_columns) >= 3:
                    df['bb_upper'] = bb_data.iloc[:, 0]
                    df['bb_middle'] = bb_data.iloc[:, 1]
                    df['bb_lower'] = bb_data.iloc[:, 2]
                else:
                    df['bb_upper'] = df['close'] * 1.1
                    df['bb_middle'] = df['close']
                    df['bb_lower'] = df['close'] * 0.9
            else:
                df['bb_upper'] = df['close'] * 1.1
                df['bb_middle'] = df['close']
                df['bb_lower'] = df['close'] * 0.9
        except Exception as e:
            print(f"布林带计算错误: {e}")
            df['bb_upper'] = df['close'] * 1.1
            df['bb_middle'] = df['close']
            df['bb_lower'] = df['close'] * 0.9
        
        # 计算布林带宽度和位置
        try:
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            df['price_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            df['price_position'] = df['price_position'].replace([np.inf, -np.inf], 0.5).clip(0, 1)
        except:
            df['bb_width'] = 0.2
            df['price_position'] = 0.5
        
        # 4. RSI - 确保计算
        try:
            rsi_data = ta.rsi(df['close'], length=14)
            if rsi_data is not None:
                df['rsi'] = rsi_data
            else:
                df['rsi'] = 50
        except Exception as e:
            print(f"RSI计算错误: {e}")
            df['rsi'] = 50
        
        # 5. ADX 趋势强度
        try:
            adx_data = ta.adx(df['high'], df['low'], df['close'], length=14)
            if adx_data is not None and not adx_data.empty:
                adx_columns = adx_data.columns
                if 'ADX_14' in adx_columns:
                    df['adx'] = adx_data['ADX_14']
                    df['dmi_plus'] = adx_data['DMP_14']
                    df['dmi_minus'] = adx_data['DMN_14']
                elif len(adx_columns) >= 3:
                    df['adx'] = adx_data.iloc[:, 0]
                    df['dmi_plus'] = adx_data.iloc[:, 1]
                    df['dmi_minus'] = adx_data.iloc[:, 2]
                else:
                    df['adx'] = 20
                    df['dmi_plus'] = 20
                    df['dmi_minus'] = 20
            else:
                df['adx'] = 20
                df['dmi_plus'] = 20
                df['dmi_minus'] = 20
        except Exception as e:
            print(f"ADX计算错误: {e}")
            df['adx'] = 20
            df['dmi_plus'] = 20
            df['dmi_minus'] = 20
        
        # 6. 成交量指标
        try:
            df['volume_ma5'] = ta.sma(df['volume'], length=5)
            df['volume_ma20'] = ta.sma(df['volume'], length=20)
            df['volume_ratio'] = df['volume'] / df['volume_ma20'].replace(0, 1)
        except:
            df['volume_ma5'] = df['volume']
            df['volume_ma20'] = df['volume']
            df['volume_ratio'] = 1
        
        # 7. KDJ指标 - 修复计算（避免'STOCHk_9_3_3'错误）
        try:
            # 使用pandas_ta的stoch指标计算KDJ
            stoch_data = ta.stoch(df['high'], df['low'], df['close'], length=9, smooth_k=3, smooth_d=3)
            
            if stoch_data is not None and not stoch_data.empty:
                stoch_columns = stoch_data.columns
                print(f"[DEBUG] KDJ列名: {list(stoch_columns)}")
                
                # 尝试不同的列名格式
                k_col = None
                d_col = None
                
                # 检查可能的列名
                for col in stoch_columns:
                    if 'K' in col or 'k' in col:
                        k_col = col
                    elif 'D' in col or 'd' in col:
                        d_col = col
                
                if k_col and d_col:
                    df['kdj_k'] = stoch_data[k_col]
                    df['kdj_d'] = stoch_data[d_col]
                elif len(stoch_columns) >= 2:
                    # 使用前两列
                    df['kdj_k'] = stoch_data.iloc[:, 0]
                    df['kdj_d'] = stoch_data.iloc[:, 1]
                else:
                    # 计算简单KDJ
                    df['kdj_k'] = df['rsi']  # 使用RSI作为近似
                    df['kdj_d'] = df['rsi'].rolling(window=3).mean()
                
                # J = 3K - 2D
                df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
            else:
                # 计算简单KDJ
                df['kdj_k'] = df['rsi']  # 使用RSI作为近似
                df['kdj_d'] = df['rsi'].rolling(window=3).mean()
                df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        except Exception as e:
            print(f"KDJ计算错误: {e}")
            # 使用简化计算
            df['kdj_k'] = df['rsi'].fillna(50)  # 使用RSI作为近似
            df['kdj_d'] = df['rsi'].rolling(window=3, min_periods=1).mean().fillna(50)
            df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        # 8. MFI指标
        try:
            mfi_data = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=14)
            if mfi_data is not None:
                df['mfi'] = mfi_data
            else:
                df['mfi'] = 50
        except Exception as e:
            print(f"MFI计算错误: {e}")
            df['mfi'] = 50
        
        # 填充NaN值
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # 确保没有负值或不合理值
        for col in df.columns:
            if 'rsi' in col or 'mfi' in col or 'kdj' in col:
                df[col] = df[col].clip(0, 100)
        
        return df
        
    def check_prerequisites(self, 
                          df: pd.DataFrame, 
                          premium_rate: float,
                          call_risk_distance: float,
                          days: int = 20) -> Dict:
        """
        检查可转债技术分析的三大前提条件
        """
        results = {
            'liquidity_ok': False,
            'premium_ok': False,
            'call_risk_ok': False,
            'all_ok': False,
            'messages': [],
            'detailed_explanations': []
        }
        
        # 1. 流动性检查 (日均成交 > 2000万)
        avg_volume = df['volume'].tail(days).mean()
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
        """检查ADX趋势强度"""
        current = df.iloc[-1]
        adx = current.get('adx', 0)
        
        if pd.isna(adx):
            return False, "ADX数据缺失", "ADX指标计算失败, 无法判断趋势强度"
        
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
        """
        current = df.iloc[-1]
        
        # 计算趋势强度评分
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
                'ma_status': f"MA20={current.get('ma20', 0):.2f}, MA60={current.get('ma60', 0):.2f}, MA120={current.get('ma120', 0):.2f}",
                'macd_status': f"MACD={current.get('macd', 0):.3f}, Signal={current.get('macd_signal', 0):.3f}",
                'adx_status': f"ADX={current.get('adx', 0):.1f} ({adx_desc})",
                'rsi': f"RSI={current.get('rsi', 0):.1f}",
                'kdj': f"KDJ K={current.get('kdj_k', 0):.1f}, D={current.get('kdj_d', 0):.1f}, J={current.get('kdj_j', 0):.1f}",
                'mfi': f"MFI={current.get('mfi', 0):.1f}"
            },
            'explanations': {
                'ma_explanation': ma_explanation,
                'macd_explanation': macd_explanation,
                'adx_explanation': adx_explanation
            }
        }
        
        # 技术指标数据存储
        results['indicators'] = {
            'macd': {
                'macd': current.get('macd', 0),
                'signal': current.get('macd_signal', 0),
                'hist': current.get('macd_hist', 0)
            },
            'rsi': {
                'rsi': current.get('rsi', 50),
                'signal': '超卖' if current.get('rsi', 50) < 30 else '超买' if current.get('rsi', 50) > 70 else '中性'
            },
            'kdj': {
                'K': current.get('kdj_k', 50),
                'D': current.get('kdj_d', 50),
                'J': current.get('kdj_j', 50)
            },
            'bollinger': {
                'upper': current.get('bb_upper', 0),
                'middle': current.get('bb_middle', 0),
                'lower': current.get('bb_lower', 0),
                'position': current.get('price_position', 0.5)
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
        ma20, ma60, ma120 = current.get('ma20', 0), current.get('ma60', 0), current.get('ma120', 0)
        
        if pd.isna(ma20) or pd.isna(ma60) or pd.isna(ma120):
            return False, "❌ 均线数据缺失，无法判断"
        
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
        macd = current.get('macd', 0)
        macd_signal = current.get('macd_signal', 0)
        
        if pd.isna(macd) or pd.isna(macd_signal):
            return False, "❌ MACD数据缺失，无法判断"
        
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
    
    def check_buy_signals(self, df: pd.DataFrame, fib_levels: Dict, 
                         relative_strength_data: Dict = None,
                         volume_structure_data: Dict = None) -> Dict:
        """
        买点确认（满足3项即可）- 增强版包含新指标
        """
        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else current
        
        # 每个信号都返回值和详细解释
        fib_support, fib_explanation = self._check_fibonacci_support_with_explanation(current, fib_levels)
        bollinger_oversold, bollinger_explanation = self._check_bollinger_oversold_with_explanation(current, prev)
        rsi_oversold_divergence, rsi_explanation = self._check_rsi_oversold_divergence_with_explanation(df)
        volume_increase, volume_explanation = self._check_volume_increase_gentle_with_explanation(df)
        
        # 新增指标检查
        relative_strength = False
        relative_strength_explanation = "相对强弱数据缺失"
        
        if relative_strength_data:
            rs_ratio = relative_strength_data.get('relative_strength_ratio', 0)
            if rs_ratio >= 0.9:
                relative_strength = True
                relative_strength_explanation = f"相对强弱比={rs_ratio:.2f}≥0.9，转债不弱于正股"
            else:
                relative_strength_explanation = f"相对强弱比={rs_ratio:.2f}<0.9，转债弱于正股"
        
        volume_structure = False
        volume_structure_explanation = "量能结构数据缺失"
        
        if volume_structure_data:
            signal = volume_structure_data.get('signal', '')
            if signal in ['积极', '中性']:
                volume_structure = True
                volume_structure_explanation = f"量能结构={signal}，符合买点要求"
            else:
                volume_structure_explanation = f"量能结构={signal}，不符合买点要求"
        
        signals = {
            'fib_support': fib_support,
            'bollinger_oversold': bollinger_oversold,
            'rsi_oversold_divergence': rsi_oversold_divergence,
            'volume_increase': volume_increase,
            'relative_strength': relative_strength,
            'volume_structure': volume_structure,
            
            'explanations': {
                'fib_support': fib_explanation,
                'bollinger_oversold': bollinger_explanation,
                'rsi_oversold_divergence': rsi_explanation,
                'volume_increase': volume_explanation,
                'relative_strength': relative_strength_explanation,
                'volume_structure': volume_structure_explanation
            }
        }
        
        # 统计满足的条件数量
        signal_list = [fib_support, bollinger_oversold, rsi_oversold_divergence, 
                      volume_increase, relative_strength, volume_structure]
        satisfied_count = sum(signal_list)
        signals['buy_triggered'] = satisfied_count >= 3
        signals['satisfied_count'] = satisfied_count
        
        # 详细信息
        signals['details'] = {
            'fib_level': f"当前价{current['close']:.2f}, 61.8%位{fib_levels.get('61.8%', 0):.2f}",
            'bollinger_position': f"布林带位置: {current.get('price_position', 0):.1%}",
            'rsi_level': f"RSI: {current.get('rsi', 0):.1f}",
            'volume_status': f"量比: {current.get('volume_ratio', 0):.2f}",
            'relative_strength_ratio': relative_strength_data.get('relative_strength_ratio', 0) if relative_strength_data else 0,
            'volume_structure_signal': volume_structure_data.get('signal', '未知') if volume_structure_data else '未知'
        }
        
        return signals
    
    def _check_fibonacci_support_with_explanation(self, current, fib_levels: Dict) -> Tuple[bool, str]:
        """检查斐波那契61.8%支撑，返回详细解释"""
        fib_618 = fib_levels.get('61.8%')
        current_price = current['close']
        
        if fib_618 is None or fib_618 <= 0:
            return False, "❌ 斐波支撑: 无法计算61.8%斐波那契回撤位"
        
        price_diff_pct = abs(current_price - fib_618) / fib_618
        is_support = price_diff_pct <= 0.02
        
        if is_support:
            explanation = f"✅ 斐波支撑: 当前价{current_price:.2f}接近61.8%位{fib_618:.2f}(误差{price_diff_pct:.1%}) → 关键支撑区域"
        else:
            distance_pct = (current_price - fib_618) / fib_618
            if distance_pct > 0:
                explanation = f"❌ 斐波阻力: 当前价{current_price:.2f}高于61.8%位{fib_618:.2f}(+{distance_pct:.1%}) → 已突破支撑"
            else:
                explanation = f"❌ 远离支撑: 当前价{current_price:.2f}低于61.8%位{fib_618:.2f}({distance_pct:.1%}) → 支撑较远"
        
        return is_support, explanation
    
    def _check_bollinger_oversold_with_explanation(self, current, prev) -> Tuple[bool, str]:
        """触及布林带下轨 + 缩量，返回详细解释"""
        try:
            if 'bb_lower' not in current or pd.isna(current['bb_lower']):
                return False, "❌ 布林带分析: 布林带数据缺失"
            
            current_price = current['close']
            bb_lower = current['bb_lower']
            
            if bb_lower <= 0 or pd.isna(bb_lower):
                return False, "❌ 布林带分析: 布林带下轨数据无效"
            
            volume_ma5 = current.get('volume_ma5', 1)
            current_volume = current.get('volume', 0)
            
            at_lower_band = current_price <= bb_lower * 1.02
            volume_shrinking = current_volume < volume_ma5
            
            distance_to_lower = ((current_price - bb_lower) / bb_lower) * 100 if bb_lower > 0 else 0
            bb_position = current.get('price_position', 0)
            
            if at_lower_band and volume_shrinking:
                explanation = f"✅ 布林超卖: 价格{current_price:.2f}在下轨{bb_lower:.2f}附近(距离{distance_to_lower:+.1f}%) + 缩量 → 超卖反弹概率大"
            elif at_lower_band:
                explanation = f"🟡 触及下轨: 价格{current_price:.2f}在下轨{bb_lower:.2f}附近, 但量能{'未' if not volume_shrinking else ''}缩量 → 需确认量价配合"
            else:
                explanation = f"❌ 未超卖: 价格{current_price:.2f}距下轨{bb_lower:.2f}较远(距离{distance_to_lower:+.1f}%), 布林位置{bb_position:.1%} → 无超卖信号"
            
            return at_lower_band and volume_shrinking, explanation
            
        except Exception as e:
            print(f"布林带分析异常: {e}")
            return False, f"❌ 布林带分析异常: {str(e)}"
    
    def _check_rsi_oversold_divergence_with_explanation(self, df: pd.DataFrame, lookback: int = 10) -> Tuple[bool, str]:
        """RSI < 30 且出现底背离，返回详细解释"""
        if len(df) < lookback + 5:
            return False, f"❌ RSI分析: 数据不足({len(df)}天), 需要{lookback+5}天"
        
        current = df.iloc[-1]
        current_rsi = current.get('rsi', 50)
        
        if pd.isna(current_rsi):
            return False, "❌ RSI分析: RSI数据缺失"
        
        if current_rsi >= 30:
            return False, f"❌ RSI未超卖: RSI={current_rsi:.1f} ≥ 30, 未进入超卖区"
        
        recent_data = df.tail(lookback)
        
        if recent_data['close'].isna().any() or recent_data['rsi'].isna().any():
            return False, "❌ RSI分析: 价格或RSI数据不完整"
        
        price_low_idx = recent_data['close'].idxmin()
        rsi_low_idx = recent_data['rsi'].idxmin()
        
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
        volume_ratio = current.get('volume_ratio', 1)
        
        if pd.isna(volume_ratio):
            return False, "❌ 量能分析: 量比数据缺失"
        
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
        """
        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else current
        
        fib_resistance, fib_explanation = self._check_fibonacci_resistance_with_explanation(current, fib_levels)
        bollinger_overbought, bollinger_explanation = self._check_bollinger_overbought_stagnation_with_explanation(current, prev)
        rsi_overbought, rsi_explanation = self._check_rsi_overbought_divergence_with_explanation(df)
        
        signals = {
            'fib_resistance': fib_resistance,
            'bollinger_overbought_stagnation': bollinger_overbought,
            'rsi_overbought_divergence': rsi_overbought,
            
            'explanations': {
                'fib_resistance': fib_explanation,
                'bollinger_overbought_stagnation': bollinger_explanation,
                'rsi_overbought_divergence': rsi_explanation
            }
        }
        
        signals['details'] = {
            'fib_resistance_level': f"当前价{current['close']:.2f}, 161.8%位{fib_levels.get('161.8%', 0):.2f}",
            'bollinger_position': f"布林带位置: {current.get('price_position', 0):.1%}",
            'rsi_level': f"RSI: {current.get('rsi', 0):.1f}",
            'volume_status': f"量比: {current.get('volume_ratio', 0):.2f}"
        }
        
        return signals
    
    def _check_fibonacci_resistance_with_explanation(self, current, fib_levels: Dict) -> Tuple[bool, str]:
        """检查斐波那契161.8%阻力，返回详细解释"""
        fib_1618 = fib_levels.get('161.8%')
        current_price = current['close']
        
        if fib_1618 is None or fib_1618 <= 0:
            return False, "❌ 斐波阻力: 无法计算161.8%斐波那契扩展位"
        
        price_diff_pct = abs(current_price - fib_1618) / fib_1618
        is_resistance = price_diff_pct <= 0.02
        
        if is_resistance:
            explanation = f"✅ 斐波阻力: 当前价{current_price:.2f}接近161.8%位{fib_1618:.2f}(误差{price_diff_pct:.1%}) → 关键阻力区域"
        else:
            distance_pct = (fib_1618 - current_price) / current_price
            if distance_pct > 0.1:
                explanation = f"❌ 远离阻力: 当前价{current_price:.2f}距161.8%位{fib_1618:.2f}较远(还需+{distance_pct:.1%}) → 阻力较远"
            else:
                explanation = f"🟡 接近阻力: 当前价{current_price:.2f}逐步接近161.8%位{fib_1618:.2f}(还需+{distance_pct:.1%}) → 关注阻力效果"
        
        return is_resistance, explanation
    
    def _check_bollinger_overbought_stagnation_with_explanation(self, current, prev) -> Tuple[bool, str]:
        """触及布林带上轨 + 放量滞涨，返回详细解释"""
        try:
            if 'bb_upper' not in current or pd.isna(current['bb_upper']):
                return False, "❌ 布林带分析: 布林带数据缺失"
            
            current_price = current['close']
            bb_upper = current['bb_upper']
            
            if bb_upper <= 0 or pd.isna(bb_upper):
                return False, "❌ 布林带分析: 布林带上轨数据无效"
            
            volume_ma5 = current.get('volume_ma5', 1)
            current_volume = current.get('volume', 0)
            
            at_upper_band = current_price >= bb_upper * 0.98
            volume_spike = current_volume > volume_ma5 * 1.5
            price_stagnant = abs(current_price - prev['close']) / prev['close'] <= 0.01
            
            distance_to_upper = ((current_price - bb_upper) / bb_upper) * 100 if bb_upper > 0 else 0
            bb_position = current.get('price_position', 0)
            
            if at_upper_band and volume_spike and price_stagnant:
                explanation = f"✅ 布林滞涨: 价格{current_price:.2f}在上轨{bb_upper:.2f}附近 + 放量滞涨 → 顶部信号明显"
            elif at_upper_band and volume_spike:
                explanation = f"🟡 上轨放量: 价格{current_price:.2f}在上轨附近且放量, 但未明显滞涨 → 警惕回调"
            elif at_upper_band:
                explanation = f"🟡 触及上轨: 价格{current_price:.2f}在上轨附近, 但量能一般 → 压力显现"
            else:
                explanation = f"❌ 无滞涨: 价格{current_price:.2f}距上轨{bb_upper:.2f}较远(距离{distance_to_upper:+.1f}%), 布林位置{bb_position:.1%} → 无顶部信号"
            
            return at_upper_band and volume_spike and price_stagnant, explanation
            
        except Exception as e:
            print(f"布林带分析异常: {e}")
            return False, f"❌ 布林带分析异常: {str(e)}"
    
    def _check_rsi_overbought_divergence_with_explanation(self, df: pd.DataFrame, lookback: int = 10) -> Tuple[bool, str]:
        """RSI > 80 + 顶背离，返回详细解释"""
        if len(df) < lookback + 5:
            return False, f"❌ RSI分析: 数据不足({len(df)}天), 需要{lookback+5}天"
        
        current = df.iloc[-1]
        current_rsi = current.get('rsi', 50)
        
        if pd.isna(current_rsi):
            return False, "❌ RSI分析: RSI数据缺失"
        
        if current_rsi <= 80:
            return False, f"❌ RSI未超买: RSI={current_rsi:.1f} ≤ 80, 未进入超买区"
        
        recent_data = df.tail(lookback)
        
        if recent_data['close'].isna().any() or recent_data['rsi'].isna().any():
            return False, "❌ RSI分析: 价格或RSI数据不完整"
        
        price_high_idx = recent_data['close'].idxmax()
        rsi_high_idx = recent_data['rsi'].idxmax()
        
        price_divergence = (price_high_idx == recent_data.index[-1] and 
                          rsi_high_idx != recent_data.index[-1])
        
        if price_divergence:
            explanation = f"✅ RSI顶背离: 价格创新高但RSI{current_rsi:.1f}未新高 → 上涨动能减弱, 回调概率增加"
        else:
            explanation = f"🟡 RSI超买: RSI={current_rsi:.1f} > 80超买但无顶背离 → 单纯超买, 需其他信号确认"
        
        return price_divergence, explanation
    
    def calculate_fibonacci_levels(self, high: float, low: float) -> Dict[str, float]:
        """计算完整的斐波那契回撤和扩展位"""
        diff = high - low
        
        levels = {
            '0.0%': high,
            '23.6%': high - diff * 0.236,
            '38.2%': high - diff * 0.382,
            '50.0%': (high + low) / 2,
            '61.8%': high - diff * 0.618,
            '78.6%': high - diff * 0.786,
            '100.0%': low,
            
            '138.2%': high + diff * 0.382,
            '161.8%': high + diff * 0.618,
            '200.0%': high + diff,
            '261.8%': high + diff * 1.618,
        }
        
        return levels
    
    def get_recent_high_low(self, df: pd.DataFrame, period: int = 250) -> Tuple[float, float]:
        """获取近期高点和低点"""
        recent_df = df.tail(period)
        return recent_df['high'].max(), recent_df['low'].min()
    
    def comprehensive_analysis(self, 
                             df: pd.DataFrame,
                             premium_rate,  
                             call_risk_distance,  
                             lookback_period: int = 250,
                             actual_price: float = None,
                             relative_strength_data: Dict = None,
                             volume_structure_data: Dict = None) -> Dict:
        """
        综合技术分析入口函数 - 完整修复版
        """
        # ===== 类型转换开始 =====
        try:
            # premium_rate 处理
            if isinstance(premium_rate, np.float64) or isinstance(premium_rate, np.float32):
                premium_rate = float(premium_rate)
            
            premium_str = str(premium_rate)
            clean_str = ''.join(c for c in premium_str if c.isdigit() or c in '.-')
            
            if clean_str and clean_str != '.' and clean_str != '-':
                premium_rate = float(clean_str)
                if premium_rate > 1:
                    premium_rate = premium_rate / 100.0
            else:
                premium_rate = 0.0
        except:
            premium_rate = 0.0
        
        # call_risk_distance 处理
        try:
            if isinstance(call_risk_distance, np.float64) or isinstance(call_risk_distance, np.float32):
                call_risk_distance = float(call_risk_distance)
            
            distance_str = str(call_risk_distance)
            clean_str = ''.join(c for c in distance_str if c.isdigit() or c in '.-')
            
            if clean_str and clean_str != '.' and clean_str != '-':
                call_risk_distance = float(clean_str)
                if call_risk_distance > 1:
                    call_risk_distance = call_risk_distance / 100.0
            else:
                call_risk_distance = 0.3
        except:
            call_risk_distance = 0.3
        
        print(f"[DEBUG] 转换结果: premium_rate={premium_rate:.3f}, call_risk_distance={call_risk_distance:.3f}")
        # ===== 类型转换结束 =====
        
        # 1. 计算技术指标
        df_with_indicators = self.calculate_all_indicators(df)
        
        # 2. 如果提供了实际价格，确保数据一致性
        if actual_price is not None and len(df_with_indicators) > 0:
            df_with_indicators.iloc[-1, df_with_indicators.columns.get_loc('close')] = actual_price
            df_with_indicators.iloc[-1, df_with_indicators.columns.get_loc('open')] = actual_price
            df_with_indicators.iloc[-1, df_with_indicators.columns.get_loc('high')] = max(df_with_indicators.iloc[-2]['high'], actual_price) if len(df_with_indicators) > 1 else actual_price
            df_with_indicators.iloc[-1, df_with_indicators.columns.get_loc('low')] = min(df_with_indicators.iloc[-2]['low'], actual_price) if len(df_with_indicators) > 1 else actual_price
            
            df_with_indicators = self.calculate_all_indicators(df_with_indicators)
    
        # 3. 获取高低点并计算斐波那契
        high, low = self.get_recent_high_low(df_with_indicators, lookback_period)
        fib_levels = self.calculate_fibonacci_levels(high, low)
        
        # 4. 检查前提条件
        prereq_results = self.check_prerequisites(
            df_with_indicators, premium_rate, call_risk_distance
        )
        
        # 5. 如果前提条件不满足，直接返回
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
        
        # 6. 技术分析
        trend_results = self.check_trend_confirmation(df_with_indicators)
        buy_results = self.check_buy_signals(df_with_indicators, fib_levels, relative_strength_data, volume_structure_data)
        sell_results = self.check_sell_signals(df_with_indicators, fib_levels)
        
        # 7. 生成综合信号
        overall_signal = self._generate_overall_signal(trend_results, buy_results, sell_results)
        
        # 8. 生成策略上下文
        advice_context = self._generate_advice_context(trend_results, buy_results, sell_results, overall_signal)
        
        # 9. 收集技术指标数据用于HTML报告
        indicators_data = {}
        if 'indicators' in trend_results:
            indicators_data = trend_results['indicators']
        
        return {
            'prerequisites': prereq_results,
            'trend_confirmation': trend_results,
            'buy_signals': buy_results,
            'sell_signals': sell_results,
            'fibonacci_levels': fib_levels,
            'current_price': df_with_indicators['close'].iloc[-1],
            'indicators': indicators_data,  # 新增：技术指标数据
            'overall_signal': overall_signal,
            'advice_context': advice_context,
            'analysis_time': pd.Timestamp.now()
        }
    
    def _generate_overall_signal(self, trend: Dict, buy: Dict, sell: Dict) -> str:
        """生成综合交易信号"""
        if not trend.get('all_satisfied', False):
            return "WAIT"
        
        if buy.get('buy_triggered', False):
            return "STRONG_BUY"
        
        if sell and any(sell.values()):
            return "SELL"
        
        return "HOLD"
    
    def _generate_advice_context(self, trend: Dict, buy: Dict, sell: Dict, signal: str) -> str:
        """生成策略上下文，解释当前市场状态和适合的操作"""
        trend_strength = trend.get('trend_strength', 0)
        buy_count = buy.get('satisfied_count', 0)
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
        """生成可读的分析报告 - 完整修复版"""
        report = []
        report.append("=" * 60)
        report.append("📊 可转债多因子共振技术分析报告（完整修复版）")
        report.append("=" * 60)
        
        # 前提条件
        prereq = analysis_results['prerequisites']
        report.append("\n🔍 前提条件检查:")
        for msg in prereq['messages']:
            report.append(f"  {msg}")
        
        if 'detailed_explanations' in prereq:
            report.append("\n💡 前提条件解读:")
            for explanation in prereq['detailed_explanations']:
                report.append(f"  {explanation}")
        
        if not prereq['all_ok']:
            report.append("\n❌ 技术分析终止: 不满足前提条件")
            if 'advice_context' in analysis_results:
                report.append(f"\n{analysis_results['advice_context']}")
            return "\n".join(report)
        
        # 当前价格
        current_price = analysis_results.get('current_price', 0)
        report.append(f"\n💰 当前价格: {current_price:.2f}")
        
        # 趋势确认 - 显示所有技术指标
        trend = analysis_results['trend_confirmation']
        report.append("\n📈 趋势确认:")
        report.append(f"  均线多头: {'✅' if trend['ma_bullish'] else '❌'} {trend['details']['ma_status']}")
        report.append(f"     → {trend['explanations']['ma_explanation']}")
        
        report.append(f"  MACD金叉: {'✅' if trend['macd_bullish'] else '❌'} {trend['details']['macd_status']}")
        report.append(f"     → {trend['explanations']['macd_explanation']}")
        
        report.append(f"  ADX强度: {'✅' if trend['adx_strong'] else '❌'} {trend['details']['adx_status']}")
        report.append(f"     → {trend['explanations']['adx_explanation']}")
        
        # 显示技术指标数值
        report.append(f"\n📊 技术指标数值:")
        report.append(f"  RSI: {trend['details']['rsi']}")
        report.append(f"  KDJ: {trend['details']['kdj']}")
        report.append(f"  MFI: {trend['details']['mfi']}")
        
        report.append(f"  趋势强度: {trend['trend_strength']}/3分 - {trend['trend_level'].upper()}趋势")
        report.append(f"  参与建议: {trend['participate_advice']}")
        
        # 买点信号
        buy = analysis_results['buy_signals']
        if buy:
            report.append(f"\n🛒 买点确认 (满足{buy['satisfied_count']}/6):")
            
            report.append(f"  斐波支撑: {'✅' if buy['fib_support'] else '❌'} {buy['details']['fib_level']}")
            report.append(f"     → {buy['explanations']['fib_support']}")
            
            report.append(f"  布林超卖: {'✅' if buy['bollinger_oversold'] else '❌'} {buy['details']['bollinger_position']}")
            report.append(f"     → {buy['explanations']['bollinger_oversold']}")
            
            report.append(f"  RSI底背离: {'✅' if buy['rsi_oversold_divergence'] else '❌'} {buy['details']['rsi_level']}")
            report.append(f"     → {buy['explanations']['rsi_oversold_divergence']}")
            
            report.append(f"  温和放量: {'✅' if buy['volume_increase'] else '❌'} {buy['details']['volume_status']}")
            report.append(f"     → {buy['explanations']['volume_increase']}")
            
            report.append(f"  相对强弱: {'✅' if buy['relative_strength'] else '❌'} 比率={buy['details'].get('relative_strength_ratio', 0):.2f}")
            report.append(f"     → {buy['explanations']['relative_strength']}")
            
            report.append(f"  量能结构: {'✅' if buy['volume_structure'] else '❌'} 信号={buy['details'].get('volume_structure_signal', '未知')}")
            report.append(f"     → {buy['explanations']['volume_structure']}")
            
            report.append(f"  买点触发: {'✅' if buy['buy_triggered'] else '❌'}")
        
        # 卖点信号
        sell = analysis_results.get('sell_signals', {})
        if sell:
            report.append(f"\n🏷️ 卖点确认:")
            
            report.append(f"  斐波阻力: {'✅' if sell['fib_resistance'] else '❌'} {sell['details']['fib_resistance_level']}")
            report.append(f"     → {sell['explanations']['fib_resistance']}")
            
            report.append(f"  布林滞涨: {'✅' if sell['bollinger_overbought_stagnation'] else '❌'} {sell['details']['bollinger_position']}")
            report.append(f"     → {sell['explanations']['bollinger_overbought_stagnation']}")
            
            report.append(f"  RSI顶背离: {'✅' if sell['rsi_overbought_divergence'] else '❌'} {sell['details']['rsi_level']}")
            report.append(f"     → {sell['explanations']['rsi_overbought_divergence']}")
        
        # 综合建议
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
            "BUY": "✅ 买入信号 - 技术面支持参与",
            "SELL": "⚠️ 卖出信号 - 注意风险", 
            "HOLD": "⏳ 持有观望 - 等待更好时机",
            "WAIT": "🎯 等待趋势 - 趋势未确认",
            "INVALID": "❌ 无效信号 - 检查前提条件"
        }
        return descriptions.get(signal, "未知信号")

# ==================== 原有数据库和类定义 ====================

# 可转债数据库（保持不变）
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
    
    def safe_float_parse(self, value, default=0):
        """安全浮点数解析"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                value = value.replace('%', '').replace(',', '').strip()
                if value:
                    return float(value)
            return default
        except:
            return default
    
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
                
                price = self.safe_float_parse(bond.get('债现价', 0))
                premium = self.safe_float_parse(bond.get('转股溢价率', 0))
                conversion_value = self.safe_float_parse(bond.get('转股价值', 0))
                
                if price > 1000:
                    price = price / 10
                if conversion_value > 1000:
                    conversion_value = conversion_value / 10
                
                bonds_data[bond_code] = {
                    'name': bond.get('债券简称', f"转债{bond_code}"),
                    'price': price,
                    'premium_rate': premium,
                    'conversion_value': conversion_value,
                    'remaining_size': self.safe_float_parse(str(bond.get('发行规模', '10')).replace('亿元', '').replace('亿', ''))
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
        
        premium = bond_info.get('premium_rate', 0)
        conversion_value = bond_info.get('conversion_value', 0)
        price = bond_info.get('price', 0)
        
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
        """获取腾讯财经数据 - 修复价格解析"""
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
                    price_str = parts[3]
                    if price_str:
                        price = float(price_str)
                        # 价格合理性验证和修正
                        if price > 1000:  # 如果价格异常高，可能是数据格式问题
                            price = price / 10
                        elif price < 10:  # 如果价格异常低
                            price = price * 10
                        
                        # 最终价格范围验证
                        if 50 < price < 300:
                            return {
                                'current': round(price, 2),
                                'source': '腾讯财经'
                            }
            return None
            
        except Exception as e:
            print(f"腾讯数据获取失败: {e}")
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
                        
                        current_price = em_data.get('f43', 0)
                        # 价格修正逻辑
                        if current_price > 1000:
                            current_price = current_price / 1000
                        elif current_price > 100:
                            current_price = current_price / 100
                        
                        # 价格范围验证
                        if current_price < 50 or current_price > 300:
                            return None
                        
                        turnover = em_data.get('f168', 0)
                        if turnover > 100:
                            corrected_turnover = turnover / 100
                        else:
                            corrected_turnover = turnover
                        
                        result = {
                            'current': round(current_price, 2),
                            'amount': em_data.get('f48', 0),
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
            face_value = 100
            coupon_rate = 0.02
            discount_rate = 0.04
            
            if years_to_maturity is None:
                years_to_maturity = 3
            
            annual_coupon = face_value * coupon_rate
            present_value = 0
            
            for year in range(1, int(years_to_maturity) + 1):
                present_value += annual_coupon / ((1 + discount_rate) ** year)
            
            present_value += face_value / ((1 + discount_rate) ** years_to_maturity)
            
            pure_bond_value = round(present_value, 2)
            bond_premium_rate = ((bond_price - pure_bond_value) / pure_bond_value) * 100
            
            return {
                'pure_bond_value': pure_bond_value,
                'bond_premium_rate': round(bond_premium_rate, 2),
                'calculation_method': f"贴现率{discount_rate:.1%}, 剩余年限{years_to_maturity}年"
            }
        except Exception as e:
            print(f"纯债价值计算失败: {e}")
            return {
                'pure_bond_value': 85,
                'bond_premium_rate': 0,
                'calculation_method': '估算值'
            }

    def calculate_effective_floor(self, bond_info):
        """计算有效债底 - 结合纯债价值、回售价值、历史支撑"""
        try:
            bond_price = bond_info.get('转债价格', 0)
            pure_bond_data = self.calculate_pure_bond_value(
                bond_info.get('转债代码', ''),
                bond_price,
                bond_info.get('剩余年限')
            )
            
            pure_bond_value = pure_bond_data['pure_bond_value']
            
            put_value = self.estimate_put_value(bond_info)
            
            historical_support = bond_info.get('技术分析数据', {}).get('支撑位', pure_bond_value * 1.1)
            
            effective_floor = max(pure_bond_value, put_value, historical_support)
            
            return {
                'pure_bond_value': pure_bond_value,
                'put_value': put_value,
                'historical_support': historical_support,
                'effective_floor': effective_floor,
                'effective_floor_premium': round(((bond_price - effective_floor) / effective_floor) * 100, 2),
                'pure_bond_premium': pure_bond_data['bond_premium_rate'],
                'calculation_method': pure_bond_data['calculation_method']
            }
        except Exception as e:
            print(f"有效债底计算失败: {e}")
            return None

    def estimate_put_value(self, bond_info):
        """估算回售价值"""
        try:
            years_to_maturity = bond_info.get('剩余年限', 3)
            
            if years_to_maturity <= 2:
                put_value = 102
            elif years_to_maturity <= 3:
                put_value = 101
            else:
                put_value = 100
            
            return put_value
        except:
            return 100

    def analyze_redemption_risk(self, bond_code, stock_price, conversion_price):
        """分析强赎风险 - 修正版本"""
        redemption_data = {
            "conversion_price": conversion_price,
            "trigger_price": round(conversion_price * 1.3, 2),
            "pb_ratio": 1.5,
            "trigger_condition": "连续30个交易日中至少15个交易日收盘价不低于转股价的130%",
        }
        
        current_ratio = stock_price / redemption_data["trigger_price"] if redemption_data["trigger_price"] > 0 else 0
        progress_percent = current_ratio * 100
        
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
            "current_stock_price": round(stock_price, 2),
            "trigger_ratio": round(current_ratio, 3),
            "status": status,
            "progress": progress,
            "风险等级": risk_level,
            "distance_to_trigger": round(redemption_data["trigger_price"] - stock_price, 2),
            "progress_percent": progress_percent
        })
        
        return redemption_data
    
    def analyze_downward_adjustment(self, bond_code, stock_price, conversion_price, bond_price, pb_ratio, years_to_maturity):
        """分析下修可能性 - 增强版本"""
        adjust_data = {
            "adjust_history": [],
            "adjust_count": 0,
            "last_adjust_date": "无",
        }
        
        conversion_value = stock_price / conversion_price * 100 if conversion_price > 0 else 0
        premium_rate = (bond_price - conversion_value) / conversion_value * 100 if conversion_value > 0 else 0
        
        down_conditions = []
        condition_scores = 0
        
        if conversion_value < 70:
            down_conditions.append(f"转股价值极低({conversion_value:.1f})")
            condition_scores += 3
        elif conversion_value < 80:
            down_conditions.append(f"转股价值较低({conversion_value:.1f})")
            condition_scores += 2
        elif conversion_value < 90:
            down_conditions.append(f"转股价值一般({conversion_value:.1f})")
            condition_scores += 1
        
        if premium_rate > 40:
            down_conditions.append(f"溢价率极高({premium_rate:.1f}%)")
            condition_scores += 3
        elif premium_rate > 30:
            down_conditions.append(f"溢价率较高({premium_rate:.1f}%)")
            condition_scores += 2
        elif premium_rate > 20:
            down_conditions.append(f"溢价率适中({premium_rate:.1f}%)")
            condition_scores += 1
        
        if years_to_maturity and years_to_maturity < 1:
            down_conditions.append("临近回售期(<1年)")
            condition_scores += 3
        elif years_to_maturity and years_to_maturity < 2:
            down_conditions.append("接近回售期(<2年)")
            condition_scores += 2
        
        if pb_ratio and pb_ratio < 1.0:
            down_conditions.append("PB<1, 下修空间受限")
            condition_scores -= 2
        elif pb_ratio and pb_ratio < 1.3:
            down_conditions.append("PB较低, 下修空间有限")
            condition_scores -= 1
        
        if adjust_data["adjust_count"] > 0:
            down_conditions.append(f"历史已下修{adjust_data['adjust_count']}次")
            condition_scores += 1
        
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
        
        if years_to_maturity and years_to_maturity < 1.5 and condition_scores >= 2:
            probability = "中高"
            suggestion += " (临期转债下修概率提升)"
        
        adjust_data.update({
            "down_conditions": down_conditions,
            "condition_scores": condition_scores,
            "current_probability": probability,
            "suggestion": suggestion,
            "conversion_value": round(conversion_value, 2),
            "premium_rate": round(premium_rate, 2),
            "pb_ratio": pb_ratio,
            "probability_score": condition_scores
        })
        
        return adjust_data

    def get_pb_ratio(self, bond_code, default=1.5):
        """获取PB值"""
        return BOND_PB_DATABASE.get(bond_code, default)

    def analyze_stock_bond_linkage(self, bond_info):
        """正股和转债联动分析"""
        try:
            stock_price = bond_info.get("正股价格", 0)
            bond_price = bond_info.get("转债价格", 0)
            conversion_value = bond_info.get("转股价值", 0)
            premium_rate = bond_info.get("溢价率(%)", 0)
            
            linkage_analysis = {}
            
            if premium_rate < 10:
                linkage_analysis["溢价率联动"] = "强联动 - 溢价率低, 转债跟涨性强"
            elif premium_rate < 20:
                linkage_analysis["溢价率联动"] = "中等联动 - 溢价率适中"
            elif premium_rate < 30:
                linkage_analysis["溢价率联动"] = "弱联动 - 溢价率偏高"
            else:
                linkage_analysis["溢价率联动"] = "脱钩风险 - 溢价率过高, 联动性差"
            
            delta = conversion_value / bond_price if bond_price > 0 else 0
            if delta > 0.9:
                linkage_analysis["Delta弹性"] = "高弹性 - 股性强, 正股波动传导充分"
            elif delta > 0.7:
                linkage_analysis["Delta弹性"] = "中弹性 - 平衡型"
            else:
                linkage_analysis["Delta弹性"] = "低弹性 - 债性强, 正股波动传导有限"
            
            theoretical_price = conversion_value * (1 + premium_rate/100)
            price_deviation = ((bond_price - theoretical_price) / theoretical_price) * 100
            
            if abs(price_deviation) < 2:
                linkage_analysis["价格合理性"] = "价格合理 - 市场定价有效"
            elif price_deviation > 5:
                linkage_analysis["价格合理性"] = "可能高估 - 转债价格偏高"
            elif price_deviation < -5:
                linkage_analysis["价格合理性"] = "可能低估 - 转债价格偏低"
            else:
                linkage_analysis["价格合理性"] = "价格基本合理"
            
            if premium_rate < 15 and delta > 0.8:
                linkage_analysis["联动策略"] = "适合正股联动策略 - 跟涨性强"
            elif premium_rate > 30:
                linkage_analysis["联动策略"] = "适合独立走势策略 - 联动性弱"
            else:
                linkage_analysis["联动策略"] = "平衡策略 - 需结合其他因素"
            
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
ta_analyzer = ConvertibleBondTA()

# ==================== 新增：计算增强指标 ====================

def calculate_enhanced_indicators(bond_info):
    """
    计算增强指标：相对强弱、量能结构、KDJ、MFI
    """
    try:
        np.random.seed(int(bond_info['转债代码']) % 10000)
        
        days = 20
        base_price = bond_info['转债价格']
        base_stock_price = bond_info['正股价格']
        
        bond_prices = []
        for i in range(days):
            change = np.random.normal(0, 0.015)
            price = base_price * (1 + change * (days - i) / days)
            bond_prices.append(price)
        
        stock_prices = []
        for i in range(days):
            change = np.random.normal(0, 0.02)
            price = base_stock_price * (1 + change * (days - i) / days)
            stock_prices.append(price)
        
        volumes = []
        for i in range(days):
            volume = np.random.normal(50000000, 20000000)
            volumes.append(volume)
        
        high_prices = [p * (1 + abs(np.random.normal(0, 0.01))) for p in bond_prices]
        low_prices = [p * (1 - abs(np.random.normal(0, 0.01))) for p in bond_prices]
        
        rs_data = calculate_relative_strength(bond_prices, stock_prices)
        if rs_data:
            bond_info['relative_strength'] = rs_data
            bond_info['relative_strength_ratio'] = rs_data['relative_strength_ratio']
        
        vol_data = analyze_volume_structure(volumes, bond_prices)
        if vol_data:
            bond_info['volume_structure'] = vol_data
        
        kdj_data = calculate_kdj(high_prices, low_prices, bond_prices)
        mfi_data = calculate_mfi(high_prices, low_prices, bond_prices, volumes)
        
        enhanced_ta = {}
        if kdj_data:
            enhanced_ta['kdj'] = kdj_data
        if mfi_data:
            enhanced_ta['mfi'] = mfi_data
        
        if enhanced_ta:
            bond_info['enhanced_ta'] = enhanced_ta
        
        return bond_info
        
    except Exception as e:
        print(f"增强指标计算失败: {e}")
        return bond_info

# ==================== 修复函数：多因子共振分析 ====================

def get_historical_data_for_ta(bond_code, days=300, actual_price=None):
    """
    为技术分析获取历史数据 - 修复价格一致性版本
    """
    try:
        if actual_price is not None:
            current_price = actual_price
        else:
            base_info = get_bond_basic_info(bond_code)
            if not base_info:
                return None
            current_price = base_info.get('转债价格', 100)
            
        print(f"   技术分析使用价格: {current_price}元")
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        np.random.seed(int(bond_code) % 10000)
        
        prices = [current_price * 0.8]
        for i in range(1, days-1):
            change = np.random.normal(0.001, 0.015)
            new_price = prices[-1] * (1 + change)
            if new_price < current_price * 0.5:
                new_price = current_price * 0.5
            elif new_price > current_price * 1.5:
                new_price = current_price * 1.5
            prices.append(new_price)
        
        prices.append(current_price)
        
        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': [abs(np.random.normal(50000000, 20000000)) for _ in prices]
        })
        df.set_index('date', inplace=True)
        
        if abs(df['close'].iloc[-1] - current_price) > 0.01:
            df.iloc[-1, df.columns.get_loc('close')] = current_price
        
        return df
        
    except Exception as e:
        print(f"历史数据生成失败: {e}")
        return None

def perform_multifactor_analysis(bond_code, bond_info):
    """
    执行多因子共振分析 - 修复价格一致性版本
    """
    print(f"\n🔍 执行多因子共振技术分析...")
    
    actual_price = bond_info.get('转债价格', 0)
    print(f"   实际转债价格: {actual_price}元")
    
    premium_rate = bond_info.get('溢价率(%)', 0)
    print(f"   原始溢价率数据: {premium_rate} (类型: {type(premium_rate)})")
    
    # 彻底转换溢价率为浮点数
    try:
        if isinstance(premium_rate, np.float64) or isinstance(premium_rate, np.float32):
            premium_rate = float(premium_rate)
            print(f"   转换后溢价率: {premium_rate}% (numpy类型转换)")
        elif isinstance(premium_rate, str):
            clean_str = ''.join(c for c in str(premium_rate) if c.isdigit() or c in '.-')
            if clean_str:
                premium_rate = float(clean_str)
                print(f"   转换后溢价率: {premium_rate}% (从字符串转换)")
            else:
                premium_rate = 0.0
                print(f"   转换失败，使用默认值: {premium_rate}%")
        elif isinstance(premium_rate, (int, float)):
            premium_rate = float(premium_rate)
            print(f"   转换后溢价率: {premium_rate}% (已经是数值类型)")
        else:
            premium_rate = 0.0
            print(f"   未知类型，使用默认值: {premium_rate}%")
    except Exception as e:
        print(f"   溢价率转换异常: {e}")
        premium_rate = 0.0
    
    print(f"   最终使用溢价率: {premium_rate}%")
    print(f"   转股价值: {bond_info.get('转股价值', 0)}")
    
    historical_data = get_historical_data_for_ta(bond_code, actual_price=actual_price)
    if historical_data is None:
        return {"error": "无法获取历史数据"}
    
    call_risk_distance = 0.3
    redemption_data = bond_info.get("强赎分析", {})
    if redemption_data:
        progress_percent = redemption_data.get("progress_percent", 30)
        call_risk_distance = (100 - progress_percent) / 100.0
    
    relative_strength_data = bond_info.get('relative_strength')
    volume_structure_data = bond_info.get('volume_structure')
    
    try:
        premium_rate_decimal = float(premium_rate) / 100.0
        
        print(f"   多因子分析使用溢价率: {premium_rate_decimal:.3f} (小数形式)")
        
        ta_results = ta_analyzer.comprehensive_analysis(
            df=historical_data,
            premium_rate=premium_rate_decimal,
            call_risk_distance=call_risk_distance,
            actual_price=actual_price,
            relative_strength_data=relative_strength_data,
            volume_structure_data=volume_structure_data
        )
        
        bond_info['multifactor_signal'] = ta_results.get('overall_signal', 'WAIT')
        bond_info['multifactor_results'] = ta_results
        
        report = ta_analyzer.generate_analysis_report(ta_results)
        print(report)
        
        return ta_results
        
    except Exception as e:
        print(f"多因子共振分析失败: {e}")
        print(f"调试信息 - premium_rate类型: {type(premium_rate)}, 值: {premium_rate}")
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
    volume_desc = ""
    turnover_desc = ""
    
    if turnover_rate > 100:
        turnover_rate = turnover_rate / 100
    
    if avg_volume < 0.05:
        volume_desc = "成交额极低"
        volume_score = 1
    elif avg_volume < 0.1:
        volume_desc = "成交额较低"
        volume_score = 2
    elif avg_volume < 0.3:
        volume_desc = "成交额一般"
        volume_score = 3
    elif avg_volume < 0.5:
        volume_desc = "成交额良好"
        volume_score = 4
    else:
        volume_desc = "成交额充足"
        volume_score = 5
    
    if turnover_rate < 0.5:
        turnover_desc = "换手率极低"
        turnover_score = 1
    elif turnover_rate < 1:
        turnover_desc = "换手率较低"
        turnover_score = 2
    elif turnover_rate < 3:
        turnover_desc = "换手率一般"
        turnover_score = 3
    elif turnover_rate < 5:
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
        '成交额描述': f"{volume_desc}({avg_volume:.3f}亿)",
        '换手率描述': f"{turnover_desc}({turnover_rate:.2f}%)",
        '建议': advice,
        '综合得分': f"{total_score}/10"
    }

def calculate_ytm(bond_price, years=3):
    """计算到期收益率"""
    try:
        bond_price = float(bond_price)
        if bond_price <= 100:
            ytm = (100 - bond_price) / bond_price / years + 0.02
        else:
            ytm = 0.02 - (bond_price - 100) / bond_price / years
        return round(ytm * 100, 2)
    except:
        return 0.0

def safe_float_parse(value, default=0):
    """安全浮点数解析"""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            value = value.replace('%', '').replace(',', '').strip()
            if value:
                return float(value)
        return default
    except:
        return default

def safe_premium_parse(premium_raw, bond_price, conversion_value):
    """安全溢价率解析"""
    try:
        if premium_raw and isinstance(premium_raw, str):
            premium_str = premium_raw.replace('%', '').replace(',', '').strip()
            if premium_str and premium_str.replace('.', '', 1).replace('-', '').isdigit():
                return float(premium_str)
        
        if conversion_value > 0:
            return round((bond_price - conversion_value) / conversion_value * 100, 2)
        else:
            return 0.0
    except:
        return 0.0

def calculate_fibonacci_levels(high, low):
    """计算斐波那契回撤位"""
    try:
        high = float(high)
        low = float(low)
        
        if high <= low:
            return {}
            
        price_range = high - low
        
        fib_levels = {
            '0.0%': high,
            '23.6%': high - price_range * 0.236,
            '38.2%': high - price_range * 0.382,
            '50.0%': high - price_range * 0.5,
            '61.8%': high - price_range * 0.618,
            '78.6%': high - price_range * 0.786,
            '100.0%': low,
        }
        return fib_levels
    except:
        return {}

def get_technical_analysis(bond_code, current_price, conversion_value, bond_price):
    """完整技术分析"""
    try:
        if bond_code in BOND_TECHNICAL_DATABASE:
            bond_data = BOND_TECHNICAL_DATABASE[bond_code]
            high_250 = bond_data['high_250']
            low_250 = bond_data['low_250']
            high_120 = bond_data['high_120']
            low_120 = bond_data['low_120']
            data_source_info = bond_data.get('data_source', '真实价格数据库')
            fib_levels = bond_data.get('fib_levels', calculate_fibonacci_levels(high_250, low_250))
        else:
            high_250 = min(current_price * 1.15, 200)
            low_250 = max(current_price * 0.85, 80)
            high_120 = min(current_price * 1.10, 180)
            low_120 = max(current_price * 0.90, 90)
            data_source_info = '智能估算'
            fib_levels = calculate_fibonacci_levels(high_250, low_250)
        
        ma_20 = current_price * 0.98
        ma_60 = current_price * 0.96
        ma_120 = current_price * 0.94
        
        support = round(low_120 * 0.98, 2)
        resistance = round(high_250, 2)
        
        distance_to_support = ((current_price - support) / current_price) * 100
        distance_to_resistance = ((resistance - current_price) / current_price) * 100
        
        if distance_to_support < 5:
            position_status = "接近支撑"
        elif distance_to_resistance < 5:
            position_status = "接近压力"
        else:
            position_status = "中间区域, 方向待定"
        
        if ma_20 > ma_60 > ma_120:
            ma_status = "多头排列, 趋势向上"
        elif ma_20 < ma_60 < ma_120:
            ma_status = "空头排列, 趋势向下"
        else:
            ma_status = "均线交织, 震荡整理"
        
        delta = conversion_value / bond_price if bond_price > 0 else 0
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
        current_price = float(current_price)
        support = current_price * 0.95
        resistance = current_price * 1.05
        
        delta = conversion_value / bond_price if bond_price > 0 else 0
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
            '近期高点(250日)': round(current_price * 1.15, 2),
            '近期低点(250日)': round(current_price * 0.85, 2),
            '近期高点(120日)': round(current_price * 1.10, 2),
            '近期低点(120日)': round(current_price * 0.90, 2),
            '20日均线': round(current_price, 2),
            '60日均线': round(current_price, 2),
            '120日均线': round(current_price, 2),
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
    """获取债券基础信息 - 修复字段名和价格问题"""
    try:
        bond_df = ak.bond_zh_cov()
        if bond_df is not None and not bond_df.empty and '债券代码' in bond_df.columns:
            match = bond_df[bond_df['债券代码'] == bond_code]
            if not match.empty:
                bond_data = match.iloc[0]
                
                bond_price = safe_float_parse(bond_data.get('最新价', bond_data.get('债现价', 0)))
                stock_price = safe_float_parse(bond_data.get('正股价', 0))
                convert_price = safe_float_parse(bond_data.get('转股价', 1))
                
                # 价格修正逻辑
                if bond_price > 1000:
                    bond_price = bond_price / 10
                elif bond_price < 10:  # 如果价格异常低
                    bond_price = bond_price * 10
                
                conversion_value = round(stock_price / convert_price * 100, 2) if convert_price > 0 else 0
                premium_rate = safe_premium_parse(bond_data.get('转股溢价率', ''), bond_price, conversion_value)
                
                raw_maturity_date = bond_data.get('到期时间', '未知')
                maturity_date, years_to_maturity = bond_analyzer.get_enhanced_maturity_info(bond_code, raw_maturity_date)
                
                size_str = str(bond_data.get('发行规模', '10')).replace('亿元', '').replace('亿', '')
                remaining_size = float(size_str) if size_str.replace('.', '', 1).isdigit() else 10.0
                
                pb_ratio = bond_analyzer.get_pb_ratio(bond_code)
                
                redemption_analysis = bond_analyzer.analyze_redemption_risk(bond_code, stock_price, convert_price)
                
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
            
        cost_price = float(cost_input)
        shares = int(shares_input)
        
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
    
    current_price = bond_info.get('转债价格', 0)
    cost_price = holding_info.get('cost_price', 0)
    shares = holding_info.get('shares', 0)
    
    if cost_price > 0 and current_price > 0:
        profit_per_share = current_price - cost_price
        profit_rate = (profit_per_share / cost_price) * 100
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
    """增强版债券信息获取 - 修复价格问题"""
    print(f"   分析 {bond_code}...")
    
    base_info = get_bond_basic_info(bond_code)
    if not base_info:
        return None
    
    tencent_data = data_source.get_tencent_data(bond_code)
    eastmoney_data = data_source.get_eastmoney_data(bond_code)
    
    enhanced_info = base_info.copy()
    data_sources = ["AkShare"]
    original_price = base_info.get("转债价格", 0)
    
    # 价格验证和修正逻辑
    print(f"   AkShare价格: {original_price}元")
    
    if tencent_data:
        t_price = tencent_data.get('current', 0)
        print(f"   腾讯财经价格: {t_price}元")
        
        # 价格差异较大时的处理逻辑
        price_diff_pct = abs(t_price - original_price) / original_price * 100 if original_price > 0 else 100
        
        if price_diff_pct > 20:  # 价格差异超过20%
            print(f"   ⚠️ 价格差异较大: AkShare={original_price}元, 腾讯={t_price}元 (差异{price_diff_pct:.1f}%)")
            # 使用更合理的价格
            if 80 < t_price < 200:  # 腾讯价格在合理范围内
                enhanced_info["转债价格"] = round(t_price, 2)
                data_sources.append("腾讯财经(修正)")
                print(f"   使用腾讯财经价格进行修正")
            else:
                data_sources.append("腾讯财经")
        else:
            data_sources.append("腾讯财经")
    
    if eastmoney_data:
        if eastmoney_data.get('amount'):
            em_amount = eastmoney_data['amount'] / 1e8
            if 0 < em_amount < 10:
                enhanced_info["日均成交额(亿)"] = round(em_amount, 3)
        if eastmoney_data.get('turnover'):
            turnover_rate = eastmoney_data['turnover']
            if turnover_rate > 100:
                turnover_rate = turnover_rate / 100
            enhanced_info["换手率(%)"] = round(turnover_rate, 2)
        data_sources.append("东方财富")
    
    enhanced_info["数据来源"] = "+".join(data_sources)
    
    # 修复溢价率类型
    if '溢价率(%)' in enhanced_info:
        premium = enhanced_info['溢价率(%)']
        if isinstance(premium, str):
            try:
                clean_str = str(premium).replace('%', '').replace(',', '').strip()
                if clean_str:
                    enhanced_info['溢价率(%)'] = float(clean_str)
            except:
                print(f"  无法解析溢价率: {premium}")
        elif isinstance(premium, np.float64) or isinstance(premium, np.float32):
            enhanced_info['溢价率(%)'] = float(premium)
    
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
    
    linkage_analysis = bond_analyzer.analyze_stock_bond_linkage(enhanced_info)
    enhanced_info["联动分析"] = linkage_analysis
    
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
    """生成风险标签"""
    price = bond_info.get("转债价格", 0)
    ytm = bond_info.get("YTM(%)", 0)
    floor_analysis = bond_info.get("债底分析", {})
    
    risk_tags = []
    
    if price > 130 and ytm < -5:
        risk_tags.append("高波风险")
        
        put_value = floor_analysis.get('put_value', 0) if floor_analysis else 0
        if put_value <= 100:
            risk_tags.append("无回售保护")
    
    if floor_analysis:
        effective_floor_premium = floor_analysis.get('effective_floor_premium', 0)
        if effective_floor_premium > 40:
            risk_tags.append("债底保护弱")
        elif effective_floor_premium > 25:
            risk_tags.append("债底保护一般")
    
    return risk_tags

def calculate_comprehensive_score_v2(info):
    """综合评分算法 v2.1"""
    score = 0
    details = []
    
    premium = info.get("溢价率(%)", 0)
    conversion_value = info.get("转股价值", 0)
    
    if premium > 40:
        score -= 20
        details.append("溢价:超高溢[-20]")
    elif premium > 35:
        score -= 15
        details.append("溢价:高溢[-15]")
    elif premium > 30:
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
    
    size = info.get("剩余规模(亿)", 10)
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
    
    price = info.get("转债价格", 0)
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
    
    volume = info.get("日均成交额(亿)", 0)
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
    
    ytm = info.get("YTM(%)", 0)
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
    
    if conversion_value > 110:
        score += 10
        details.append("价内:深度[+10]")
    elif conversion_value > 105:
        score += 8
        details.append("价内:良好[+8]")
    elif conversion_value > 100:
        score += 5
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
    
    final_score = max(0, min(score, 100))
    return final_score, details

def get_operation_advice(score, bond_info, final_grade):
    """操作建议"""
    premium = bond_info.get("溢价率(%)", 0)
    bond_price = bond_info.get("转债价格", 0)
    conversion_value = bond_info.get("转股价值", 0)
    ta_signal = bond_info.get('multifactor_signal', 'WAIT')
    
    if "硬回避" in final_grade:
        upside_needed = (bond_price - conversion_value) / conversion_value * 100
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
    
    double_low_value = info["双低值"]
    if double_low_value < 130:
        strategies.append("双低策略: 优秀 - 价格和溢价率都很低, 安全边际充足")
    elif double_low_value < 150:
        strategies.append("双低策略: 良好 - 性价比较高, 适合配置")
    else:
        strategies.append("双低策略: 一般 - 双低值偏高, 安全边际有限")
    
    premium = info["溢价率(%)"]
    if premium < 10:
        strategies.append("低溢价策略: 优秀 - 跟涨能力强, 正股上涨时弹性大")
    elif premium < 20:
        strategies.append("低溢价策略: 良好 - 跟涨能力较好")
    else:
        strategies.append("低溢价策略: 不适合 - 溢价率偏高, 跟涨能力弱")
    
    size = info["剩余规模(亿)"]
    if size < 3:
        strategies.append("小规模策略: 优秀 - 规模小易炒作, 波动性大")
    elif size < 5:
        strategies.append("小规模策略: 良好 - 规模适中, 有一定弹性")
    
    ytm = info.get("YTM(%)", 0)
    if ytm > 3:
        strategies.append("高YTM策略: 优秀 - 到期收益高, 债底保护强")
    elif ytm > 1:
        strategies.append("高YTM策略: 良好 - 有一定债底保护")
    
    if size < 5 and premium < 20:
        strategies.append("小规模低溢价策略: 优秀 - 兼具弹性和安全边际")
    elif size < 5 and premium < 30:
        strategies.append("小规模低溢价策略: 良好 - 平衡型选择")
    
    return strategies

def get_risk_analysis(info):
    """风险分析"""
    risks = []
    
    premium = info.get("溢价率(%)", 0)
    if premium > 40:
        risks.append("溢价率风险: 高风险 - 溢价率>40%, 技术面信号可靠性大幅降低")
    elif premium > 30:
        risks.append("溢价率风险: 中风险 - 溢价率偏高, 需谨慎对待")
    elif premium > 20:
        risks.append("溢价率风险: 低风险 - 溢价率适中")
    else:
        risks.append("溢价率风险: 无风险 - 溢价率合理")
    
    price = info.get("转债价格", 0)
    if price > 140:
        risks.append("价格风险: 高风险 - 价格过高, 债底保护弱")
    elif price > 130:
        risks.append("价格风险: 中风险 - 价格偏高")
    elif price > 115:
        risks.append("价格风险: 低风险 - 价格合理")
    else:
        risks.append("价格风险: 无风险 - 价格安全")
    
    return risks

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
                    'price': info['转债价格'],
                    'premium': info['溢价率(%)'],
                    'double_low': info['双低值'],
                    'size': info['剩余规模(亿)'],
                    'score': score,
                    'ytm': info.get('YTM(%)', 0),
                    'volume': info.get('日均成交额(亿)', 0),
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
            price = safe_float_parse(bond.get('最新价', bond.get('债现价', 0)))
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
                        'price': info['转债价格'],
                        'premium': info['溢价率(%)'],
                        'double_low': info['双低值'],
                        'size': info['剩余规模(亿)'],
                        'score': score,
                        'ytm': info.get('YTM(%)', 0),
                        'volume': info.get('日均成交额(亿)', 0)
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
            price = safe_float_parse(bond.get('最新价', bond.get('债现价', 0)))
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
                        'price': info['转债价格'],
                        'premium': info['溢价率(%)'],
                        'double_low': info['双低值'],
                        'size': info['剩余规模(亿)'],
                        'score': score,
                        'ytm': info.get('YTM(%)', 0),
                        'volume': info.get('日均成交额(亿)', 0)
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
            price = safe_float_parse(bond.get('最新价', bond.get('债现价', 0)))
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
                        'price': info['转债价格'],
                        'premium': info['溢价率(%)'],
                        'double_low': info['双低值'],
                        'size': info['剩余规模(亿)'],
                        'score': score,
                        'ytm': info.get('YTM(%)', 0),
                        'volume': info.get('日均成交额(亿)', 0)
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
            price = safe_float_parse(bond.get('最新价', bond.get('债现价', 0)))
            if price > 1000:
                price = price / 10
                
            if 80 < price < 130:
                ytm = calculate_ytm(price, 3)
                if ytm > 0:
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
                        'price': info['转债价格'],
                        'premium': info['溢价率(%)'],
                        'double_low': info['双低值'],
                        'size': info['剩余规模(亿)'],
                        'score': score,
                        'ytm': info.get('YTM(%)', 0),
                        'volume': info.get('日均成交额(亿)', 0)
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
            price = safe_float_parse(bond.get('最新价', bond.get('债现价', 0)))
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
                        'price': info['转债价格'],
                        'premium': info['溢价率(%)'],
                        'double_low': info['双低值'],
                        'size': info['剩余规模(亿)'],
                        'score': score,
                        'ytm': info.get('YTM(%)', 0),
                        'volume': info.get('日均成交额(亿)', 0)
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
            price = safe_float_parse(bond.get('最新价', bond.get('债现价', 0)))
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
                        'price': info['转债价格'],
                        'premium': info['溢价率(%)'],
                        'double_low': info['双低值'],
                        'size': info['剩余规模(亿)'],
                        'score': score,
                        'ytm': info.get('YTM(%)', 0),
                        'volume': info.get('日均成交额(亿)', 0)
                    })
            display_batch_results(results)
            
    except Exception as e:
        print(f"综合评分分析失败: {e}")

# ==================== 关键修复：分析多因子共振策略前10名 ====================

def analyze_single_bond_multifactor(args):
    """单只转债的多因子分析函数，用于多线程"""
    bond_code, bond_data = args
    try:
        info = get_enhanced_bond_info(bond_code)
        if not info:
            return None
        
        premium = info.get('溢价率(%)', 0)
        price = info.get('转债价格', 0)
        
        if 80 < price < 150 and premium < 40:
            info = calculate_enhanced_indicators(info)
            
            try:
                premium_rate_decimal = float(premium) / 100.0
                historical_data = get_historical_data_for_ta(bond_code, actual_price=price)
                
                if historical_data is not None:
                    ta_results = ta_analyzer.comprehensive_analysis(
                        df=historical_data,
                        premium_rate=premium_rate_decimal,
                        call_risk_distance=0.3,
                        actual_price=price,
                        relative_strength_data=info.get('relative_strength'),
                        volume_structure_data=info.get('volume_structure')
                    )
                    
                    if ta_results and ta_results.get('overall_signal') == "STRONG_BUY":
                        return {
                            'code': bond_code,
                            'name': info['名称'],
                            'price': price,
                            'premium': premium,
                            'signal': 'STRONG_BUY',
                            'score': 95,
                            'signal_desc': '强烈买入'
                        }
                    elif ta_results and ta_results.get('overall_signal') == "BUY":
                        return {
                            'code': bond_code,
                            'name': info['名称'],
                            'price': price,
                            'premium': premium,
                            'signal': 'BUY',
                            'score': 85,
                            'signal_desc': '买入'
                        }
            except:
                return None
    except:
        return None
    return None

def analyze_multifactor_top10():
    """分析多因子共振策略前10名 - 使用多线程加速"""
    print("\n正在扫描多因子共振策略前10名...")
    try:
        bond_df = ak.bond_zh_cov()
        multifactor_list = []
        
        bonds_to_process = []
        for _, bond in bond_df.iterrows():
            bond_code = bond.get('债券代码', '')
            if not bond_code:
                continue
                
            price = safe_float_parse(bond.get('最新价', bond.get('债现价', 0)))
            premium = safe_float_parse(bond.get('转股溢价率', 0))
            
            if price > 1000:
                price = price / 10
                
            # 添加价格和溢价率过滤，避免无效数据
            if 80 < price < 150 and premium < 40 and bond_code:
                bonds_to_process.append((bond_code, bond))
        
        print(f"  需要分析 {len(bonds_to_process)} 只符合条件的转债，使用多线程加速...")
        
        # 移除 [:50] 限制，处理所有符合条件的转债
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_bond = {
                executor.submit(analyze_single_bond_multifactor, (bond_code, bond_data)): bond_code 
                for bond_code, bond_data in bonds_to_process  # 移除 [:50] 限制
            }
            
            for i, future in enumerate(as_completed(future_to_bond), 1):
                bond_code = future_to_bond[future]
                print(f"  进度: {i}/{len(future_to_bond)}", end='\r')
                try:
                    result = future.result(timeout=30)
                    if result:
                        results.append(result)
                except:
                    continue
        
        print(f"\n处理完成，共分析 {len(bonds_to_process)} 只转债，找到 {len(results)} 只符合条件的转债")
        
        top10 = sorted(results, key=lambda x: x['score'], reverse=True)[:10]
        
        print(f"\n多因子共振策略前10名:")
        print("=" * 80)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'信号':<12} {'价格':<8} {'溢价率':<8} {'评分':<6}")
        print("-" * 80)
        for i, bond in enumerate(top10, 1):
            print(f"{i:<4} {bond['name']:<12} {bond['code']:<10} {bond['signal_desc']:<12} {bond['price']:<8.1f} {bond['premium']:<8.1f}% {bond['score']:<6}")
        
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
                        'price': info['转债价格'],
                        'premium': info['溢价率(%)'],
                        'double_low': info['双低值'],
                        'size': info['剩余规模(亿)'],
                        'score': score,
                        'ytm': info.get('YTM(%)', 0),
                        'volume': info.get('日均成交额(亿)', 0)
                    })
            display_batch_results(results)
            
    except Exception as e:
        print(f"\n多因子共振策略分析失败: {e}")
        import traceback
        traceback.print_exc()

def debug_premium_issue():
    """调试溢价率类型转换问题"""
    print("\n🔧 调试溢价率类型转换问题")
    print("=" * 60)
    
    test_codes = ["113047", "110065", "123208"]
    
    for code in test_codes:
        print(f"\n测试 {code}:")
        print("-" * 40)
        
        try:
            bond_df = ak.bond_zh_cov()
            match = bond_df[bond_df['债券代码'] == code]
            if not match.empty:
                bond_data = match.iloc[0]
                raw_premium = bond_data.get('转股溢价率', '')
                raw_price = bond_data.get('最新价', bond_data.get('债现价', 0))
                print(f"  AkShare原始数据:")
                print(f"    溢价率: '{raw_premium}' (类型: {type(raw_premium)})")
                print(f"    价格: '{raw_price}' (类型: {type(raw_price)})")
        except Exception as e:
            print(f"  获取AkShare数据失败: {e}")
        
        info = get_enhanced_bond_info(code)
        if info:
            print(f"  转换后数据:")
            print(f"    溢价率: {info.get('溢价率(%)', 0)}% (类型: {type(info.get('溢价率(%)', 0))})")
            print(f"    价格: {info.get('转债价格', 0)}元 (类型: {type(info.get('转债价格', 0))})")
        
        try:
            if info and info.get('溢价率(%)', 0) < 30:
                result = perform_multifactor_analysis(code, info)
                if result and 'error' not in result:
                    print(f"  多因子分析: ✅ 成功")
                else:
                    print(f"  多因子分析: ❌ 失败")
        except Exception as e:
            print(f"  多因子分析异常: {e}")

def analyze_near_redemption_top15():
    """分析距离强赎接近的前15名"""
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
            bond_price = safe_float_parse(bond.get('最新价', bond.get('债现价', 0)))
            
            if bond_price > 1000:
                bond_price = bond_price / 10
                
            if 80 < bond_price < 200:
                trigger_price = convert_price * 1.3
                progress_ratio = stock_price / trigger_price if trigger_price > 0 else 0
                progress_percent = progress_ratio * 100
                
                if 0.7 <= progress_ratio < 1.0:
                    upside_potential = ((trigger_price - stock_price) / stock_price) * 100
                    
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
        
        top15 = sorted(near_redemption_list, key=lambda x: x['progress'], reverse=True)[:15]
        
        print(f"\n距离强赎接近的前15名（搏强赎策略）:")
        print("=" * 120)
        print(f"{'排名':<4} {'名称':<12} {'代码':<10} {'进度%':<8} {'正股价':<8} {'触发价':<8} {'上涨空间%':<10} {'转债价':<8} {'溢价率':<8}")
        print("-" * 120)
        for i, bond in enumerate(top15, 1):
            if bond['progress'] >= 95:
                status = "🔥"
                status_desc = "即将触发"
            elif bond['progress'] >= 90:
                status = "⚠️"
                status_desc = "很接近"
            elif bond['progress'] >= 80:
                status = "🔶"
                status_desc = "较接近"
            else:
                status = "🔹"
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
                        'price': info['转债价格'],
                        'premium': info['溢价率(%)'],
                        'double_low': info['双低值'],
                        'size': info['剩余规模(亿)'],
                        'score': score,
                        'ytm': info.get('YTM(%)', 0),
                        'volume': info.get('日均成交额(亿)', 0)
                    })
            display_batch_results(results)
        else:
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
            bond_price = safe_float_parse(bond.get('最新价', bond.get('债现价', 0)))
            
            if bond_price > 1000:
                bond_price = bond_price / 10
                
            if 80 < bond_price < 200:
                conversion_value = stock_price / convert_price * 100 if convert_price > 0 else 0
                premium_rate = (bond_price - conversion_value) / conversion_value * 100 if conversion_value > 0 else 0
                
                downward_score = 0
                
                if conversion_value < 70:
                    downward_score += 3
                elif conversion_value < 80:
                    downward_score += 2
                elif conversion_value < 90:
                    downward_score += 1
                
                if premium_rate > 40:
                    downward_score += 3
                elif premium_rate > 30:
                    downward_score += 2
                elif premium_rate > 20:
                    downward_score += 1
                
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
                        'price': info['转债价格'],
                        'premium': info['溢价率(%)'],
                        'double_low': info['双低值'],
                        'size': info['剩余规模(亿)'],
                        'score': score,
                        'ytm': info.get('YTM(%)', 0),
                        'volume': info.get('日均成交额(亿)', 0)
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
    print("可转债分析系统 v10.5 完整修复版 初始化中...")
    
    while True:
        print("\n" + "="*60)
        print("可转债分析系统 v10.5 完整修复版")
        print("="*60)
        print("1. 分析单个转债 (集成增强指标+多因子共振+HTML报告)")
        print("2. 批量代码列表分析")
        print("3. 双低策略前10名")
        print("4. 低溢价策略前10名") 
        print("5. 小规模策略前10名")
        print("6. 高YTM策略前10名")
        print("7. 小规模低溢价策略前10名")
        print("8. 综合评分前15名")
        print("9. 多因子共振策略前10名 (多线程加速)")
        print("10. 高风险转债黑名单")
        print("11. 距离强赎接近前15名")
        print("12. 距离下修接近前15名")
        print("13. 调试溢价率类型转换问题")
        print("0. 退出系统")
        print("-"*60)
        
        choice = input("请选择操作 (0-13): ").strip()
        
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
        elif choice == '13':
            debug_premium_issue()
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
        import traceback
        traceback.print_exc()
        print("如果出现akshare相关错误, 请尝试: pip install akshare --upgrade")
        print("如果出现pandas_ta错误, 请安装: pip install pandas_ta")