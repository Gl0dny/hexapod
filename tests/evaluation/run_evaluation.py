"""
Main evaluation script that runs all tests and generates a comprehensive report.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List

from tests.evaluation.evaluate_ssl import SSLEvaluator
from tests.evaluation.evaluate_kws import KWSEvaluator

class EvaluationRunner:
    """Runs the complete evaluation and generates reports."""
    
    def __init__(self,
                 log_dir: Path = Path("logs/evaluation"),
                 picovoice_access_key: str = "YOUR_ACCESS_KEY"):
        """
        Initialize the evaluation runner.
        
        Args:
            log_dir: Base directory for evaluation logs
            picovoice_access_key: Picovoice access key for KWS evaluation
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / "evaluation.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("evaluation_runner")
        
        # Initialize evaluators
        self.ssl_evaluator = SSLEvaluator(log_dir=self.log_dir / "ssl")
        self.kws_evaluator = KWSEvaluator(
            keyword_path=Path('src/kws/porcupine/hexapod_en_raspberry-pi_v3_0_0.ppn'),
            context_path=Path('src/kws/rhino/hexapod_en_raspberry-pi_v3_0_0.rhn'),
            access_key=picovoice_access_key,
            log_dir=self.log_dir / "kws"
        )
        
    def run_ssl_evaluation(self) -> Dict:
        """Run SSL evaluation tests."""
        self.logger.info("Starting SSL evaluation...")
        
        # Static DOA evaluation
        true_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        static_results = self.ssl_evaluator.evaluate_static_doa(true_angles)
        static_summary = self.ssl_evaluator.analyze_results(static_results)
        
        # Dynamic DOA evaluation
        dynamic_results = self.ssl_evaluator.evaluate_dynamic_doa('walk', 90.0)
        
        # Multiple sources evaluation
        source_angles = [45, 135, 225, 315]
        multiple_results = self.ssl_evaluator.evaluate_multiple_sources(source_angles)
        
        return {
            'static': static_summary,
            'dynamic': dynamic_results,
            'multiple': multiple_results
        }
    
    def run_kws_evaluation(self) -> Dict:
        """Run KWS evaluation tests."""
        self.logger.info("Starting KWS evaluation...")
        
        # Wake word evaluation
        wake_word_results = self.kws_evaluator.evaluate_wake_word(num_tests=10)
        wake_word_summary = self.kws_evaluator.analyze_results(wake_word_results, 'wake_word')
        
        # Command recognition evaluation
        commands = ['walk forward', 'turn left', 'turn right', 'stop']
        command_results = self.kws_evaluator.evaluate_command_recognition(commands)
        command_summary = self.kws_evaluator.analyze_results(command_results, 'command_recognition')
        
        # Resource usage measurement
        resource_results = self.kws_evaluator.measure_resource_usage()
        
        return {
            'wake_word': wake_word_summary,
            'command_recognition': command_summary,
            'resource_usage': resource_results
        }
    
    def generate_plots(self, results: Dict) -> None:
        """
        Generate plots from evaluation results.
        
        Args:
            results: Dictionary containing evaluation results
        """
        # Set style
        plt.style.use('seaborn')
        
        # SSL plots
        ssl_dir = self.log_dir / "ssl" / "plots"
        ssl_dir.mkdir(parents=True, exist_ok=True)
        
        # Static DOA error plot
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=results['ssl']['static'], x='true_angle', y='mae')
        plt.title('DOA Error by Angle')
        plt.xlabel('True Angle (degrees)')
        plt.ylabel('Mean Absolute Error (degrees)')
        plt.savefig(ssl_dir / "static_doa_error.png")
        plt.close()
        
        # Dynamic DOA error plot
        plt.figure(figsize=(10, 6))
        plt.plot(results['ssl']['dynamic']['timestamp'], 
                results['ssl']['dynamic']['measured_angle'],
                label='Measured')
        plt.axhline(y=results['ssl']['dynamic']['true_angle'], 
                   color='r', linestyle='--', label='True')
        plt.title('Dynamic DOA Tracking')
        plt.xlabel('Time (s)')
        plt.ylabel('Angle (degrees)')
        plt.legend()
        plt.savefig(ssl_dir / "dynamic_doa_tracking.png")
        plt.close()
        
        # KWS plots
        kws_dir = self.log_dir / "kws" / "plots"
        kws_dir.mkdir(parents=True, exist_ok=True)
        
        # Wake word detection rate plot
        plt.figure(figsize=(10, 6))
        sns.barplot(data=results['kws']['wake_word'], 
                   x='noise_level', y='detection_rate')
        plt.title('Wake Word Detection Rate vs. Noise')
        plt.xlabel('Noise Level')
        plt.ylabel('Detection Rate')
        plt.savefig(kws_dir / "wake_word_detection.png")
        plt.close()
        
        # Command recognition accuracy plot
        plt.figure(figsize=(10, 6))
        command_acc = pd.DataFrame.from_dict(
            results['kws']['command_recognition']['per_command_accuracy'],
            orient='index',
            columns=['accuracy']
        )
        sns.barplot(data=command_acc, x=command_acc.index, y='accuracy')
        plt.title('Command Recognition Accuracy')
        plt.xlabel('Command')
        plt.ylabel('Accuracy')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(kws_dir / "command_accuracy.png")
        plt.close()
        
        # Resource usage plot
        plt.figure(figsize=(10, 6))
        plt.plot(results['kws']['resource_usage']['timestamp'],
                results['kws']['resource_usage']['cpu_percent'],
                label='CPU Usage')
        plt.title('System Resource Usage')
        plt.xlabel('Time (s)')
        plt.ylabel('CPU Usage (%)')
        plt.legend()
        plt.savefig(kws_dir / "resource_usage.png")
        plt.close()
    
    def generate_report(self, results: Dict) -> None:
        """
        Generate a comprehensive evaluation report.
        
        Args:
            results: Dictionary containing evaluation results
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'platform': 'Raspberry Pi',
                'python_version': '3.9.0',
                'odas_version': '1.0.0',
                'picovoice_version': '2.0.0'
            },
            'results': results
        }
        
        # Save report
        report_path = self.log_dir / f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4)
        
        # Generate plots
        self.generate_plots(results)
        
        self.logger.info(f"Evaluation report generated: {report_path}")
    
    def run(self) -> None:
        """Run the complete evaluation."""
        self.logger.info("Starting complete evaluation...")
        
        # Run evaluations
        ssl_results = self.run_ssl_evaluation()
        kws_results = self.run_kws_evaluation()
        
        # Combine results
        results = {
            'ssl': ssl_results,
            'kws': kws_results
        }
        
        # Generate report
        self.generate_report(results)
        
        self.logger.info("Evaluation completed successfully")

def main():
    """Main evaluation script."""
    runner = EvaluationRunner()
    runner.run()

if __name__ == "__main__":
    main() 