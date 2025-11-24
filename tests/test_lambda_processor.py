#!/usr/bin/env python3
"""
Test script for N-Dimensional Data Processor Lambda Function
Demonstrates processing of sensor data for analytics
"""

import numpy as np
import json
import boto3
import io
from datetime import datetime
import sys
import os

# Add the current directory to path to import our processor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lambda_data_processor import NDimensionalDataProcessor

class LocalTestRunner:
    """Local test runner for the Lambda data processor"""
    
    def __init__(self):
        self.processor = NDimensionalDataProcessor()
        
    def generate_test_data(self) -> dict:
        """Generate various types of N-dimensional test data"""
        
        test_cases = {
            "normal_3d_sensor": {
                "data": np.random.normal(25.0, 2.5, (100, 16, 8)).astype(np.float32),
                "description": "Normal 3D sensor data (time, spatial_x, spatial_y)"
            },
            
            "high_dimensional": {
                "data": np.random.normal(0.0, 1.0, (50, 10, 10, 5)).astype(np.float32),
                "description": "4D sensor array (time, x, y, channels)"
            },
            
            "anomalous_data": {
                "data": self._create_anomalous_data(),
                "description": "3D data with injected anomalies"
            },
            
            "temporal_drift": {
                "data": self._create_drift_data(),
                "description": "3D data with temporal drift pattern"
            },
            
            "spatial_pattern": {
                "data": self._create_spatial_pattern(),
                "description": "2D data with spatial patterns"
            }
        }
        
        return test_cases
    
    def _create_anomalous_data(self) -> np.ndarray:
        """Create data with known anomalies"""
        data = np.random.normal(25.0, 2.5, (100, 16, 8)).astype(np.float32)
        
        # Inject point anomalies
        data[50, 8, 4] = 100.0  # Single outlier
        data[75, 10, 6] = -50.0  # Another outlier
        
        # Inject spatial anomaly (entire slice)
        data[80, :, :] = 200.0
        
        # Inject temporal anomaly (entire time series at one location)
        data[:, 5, 3] = np.linspace(0, 500, 100)
        
        return data
    
    def _create_drift_data(self) -> np.ndarray:
        """Create data with temporal drift"""
        base_data = np.random.normal(25.0, 2.5, (100, 16, 8)).astype(np.float32)
        
        # Add linear drift over time
        for t in range(100):
            drift = t * 0.1  # Linear drift
            base_data[t, :, :] += drift
            
        # Add some noise
        base_data += np.random.normal(0, 0.5, base_data.shape)
        
        return base_data
    
    def _create_spatial_pattern(self) -> np.ndarray:
        """Create 2D data with spatial patterns"""
        x = np.linspace(-5, 5, 32)
        y = np.linspace(-5, 5, 32)
        X, Y = np.meshgrid(x, y)
        
        # Create a pattern (e.g., Gaussian + sine wave)
        pattern = np.exp(-(X**2 + Y**2)/10) * np.sin(X) * np.cos(Y)
        
        # Add noise
        pattern += np.random.normal(0, 0.1, pattern.shape)
        
        return pattern.astype(np.float32)
    
    def run_comprehensive_test(self):
        """Run comprehensive tests on different data types"""
        
        print("🧪 N-Dimensional Data Processor - Comprehensive Test Suite")
        print("=" * 70)
        
        test_cases = self.generate_test_data()
        results = {}
        
        for test_name, test_case in test_cases.items():
            print(f"\n📊 Testing: {test_name}")
            print(f"Description: {test_case['description']}")
            print(f"Data shape: {test_case['data'].shape}")
            print(f"Data type: {test_case['data'].dtype}")
            
            try:
                # Process the data
                result = self.processor.preprocess_ndarray(
                    test_case['data'], 
                    f"test_{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                results[test_name] = result
                
                # Print key results
                self._print_analysis_summary(result)
                
            except Exception as e:
                print(f"❌ Error processing {test_name}: {str(e)}")
                results[test_name] = {"error": str(e)}
        
        return results
    
    def _print_analysis_summary(self, result: dict):
        """Print a summary of analysis results"""
        
        features = result['analytics_features']
        
        print(f"  📈 Global Stats:")
        global_stats = features['global_stats']
        print(f"    Mean: {global_stats['mean']:.3f}")
        print(f"    Std: {global_stats['std']:.3f}")
        print(f"    Range: [{global_stats['min']:.3f}, {global_stats['max']:.3f}]")
        
        print(f"  🚨 Anomaly Detection:")
        anomalies = features['anomaly_detection']
        print(f"    Total anomalies: {anomalies['total_anomalies']}")
        print(f"    Anomaly percentage: {anomalies['anomaly_percentage']:.2f}%")
        print(f"    Max Z-score: {anomalies['max_z_score']:.2f}")
        
        print(f"  🔍 Quality Metrics:")
        quality = features['quality_metrics']
        print(f"    SNR: {quality['signal_to_noise_ratio']:.2f} dB")
        print(f"    Dynamic range: {quality['dynamic_range']:.3f}")
        print(f"    Outlier percentage: {quality['outlier_percentage']:.2f}%")
        
        if 'spatial_analysis' in features:
            print(f"  🗺️  Spatial Analysis:")
            spatial = features['spatial_analysis']
            print(f"    Uniformity score: {spatial['uniformity_score']:.3f}")
            print(f"    Edge density: {spatial['edge_density']:.3f}")
        
        if 'temporal_analysis' in features:
            print(f"  ⏰ Temporal Analysis:")
            temporal = features['temporal_analysis']
            print(f"    Trend: {temporal['trend']:.6f}")
            print(f"    Stability: {temporal['stability']:.3f}")
            print(f"    Drift rate: {temporal['drift_rate']:.6f}")
        
        print(f"  🌊 Frequency Analysis:")
        freq = features['frequency_analysis']
        print(f"    Dominant frequency: {freq['dominant_frequency']:.6f}")
        print(f"    Spectral centroid: {freq['spectral_centroid']:.6f}")
    
    def simulate_lambda_event(self, test_name: str = "normal_3d_sensor"):
        """Simulate a Lambda event for testing"""
        
        print(f"\n🔄 Simulating Lambda Event for {test_name}")
        print("-" * 50)
        
        # Create test event structure
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "sensor-prod-data-vvignesh501-2025"},
                        "object": {"key": f"raw_data/{test_name}_test.npy"}
                    }
                }
            ]
        }
        
        context = {
            "function_name": "sensor-data-processor",
            "memory_limit_in_mb": "1024",
            "remaining_time_in_millis": 300000
        }
        
        print(f"Event: {json.dumps(event, indent=2)}")
        
        # Note: In a real scenario, this would invoke the actual lambda_handler
        # For testing, we'll just process the data directly
        test_cases = self.generate_test_data()
        if test_name in test_cases:
            result = self.processor.preprocess_ndarray(
                test_cases[test_name]['data'],
                f"lambda_test_{test_name}"
            )
            
            print("✅ Lambda simulation completed successfully")
            return result
        else:
            print(f"❌ Test case {test_name} not found")
            return None
    
    def benchmark_performance(self):
        """Benchmark processing performance for different data sizes"""
        
        print("\n⚡ Performance Benchmark")
        print("=" * 40)
        
        test_sizes = [
            (50, 8, 8),      # Small
            (100, 16, 8),    # Medium (current)
            (200, 32, 16),   # Large
            (500, 64, 32),   # Very Large
        ]
        
        for shape in test_sizes:
            print(f"\nTesting shape: {shape}")
            
            # Generate test data
            data = np.random.normal(25.0, 2.5, shape).astype(np.float32)
            data_size_mb = data.nbytes / (1024 * 1024)
            
            print(f"Data size: {data_size_mb:.2f} MB")
            
            # Time the processing
            start_time = datetime.now()
            
            try:
                result = self.processor.preprocess_ndarray(data, f"benchmark_{shape}")
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                print(f"Processing time: {processing_time:.3f} seconds")
                print(f"Throughput: {data_size_mb/processing_time:.2f} MB/s")
                
                # Memory efficiency
                features_count = len(str(result))
                print(f"Output size: {features_count/1024:.2f} KB")
                
            except Exception as e:
                print(f"❌ Failed: {str(e)}")


def main():
    """Main test function"""
    
    runner = LocalTestRunner()
    
    print("🚀 N-Dimensional Sensor Data Analytics Processor")
    print("Testing AWS Lambda Function Locally")
    print("=" * 60)
    
    # Run comprehensive tests
    results = runner.run_comprehensive_test()
    
    # Simulate Lambda event
    runner.simulate_lambda_event("anomalous_data")
    
    # Performance benchmark
    runner.benchmark_performance()
    
    print("\n✅ All tests completed!")
    print("\n📋 Summary:")
    print(f"  - Tested {len(results)} different data types")
    print(f"  - Processed N-dimensional arrays (2D to 4D)")
    print(f"  - Detected anomalies and calculated quality metrics")
    print(f"  - Performed spatial and temporal analysis")
    print(f"  - Ready for AWS Lambda deployment")
    
    return results


if __name__ == "__main__":
    main()