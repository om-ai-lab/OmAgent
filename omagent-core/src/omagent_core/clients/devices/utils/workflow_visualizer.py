import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches
matplotlib.use('Agg')  # Non-interactive backend for headless servers
import io
import base64
from PIL import Image
import json
import re
import math
import hashlib

def visualize_workflow_graph(workflow_json):
    """
    Create a visualization of a workflow defined by workflow_json using networkx.
    
    Args:
        workflow_json: A dictionary containing the workflow definition
        
    Returns:
        PIL Image object with the graph visualization
    """
    # Convert from string to dict if necessary
    if isinstance(workflow_json, str):
        workflow_json = json.loads(workflow_json)
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Collect subtasks for DO_WHILE nodes
    do_while_subtasks = {}
    switch_subtasks = {}  # New collection for SWITCH decision cases
    subtask_parents = {}
    
    # First pass to add all nodes
    for task in workflow_json["tasks"]:
        task_ref_name = task["taskReferenceName"]
        task_name = task["name"]
        task_type = task["type"]
        
        # Store task details as node attributes
        G.add_node(task_ref_name, label=f"{task_name}\n({task_type})", task_type=task_type, level=0)
        
        # Add subtasks for DO_WHILE tasks
        if task_type == "DO_WHILE" and "loopOver" in task:
            subtasks = []
            for subtask in task["loopOver"]:
                subtask_ref = subtask["taskReferenceName"]
                full_ref = f"{task_ref_name}_{subtask_ref}"
                subtasks.append(full_ref)
                subtask_parents[full_ref] = task_ref_name
                
                # Add the subtask node, preserving its original task type
                G.add_node(
                    full_ref, 
                    label=f"{subtask['name']}\n({subtask['type']})",
                    task_type=subtask['type'],  # Keep the original task type (SWITCH, SIMPLE, etc.)
                    is_subtask=True,
                    parent=task_ref_name,
                    level=1
                )
            
            do_while_subtasks[task_ref_name] = subtasks
            
        # Add decision case tasks for SWITCH tasks
        elif task_type == "SWITCH" and "decisionCases" in task:
            switch_cases = {}
            
            # Process each decision case
            for case_value, case_tasks in task["decisionCases"].items():
                case_subtasks = []
                
                for i, subtask in enumerate(case_tasks):
                    subtask_ref = subtask["taskReferenceName"]
                    # Use a format that includes the case value to avoid name collisions
                    full_ref = f"{task_ref_name}_{case_value}_{subtask_ref}"
                    case_subtasks.append(full_ref)
                    subtask_parents[full_ref] = task_ref_name
                    
                    # Add the case task node
                    G.add_node(
                        full_ref,
                        label=f"{subtask['name']}\n({subtask['type']})",
                        task_type=subtask['type'],
                        is_switch_case=True,  # Mark as switch case
                        case_value=case_value,  # Store the case value
                        parent=task_ref_name,
                        level=1
                    )
                
                if case_subtasks:
                    switch_cases[case_value] = case_subtasks
            
            # Also handle default case if it exists
            if "defaultCase" in task and task["defaultCase"]:
                default_tasks = []
                
                for i, subtask in enumerate(task["defaultCase"]):
                    subtask_ref = subtask["taskReferenceName"]
                    full_ref = f"{task_ref_name}_default_{subtask_ref}"
                    default_tasks.append(full_ref)
                    subtask_parents[full_ref] = task_ref_name
                    
                    G.add_node(
                        full_ref,
                        label=f"{subtask['name']}\n({subtask['type']})",
                        task_type=subtask['type'],
                        is_switch_case=True,
                        case_value="default",
                        parent=task_ref_name,
                        level=1
                    )
                
                if default_tasks:
                    switch_cases["default"] = default_tasks
            
            if switch_cases:
                switch_subtasks[task_ref_name] = switch_cases
    
    # Add edges between main tasks
    main_task_refs = [t["taskReferenceName"] for t in workflow_json["tasks"]]
    task_to_index = {task: i for i, task in enumerate(main_task_refs)}
    
    # Connect main tasks but skip DO_WHILE tasks with subtasks
    for i in range(len(main_task_refs) - 1):
        current_task = main_task_refs[i]
        next_task = main_task_refs[i+1]
        
        current_type = next(t["type"] for t in workflow_json["tasks"] if t["taskReferenceName"] == current_task)
        
        # If current task is DO_WHILE with subtasks, we'll handle its connections differently
        if current_type == "DO_WHILE" and current_task in do_while_subtasks and do_while_subtasks[current_task]:
            # Will be handled in subtask connections
            pass
        else:
            G.add_edge(current_task, next_task, main_flow=True)
    
    # Add edges for subtasks and connect them to the main flow
    for task_ref, subtasks in do_while_subtasks.items():
        if not subtasks:
            continue
            
        # Connect the DO_WHILE task to its first subtask
        G.add_edge(task_ref, subtasks[0], entry_flow=True)
        
        # Connect subtasks in sequence
        for i in range(len(subtasks) - 1):
            G.add_edge(subtasks[i], subtasks[i+1], sub_flow=True)
        
        # Find the next task in the main flow
        task_index = task_to_index[task_ref]
        if task_index < len(main_task_refs) - 1:
            next_main_task = main_task_refs[task_index + 1]
            
            # Connect the last subtask to the next main task
            G.add_edge(subtasks[-1], next_main_task, exit_flow=True)
        
        # Add loop back edge from last subtask to first subtask
        G.add_edge(subtasks[-1], subtasks[0], style="dashed", loop_back=True)
    
    # Add edges for SWITCH decision cases
    for switch_ref, switch_cases in switch_subtasks.items():
        # Find the next task in the main flow
        task_index = task_to_index[switch_ref]
        next_main_task = None
        if task_index < len(main_task_refs) - 1:
            next_main_task = main_task_refs[task_index + 1]
        
        # Connect each case's tasks
        for case_value, case_tasks in switch_cases.items():
            if not case_tasks:
                continue
                
            # Connect switch to first task in this case
            G.add_edge(switch_ref, case_tasks[0], case_flow=True, case_value=case_value)
            
            # Connect tasks within this case in sequence
            for i in range(len(case_tasks) - 1):
                G.add_edge(case_tasks[i], case_tasks[i+1], sub_flow=True)
            
            # Connect the last task to the next main task
            if next_main_task and len(case_tasks) > 0:
                # Use a special edge type for exit from case flow
                G.add_edge(case_tasks[-1], next_main_task, case_exit_flow=True, case_value=case_value)
    
    # Create input dependency edges based on parameter references
    for task in workflow_json["tasks"]:
        if "inputParameters" in task:
            task_ref_name = task["taskReferenceName"]
            for param_name, param_value in task["inputParameters"].items():
                if isinstance(param_value, str):
                    # Look for pattern like ${another_task.output.something}
                    references = re.findall(r'\${([^.}]+)', param_value)
                    for ref_task_name in references:
                        # Add edge if the referenced task exists in our graph
                        if ref_task_name in G:
                            G.add_edge(ref_task_name, task_ref_name, dependency=True)
    
    # Set up the visualization with a dark theme suitable for OmAgent
    plt.figure(figsize=(18, 14))  # Larger figure
    plt.rcParams.update({
        'text.color': 'white',
        'axes.labelcolor': 'white',
        'axes.edgecolor': 'white',
        'xtick.color': 'white',
        'ytick.color': 'white',
        'figure.facecolor': '#1e1f24',
        'axes.facecolor': '#1e1f24'
    })
    
    # Create a custom hierarchical layout with integrated DO_WHILE subtasks
    pos = {}
    
    # Calculate the levels - we need to find out where to insert subtasks
    task_level = {}
    level_count = 0
    
    for i, task_ref in enumerate(main_task_refs):
        task_type = next(t["type"] for t in workflow_json["tasks"] if t["taskReferenceName"] == task_ref)
        
        # Assign current level
        task_level[task_ref] = level_count
        level_count += 1
        
        # If it's a DO_WHILE with subtasks, insert those at the next levels
        if task_type == "DO_WHILE" and task_ref in do_while_subtasks and do_while_subtasks[task_ref]:
            for subtask in do_while_subtasks[task_ref]:
                task_level[subtask] = level_count
                level_count += 1
        
        # If it's a SWITCH with decision cases, insert case tasks at the next levels
        elif task_type == "SWITCH" and task_ref in switch_subtasks:
            # Group tasks by their case values for better organization
            all_case_tasks = []
            for case_value, case_tasks in switch_subtasks[task_ref].items():
                for task in case_tasks:
                    all_case_tasks.append(task)
                    task_level[task] = level_count
                level_count += 1  # Increment level after each case group
    
    # Get total number of levels
    total_levels = level_count
    
    # Position nodes vertically based on their level with special handling for SWITCH cases
    vertical_spacing = 4.5  # Increased spacing between levels
    for node in G.nodes():
        if node in task_level:
            y_pos = (total_levels - task_level[node] - 1) * vertical_spacing
            
            # Special handling for switch cases - arrange them horizontally
            is_switch_case = G.nodes[node].get("is_switch_case", False)
            parent = G.nodes[node].get("parent", "")
            
            if is_switch_case:
                # Switch cases are positioned slightly to the right of the center
                x_pos = 4  # Position closer to center for better visibility
            else:
                # Main tasks and DO_WHILE subtasks stay in the center column
                x_pos = 0
                
            pos[node] = (x_pos, y_pos)
    
    # Position SWITCH case nodes in columns by case value - use a more compact arrangement
    for switch_ref, switch_cases in switch_subtasks.items():
        if switch_ref not in pos:
            continue
            
        switch_y = pos[switch_ref][1]
        case_count = len(switch_cases)
        
        # Calculate positions for different cases
        if case_count > 0:
            # Arrange cases in a horizontal pattern
            for i, (case_value, case_tasks) in enumerate(switch_cases.items()):
                if not case_tasks:
                    continue
                
                # Calculate horizontal position for this case
                # Even cases go to the right, odd cases go to the left
                if i % 2 == 0:
                    # Right side
                    case_x = 6 + (i // 2) * 3
                else:
                    # Left side
                    case_x = -6 - (i // 2) * 3
                
                # Position all tasks in this case
                for j, task in enumerate(case_tasks):
                    task_y = switch_y - (j + 1) * 2.5  # Position below the switch task
                    pos[task] = (case_x, task_y)
                    
                    # Update task level to ensure proper ordering in the visualization
                    task_level[task] = task_level[switch_ref] + j + 1
    
    # For a cleaner look, make sure SWITCH tasks are properly aligned with their case tasks
    for node in G.nodes():
        if G.nodes[node].get("task_type", "") == "SWITCH" and node in switch_subtasks:
            # Get all case tasks
            all_case_tasks = []
            for case_tasks in switch_subtasks[node].values():
                all_case_tasks.extend(case_tasks)
                
            # If there are case tasks, adjust position
            if all_case_tasks and all(task in pos for task in all_case_tasks):
                # Set the SWITCH node position to the center of its case tasks
                case_x_positions = [pos[task][0] for task in all_case_tasks]
                if case_x_positions:
                    switch_x = sum(case_x_positions) / len(case_x_positions)
                    pos[node] = (switch_x, pos[node][1])
    
    # Adjust positions to prevent node overlap
    # Keep track of how many nodes are at each level
    level_positions = {}
    for node, position in pos.items():
        level = task_level.get(node, 0)
        if level not in level_positions:
            level_positions[level] = []
        level_positions[level].append(node)
    
    # Group SWITCH cases by their parent and case value for better arrangement
    switch_case_groups = {}
    for node in G.nodes():
        if G.nodes[node].get("is_switch_case", False):
            parent = G.nodes[node].get("parent", "")
            case_value = G.nodes[node].get("case_value", "")
            key = f"{parent}_{case_value}"
            
            if key not in switch_case_groups:
                switch_case_groups[key] = []
            
            switch_case_groups[key].append(node)
    
    # Spread nodes horizontally at levels with multiple nodes
    horizontal_spacing = 6.0  # Increased horizontal spacing
    for level, nodes in level_positions.items():
        # Skip levels with only one node
        if len(nodes) <= 1:
            continue
            
        # Filter out switch case nodes (they'll be handled separately)
        regular_nodes = [n for n in nodes if not G.nodes[n].get("is_switch_case", False)]
        
        if regular_nodes:
            # Handle regular nodes
            total_width = (len(regular_nodes) - 1) * horizontal_spacing
            start_x = -total_width / 2
            
            # Sort nodes to ensure consistent ordering
            regular_nodes.sort(key=lambda n: n if not G.nodes[n].get("is_subtask", False) else G.nodes[n].get("parent", "") + n)
            
            for i, node in enumerate(regular_nodes):
                x_pos = start_x + i * horizontal_spacing
                y_pos = pos[node][1]
                pos[node] = (x_pos, y_pos)
    
    # Position SWITCH case nodes in columns by case value
    for key, case_nodes in switch_case_groups.items():
        if not case_nodes:
            continue
            
        parent, case_value = key.rsplit("_", 1)
        
        # Calculate horizontal offset for this case (to separate different cases)
        case_hash = int(hashlib.md5(case_value.encode()).hexdigest(), 16) % 5
        case_x_offset = (case_hash - 2) * 5  # Range from -10 to +10
        
        # For each node in this case
        for i, node in enumerate(case_nodes):
            if node in pos:
                x_pos = 8 + case_x_offset
                y_pos = pos[node][1]
                pos[node] = (x_pos, y_pos)
    
    # Create rectangular node shapes with distinct sizes for different types
    node_shapes = {}
    for node in G.nodes():
        task_type = G.nodes[node].get("task_type", "SIMPLE")
        is_subtask = G.nodes[node].get("is_subtask", False)
        is_switch_case = G.nodes[node].get("is_switch_case", False)
        case_value = G.nodes[node].get("case_value", "")
        
        if task_type == "DO_WHILE":
            color = "#2196f3"  # Blue for DO_WHILE
            width = 4.5  # Increased width
            height = 2.2  # Increased height
            alpha = 0.9
            ec = 'white'
            lw = 2
            zorder = 3
        elif task_type == "SWITCH":
            if is_subtask:
                # Switch inside a DO_WHILE - blend of SWITCH color and subtask style
                color = "#ffc107"  # Amber/yellow for SWITCH
                width = 4.0  # Slightly smaller as it's a subtask
                height = 2.0
                alpha = 0.9
                ec = 'white'
                lw = 1.5
                zorder = 2
            else:
                # Regular SWITCH task
                color = "#ffc107"  # Amber/yellow for SWITCH
                width = 4.5
                height = 2.2
                alpha = 0.9
                ec = 'white'
                lw = 2
                zorder = 3
        elif is_switch_case:
            # Tasks that are part of a SWITCH case - use a variant color based on the case
            # Create a predictable color for each case value
            
            # Generate a hash from the case value for color consistency
            case_hash = int(hashlib.md5(case_value.encode()).hexdigest(), 16)
            
            # Preset colors for common cases
            if case_value == "default":
                color = "#e57373"  # Light red for default case
            elif case_value == "pdf":
                color = "#4db6ac"  # Teal for PDF
            elif case_value == "web":
                color = "#7986cb"  # Indigo for web
            else:
                # Use the hash to select one of several preset colors
                colors = ["#4db6ac", "#7986cb", "#9575cd", "#4fc3f7", "#81c784", "#fff176", "#ffb74d"]
                color = colors[case_hash % len(colors)]
                
            width = 4.0
            height = 2.0
            alpha = 0.9
            ec = 'white'
            lw = 1.5
            zorder = 2
        elif is_subtask:
            color = "#4caf50"  # Green for subtasks
            width = 4.0  # Increased width
            height = 2.0  # Increased height
            alpha = 0.9
            ec = 'white'
            lw = 1.5
            zorder = 2
        else:
            color = "#9c27b0"  # Purple for regular tasks
            width = 4.5  # Increased width
            height = 2.2  # Increased height
            alpha = 0.9
            ec = 'white'
            lw = 2
            zorder = 3
            
        node_shapes[node] = {
            'width': width,
            'height': height,
            'color': color,
            'alpha': alpha,
            'ec': ec,
            'lw': lw,
            'zorder': zorder
        }
    
    # Draw nodes as rectangles
    for node, shape in node_shapes.items():
        if node not in pos:
            continue  # Skip if no position
            
        rect = mpatches.Rectangle(
            (pos[node][0] - shape['width']/2, pos[node][1] - shape['height']/2),
            shape['width'], shape['height'],
            color=shape['color'], 
            alpha=shape['alpha'], 
            ec=shape['ec'], 
            lw=shape['lw'], 
            zorder=shape['zorder']
        )
        plt.gca().add_patch(rect)
    
    # Draw labels with white text
    for node in pos:
        plt.text(
            pos[node][0], pos[node][1],
            G.nodes[node]['label'],
            color='white',
            fontsize=12,  # Increased font size
            fontweight='bold',
            ha='center',
            va='center',
            zorder=10
        )
    
    # Draw different types of edges
    for u, v, data in G.edges(data=True):
        if u not in pos or v not in pos:
            continue  # Skip if positions are not defined
            
        is_main_flow = data.get('main_flow', False)
        is_sub_flow = data.get('sub_flow', False)
        is_loop_back = data.get('loop_back', False)
        is_dependency = data.get('dependency', False)
        is_entry_flow = data.get('entry_flow', False)
        is_exit_flow = data.get('exit_flow', False)
        is_case_flow = data.get('case_flow', False)
        is_case_exit_flow = data.get('case_exit_flow', False)
        case_value = data.get('case_value', "")
        
        # Different edge styles
        if is_loop_back:
            # Loop back edges (dashed red)
            # Calculate a better curve for the loop back
            # Determine direction (up or down) based on node positions
            y_diff = pos[v][1] - pos[u][1]
            curve_direction = 1 if y_diff > 0 else -1  # Curve right if going up, left if going down
            
            # Determine the outward extension of the curve
            curve_extent = 6.0  # Increased curve size
            
            control_pts = [
                (pos[u][0] + curve_direction * 2, pos[u][1]),  # Move out from source
                (pos[u][0] + curve_direction * curve_extent, (pos[u][1] + pos[v][1]) / 2),  # Bulge outwards
                (pos[v][0] + curve_direction * 2, pos[v][1])   # Move in to target
            ]
            
            # Create curved path for the loop back
            path = mpatches.Path(
                [(pos[u][0], pos[u][1])] + control_pts + [(pos[v][0], pos[v][1])],
                [mpatches.Path.MOVETO] + [mpatches.Path.CURVE4] * 3 + [mpatches.Path.LINETO]
            )
            
            # Create the arrow patch
            arrow_style = mpatches.ArrowStyle('->', head_length=12, head_width=9)
            arrow_patch = mpatches.FancyArrowPatch(
                path=path,
                arrowstyle=arrow_style,
                color='#f44336',  # Red
                linestyle='dashed',
                linewidth=2.0,  # Increased linewidth
                zorder=1
            )
            plt.gca().add_patch(arrow_patch)
        elif is_case_flow:
            # SWITCH case flow - with label showing the case value
            # Determine the midpoint for the label
            mid_x = (pos[u][0] + pos[v][0]) / 2
            mid_y = (pos[u][1] + pos[v][1]) / 2
            
            # Pick color based on case value
            if case_value == "default":
                color = "#e57373"  # Light red for default case
            elif case_value == "pdf":
                color = "#4db6ac"  # Teal for PDF
            elif case_value == "web":
                color = "#7986cb"  # Indigo for web
            else:
                # Generate color from hash
                case_hash = int(hashlib.md5(case_value.encode()).hexdigest(), 16)
                colors = ["#4db6ac", "#7986cb", "#9575cd", "#4fc3f7", "#81c784", "#fff176", "#ffb74d"]
                color = colors[case_hash % len(colors)]
            
            # Calculate the curve of the arrow based on position relationship
            direction = 1 if pos[v][0] > pos[u][0] else -1
            rad = 0.3 * direction  # Curve right if target is to the right, left if to the left
            
            # Draw the arrow with appropriate curve
            plt.annotate(
                '', xy=pos[v], xytext=pos[u],
                arrowprops=dict(
                    arrowstyle='->', 
                    color=color,
                    lw=2.0,
                    shrinkA=25,
                    shrinkB=25,
                    connectionstyle=f'arc3,rad={rad}'
                ),
                zorder=1
            )
            
            # Add a label with the case value in a more visible position
            plt.text(
                mid_x, mid_y,
                f"case: {case_value}",
                color=color,
                fontsize=10,  # Slightly larger for better visibility
                fontweight='bold',
                ha='center',
                va='center',
                bbox=dict(facecolor='#1e1f24', alpha=0.8, edgecolor=color, boxstyle='round,pad=0.3'),
                zorder=2
            )
        elif is_dependency:
            # Dependency edges (curved orange)
            plt.annotate(
                '', xy=pos[v], xytext=pos[u],
                arrowprops=dict(
                    arrowstyle='->', 
                    color='#ff9800',  # Orange
                    lw=1.8,  # Increased linewidth
                    shrinkA=25,
                    shrinkB=25,
                    connectionstyle='arc3,rad=0.3'
                ),
                zorder=1
            )
        elif is_case_exit_flow:
            # Draw a connecting line from the end of a case back to the main flow
            # Use same color scheme as the case flows for consistency
            if case_value == "default":
                color = "#e57373"  # Light red for default case
            elif case_value == "pdf":
                color = "#4db6ac"  # Teal for PDF
            elif case_value == "web":
                color = "#7986cb"  # Indigo for web
            else:
                # Generate color from hash
                case_hash = int(hashlib.md5(case_value.encode()).hexdigest(), 16)
                colors = ["#4db6ac", "#7986cb", "#9575cd", "#4fc3f7", "#81c784", "#fff176", "#ffb74d"]
                color = colors[case_hash % len(colors)]
            
            # Calculate curve for connecting back to main flow
            direction = 1 if pos[v][0] > pos[u][0] else -1
            rad = 0.4 * direction  # Stronger curve for the return path
            
            # Draw the return arrow
            plt.annotate(
                '', xy=pos[v], xytext=pos[u],
                arrowprops=dict(
                    arrowstyle='->', 
                    color=color,
                    lw=1.8,
                    shrinkA=25,
                    shrinkB=25,
                    connectionstyle=f'arc3,rad={rad}'
                ),
                zorder=1
            )
        elif is_main_flow or is_entry_flow or is_exit_flow or is_sub_flow:
            # All flow connections (white arrows)
            shrink_a = shape_width = node_shapes[u]['width'] / 2 if u in node_shapes else 20
            shrink_b = shape_width = node_shapes[v]['width'] / 2 if v in node_shapes else 20
            
            plt.annotate(
                '', xy=pos[v], xytext=pos[u],
                arrowprops=dict(
                    arrowstyle='->', 
                    color='white',
                    lw=2.2,  # Increased linewidth
                    shrinkA=shrink_a + 5,
                    shrinkB=shrink_b + 5
                ),
                zorder=1
            )
        else:
            # Default edge style
            plt.annotate(
                '', xy=pos[v], xytext=pos[u],
                arrowprops=dict(
                    arrowstyle='->', 
                    color='white',
                    lw=1.8,  # Increased linewidth
                    shrinkA=25,
                    shrinkB=25
                ),
                zorder=1
            )
    
    # Group subtasks of DO_WHILE with background rectangle
    for task_ref, subtasks in do_while_subtasks.items():
        if not subtasks:
            continue
            
        # Find the bounds of the subtasks
        xs = [pos[s][0] for s in subtasks if s in pos]
        ys = [pos[s][1] for s in subtasks if s in pos]
        
        if not xs or not ys:
            continue
        
        # Also include the parent DO_WHILE node in the grouping
        if task_ref in pos:
            xs.append(pos[task_ref][0])
            ys.append(pos[task_ref][1])
            
        # Calculate the rectangle dimensions with padding
        padding = 2.5  # Increased padding
        min_x = min(xs) - padding - 2.0
        max_x = max(xs) + padding + 2.0
        min_y = min(ys) - padding - 1.5
        max_y = max(ys) + padding + 1.5
        
        # Draw a background rectangle to group the subtasks
        group_rect = mpatches.Rectangle(
            (min_x, min_y),
            max_x - min_x, max_y - min_y,
            color='#263238',  # Dark blue-gray background
            alpha=0.4,  # Slightly reduced opacity
            ec='#78909c',  # Lighter border
            lw=1.5,
            zorder=0  # Behind nodes
        )
        plt.gca().add_patch(group_rect)
        
        # Add a label for the group in a better position
        label_y = max_y - 0.8
        plt.text(
            (min_x + max_x) / 2, label_y,
            f"{G.nodes[task_ref]['label']} subtasks",
            color='#b0bec5',  # Light gray text
            fontsize=10,  # Increased font size
            ha='center',
            va='center',
            bbox=dict(facecolor='#1e1f24', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.3'),
            zorder=0
        )
    
    # Group SWITCH case tasks by their parent and case value
    for switch_ref, switch_cases in switch_subtasks.items():
        if not G.nodes[switch_ref]['task_type'] == "SWITCH":
            continue
            
        for case_value, case_tasks in switch_cases.items():
            if not case_tasks:
                continue
                
            # Find the bounds of this case's tasks
            xs = [pos[task][0] for task in case_tasks if task in pos]
            ys = [pos[task][1] for task in case_tasks if task in pos]
            
            if not xs or not ys:
                continue
                
            # Calculate the rectangle dimensions with padding
            padding = 2.0
            min_x = min(xs) - padding - 1.5
            max_x = max(xs) + padding + 1.5
            min_y = min(ys) - padding - 1.0
            max_y = max(ys) + padding + 1.0
            
            # Pick color based on case value
            if case_value == "default":
                color = "#e57373"  # Light red for default case
                bg_color = "#6d2b2b"  # Darker version for background
            elif case_value == "pdf":
                color = "#4db6ac"  # Teal for PDF
                bg_color = "#1e4d48"  # Darker version for background
            elif case_value == "web":
                color = "#7986cb"  # Indigo for web
                bg_color = "#303b57"  # Darker version for background
            else:
                # Generate color from hash
                case_hash = int(hashlib.md5(case_value.encode()).hexdigest(), 16)
                colors = ["#4db6ac", "#7986cb", "#9575cd", "#4fc3f7", "#81c784", "#fff176", "#ffb74d"]
                bg_colors = ["#1e4d48", "#303b57", "#43355d", "#1e5b73", "#356339", "#706930", "#6d4c20"]
                color_idx = case_hash % len(colors)
                color = colors[color_idx]
                bg_color = bg_colors[color_idx]
            
            # Draw a background rectangle to group the case tasks
            group_rect = mpatches.Rectangle(
                (min_x, min_y),
                max_x - min_x, max_y - min_y,
                color=bg_color,  # Background color matching the case
                alpha=0.4,
                ec=color,  # Border matching the case color
                lw=1.5,
                zorder=0  # Behind nodes
            )
            plt.gca().add_patch(group_rect)
            
            # Add a label for the case
            plt.text(
                (min_x + max_x) / 2, max_y - 0.7,
                f"Case: {case_value}",
                color=color,
                fontsize=9,
                ha='center',
                va='center',
                bbox=dict(facecolor='#1e1f24', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'),
                zorder=0
            )
    
    # Add workflow title
    plt.title(f"Workflow: {workflow_json['name']}", fontsize=18, color='white', pad=20)  # Larger title, more padding
    plt.axis('off')
    
    # Add legend with larger elements
    legend_elements = [
        mpatches.Patch(color='#9c27b0', label='Regular task (SIMPLE)'),
        mpatches.Patch(color='#2196f3', label='DO_WHILE loop'),
        mpatches.Patch(color='#4caf50', label='Subtask (within loop)'),
        mpatches.Patch(color='#ffc107', label='SWITCH task'),
        mpatches.Patch(color='#4db6ac', label='SWITCH case: pdf'),
        mpatches.Patch(color='#7986cb', label='SWITCH case: web'),
        mpatches.Patch(color='#e57373', label='SWITCH case: default'),
        plt.Line2D([0], [0], color='white', lw=2.5, label='Sequence flow'),
        plt.Line2D([0], [0], color='#4db6ac', lw=2.0, label='Case entry/exit'),
        plt.Line2D([0], [0], color='#f44336', lw=2.5, linestyle='dashed', label='Loop back'),
        plt.Line2D([0], [0], color='#ff9800', lw=2.0, label='Dependency')
    ]
    plt.legend(handles=legend_elements, loc='upper right', frameon=True, 
               facecolor='#2d2e33', edgecolor='white', fontsize=12)
    
    # Adjust plot limits to ensure all nodes are visible with more padding
    if pos:
        all_xs = [p[0] for p in pos.values()]
        all_ys = [p[1] for p in pos.values()]
        x_margin = 10  # Increased margin
        y_margin = 4   # Increased margin
        plt.xlim(min(all_xs) - x_margin, max(all_xs) + x_margin)
        plt.ylim(min(all_ys) - y_margin, max(all_ys) + y_margin)
    
    # Convert plot to PIL Image
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='#1e1f24')
    buf.seek(0)
    img = Image.open(buf)
    plt.close()
    
    return img 