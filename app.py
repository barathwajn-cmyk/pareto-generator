import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

# --- PAGE SETUP ---
st.set_page_config(page_title="Auto Pareto Generator", layout="centered")
st.title("📊 Auto Pareto Chart Generator")
st.write("Upload your defect data (CSV or Excel) below to instantly generate a Pareto chart. No coding required!")

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    # Read the file into a Pandas DataFrame
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("File uploaded successfully!")
        
        # --- COLUMN SELECTION ---
        st.write("### Select your columns")
        col1, col2 = st.columns(2)
        
        with col1:
            defect_col = st.selectbox("Which column has the Defect Names?", df.columns)
        with col2:
            qty_col = st.selectbox("Which column has the Quantities?", df.columns)
            
        # --- GENERATE CHART BUTTON ---
        if st.button("Generate Pareto Chart"):
            
            # 1. Data Processing
            # Group by defect just in case there are duplicates, and sum the quantities
            processed_df = df.groupby(defect_col)[qty_col].sum().reset_index()
            # Sort from highest to lowest (Crucial for Pareto)
            processed_df = processed_df.sort_values(by=qty_col, ascending=False).reset_index(drop=True)
            
            labels = processed_df[defect_col].astype(str).tolist()
            counts = processed_df[qty_col].tolist()
            
            # Calculate cumulative percentages
            total_defects = sum(counts)
            cumulative_counts = np.cumsum(counts)
            cumulative_percent = (cumulative_counts / total_defects) * 100

            # 2. Chart Generation (Backend)
            fig, ax1 = plt.subplots(figsize=(14, 7))

            # Bar Chart (Actual Quantity)
            bar_color = '#4285F4' 
            bars = ax1.bar(labels, counts, color=bar_color, width=0.6, label='Actual Quantity')
            ax1.set_ylabel('Quantity', color='black')
            
            # Add dynamic headroom so text doesn't get cut off
            max_val = max(counts)
            ax1.set_ylim(0, max_val * 1.15) 
            ax1.set_xticks(range(len(labels)))
            ax1.set_xticklabels(labels, rotation=45, ha='right')

            # Add values on top of bars
            for bar in bars:
                yval = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2, yval + (max_val*0.02), int(yval), 
                         ha='center', va='bottom', color=bar_color, fontweight='bold', fontsize=9)

            # Line Chart (Cumulative Percentage)
            ax2 = ax1.twinx()
            line_color = '#EA4335' 
            ax2.plot(labels, cumulative_percent, color=line_color, marker='o', linewidth=2, label='Cumm Rej %')
            ax2.set_ylim(0, 110)
            ax2.yaxis.set_major_formatter(mtick.PercentFormatter())

            # Add percentage labels to the line chart
            for i in range(len(labels)):
                ax2.text(i, cumulative_percent[i] + 3, f'{cumulative_percent[i]:.1f}%', 
                         ha='center', va='bottom', color=line_color, fontweight='bold', fontsize=8)

            # Title and formatting
            plt.title('Defect Pareto Analysis', fontsize=16)
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            ax1.spines['top'].set_visible(False)
            ax2.spines['top'].set_visible(False)

            # Legend
            lines_1, labels_1 = ax1.get_legend_handles_labels()
            lines_2, labels_2 = ax2.get_legend_handles_labels()
            ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left', bbox_to_anchor=(1.05, 0.5))

            plt.tight_layout()
            
            # 3. Display Chart to User
            st.pyplot(fig)
            st.balloons() # Add a fun little animation when it works!
            
    except Exception as e:
        st.error(f"Oops! Something went wrong reading the file. Error: {e}")
