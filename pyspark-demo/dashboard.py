"""
Real-time Dashboard - Visualize PySpark analytics
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import os
from datetime import datetime
from local_demo import LocalParquetDemo

# Page config
st.set_page_config(
    page_title="Sensor Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .performance-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_demo():
    """Initialize local demo"""
    return LocalParquetDemo()

@st.cache_data(ttl=60)
def load_comparison_results():
    """Load Parquet vs JSON comparison"""
    try:
        with open('/app/data/comparison_results.json', 'r') as f:
            return json.load(f)
    except:
        return None

def main():
    st.title("🚀 Real-Time Sensor Analytics Dashboard")
    st.markdown("**Powered by Parquet - Local Demo**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.info(f"**Mode:** Local File System")
        
        num_records = st.slider("Number of Records", 50, 500, 100, 50)
        
        if st.button("🔄 Generate New Data", use_container_width=True):
            demo = get_demo()
            with st.spinner("Generating data..."):
                demo.run_demo(num_records=num_records)
            st.cache_data.clear()
            st.success("✅ Data generated!")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📈 Dashboard Features")
        st.markdown("""
        - Parquet storage optimization
        - Interactive visualizations
        - Performance metrics
        - Local file processing
        """)
    
    # Load comparison results
    comparison = load_comparison_results()
    
    if comparison:
        st.header("💾 Storage Optimization Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "JSON Size",
                f"{comparison['json_size']/1024:.2f} KB",
                delta=None
            )
        
        with col2:
            st.metric(
                "Parquet Size",
                f"{comparison['parquet_size']/1024:.2f} KB",
                delta=f"-{comparison['savings_percent']:.1f}%",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "Storage Saved",
                f"{comparison['savings_bytes']/1024:.2f} KB",
                delta=f"{comparison['compression_ratio']:.2f}x compression"
            )
        
        with col4:
            st.metric(
                "Read Speedup",
                f"{comparison['speedup']:.2f}x",
                delta="Faster with Parquet"
            )
        
        # Visualization
        fig = go.Figure(data=[
            go.Bar(
                name='JSON',
                x=['Storage Size'],
                y=[comparison['json_size']/1024],
                marker_color='#e74c3c'
            ),
            go.Bar(
                name='Parquet',
                x=['Storage Size'],
                y=[comparison['parquet_size']/1024],
                marker_color='#2ecc71'
            )
        ])
        fig.update_layout(
            title="Storage Comparison (KB)",
            yaxis_title="Size (KB)",
            barmode='group',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # PySpark Analytics
    st.header("⚡ PySpark Real-Time Analytics")
    
    with st.spinner("Loading data from S3 and processing with PySpark..."):
        try:
            processor = get_processor()
            results = processor.get_realtime_dashboard_data()
            
            # Performance metrics
            perf = results['performance']
            st.markdown(f"""
            <div class="performance-box">
                <strong>⚡ Performance Metrics:</strong><br>
                • Data Load Time: <strong>{perf['load_time']*1000:.2f}ms</strong><br>
                • Analysis Time: <strong>{perf['analysis_time']*1000:.2f}ms</strong><br>
                • Total Processing: <strong>{perf['total_time']*1000:.2f}ms</strong>
            </div>
            """, unsafe_allow_html=True)
            
            # Overall Statistics
            st.subheader("📊 Overall Sensor Metrics")
            stats = results['analysis']['overall_stats']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Avg Temperature", f"{stats['avg_temp']:.2f}°C")
            with col2:
                st.metric("Avg Humidity", f"{stats['avg_humidity']:.2f}%")
            with col3:
                st.metric("Avg Pressure", f"{stats['avg_pressure']:.2f} hPa")
            with col4:
                st.metric("Avg Battery", f"{stats['avg_battery']:.1f}%")
            
            # Location Analysis
            st.subheader("📍 Analysis by Location")
            location_df = pd.DataFrame(results['analysis']['location_stats'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    location_df,
                    x='location',
                    y='sensor_count',
                    title='Sensors per Location',
                    color='sensor_count',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.scatter(
                    location_df,
                    x='avg_temp',
                    y='avg_humidity',
                    size='sensor_count',
                    color='location',
                    title='Temperature vs Humidity by Location',
                    labels={'avg_temp': 'Avg Temperature (°C)', 
                           'avg_humidity': 'Avg Humidity (%)'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Status Distribution
            st.subheader("🔔 Sensor Status Distribution")
            status_df = pd.DataFrame(results['analysis']['status_distribution'])
            
            fig = px.pie(
                status_df,
                values='count',
                names='status',
                title='Sensor Status',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Low Battery Alert
            low_battery = results['analysis']['low_battery_sensors']
            if low_battery:
                st.subheader("⚠️ Low Battery Alerts")
                battery_df = pd.DataFrame(low_battery)
                st.dataframe(
                    battery_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("✅ All sensors have adequate battery levels")
            
            # Raw data preview
            with st.expander("📋 View Raw Data"):
                spark_df = results['dataframe']
                pandas_df = spark_df.limit(50).toPandas()
                st.dataframe(pandas_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("Make sure to run parquet_converter.py first to generate data!")

if __name__ == '__main__':
    main()
