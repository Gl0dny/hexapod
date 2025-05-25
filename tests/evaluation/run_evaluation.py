"""
Main script for running the evaluation.
"""

<<<<<<< HEAD
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import pandas as pd
import numpy as np
=======
import argparse
from pathlib import Path
>>>>>>> a849efe6a0a14b327470acba46b0c20b05120d10
import logging
import json
from datetime import datetime

<<<<<<< HEAD
from tests.evaluation.evaluate_ssl import SSLEvaluator
from tests.evaluation.evaluate_kws import KWSEvaluator
=======
from .evaluator import (
    StaticEvaluator,
    DynamicEvaluator,
    EnvironmentalEvaluator
)
>>>>>>> a849efe6a0a14b327470acba46b0c20b05120d10

def setup_logging(output_dir: Path):
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(output_dir / 'evaluation.log'),
            logging.StreamHandler()
        ]
    )

def run_static_evaluation(output_dir: Path):
    """Run static evaluation tests."""
    evaluator = StaticEvaluator(output_dir / 'static')
    
    # Test DOA estimation
    true_angles = list(range(0, 360, 45))  # Test every 45 degrees
    distances = [1.0, 2.0, 3.0]  # Test different distances
    evaluator.evaluate_doa(true_angles, distances)
    
    # Test KWS
    commands = [
        "move forward",
        "turn left",
        "turn right",
        "stop",
        "stand up",
        "sit down"
    ]
    evaluator.evaluate_kws(commands)
    
    # Save results
    evaluator.save_results('static_results.json')

def run_dynamic_evaluation(output_dir: Path):
    """Run dynamic evaluation tests."""
    evaluator = DynamicEvaluator(output_dir / 'dynamic')
    
    # Test different gaits
    gait_types = [
        "tripod",
        "wave",
        "ripple"
    ]
    evaluator.evaluate_motion_compensation(gait_types)
    
    # Save results
    evaluator.save_results('dynamic_results.json')

def run_environmental_evaluation(output_dir: Path):
    """Run environmental evaluation tests."""
    evaluator = EnvironmentalEvaluator(output_dir / 'environmental')
    
    # Test different environments
    room_sizes = ["small", "medium", "large"]
    surface_types = ["hard", "soft", "mixed"]
    evaluator.evaluate_environmental_robustness(room_sizes, surface_types)
    
    # Save results
    evaluator.save_results('environmental_results.json')

def main():
    parser = argparse.ArgumentParser(description='Run hexapod system evaluation')
    parser.add_argument('--output-dir', type=Path, default=Path('evaluation_results'),
                      help='Directory to store evaluation results')
    parser.add_argument('--evaluation-type', type=str, choices=['static', 'dynamic', 'environmental', 'all'],
                      default='all', help='Type of evaluation to run')
    args = parser.parse_args()
    
    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = args.output_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up logging
    setup_logging(output_dir)
    logger = logging.getLogger(__name__)
    
    try:
        if args.evaluation_type in ['static', 'all']:
            logger.info("Running static evaluation...")
            run_static_evaluation(output_dir)
        
        if args.evaluation_type in ['dynamic', 'all']:
            logger.info("Running dynamic evaluation...")
            run_dynamic_evaluation(output_dir)
        
        if args.evaluation_type in ['environmental', 'all']:
            logger.info("Running environmental evaluation...")
            run_environmental_evaluation(output_dir)
        
        logger.info("Evaluation completed successfully")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main() 