#!/usr/bin/env python3
"""
Fast Robot Navigation Runner
Demonstrates the simplified and optimized robot workflow with improved speed and efficiency.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.container import container
from omagent_core.utils.logger import logging

# Import the new fast workers
from examples.robot.agent.RobotInitializer.RobotInitializer import RobotInitializer
from examples.robot.agent.SmartNavigator.SmartNavigator import SmartNavigator
from examples.robot.agent.MemoryProcessor.MemoryProcessor import MemoryProcessor

logging.init_logger("omagent", "omagent", level="INFO")
logger = logging.get_logger(__name__)

async def run_fast_robot_navigation(instruction: str = "Find a chair in the room"):
    """
    Run the fast robot navigation workflow.
    
    Args:
        instruction: Natural language navigation instruction
    """
    
    print("🚀 Starting Fast Robot Navigation Workflow")
    print(f"📝 Instruction: {instruction}")
    print("=" * 60)
    
    try:
        # Initialize the container
        container.register_stm("RedisSTM")
        container.start_stm()
        
        # Load the fast workflow
        workflow_file = Path(__file__).parent / "FastRobotWorkflow_workflow.json"
        
        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_file}")
        
        # Create and run workflow
        workflow = ConductorWorkflow(
            workflow_file=str(workflow_file),
            workers=[RobotInitializer, SmartNavigator, MemoryProcessor]
        )
        
        print("⚡ Workflow initialized - Starting navigation...")
        
        # Run the workflow with the instruction
        result = await workflow.run(
            workflow_input={"instruction": instruction},
            wait_for_completion=True
        )
        
        print("\n" + "=" * 60)
        print("🎯 Fast Robot Navigation Complete!")
        print(f"✅ Result: {result}")
        
        # Display performance summary
        if result and "workflow_instance_id" in result:
            workflow_id = result["workflow_instance_id"]
            stm = container.get_stm()
            
            # Get final statistics
            step_count = stm.get(workflow_id, {}).get("step_count", 0)
            goal_achieved = stm.get(workflow_id, {}).get("goal_achieved", False)
            target_object = stm.get(workflow_id, {}).get("target_object", "unknown")
            
            print(f"📊 Performance Summary:")
            print(f"   • Target: {target_object}")
            print(f"   • Steps taken: {step_count}")
            print(f"   • Goal achieved: {'✅ Yes' if goal_achieved else '❌ No'}")
            print(f"   • Efficiency: {(1.0 - step_count/10.0)*100:.1f}% (fewer steps = better)")
        
        return result
        
    except Exception as e:
        logger.error(f"Fast robot navigation failed: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return None
    
    finally:
        # Cleanup
        try:
            container.stop_stm()
        except:
            pass

def main():
    """Main entry point for the fast robot navigation."""
    
    # Default instruction
    default_instruction = "Find a chair in the room"
    
    # Get instruction from command line or use default
    if len(sys.argv) > 1:
        instruction = " ".join(sys.argv[1:])
    else:
        instruction = default_instruction
        print(f"💡 Using default instruction: {instruction}")
        print("   You can provide custom instructions as command line arguments")
        print("   Example: python run_fast_robot.py 'Find a red apple on the table'")
        print()
    
    # Run the workflow
    result = asyncio.run(run_fast_robot_navigation(instruction))
    
    if result:
        print("\n🎉 Fast robot navigation completed successfully!")
        print("🔥 Key improvements:")
        print("   • 3 workers instead of 8 (62% reduction)")
        print("   • Unified navigation cycle (faster execution)")
        print("   • Optimized memory operations (reduced overhead)")
        print("   • Smart caching (avoid redundant processing)")
        print("   • Streamlined decision making (single LLM call per step)")
    else:
        print("\n❌ Fast robot navigation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 