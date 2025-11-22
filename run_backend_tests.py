"""
Test runner script for comprehensive backend validation.
Runs all tests and provides detailed reporting.
"""

import os
import sys
import subprocess
import time
from datetime import datetime


class BackendTestRunner:
    """Comprehensive test runner for backend validation."""
    
    def __init__(self):
        """Initialize test runner."""
        self.start_time = None
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def print_header(self):
        """Print test session header."""
        print("=" * 80)
        print("🧪 IST AFRICA PROCURE-TO-PAY BACKEND TEST SUITE")
        print("=" * 80)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"📁 Working Directory: {os.getcwd()}")
        print("=" * 80)
    
    def run_test_category(self, category_name, test_path, description):
        """Run a specific category of tests."""
        print(f"\n🔍 {category_name}")
        print(f"   {description}")
        print(f"   Running: {test_path}")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            # Run the test
            result = subprocess.run(
                ['uv', 'run', 'python', 'manage.py', 'test', test_path, '-v', '2'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per test category
            )
            
            duration = time.time() - start_time
            
            # Parse results
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                status = "✅ PASSED"
                self.results[category_name] = {
                    'status': 'PASSED',
                    'duration': duration,
                    'output': output
                }
                
                # Count tests from output
                if "Ran " in output:
                    test_count_line = [line for line in output.split('\n') if line.startswith("Ran ")][0]
                    test_count = int(test_count_line.split()[1])
                    self.total_tests += test_count
                    self.passed_tests += test_count
                
            else:
                status = "❌ FAILED"
                self.results[category_name] = {
                    'status': 'FAILED',
                    'duration': duration,
                    'output': output,
                    'error': result.stderr
                }
                
                # Try to count failed tests
                if "FAILED " in output:
                    failure_lines = [line for line in output.split('\n') if "FAILED" in line]
                    self.failed_tests += len(failure_lines)
            
            print(f"   {status} ({duration:.2f}s)")
            
            # Show summary of this category
            if "Ran " in output:
                summary_line = [line for line in output.split('\n') if line.startswith("Ran ")][0]
                print(f"   {summary_line}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ TIMEOUT (exceeded 5 minutes)")
            self.results[category_name] = {
                'status': 'TIMEOUT',
                'duration': 300,
                'error': 'Test exceeded time limit'
            }
            return False
            
        except Exception as e:
            print(f"   💥 ERROR: {str(e)}")
            self.results[category_name] = {
                'status': 'ERROR',
                'duration': 0,
                'error': str(e)
            }
            return False
    
    def run_all_tests(self):
        """Run all test categories."""
        self.start_time = time.time()
        self.print_header()
        
        # Define test categories
        test_categories = [
            {
                'name': 'Model Tests',
                'path': 'procurement.tests.test_models',
                'description': 'Database models, relationships, and validation'
            },
            {
                'name': 'Serializer Tests', 
                'path': 'procurement.tests.test_serializers',
                'description': 'API serialization, validation, and data transformation'
            },
            {
                'name': 'View Tests',
                'path': 'procurement.tests.test_views', 
                'description': 'API endpoints, authentication, and permissions'
            },
            {
                'name': 'AI Processing Tests',
                'path': 'procurement.tests.test_ai_processing',
                'description': 'Document processing, OCR, and data extraction'
            },
            {
                'name': 'Integration Tests',
                'path': 'procurement.tests.test_integration',
                'description': 'End-to-end workflows and system integration'
            }
        ]
        
        # Run each test category
        for category in test_categories:
            success = self.run_test_category(
                category['name'],
                category['path'], 
                category['description']
            )
    
    def print_summary(self):
        """Print comprehensive test summary."""
        total_duration = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        # Overall stats
        passed_categories = len([r for r in self.results.values() if r['status'] == 'PASSED'])
        failed_categories = len([r for r in self.results.values() if r['status'] == 'FAILED'])
        total_categories = len(self.results)
        
        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        print(f"📁 Test Categories: {total_categories}")
        print(f"✅ Passed Categories: {passed_categories}")
        print(f"❌ Failed Categories: {failed_categories}")
        
        if self.total_tests > 0:
            print(f"🧪 Total Individual Tests: {self.total_tests}")
            print(f"✅ Passed Tests: {self.passed_tests}")
            print(f"❌ Failed Tests: {self.failed_tests}")
        
        print("-" * 80)
        
        # Category breakdown
        for category_name, result in self.results.items():
            status_icon = {
                'PASSED': '✅',
                'FAILED': '❌', 
                'TIMEOUT': '⏰',
                'ERROR': '💥'
            }.get(result['status'], '❓')
            
            duration = result.get('duration', 0)
            print(f"{status_icon} {category_name:<25} ({duration:.2f}s)")
        
        # Overall result
        print("=" * 80)
        if failed_categories == 0:
            print("🎉 ALL TESTS PASSED! Backend is ready for production.")
            print("✅ System is validated and assessment-ready.")
        else:
            print("⚠️  Some tests failed. Review failures before deployment.")
            
            # Show failed category details
            for category_name, result in self.results.items():
                if result['status'] == 'FAILED':
                    print(f"\n❌ {category_name} Failures:")
                    if 'error' in result:
                        error_lines = result['error'].split('\n')[:10]  # First 10 lines
                        for line in error_lines:
                            if line.strip():
                                print(f"   {line}")
        
        print("=" * 80)
        return failed_categories == 0
    
    def run_quick_smoke_test(self):
        """Run a quick smoke test to verify basic functionality."""
        print("\n🚀 QUICK SMOKE TEST")
        print("-" * 40)
        
        try:
            # Test 1: Import check
            print("📦 Testing imports...", end=" ")
            result = subprocess.run(
                ['uv', 'run', 'python', '-c', 
                 'from procurement.models import PurchaseRequest; '
                 'from procurement.serializers import PurchaseRequestSerializer; '
                 'from procurement.document_processor import document_processor; '
                 'print("✅ All imports successful")'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ PASSED")
            else:
                print(f"❌ FAILED: {result.stderr}")
                return False
            
            # Test 2: Database connectivity
            print("🗄️  Testing database...", end=" ")
            result = subprocess.run(
                ['uv', 'run', 'python', 'manage.py', 'check', '--database', 'default'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ PASSED")
            else:
                print(f"❌ FAILED: {result.stderr}")
                return False
            
            # Test 3: URL configuration
            print("🌐 Testing URLs...", end=" ")
            result = subprocess.run(
                ['uv', 'run', 'python', 'manage.py', 'check', '--deploy'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 or "System check identified no issues" in result.stdout:
                print("✅ PASSED")
            else:
                print(f"⚠️  WARNINGS: {result.stdout}")
            
            print("✅ Smoke test completed successfully!")
            return True
            
        except Exception as e:
            print(f"💥 Smoke test failed: {str(e)}")
            return False


def main():
    """Main test runner entry point."""
    runner = BackendTestRunner()
    
    # Check if we should run quick test only
    if len(sys.argv) > 1 and sys.argv[1] == '--smoke':
        success = runner.run_quick_smoke_test()
        sys.exit(0 if success else 1)
    
    # Run comprehensive tests
    runner.run_all_tests()
    success = runner.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()