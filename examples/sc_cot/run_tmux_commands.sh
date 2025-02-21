#!/bin/bash

# 定义要执行的命令
run_command() {
    local session=$1
    local number=$2
    
    echo "处理会话 $session - 步骤 1: 切换目录"
    tmux send-keys -t $session "cd /data23/ljc/project/wang_ze/OmAgent/examples/sc_cot" C-m
    sleep 1
    
    #echo "处理会话 $session - 步骤 2: 激活 conda 环境"
    tmux send-keys -t $session "source /data23/ljc/anaconda3/bin/activate" C-m
    sleep 2
    tmux send-keys -t $session "conda activate py310" C-m
    sleep 2
    
    echo "处理会话 $session - 步骤 3: 终止现有进程"
    tmux send-keys -t $session C-c  # 使用 Ctrl+C 终止
    sleep 2  # 给足够时间让进程终止
    
    echo "处理会话 $session - 步骤 4: 清理屏幕"
    tmux send-keys -t $session "clear" C-m
    sleep 1
    
    echo "处理会话 $session - 步骤 5: 启动新程序"
    tmux send-keys -t $session "python eval_batch_${number}.py" C-m
    sleep 2  # 给程序启动一些时间
}

# 为每个会话执行对应的命令
for i in {2..5}; do
    session="ljc_${i}"
    echo "==============================================="
    echo "开始处理会话 $session"
    echo "==============================================="
    run_command $session $i
    echo "完成处理会话 $session"
    echo ""
    # 在处理下一个会话之前等待一会
    sleep 2
done

echo "所有命令已发送到对应的tmux会话" 
