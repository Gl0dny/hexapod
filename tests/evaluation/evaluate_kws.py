"""
Keyword Spotting (KWS) evaluation script.
This script implements systematic evaluation of the KWS system's performance.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging
import time
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
import psutil
import os

from src.kws.voice_control import VoiceControl
from src.control import ControlInterface

class KWSEvaluator:
    """Evaluates the performance of the Keyword Spotting system."""
    
    def __init__(self,
                 keyword_path: Path,
                 context_path: Path,
                 access_key: str,
                 log_dir: Path = Path("logs/evaluation/kws"),
                 test_duration: float = 5.0):
        """
        Initialize the KWS evaluator.
        
        Args:
            keyword_path: Path to wake word model
            context_path: Path to context model
            access_key: Picovoice access key
            log_dir: Directory to store evaluation results
            test_duration: Duration of each test in seconds
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_duration = test_duration
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / "evaluation.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("kws_evaluator")
        
        # Initialize system components
        self.control_interface = ControlInterface()
        self.voice_control = VoiceControl(
            keyword_path=keyword_path,
            context_path=context_path,
            access_key=access_key,
            control_interface=self.control_interface,
            device_index=-1  # Auto-select device
        )
        
    def evaluate_wake_word(self,
                          num_tests: int = 10,
                          noise_level: float = 0.0) -> pd.DataFrame:
        """
        Evaluate wake word detection performance.
        
        Args:
            num_tests: Number of tests to perform
            noise_level: Level of background noise (0.0 to 1.0)
            
        Returns:
            DataFrame containing evaluation results
        """
        results = []
        
        for test in range(num_tests):
            self.logger.info(f"Wake word test {test + 1}/{num_tests}")
            
            # Start voice control
            self.voice_control.start()
            
            # Collect metrics
            start_time = time.time()
            detections = []
            false_alarms = 0
            
            while time.time() - start_time < self.test_duration:
                # Monitor for wake word detections
                if self.voice_control.wake_word_detected:
                    detections.append(time.time())
                    self.voice_control.wake_word_detected = False
                
                # Simulate false alarms based on noise level
                if np.random.random() < noise_level * 0.1:
                    false_alarms += 1
                
                time.sleep(0.1)
            
            # Calculate metrics
            detection_times = np.array(detections) - start_time
            avg_detection_time = np.mean(detection_times) if len(detection_times) > 0 else float('inf')
            
            results.append({
                'test_id': test,
                'num_detections': len(detections),
                'false_alarms': false_alarms,
                'avg_detection_time': avg_detection_time,
                'noise_level': noise_level
            })
            
            self.voice_control.stop()
            time.sleep(1)  # Wait between tests
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df.to_csv(self.log_dir / f"wake_word_results_{timestamp}.csv", index=False)
        
        return results_df
    
    def evaluate_command_recognition(self,
                                   commands: List[str],
                                   num_tests: int = 5) -> pd.DataFrame:
        """
        Evaluate command recognition performance.
        
        Args:
            commands: List of commands to test
            num_tests: Number of tests per command
            
        Returns:
            DataFrame containing evaluation results
        """
        results = []
        
        for command in commands:
            self.logger.info(f"Testing command: {command}")
            
            for test in range(num_tests):
                # Start voice control
                self.voice_control.start()
                
                # Simulate command
                start_time = time.time()
                recognition_time = None
                recognized = False
                
                while time.time() - start_time < self.test_duration:
                    if self.voice_control.last_recognized_command == command:
                        recognition_time = time.time() - start_time
                        recognized = True
                        break
                    time.sleep(0.1)
                
                results.append({
                    'command': command,
                    'test_id': test,
                    'recognized': recognized,
                    'recognition_time': recognition_time if recognized else float('inf')
                })
                
                self.voice_control.stop()
                time.sleep(1)  # Wait between tests
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df.to_csv(self.log_dir / f"command_recognition_results_{timestamp}.csv", index=False)
        
        return results_df
    
    def measure_resource_usage(self, duration: float = 30.0) -> pd.DataFrame:
        """
        Measure system resource usage during KWS operation.
        
        Args:
            duration: Duration of measurement in seconds
            
        Returns:
            DataFrame containing resource usage measurements
        """
        results = []
        process = psutil.Process(os.getpid())
        
        # Start voice control
        self.voice_control.start()
        
        # Collect measurements
        start_time = time.time()
        while time.time() - start_time < duration:
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            
            results.append({
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'memory_rss': memory_info.rss,
                'memory_vms': memory_info.vms
            })
            
            time.sleep(1)
        
        self.voice_control.stop()
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df.to_csv(self.log_dir / f"resource_usage_{timestamp}.csv", index=False)
        
        return results_df
    
    def analyze_results(self, results_df: pd.DataFrame, test_type: str) -> Dict:
        """
        Analyze evaluation results and calculate summary statistics.
        
        Args:
            results_df: DataFrame containing evaluation results
            test_type: Type of test ('wake_word' or 'command_recognition')
            
        Returns:
            Dictionary containing summary statistics
        """
        if test_type == 'wake_word':
            summary = {
                'mean_detection_time': results_df['avg_detection_time'].mean(),
                'detection_rate': results_df['num_detections'].mean() / self.test_duration,
                'false_alarm_rate': results_df['false_alarms'].mean() / self.test_duration,
                'success_rate': (results_df['num_detections'] > 0).mean()
            }
        elif test_type == 'command_recognition':
            summary = {
                'mean_recognition_time': results_df['recognition_time'].mean(),
                'recognition_rate': results_df['recognized'].mean(),
                'per_command_accuracy': results_df.groupby('command')['recognized'].mean().to_dict()
            }
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        # Save summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(self.log_dir / f"summary_{test_type}_{timestamp}.json", 'w') as f:
            json.dump(summary, f, indent=4)
        
        return summary

def main():
    """Main evaluation script."""
    # Initialize evaluator
    evaluator = KWSEvaluator(
        keyword_path=Path('src/kws/porcupine/hexapod_en_raspberry-pi_v3_0_0.ppn'),
        context_path=Path('src/kws/rhino/hexapod_en_raspberry-pi_v3_0_0.rhn'),
        access_key='2DF2OdgHUpED3jZw001aag1DT43ORS74dtI9mYQeN91R4lGZ3Zy6Rw=='  # Replace with actual access key
    )
    
    # Wake word evaluation
    wake_word_results = evaluator.evaluate_wake_word(num_tests=10)
    wake_word_summary = evaluator.analyze_results(wake_word_results, 'wake_word')
    
    # Command recognition evaluation
    commands = ['walk forward', 'turn left', 'turn right', 'stop']
    command_results = evaluator.evaluate_command_recognition(commands)
    command_summary = evaluator.analyze_results(command_results, 'command_recognition')
    
    # Resource usage measurement
    resource_results = evaluator.measure_resource_usage()
    
    print("Evaluation completed. Results saved in logs/evaluation/kws/")

if __name__ == "__main__":
    main() 