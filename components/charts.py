"""
可视化图表组件
基于Plotly和Matplotlib实现交互式图表
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import plotly.figure_factory as ff


class ChartGenerator:
    """图表生成器"""
    
    def __init__(self):
        self.color_palette = {
            'primary': '#1f77b4',
            'success': '#2ca02c',
            'warning': '#ff7f0e',
            'danger': '#d62728',
            'info': '#17becf'
        }
        self.template = 'plotly_white'
    
    def create_kpi_card(self, title: str, value: str, change: Optional[str] = None,
                        status: str = 'normal') -> Dict:
        """创建KPI卡片数据"""
        colors = {
            'normal': self.color_palette['info'],
            'good': self.color_palette['success'],
            'warning': self.color_palette['warning'],
            'danger': self.color_palette['danger']
        }
        
        return {
            'title': title,
            'value': value,
            'change': change,
            'status': status,
            'color': colors.get(status, colors['normal'])
        }
    
    def create_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                         title: str = '', show_trend: bool = True) -> go.Figure:
        """创建折线图"""
        fig = go.Figure()
        
        # 主数据线
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode='lines+markers',
            name=y_col,
            line=dict(color=self.color_palette['primary'], width=2),
            marker=dict(size=6)
        ))
        
        # 趋势线
        if show_trend and len(df) > 1:
            z = np.polyfit(range(len(df)), df[y_col], 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=p(range(len(df))),
                mode='lines',
                name='趋势',
                line=dict(color=self.color_palette['warning'], width=1, dash='dash')
            ))
        
        fig.update_layout(
            title=title,
            template=self.template,
            hovermode='x unified',
            xaxis_title=x_col,
            yaxis_title=y_col,
            showlegend=True
        )
        
        return fig
    
    def create_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str,
                        title: str = '', horizontal: bool = False) -> go.Figure:
        """创建柱状图"""
        if horizontal:
            fig = go.Figure(go.Bar(
                y=df[x_col],
                x=df[y_col],
                orientation='h',
                marker_color=self.color_palette['primary']
            ))
            fig.update_layout(
                title=title,
                template=self.template,
                yaxis_title=x_col,
                xaxis_title=y_col
            )
        else:
            fig = go.Figure(go.Bar(
                x=df[x_col],
                y=df[y_col],
                marker_color=self.color_palette['primary']
            ))
            fig.update_layout(
                title=title,
                template=self.template,
                xaxis_title=x_col,
                yaxis_title=y_col
            )
        
        return fig
    
    def create_pie_chart(self, df: pd.DataFrame, names_col: str, values_col: str,
                        title: str = '') -> go.Figure:
        """创建饼图"""
        fig = go.Figure(data=[go.Pie(
            labels=df[names_col],
            values=df[values_col],
            hole=0.3,
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            title=title,
            template=self.template,
            showlegend=True
        )
        
        return fig
    
    def create_heatmap(self, df: pd.DataFrame, x_col: str, y_col: str, 
                       value_col: str, title: str = '') -> go.Figure:
        """创建热力图"""
        pivot_df = df.pivot_table(values=value_col, index=y_col, 
                                  columns=x_col, aggfunc='mean')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='RdYlGn_r',
            colorbar=dict(title=value_col)
        ))
        
        fig.update_layout(
            title=title,
            template=self.template,
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        
        return fig
    
    def create_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str,
                           color_col: Optional[str] = None, title: str = '') -> go.Figure:
        """创建散点图"""
        if color_col:
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col,
                           title=title, template=self.template)
        else:
            fig = go.Figure(data=go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='markers',
                marker=dict(
                    color=self.color_palette['primary'],
                    size=10,
                    opacity=0.6
                )
            ))
            fig.update_layout(
                title=title,
                template=self.template,
                xaxis_title=x_col,
                yaxis_title=y_col
            )
        
        return fig
    
    def create_multi_line_chart(self, df: pd.DataFrame, x_col: str, 
                                y_cols: List[str], title: str = '') -> go.Figure:
        """创建多线折线图"""
        fig = go.Figure()
        
        colors = [self.color_palette['primary'], self.color_palette['success'],
                 self.color_palette['warning'], self.color_palette['danger']]
        
        for i, y_col in enumerate(y_cols):
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='lines+markers',
                name=y_col,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title=title,
            template=self.template,
            hovermode='x unified',
            xaxis_title=x_col,
            yaxis_title='值',
            showlegend=True
        )
        
        return fig
    
    def create_gauge_chart(self, value: float, title: str, 
                          min_val: float = 0, max_val: float = 100,
                          thresholds: Optional[Dict] = None) -> go.Figure:
        """创建仪表盘图"""
        if thresholds is None:
            thresholds = {
                'good': {'min': 0, 'max': max_val * 0.6},
                'warning': {'min': max_val * 0.6, 'max': max_val * 0.8},
                'danger': {'min': max_val * 0.8, 'max': max_val}
            }
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title={'text': title},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [min_val, max_val]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [thresholds['good']['min'], thresholds['good']['max']], 
                     'color': self.color_palette['success']},
                    {'range': [thresholds['warning']['min'], thresholds['warning']['max']], 
                     'color': self.color_palette['warning']},
                    {'range': [thresholds['danger']['min'], thresholds['danger']['max']], 
                     'color': self.color_palette['danger']}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_val * 0.9
                }
            }
        ))
        
        fig.update_layout(template=self.template)
        
        return fig
    
    def create_radar_chart(self, categories: List[str], values: List[float],
                          title: str = '') -> go.Figure:
        """创建雷达图"""
        fig = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],  # 闭合
            theta=categories + [categories[0]],
            fill='toself',
            name=title,
            line_color=self.color_palette['primary']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) * 1.2]
                )),
            showlegend=True,
            title=title,
            template=self.template
        )
        
        return fig
    
    def create_funnel_chart(self, df: pd.DataFrame, stage_col: str, 
                           value_col: str, title: str = '') -> go.Figure:
        """创建漏斗图"""
        fig = go.Figure(go.Funnel(
            y=df[stage_col],
            x=df[value_col],
            textposition="inside",
            textinfo="value+percent initial",
            marker=dict(
                color=[self.color_palette['primary'], self.color_palette['success'],
                      self.color_palette['warning'], self.color_palette['danger']]
            )
        ))
        
        fig.update_layout(
            title=title,
            template=self.template
        )
        
        return fig
    
    def create_treemap(self, df: pd.DataFrame, path_cols: List[str], 
                      value_col: str, title: str = '') -> go.Figure:
        """创建树状图"""
        fig = px.treemap(
            df,
            path=path_cols,
            values=value_col,
            title=title,
            color=value_col,
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(template=self.template)
        
        return fig
    
    def create_sunburst(self, df: pd.DataFrame, path_cols: List[str], 
                       value_col: str, title: str = '') -> go.Figure:
        """创建旭日图"""
        fig = px.sunburst(
            df,
            path=path_cols,
            values=value_col,
            title=title,
            color=value_col,
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(template=self.template)
        
        return fig


# 使用示例
if __name__ == "__main__":
    # 创建示例数据
    import pandas as pd
    from datetime import datetime, timedelta
    
    # 时间序列数据
    dates = pd.date_range(start='2026-01-01', periods=30, freq='D')
    values = np.random.randn(30).cumsum() + 100
    
    df_time = pd.DataFrame({
        '日期': dates,
        '客运量': values * 100
    })
    
    # 创建图表
    chart_gen = ChartGenerator()
    
    # 折线图
    fig_line = chart_gen.create_line_chart(df_time, '日期', '客运量', '近30日客运量趋势')
    fig_line.show()
    
    # 仪表盘
    fig_gauge = chart_gen.create_gauge_chart(87.5, '出车率', max_val=100)
    fig_gauge.show()
