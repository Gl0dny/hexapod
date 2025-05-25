"""
Sound Source Localization (SSL) evaluation script.
This script implements systematic evaluation of the SSL system's performance.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging
import time
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime

from odas.odas_server import ODASServer
from robot import Hexapod
from control import ControlInterface

class SSLEvaluator:
    """Evaluates the performance of the Sound Source Localization system."""
    
    def __init__(self, 
                 log_dir: Path = Path("logs/evaluation/ssl"),
                 test_duration: float = 5.0,
                 sample_rate: float = 0.1):
        """
        Initialize the SSL evaluator.
        
        Args:
            log_dir: Directory to store evaluation results
            test_duration: Duration of each test in seconds
            sample_rate: Rate at which to sample DOA measurements
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_duration = test_duration
        self.sample_rate = sample_rate
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / "evaluation.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("ssl_evaluator")
        
        # Initialize system components
        self.control_interface = ControlInterface()
        self.odas_server = ODASServer()
        
    def evaluate_static_doa(self, 
                          true_angles: List[float],
                          distance: float = 1.0,
                          repetitions: int = 3) -> pd.DataFrame:
        """
        Evaluate DOA accuracy for static sound sources.
        
        Args:
            true_angles: List of true angles to test (in degrees)
            distance: Distance of sound source from robot (in meters)
            repetitions: Number of repetitions for each angle
            
        Returns:
            DataFrame containing evaluation results
        """
        results = []
        
        for angle in true_angles:
            self.logger.info(f"Testing angle: {angle}°")
            
            for rep in range(repetitions):
                # Start ODAS server
                self.odas_server.start()
                
                # Collect measurements
                measurements = []
                start_time = time.time()
                
                while time.time() - start_time < self.test_duration:
                    # Get DOA measurement
                    doa = self.odas_server.get_latest_doa()
                    if doa is not None:
                        measurements.append({
                            'timestamp': time.time(),
                            'measured_angle': doa,
                            'true_angle': angle,
                            'distance': distance
                        })
                    time.sleep(self.sample_rate)
                
                # Calculate metrics
                if measurements:
                    measured_angles = [m['measured_angle'] for m in measurements]
                    mae = np.mean(np.abs(np.array(measured_angles) - angle))
                    rmse = np.sqrt(np.mean((np.array(measured_angles) - angle) ** 2))
                    std = np.std(measured_angles)
                    
                    results.append({
                        'true_angle': angle,
                        'repetition': rep,
                        'mae': mae,
                        'rmse': rmse,
                        'std': std,
                        'num_measurements': len(measurements),
                        'distance': distance
                    })
                
                self.odas_server.close()
                time.sleep(1)  # Wait between repetitions
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df.to_csv(self.log_dir / f"static_doa_results_{timestamp}.csv", index=False)
        
        return results_df
    
    def evaluate_dynamic_doa(self,
                           motion_pattern: str,
                           true_angle: float,
                           duration: float = 10.0) -> pd.DataFrame:
        """
        Evaluate DOA accuracy during robot motion.
        
        Args:
            motion_pattern: Type of motion ('walk', 'turn', etc.)
            true_angle: True angle of sound source
            duration: Duration of test in seconds
            
        Returns:
            DataFrame containing evaluation results
        """
        results = []
        
        # Start ODAS server
        self.odas_server.start()
        
        # Start motion
        if motion_pattern == 'walk':
            self.control_interface.hexapod.walk_forward()
        elif motion_pattern == 'turn':
            self.control_interface.hexapod.turn_left()
        
        # Collect measurements
        start_time = time.time()
        while time.time() - start_time < duration:
            doa = self.odas_server.get_latest_doa()
            if doa is not None:
                results.append({
                    'timestamp': time.time(),
                    'measured_angle': doa,
                    'true_angle': true_angle,
                    'motion_pattern': motion_pattern
                })
            time.sleep(self.sample_rate)
        
        # Stop motion
        self.control_interface.hexapod.stop()
        self.odas_server.close()
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df.to_csv(self.log_dir / f"dynamic_doa_results_{timestamp}.csv", index=False)
        
        return results_df
    
    def evaluate_multiple_sources(self,
                                source_angles: List[float],
                                duration: float = 5.0) -> pd.DataFrame:
        """
        Evaluate system's ability to detect and track multiple sound sources.
        
        Args:
            source_angles: List of angles for multiple sources
            duration: Duration of test in seconds
            
        Returns:
            DataFrame containing evaluation results
        """
        results = []
        
        # Start ODAS server
        self.odas_server.start()
        
        # Collect measurements
        start_time = time.time()
        while time.time() - start_time < duration:
            tracked_sources = self.odas_server.get_tracked_sources()
            if tracked_sources:
                for source in tracked_sources:
                    results.append({
                        'timestamp': time.time(),
                        'source_id': source['id'],
                        'measured_angle': source['angle'],
                        'true_angles': source_angles
                    })
            time.sleep(self.sample_rate)
        
        self.odas_server.close()
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df.to_csv(self.log_dir / f"multiple_sources_results_{timestamp}.csv", index=False)
        
        return results_df
    
    def analyze_results(self, results_df: pd.DataFrame) -> Dict:
        """
        Analyze evaluation results and calculate summary statistics.
        
        Args:
            results_df: DataFrame containing evaluation results
            
        Returns:
            Dictionary containing summary statistics
        """
        summary = {
            'mean_mae': results_df['mae'].mean(),
            'mean_rmse': results_df['rmse'].mean(),
            'mean_std': results_df['std'].mean(),
            'total_measurements': results_df['num_measurements'].sum(),
            'success_rate': (results_df['mae'] < 5.0).mean()  # Consider measurements within 5° as successful
        }
        
        # Save summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(self.log_dir / f"summary_{timestamp}.json", 'w') as f:
            json.dump(summary, f, indent=4)
        
        return summary

def main():
    """Main evaluation script."""
    evaluator = SSLEvaluator()
    
    # Static DOA evaluation
    true_angles = [0, 45, 90, 135, 180, 225, 270, 315]
    static_results = evaluator.evaluate_static_doa(true_angles)
    static_summary = evaluator.analyze_results(static_results)
    
    # Dynamic DOA evaluation
    dynamic_results = evaluator.evaluate_dynamic_doa('walk', 90.0)
    
    # Multiple sources evaluation
    source_angles = [45, 135, 225, 315]
    multiple_results = evaluator.evaluate_multiple_sources(source_angles)
    
    print("Evaluation completed. Results saved in logs/evaluation/ssl/")

if __name__ == "__main__":
    main() 