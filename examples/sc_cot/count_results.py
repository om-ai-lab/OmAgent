import json
import os
from datetime import datetime, timedelta
import time
from flask import Flask, render_template_string
import threading
from collections import defaultdict
import glob

app = Flask(__name__)

# 存储历史数据，每个元素是 (timestamp, counts, file_names) 的元组
history_data = []

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Results Count Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .trend-up { color: green; }
        .trend-down { color: red; }
        .trend-stable { color: gray; }
        .chart { margin: 20px 0; }
        .speed { font-weight: bold; color: blue; }
        .stagnation { font-weight: bold; color: purple; }
        .status-active { background-color: #e8f5e9; }
        .status-stopped { background-color: #ffebee; }
        .status-slowing { background-color: #fff3e0; }
        .status-unknown { background-color: #f5f5f5; }
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <meta http-equiv="refresh" content="10">
</head>
<body>
    <h1>Results Count Monitor</h1>
    <p>Last updated: {{ last_update }}</p>
    
    <h2>Current Counts</h2>
    <table>
        <tr>
            <th>File Name</th>
            <th>Count</th>
            <th>Trend</th>
            <th>Speed (per min)</th>
            <th>Status</th>
            <th>No Change For</th>
        </tr>
        {% for item in current_data %}
        <tr class="status-{{ item.status }}">
            <td>{{ item.file_name }}</td>
            <td>{{ item.count }}</td>
            <td class="{{ item.trend_class }}">{{ item.trend }}</td>
            <td class="speed">{{ item.speed }}</td>
            <td>{{ item.status }}</td>
            <td class="stagnation">{{ item.stagnation_time if item.stagnation_time else 'N/A' }}</td>
        </tr>
        {% endfor %}
        <tr class="status-{{ total_status }}">
            <th>Total</th>
            <th>{{ total_count }}</th>
            <th class="{{ total_trend_class }}">{{ total_trend }}</th>
            <th class="speed">{{ total_speed }}</th>
            <th>{{ total_status }}</th>
            <th class="stagnation">{{ total_stagnation_time if total_stagnation_time else 'N/A' }}</th>
        </tr>
    </table>

    <h2>Analysis</h2>
    <div id="trendChart"></div>
    
    <script>
        var data = {{ chart_data | safe }};
        var layout = {
            title: 'Count Trends Over Time',
            xaxis: { title: 'Time' },
            yaxis: { title: 'Count' }
        };
        Plotly.newPlot('trendChart', data, layout);
    </script>
</body>
</html>
"""

def get_all_jsonl_files():
    """获取Output目录下所有的jsonl文件"""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Output')
    return sorted(glob.glob(os.path.join(output_dir, '*.jsonl')))  # 排序以保持顺序一致

def count_elements(file_path):
    try:
        count = 0
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():  # 跳过空行
                    count += 1
        return count
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return 0
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return 0

def analyze_trends(current_data, history_data):
    if not history_data:
        return [(0, "→") for _ in range(len(current_data))]
    
    last_data = history_data[-1][1]  # 获取最后一个数据点的counts
    trends = []
    
    for curr, prev in zip(current_data, last_data):
        if curr > prev:
            trends.append((curr - prev, "↑"))
        elif curr < prev:
            trends.append((prev - curr, "↓"))
        else:
            trends.append((0, "→"))
    
    return trends

def collect_data():
    files = get_all_jsonl_files()
    file_names = [os.path.basename(f) for f in files]
    counts = []
    
    for file_path in files:
        count = count_elements(file_path)
        counts.append(count)
    
    timestamp = datetime.now()
    history_data.append((timestamp, counts, file_names))
    
    # 只保留最近3小时的数据（18个数据点）
    if len(history_data) > 18:
        history_data.pop(0)
    
    return counts, timestamp, file_names

def get_file_history(file_name, history_data):
    """获取特定文件的历史数据"""
    file_counts = []
    for _, counts, files in history_data:
        try:
            idx = files.index(file_name)
            file_counts.append(counts[idx])
        except ValueError:
            file_counts.append(0)  # 如果文件在某个时间点不存在，计数为0
    return file_counts

def calculate_stagnation_time(history_data, file_name=None):
    """计算停滞时间（最后一次变化到现在的时间）"""
    if len(history_data) < 2:
        return None
    
    if file_name is not None:
        # 获取特定文件的历史数据
        counts = get_file_history(file_name, history_data)
    else:
        # 获取总数的历史数据
        counts = [sum(counts) for _, counts, _ in history_data]
    
    timestamps = [ts for ts, _, _ in history_data]
    current_time = timestamps[-1]
    
    # 从后向前查找最后一次变化的时间点
    last_change_time = current_time
    last_value = counts[-1]
    
    for i in range(len(counts)-2, -1, -1):
        if counts[i] != last_value:
            last_change_time = timestamps[i+1]
            break
    
    # 计算时间差
    time_diff = (current_time - last_change_time).total_seconds()
    
    # 格式化时间差
    if time_diff < 60:
        return f"{int(time_diff)}s"
    elif time_diff < 3600:
        minutes = int(time_diff / 60)
        seconds = int(time_diff % 60)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(time_diff / 3600)
        minutes = int((time_diff % 3600) / 60)
        return f"{hours}h {minutes}m"

def calculate_speed(current_count, history_data, file_name=None):
    """计算平均速度（每分钟）和累积速度状态"""
    if len(history_data) < 2:
        return 0.0, "unknown", None
    
    # 获取最早和最新的数据点
    oldest_time, _, _ = history_data[0]
    newest_time, _, _ = history_data[-1]
    
    # 计算时间差（分钟）
    time_diff = (newest_time - oldest_time).total_seconds() / 60.0
    if time_diff == 0:
        return 0.0, "unknown", None
    
    # 计算停滞时间
    stagnation_time = calculate_stagnation_time(history_data, file_name)
    
    if file_name is not None:
        # 获取特定文件的历史数据
        counts = get_file_history(file_name, history_data)
        count_diff = counts[-1] - counts[0]
        
        # 检查最近5个数据点的变化
        recent_status = "active"
        if len(counts) >= 5:
            recent_counts = counts[-5:]
            if len(set(recent_counts)) == 1:  # 如果最近5个点都相同
                recent_status = "stopped"
            elif max(recent_counts) == recent_counts[0]:  # 如果最大值在最早的点
                recent_status = "slowing"
    else:
        # 计算总体速度
        total_counts = [sum(counts) for _, counts, _ in history_data]
        count_diff = total_counts[-1] - total_counts[0]
        
        # 检查总体趋势
        recent_status = "active"
        if len(total_counts) >= 5:
            recent_totals = total_counts[-5:]
            if len(set(recent_totals)) == 1:
                recent_status = "stopped"
            elif max(recent_totals) == recent_totals[0]:
                recent_status = "slowing"
    
    speed = round(count_diff / time_diff, 2) if time_diff > 0 else 0.0
    return speed, recent_status, stagnation_time

@app.route('/')
def home():
    current_counts, timestamp, file_names = collect_data()
    trends = analyze_trends(current_counts, [(ts, counts) for ts, counts, _ in history_data[:-1]] if len(history_data) > 1 else [])
    
    # 准备当前数据
    current_data = []
    for i, (file_name, count, (change, trend)) in enumerate(zip(file_names, current_counts, trends)):
        trend_class = {
            "↑": "trend-up",
            "↓": "trend-down",
            "→": "trend-stable"
        }[trend]
        
        # 计算该文件的速度、状态和停滞时间
        speed, status, stagnation_time = calculate_speed(count, history_data, file_name)
        
        current_data.append({
            "file_name": file_name,
            "count": count,
            "trend": f"{trend} ({change if change else '0'})",
            "trend_class": trend_class,
            "speed": f"{speed:+.2f}" if speed != 0 else "0.00",
            "status": status,
            "stagnation_time": stagnation_time
        })
    
    # 计算总计
    total_count = sum(current_counts)
    total_history = [sum(counts) for _, counts, _ in history_data[:-1]] if len(history_data) > 1 else []
    total_trend = "→"
    total_change = 0
    
    if total_history:
        last_total = total_history[-1]
        if total_count > last_total:
            total_trend = f"↑ ({total_count - last_total})"
            total_trend_class = "trend-up"
        elif total_count < last_total:
            total_trend = f"↓ ({last_total - total_count})"
            total_trend_class = "trend-down"
        else:
            total_trend = "→ (0)"
            total_trend_class = "trend-stable"
    else:
        total_trend_class = "trend-stable"
    
    # 计算总体速度、状态和停滞时间
    total_speed, total_status, total_stagnation_time = calculate_speed(total_count, history_data)
    
    # 准备图表数据
    chart_data = []
    timestamps = [ts.strftime('%H:%M:%S') for ts, _, _ in history_data]
    
    for file_name in file_names:
        trace = {
            'x': timestamps,
            'y': get_file_history(file_name, history_data),
            'name': file_name,
            'type': 'scatter'
        }
        chart_data.append(trace)
    
    return render_template_string(
        HTML_TEMPLATE,
        current_data=current_data,
        total_count=total_count,
        total_trend=total_trend,
        total_trend_class=total_trend_class,
        total_speed=f"{total_speed:+.2f}" if total_speed != 0 else "0.00",
        total_status=total_status,
        total_stagnation_time=total_stagnation_time,
        last_update=timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        chart_data=chart_data
    )

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def monitor():
    while True:
        collect_data()
        time.sleep(600)  # 10分钟

if __name__ == "__main__":
    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # 启动Flask服务
    run_flask() 