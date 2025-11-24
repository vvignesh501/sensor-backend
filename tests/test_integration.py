#!/usr/bin/env python3
"""
Integration Test Script
Tests the complete pipeline: FastAPI → S3 → Lambda → Redshift → Spectrum
"""

import requests
import boto3
import time
import json
from datetime import datetime

class IntegrationTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.s3_client = boto3.client('s3')
        self.redshift_client = boto3.client('redshift-data')
        self.token = None
        
    def authenticate(self):
        """Get authentication token"""
        print("🔐 Authenticating...")
        
        auth_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{self.base_url}/auth/token", data=auth_data)
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
    
    def test_sensor_endpoint(self):
        """Test sensor data generation and S3 upload"""
        print("\n🔬 Testing sensor endpoint...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/test/sensor/MM", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            test_id = result['test_id']
            print(f"✅ Sensor test created: {test_id}")
            print(f"   Data size: {result['raw_data_stats']['total_size_mb']} MB")
            return test_id
        else:
            print(f"❌ Sensor test failed: {response.status_code}")
            return None
    
    def check_s3_upload(self, test_id):
        """Check if data was uploaded to S3"""
        print(f"\n☁️ Checking S3 upload for {test_id}...")
        
        try:
            # Check source bucket
            response = self.s3_client.list_objects_v2(
                Bucket='sensor-prod-data-vvignesh501-2025',
                Prefix=f'raw_data/'
            )
            
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents'] if test_id in obj['Key']]
                if files:
                    print(f"✅ Found {len(files)} files in S3")
                    return True
            
            print("⏳ S3 upload not found yet, checking again...")
            time.sleep(5)
            return False
            
        except Exception as e:
            print(f"❌ S3 check failed: {str(e)}")
            return False
    
    def check_lambda_processing(self, test_id):
        """Check if Lambda processed the data"""
        print(f"\n⚡ Checking Lambda processing for {test_id}...")
        
        try:
            # Check processed bucket
            response = self.s3_client.list_objects_v2(
                Bucket='sensor-analytics-processed-data',
                Prefix=f'redshift_staging/'
            )
            
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents'] if test_id in obj['Key']]
                if files:
                    print(f"✅ Lambda processed data: {len(files)} files")
                    return True
            
            print("⏳ Lambda processing not complete yet...")
            return False
            
        except Exception as e:
            print(f"❌ Lambda check failed: {str(e)}")
            return False
    
    def check_redshift_data(self, test_id):
        """Check if data was loaded into Redshift"""
        print(f"\n🏢 Checking Redshift data for {test_id}...")
        
        try:
            # Query Redshift for our test data
            query_id = self.redshift_client.execute_statement(
                ClusterIdentifier='sensor-analytics-cluster',
                Database='sensor_analytics',
                DbUser='admin',
                Sql=f"SELECT COUNT(*) FROM sensor_aggregated_metrics WHERE test_id = '{test_id}'"
            )['Id']
            
            # Wait for query to complete
            self.redshift_client.get_waiter('statement_finished').wait(Id=query_id)
            
            # Get results
            result = self.redshift_client.get_statement_result(Id=query_id)
            count = result['Records'][0][0]['longValue']
            
            if count > 0:
                print(f"✅ Found {count} records in Redshift")
                return True
            else:
                print("⏳ Data not in Redshift yet...")
                return False
                
        except Exception as e:
            print(f"❌ Redshift check failed: {str(e)}")
            return False
    
    def test_spectrum_query(self):
        """Test Redshift Spectrum query on S3 data"""
        print(f"\n🌈 Testing Redshift Spectrum query...")
        
        try:
            # Query historical data via Spectrum
            query_id = self.redshift_client.execute_statement(
                ClusterIdentifier='sensor-analytics-cluster',
                Database='sensor_analytics',
                DbUser='admin',
                Sql="SELECT COUNT(*) as historical_count FROM sensor_s3_data.historical_analytics"
            )['Id']
            
            self.redshift_client.get_waiter('statement_finished').wait(Id=query_id)
            result = self.redshift_client.get_statement_result(Id=query_id)
            count = result['Records'][0][0]['longValue']
            
            print(f"✅ Spectrum query successful: {count} historical records")
            return True
            
        except Exception as e:
            print(f"❌ Spectrum query failed: {str(e)}")
            return False
    
    def test_hybrid_query(self):
        """Test hybrid query combining Redshift + Spectrum"""
        print(f"\n🔄 Testing hybrid Redshift + Spectrum query...")
        
        try:
            hybrid_sql = """
            SELECT 
                'Recent' as data_source,
                COUNT(*) as test_count,
                AVG(quality_score) as avg_quality
            FROM sensor_aggregated_metrics
            WHERE processing_time >= CURRENT_DATE - 1
            
            UNION ALL
            
            SELECT 
                'Historical' as data_source,
                COUNT(*) as test_count,
                AVG(quality_score) as avg_quality
            FROM sensor_s3_data.historical_analytics
            """
            
            query_id = self.redshift_client.execute_statement(
                ClusterIdentifier='sensor-analytics-cluster',
                Database='sensor_analytics',
                DbUser='admin',
                Sql=hybrid_sql
            )['Id']
            
            self.redshift_client.get_waiter('statement_finished').wait(Id=query_id)
            result = self.redshift_client.get_statement_result(Id=query_id)
            
            print("✅ Hybrid query successful!")
            for record in result['Records']:
                data_source = record[0]['stringValue']
                count = record[1]['longValue']
                avg_quality = record[2]['doubleValue'] if record[2] else 0
                print(f"   {data_source}: {count} tests, avg quality: {avg_quality:.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Hybrid query failed: {str(e)}")
            return False
    
    def run_complete_test(self):
        """Run complete integration test"""
        print("🚀 Starting Complete Integration Test")
        print("=" * 50)
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Test sensor endpoint
        test_id = self.test_sensor_endpoint()
        if not test_id:
            return False
        
        # Step 3: Wait and check S3 upload
        max_retries = 6
        for i in range(max_retries):
            if self.check_s3_upload(test_id):
                break
            if i == max_retries - 1:
                print("❌ S3 upload timeout")
                return False
            time.sleep(10)
        
        # Step 4: Wait and check Lambda processing
        for i in range(max_retries):
            if self.check_lambda_processing(test_id):
                break
            if i == max_retries - 1:
                print("❌ Lambda processing timeout")
                return False
            time.sleep(15)
        
        # Step 5: Wait and check Redshift data
        for i in range(max_retries):
            if self.check_redshift_data(test_id):
                break
            if i == max_retries - 1:
                print("❌ Redshift data timeout")
                return False
            time.sleep(20)
        
        # Step 6: Test Spectrum
        if not self.test_spectrum_query():
            return False
        
        # Step 7: Test hybrid query
        if not self.test_hybrid_query():
            return False
        
        print("\n🎉 COMPLETE INTEGRATION TEST SUCCESSFUL!")
        print("=" * 50)
        print("✅ FastAPI → S3 → Lambda → Redshift → Spectrum")
        print("✅ All components working together")
        print("✅ Data pipeline fully operational")
        
        return True


def main():
    """Main test function"""
    tester = IntegrationTester()
    
    print("🧪 Sensor Analytics Pipeline Integration Test")
    print("=" * 60)
    print("Testing: FastAPI → S3 → Lambda → Redshift → Spectrum")
    print("")
    
    success = tester.run_complete_test()
    
    if success:
        print("\n🎯 Integration test completed successfully!")
        print("Your pipeline is ready for production use.")
    else:
        print("\n❌ Integration test failed!")
        print("Check the error messages above for troubleshooting.")
    
    return success


if __name__ == "__main__":
    main()