#!/usr/bin/env python3
"""
Redshift Spectrum Architecture Example
Shows how to optimize sensor data storage and querying costs
"""

class SpectrumArchitectureExample:
    """Demonstrates optimal data architecture with Redshift Spectrum"""
    
    def __init__(self):
        self.data_tiers = {
            "hot": "Recent data (last 30 days) - Redshift tables",
            "warm": "Historical data (1-2 years) - S3 + Spectrum", 
            "cold": "Archive data (2+ years) - S3 Glacier + Spectrum"
        }
    
    def show_data_tiering_strategy(self):
        """Show how to tier sensor data for cost optimization"""
        
        print("🏗️ Optimal Sensor Data Architecture with Spectrum")
        print("=" * 60)
        
        architecture = {
            "Tier 1 - HOT (Redshift Tables)": {
                "data": "Last 30 days of sensor analytics",
                "storage": "Redshift cluster storage",
                "cost": "$$$$ (expensive but fastest)",
                "use_case": "Real-time dashboards, alerts, recent trends",
                "query_speed": "Sub-second",
                "tables": [
                    "sensor_time_series_analytics (recent)",
                    "sensor_spatial_analytics (recent)", 
                    "sensor_aggregated_metrics (recent)",
                    "sensor_event_data (recent)"
                ]
            },
            
            "Tier 2 - WARM (S3 + Spectrum)": {
                "data": "1-24 months of historical data",
                "storage": "S3 Standard",
                "cost": "$$ (10x cheaper than Redshift)",
                "use_case": "Historical analysis, trend reports, ML training",
                "query_speed": "5-30 seconds",
                "format": "Parquet (columnar, compressed)"
            },
            
            "Tier 3 - COLD (S3 Glacier + Spectrum)": {
                "data": "2+ years archive data",
                "storage": "S3 Glacier",
                "cost": "$ (100x cheaper than Redshift)",
                "use_case": "Compliance, long-term analysis, data science",
                "query_speed": "Minutes (after restore)",
                "format": "Parquet (highly compressed)"
            }
        }
        
        for tier, details in architecture.items():
            print(f"\n📊 {tier}")
            for key, value in details.items():
                if isinstance(value, list):
                    print(f"   {key}:")
                    for item in value:
                        print(f"     - {item}")
                else:
                    print(f"   {key}: {value}")
    
    def show_cost_comparison(self):
        """Show cost comparison with and without Spectrum"""
        
        print(f"\n💰 Cost Comparison: 5 Years of Sensor Data")
        print("=" * 50)
        
        # Assumptions: 1000 tests/day, 100MB processed data per test
        daily_data_gb = 1000 * 0.1  # 100 GB/day
        yearly_data_tb = daily_data_gb * 365 / 1000  # ~36 TB/year
        five_year_data_tb = yearly_data_tb * 5  # ~180 TB
        
        scenarios = {
            "All in Redshift (No Spectrum)": {
                "storage_cost_monthly": five_year_data_tb * 1000 * 0.25,  # $0.25/GB/month
                "compute_cost_monthly": 2000,  # Large cluster needed
                "total_monthly": None,
                "pros": ["Fastest queries", "Simple architecture"],
                "cons": ["Very expensive", "Doesn't scale well"]
            },
            
            "Hybrid with Spectrum (Recommended)": {
                "redshift_storage": 1 * 1000 * 0.25,  # 1TB hot data
                "s3_standard": 35 * 1000 * 0.023,    # 35TB warm data  
                "s3_glacier": 144 * 1000 * 0.004,    # 144TB cold data
                "compute_cost_monthly": 800,          # Smaller cluster
                "total_monthly": None,
                "pros": ["Cost effective", "Scalable", "Fast for recent data"],
                "cons": ["Slightly complex setup"]
            },
            
            "All in S3 + Spectrum": {
                "s3_storage": five_year_data_tb * 1000 * 0.023,
                "compute_cost_monthly": 400,  # Minimal cluster
                "total_monthly": None,
                "pros": ["Cheapest", "Unlimited scale"],
                "cons": ["Slower queries", "No real-time analytics"]
            }
        }
        
        # Calculate totals
        for scenario, costs in scenarios.items():
            if scenario == "All in Redshift (No Spectrum)":
                costs["total_monthly"] = costs["storage_cost_monthly"] + costs["compute_cost_monthly"]
            elif scenario == "Hybrid with Spectrum (Recommended)":
                costs["total_monthly"] = (costs["redshift_storage"] + costs["s3_standard"] + 
                                        costs["s3_glacier"] + costs["compute_cost_monthly"])
            else:
                costs["total_monthly"] = costs["s3_storage"] + costs["compute_cost_monthly"]
        
        for scenario, details in scenarios.items():
            print(f"\n📈 {scenario}")
            print(f"   Monthly Cost: ${details['total_monthly']:,.0f}")
            print(f"   Annual Cost: ${details['total_monthly'] * 12:,.0f}")
            print(f"   Pros: {', '.join(details['pros'])}")
            print(f"   Cons: {', '.join(details['cons'])}")
    
    def show_query_examples(self):
        """Show practical Spectrum query examples"""
        
        print(f"\n🔍 Practical Spectrum Query Examples")
        print("=" * 50)
        
        queries = {
            "Real-time Dashboard (Hot Data)": """
            -- Query recent data from Redshift tables (fastest)
            SELECT sensor_type, AVG(quality_score), COUNT(*)
            FROM sensor_aggregated_metrics 
            WHERE processing_time >= CURRENT_DATE - 7
            GROUP BY sensor_type;
            """,
            
            "Historical Trend Analysis (Warm Data)": """
            -- Query 2 years of data from S3 via Spectrum
            SELECT 
                DATE_TRUNC('month', processing_date) as month,
                sensor_type,
                AVG(global_mean) as monthly_avg,
                COUNT(*) as tests_count
            FROM sensor_s3_data.processed_analytics
            WHERE processing_date >= CURRENT_DATE - 730
            GROUP BY DATE_TRUNC('month', processing_date), sensor_type
            ORDER BY month DESC;
            """,
            
            "Hybrid Query (Hot + Warm Data)": """
            -- Combine recent Redshift data with historical S3 data
            SELECT * FROM (
                -- Recent data from Redshift
                SELECT test_id, sensor_type, quality_score, processing_time::DATE as date
                FROM sensor_aggregated_metrics 
                WHERE processing_time >= CURRENT_DATE - 30
                
                UNION ALL
                
                -- Historical data from S3
                SELECT test_id, sensor_type, quality_score, processing_date as date
                FROM sensor_s3_data.processed_analytics
                WHERE processing_date >= CURRENT_DATE - 365
                  AND processing_date < CURRENT_DATE - 30
            )
            WHERE quality_score < 50  -- Failed tests across all time
            ORDER BY date DESC;
            """,
            
            "Cost-Effective Archive Query": """
            -- Query 5 years of data without expensive Redshift storage
            SELECT 
                sensor_type,
                EXTRACT(year FROM processing_date) as year,
                AVG(anomaly_percentage) as yearly_anomaly_rate,
                COUNT(*) as yearly_tests
            FROM sensor_s3_data.processed_analytics
            WHERE processing_date >= '2019-01-01'
            GROUP BY sensor_type, EXTRACT(year FROM processing_date)
            ORDER BY year DESC, yearly_anomaly_rate DESC;
            """
        }
        
        for query_name, sql in queries.items():
            print(f"\n🔍 {query_name}:")
            print(sql.strip())
    
    def show_implementation_steps(self):
        """Show step-by-step implementation"""
        
        print(f"\n🚀 Implementation Steps")
        print("=" * 30)
        
        steps = [
            "1. Set up S3 buckets with proper partitioning",
            "2. Configure Glue Data Catalog for metadata",
            "3. Create external schemas in Redshift",
            "4. Set up data lifecycle policies",
            "5. Implement automated data tiering",
            "6. Create hybrid views for seamless querying"
        ]
        
        for step in steps:
            print(f"   {step}")
        
        print(f"\n📋 Data Lifecycle Example:")
        print(f"   Day 0-30: Data in Redshift tables (hot)")
        print(f"   Day 31-365: Move to S3 Standard + Spectrum (warm)")
        print(f"   Day 366+: Move to S3 Glacier + Spectrum (cold)")


def main():
    """Run the Spectrum architecture demonstration"""
    
    demo = SpectrumArchitectureExample()
    
    print("🌟 Redshift Spectrum for Sensor Data Analytics")
    print("=" * 60)
    
    demo.show_data_tiering_strategy()
    demo.show_cost_comparison()
    demo.show_query_examples()
    demo.show_implementation_steps()
    
    print(f"\n✅ Key Benefits of Spectrum:")
    print(f"   💰 90% cost reduction for historical data")
    print(f"   📈 Unlimited scalability (petabytes in S3)")
    print(f"   🔍 Query across all data with single SQL")
    print(f"   ⚡ Keep hot data fast in Redshift")
    print(f"   🏗️ No ETL needed for S3 data")


if __name__ == "__main__":
    main()