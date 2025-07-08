#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance monitoring and system health check tool
Demonstrates practical application of code quality improvement recommendations
"""

import time
import psutil
import sqlite3
import requests
import json
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Performance monitoring class - demonstrates code quality improvements
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.metrics = []
        
    def monitor_performance(self, func):
        """
        Performance monitoring decorator
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
                logger.error(f"Function {func.__name__} execution failed: {error}")
                
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            # Record performance metrics
            metric = {
                'function': func.__name__,
                'execution_time': round(execution_time, 3),
                'memory_usage': round(memory_usage, 2),
                'success': success,
                'error': error,
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics.append(metric)
            
            logger.info(
                f"Performance monitoring - {func.__name__}: "
                f"execution_time={execution_time:.3f}s, "
                f"memory_usage={memory_usage:.2f}MB, "
                f"status={'success' if success else 'failed'}"
            )
            
            return result
            
        return wrapper
    
    def check_system_health(self) -> Dict[str, Any]:
        """
        System health check
        """
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # Check database connection
        try:
            conn = sqlite3.connect('ocr_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM ocr_records')
            record_count = cursor.fetchone()[0]
            conn.close()
            
            health_status['checks']['database'] = {
                'status': 'healthy',
                'record_count': record_count,
                'message': f'Database connection normal, {record_count} records total'
            }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Database connection failed'
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Check Flask service
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                health_status['checks']['flask_service'] = {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'message': 'Flask service running normally'
                }
            else:
                health_status['checks']['flask_service'] = {
                    'status': 'unhealthy',
                    'status_code': response.status_code,
                    'message': f'Flask service response abnormal: {response.status_code}'
                }
                health_status['overall_status'] = 'unhealthy'
        except Exception as e:
            health_status['checks']['flask_service'] = {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Flask service inaccessible'
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        health_status['checks']['system_resources'] = {
            'status': 'healthy' if cpu_percent < 80 and memory.percent < 80 else 'warning',
            'cpu_usage': f"{cpu_percent}%",
            'memory_usage': f"{memory.percent}%",
            'disk_usage': f"{disk.percent}%",
            'message': f'CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%'
        }
        
        if cpu_percent > 90 or memory.percent > 90:
            health_status['overall_status'] = 'unhealthy'
        elif cpu_percent > 80 or memory.percent > 80:
            health_status['overall_status'] = 'warning'
        
        # Check upload folder
        upload_folder = Path('uploads')
        if upload_folder.exists():
            file_count = len(list(upload_folder.glob('*')))
            folder_size = sum(f.stat().st_size for f in upload_folder.glob('*') if f.is_file()) / 1024 / 1024  # MB
            
            health_status['checks']['upload_folder'] = {
                'status': 'healthy',
                'file_count': file_count,
                'folder_size_mb': round(folder_size, 2),
                'message': f'Upload folder normal, contains {file_count} files, size {folder_size:.2f}MB'
            }
        else:
            health_status['checks']['upload_folder'] = {
                'status': 'warning',
                'message': 'Upload folder does not exist'
            }
        
        return health_status
    
    def test_ocr_performance(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Test OCR performance
        """
        @self.monitor_performance
        def _test_ocr():
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file does not exist: {image_path}")
            
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{self.base_url}/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"OCR request failed: {response.status_code} - {response.text}")
        
        return _test_ocr()
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate performance report
        """
        if not self.metrics:
            return {'message': 'No performance data available'}
        
        # Calculate statistics
        execution_times = [m['execution_time'] for m in self.metrics if m['success']]
        memory_usages = [m['memory_usage'] for m in self.metrics if m['success']]
        
        success_count = sum(1 for m in self.metrics if m['success'])
        total_count = len(self.metrics)
        
        report = {
            'summary': {
                'total_operations': total_count,
                'successful_operations': success_count,
                'success_rate': f"{(success_count/total_count)*100:.1f}%" if total_count > 0 else "0%",
                'average_execution_time': f"{sum(execution_times)/len(execution_times):.3f}s" if execution_times else "N/A",
                'max_execution_time': f"{max(execution_times):.3f}s" if execution_times else "N/A",
                'min_execution_time': f"{min(execution_times):.3f}s" if execution_times else "N/A",
                'average_memory_usage': f"{sum(memory_usages)/len(memory_usages):.2f}MB" if memory_usages else "N/A"
            },
            'detailed_metrics': self.metrics[-10:],  # Last 10 operations
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """
        Save performance report to file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.json"
        
        # Create output directory
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        
        # Generate complete report
        full_report = {
            'performance_metrics': self.generate_performance_report(),
            'system_health': self.check_system_health()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Performance report saved to: {filepath}")
        return str(filepath)

def main():
    """
    Main function - demonstrates performance monitoring functionality
    """
    print("🔍 OCR System Performance Monitoring Tool")
    print("=" * 50)
    
    monitor = PerformanceMonitor()
    
    # 1. System health check
    print("\n📊 System health check...")
    health = monitor.check_system_health()
    print(f"Overall status: {health['overall_status'].upper()}")
    
    for check_name, check_result in health['checks'].items():
        status_icon = {
            'healthy': '✅',
            'warning': '⚠️',
            'unhealthy': '❌'
        }.get(check_result['status'], '❓')
        
        print(f"{status_icon} {check_name}: {check_result['message']}")
    
    # 2. OCR performance test
    print("\n🚀 OCR performance test...")
    test_image = "uploads/table_test_ocr_20250708_173524.png"
    
    if Path(test_image).exists():
        try:
            result = monitor.test_ocr_performance(test_image)
            if result:
                print(f"✅ OCR test successful")
                print(f"   Extraction confidence: {result.get('extraction_confidence', 'N/A')}%")
                print(f"   Extracted fields: {len([v for v in result.get('extracted_info', {}).values() if v and v != 'N/A'])}")
            else:
                print("❌ OCR test failed")
        except Exception as e:
            print(f"❌ OCR test exception: {str(e)}")
    else:
        print(f"⚠️ Test image does not exist: {test_image}")
    
    # 3. Generate performance report
    print("\n📈 Generating performance report...")
    report_file = monitor.save_report()
    print(f"📄 Report saved: {report_file}")
    
    # 4. Display performance summary
    performance_report = monitor.generate_performance_report()
    if 'summary' in performance_report:
        print("\n📋 Performance summary:")
        summary = performance_report['summary']
        print(f"   Total operations: {summary['total_operations']}")
        print(f"   Success rate: {summary['success_rate']}")
        print(f"   Average execution time: {summary['average_execution_time']}")
        print(f"   Average memory usage: {summary['average_memory_usage']}")
    
    print("\n✅ Performance monitoring completed!")

if __name__ == "__main__":
    main()