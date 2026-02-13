import streamlit as st
import pandas as pd
import re

from analysis import load_data, suggest_prompts, ask_llm, run_code

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="AI Business Analyst",
    page_icon="📊",
    layout="wide"
)

# ================= TITLE =================
st.title("📊 AI Business Analyst Dashboard")
st.markdown("**Upload your data file (CSV, Excel, JSON) and get AI-powered insights!**")

# ================= FILE UPLOADER =================
uploaded_file = st.file_uploader(
    "📁 Upload your data file",
    type=["csv", "xlsx", "xls", "json"],
    help="Supported formats: CSV, Excel (.xlsx, .xls), JSON"
)

# ================= MAIN APPLICATION =================
if uploaded_file:
    try:
        # File load karo
        with st.spinner("Loading data..."):
            df = load_data(uploaded_file)
        
        st.success(f"✅ Dataset Loaded Successfully! ({len(df)} rows, {len(df.columns)} columns)")
        
        # Dataset preview
        st.subheader("📋 Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Dataset info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", len(df))
        with col2:
            st.metric("Total Columns", len(df.columns))
        with col3:
            st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        
        # Column info expander
        with st.expander("📊 Column Information"):
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.values,
                'Non-Null Count': df.count().values,
                'Null Count': df.isnull().sum().values
            })
            st.dataframe(col_info, use_container_width=True)

        # ================= SIDEBAR =================
        st.sidebar.header("📌 Suggested Business Queries")
        suggestions = suggest_prompts(df)

        selected_prompt = st.sidebar.selectbox(
            "Choose a suggestion",
            ["-- Select --"] + suggestions
        )

        # ================= USER INPUT =================
        user_prompt = st.text_area(
            "💬 Or write your own custom query",
            value="" if selected_prompt == "-- Select --" else selected_prompt,
            height=100,
            placeholder="Example: Show top 5 products by revenue"
        )

        # ================= RUN ANALYSIS BUTTON =================
        if st.button("🚀 Run Analysis", type="primary"):
            if not user_prompt or user_prompt.strip() == "":
                st.warning("⚠️ Please enter a query or select from suggestions!")
            else:
                with st.spinner("🤖 AI is analyzing your data..."):
                    # LLM se code generate karo
                    llm_response = ask_llm(user_prompt)
                    
                    # Code extract karo
                    match = re.search(r"```python(.*?)```", llm_response, re.DOTALL)
                    
                    if not match:
                        st.error("❌ Invalid response from AI. Could not extract Python code.")
                        st.code(llm_response, language="text")
                    else:
                        code = match.group(1).strip()
                        
                        # Generated code dikhao
                        with st.expander("🔍 View Generated Code"):
                            st.code(code, language="python")
                        
                        # Code execute karo
                        with st.spinner("⚙️ Executing code..."):
                            output = run_code(df, code)
                        
                        # Result dikhao
                        st.subheader("📊 Analysis Results")
                        
                        if output["type"] == "dataframe":
                            st.dataframe(output["df"], use_container_width=True)
                            
                            # Download button
                            csv = output["df"].to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download Results as CSV",
                                data=csv,
                                file_name="analysis_results.csv",
                                mime="text/csv"
                            )
                        
                        elif output["type"] == "image":
                            st.image(output["path"], use_column_width=True)
                        
                        else:
                            st.text(output["output"])
    
    except Exception as e:
        st.error(f"❌ Error loading file: {str(e)}")
        st.info("💡 Tip: Make sure your file is in correct format (CSV, Excel, or JSON)")

else:
    # Instructions jab file upload nahi hui
    st.info("👆 Please upload a file to get started!")
    
    st.markdown("""
    ### 📖 How to Use:
    1. **Upload** your data file (CSV, Excel, or JSON)
    2. **Select** a suggested query or write your own
    3. **Click** "Run Analysis" button
    4. **View** AI-generated insights and visualizations
    
    ### 🎯 Supported File Types:
    - **CSV** (.csv) - Comma-separated values
    - **Excel** (.xlsx, .xls) - Microsoft Excel files
    - **JSON** (.json) - JavaScript Object Notation
    
    ### ⚡ Features:
    - 🤖 AI-powered data analysis
    - 📊 Automatic visualization generation
    - 💼 Business intelligence insights
    - 📈 Trend analysis and forecasting
    - 🎨 Interactive charts and graphs
    """)
