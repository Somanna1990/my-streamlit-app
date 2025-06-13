import streamlit as st
import subprocess
import threading
import time
import os
import sys
import io
import json
from datetime import datetime
import shutil
import socket

# Function to get local IP address
def get_local_ip():
    try:
        # Get the local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return "127.0.0.1"

# Add the project directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from compliance_pipeline import run_compliance_pipeline

# Configure the page
st.set_page_config(
    page_title="Grant Thornton CPC Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "CPC Gap Analysis Tool - Version 9\nAI-powered compliance analysis system"
    }
)

# Load custom CSS
with open(os.path.join(os.path.dirname(__file__), "assets", "style.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Global variables to track process state
process_running = False
process_output = []
process_status = "Ready"
process_progress = 0
relevant_document_count = 0
json_result_path = None
excel_result_path = None
consolidated_excel_path = None

# Pipeline stages and their progress
pipeline_stages = [
    {"name": "Document Processing", "progress": 0, "status": "Pending", "emoji": "📄"},
    {"name": "Document Validation", "progress": 0, "status": "Pending", "emoji": "✅"},
    {"name": "Phase 1: Screening Regulations", "progress": 0, "status": "Pending", "emoji": "🔎"},
    {"name": "Phase 2: Reasoning", "progress": 0, "status": "Pending", "emoji": "🧠"},
    {"name": "JSON Results", "progress": 0, "status": "Pending", "emoji": "📊"},
    {"name": "Excel Conversion", "progress": 0, "status": "Pending", "emoji": "📈"},
    {"name": "Consolidated Report", "progress": 0, "status": "Pending", "emoji": "📑"}
]

# Define simplified log messages for user understanding
def simplify_log_message(line):
    """Convert technical log messages to user-friendly messages"""
    global relevant_document_count
    if not line:
        return None
        
    # Processing documents
    if "Processing Documents" in line:
        update_stage_progress(0, 10, "In Progress")  # Start document processing
        return "🔄 Starting document processing..."
    elif "Processed" in line and "documents" in line:
        update_stage_progress(0, 100, "Complete")  # Complete document processing
        return f"📄 {line}"
        
    # Validation
    elif "Validating Documents" in line:
        update_stage_progress(1, 10, "In Progress")  # Start validation
        return "🔄 Starting document validation..."
    elif ": Relevant -" in line:
        update_stage_progress(1, None)  # Increment validation progress
        # Update relevant document count
        relevant_document_count += 1
        return f"✅ Found relevant document: {line.split(':')[0].strip()}"
    elif ": Not relevant -" in line:
        update_stage_progress(1, None)  # Increment validation progress
        return f"❌ Skipping non-relevant document: {line.split(':')[0].strip()}"
    elif "Found" in line and "relevant documents" in line:
        update_stage_progress(1, 100, "Complete")  # Complete validation
        # Extract relevant document count if not already set
        if relevant_document_count == 0:
            try:
                count = int(line.split("Found")[1].split("relevant")[0].strip())
                relevant_document_count = count
            except:
                pass
        return f"📋 {line}"
        
    # Analysis
    elif "Analyzing Compliance" in line:
        update_stage_progress(2, 10, "In Progress")  # Start Phase 1: Screening
        return "🔄 Starting compliance analysis..."
    elif "Phase 1:" in line and "checking which regulations apply" in line.lower():
        update_stage_progress(2, 50, "In Progress")  # Update Phase 1: Screening
        return "🔎 Phase 1: Screening which regulations apply to documents"
    elif "Screening regulations:" in line:
        # Extract percentage from line like "Screening regulations: 64%"
        try:
            percent = int(line.split('%')[0].split(':')[-1].strip())
            update_stage_progress(2, percent, "In Progress")
            return f"🔎 Screening regulations: {percent}% complete"
        except:
            update_stage_progress(2, None)  # Just increment if parsing fails
            return "🔎 Screening regulations in progress"
    elif "Phase 2:" in line and "detailed compliance analysis" in line.lower():
        update_stage_progress(2, 100, "Complete")  # Complete Phase 1: Screening
        update_stage_progress(3, 30, "In Progress")  # Start Phase 2: Reasoning
        return "🧠 Phase 2: Performing detailed compliance reasoning"
    elif "Analyzing document:" in line:
        update_stage_progress(3, None)  # Increment Phase 2: Reasoning progress
        return f"🔍 Analyzing: {line.split('Analyzing document:')[1].strip()}"
    elif "Reasoning progress:" in line or "Detailed analysis:" in line:
        # Extract percentage from line like "Reasoning progress: 45%" or "Detailed analysis: 45%"
        try:
            percent = int(line.split('%')[0].split(':')[-1].strip())
            update_stage_progress(3, percent, "In Progress")
            return f"🧠 Reasoning progress: {percent}% complete"
        except:
            update_stage_progress(3, None)  # Just increment if parsing fails
            return "🧠 Reasoning in progress"
    elif "Saved compliance analysis results" in line:
        update_stage_progress(3, 100, "Complete")  # Complete Phase 2: Reasoning
        update_stage_progress(4, 100, "Complete")  # Complete JSON results
        return "💾 Saved analysis results"
        
    # Report generation
    elif "Converting to Excel" in line:
        update_stage_progress(5, 50, "In Progress")  # Start Excel conversion
        return "🔄 Converting results to Excel..."
    elif "Excel report generated successfully" in line:
        update_stage_progress(5, 100, "Complete")  # Complete Excel conversion
        return "📊 Excel report generated successfully"
    elif "Generating Consolidated Report" in line:
        update_stage_progress(6, 50, "In Progress")  # Start consolidated report
        return "🔄 Creating consolidated report..."
    elif "Consolidated report generated successfully" in line:
        update_stage_progress(6, 100, "Complete")  # Complete consolidated report
        return "📑 Consolidated report created successfully"
    elif "Analysis Complete" in line:
        # Ensure all stages are complete
        for i in range(len(pipeline_stages)):
            update_stage_progress(i, 100, "Complete")
        return "🎉 Analysis Complete! Reports are ready."
        
    # Default: return the original line
    return line

def update_stage_progress(stage_index, progress=None, status=None):
    """Update progress for a specific pipeline stage"""
    global process_progress
    
    # Update status if provided
    if status is not None:
        pipeline_stages[stage_index]["status"] = status
    
    # Update progress if provided
    if progress is not None:
        pipeline_stages[stage_index]["progress"] = progress
    elif pipeline_stages[stage_index]["progress"] < 100 and pipeline_stages[stage_index]["status"] == "In Progress":
        # Increment progress by a small amount (1-3%) for more granular updates
        import random
        increment = random.randint(1, 3)  # Random increment between 1-3%
        pipeline_stages[stage_index]["progress"] += increment
        pipeline_stages[stage_index]["progress"] = min(pipeline_stages[stage_index]["progress"], 95)  # Cap at 95% until complete
    
    # Calculate overall progress based on all stages
    # Weight the stages according to their typical duration/importance
    weights = [0.05, 0.1, 0.25, 0.3, 0.1, 0.1, 0.1]  # Weights sum to 1.0
    weighted_progress = sum(stage["progress"] * weights[i] for i, stage in enumerate(pipeline_stages))
    process_progress = int(weighted_progress)

# Functions for document management
def save_uploaded_file(uploaded_file):
    """Save uploaded file to the compliance documents folder"""
    # Create directory if it doesn't exist
    upload_dir = os.path.join(os.getcwd(), 'Input', 'Compliance Documents')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def delete_document(filename):
    """Delete a document from the compliance documents folder"""
    file_path = os.path.join(os.getcwd(), 'Input', 'Compliance Documents', filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def get_document_list():
    """Get list of documents in the compliance documents folder"""
    input_dir = os.path.join(os.getcwd(), 'Input', 'Compliance Documents')
    if not os.path.exists(input_dir):
        return []
    
    # Get all PDF files with their modification times and sizes
    files = []
    for f in os.listdir(input_dir):
        if f.endswith('.pdf'):
            file_path = os.path.join(input_dir, f)
            size_kb = os.path.getsize(file_path) / 1024
            mod_time = os.path.getmtime(file_path)
            mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
            files.append({
                'name': f,
                'size': f"{size_kb:.1f} KB",
                'date': mod_date
            })
    
    # Sort by most recently modified
    files.sort(key=lambda x: os.path.getmtime(os.path.join(input_dir, x['name'])), reverse=True)
    return files

def run_analysis_thread(skip_validation=False, clean_cache=False):
    """Run the analysis in a separate thread and capture output"""
    global process_running, process_output, process_status, process_progress
    global json_result_path, excel_result_path, consolidated_excel_path
    global relevant_document_count
    
    # Reset state
    process_running = True
    process_output = []
    process_status = "Starting analysis..."
    process_progress = 0
    relevant_document_count = 0
    
    try:
        # Redirect stdout to capture output
        import io
        from contextlib import redirect_stdout
        
        # Create a custom output capture that also updates our UI
        output_capture = io.StringIO()
        
        def update_progress(line):
            global process_status, process_progress, document_count, relevant_document_count
            
            # Update progress based on output lines
            if "=== Step 1: Processing Documents ===" in line:
                process_status = "Processing documents"
                process_progress = 10
                
            elif "Processed" in line and "documents" in line:
                process_progress = 15
                # Extract number of documents processed
                try:
                    num_docs = int(line.split("Processed")[1].split("documents")[0].strip())
                    document_count = num_docs
                    process_status = f"Processed {num_docs} documents"
                except:
                    pass
                    
            elif "=== Step 2: Validating Documents ===" in line:
                process_status = "Validating documents for relevance"
                process_progress = 20
                
            elif "Found" in line and "relevant documents" in line:
                process_progress = 25
                # Extract number of relevant documents
                try:
                    num_docs = int(line.split("Found")[1].split("relevant")[0].strip())
                    relevant_document_count = num_docs
                    process_status = f"Found {num_docs} relevant documents"
                except:
                    pass
                    
            elif "=== Step 3: Analyzing Compliance ===" in line:
                process_status = "Analyzing compliance against regulations"
                process_progress = 30
                
            elif "Phase 1:" in line:
                process_status = "Checking which regulations apply"
                process_progress = 40
                
            elif "Phase 2:" in line:
                process_status = "Performing detailed compliance analysis"
                process_progress = 60
                
            elif "Saved compliance analysis results" in line:
                process_status = "Saving analysis results"
                process_progress = 75
                
            elif "=== Step 5:" in line:
                process_status = "Creating Excel report"
                process_progress = 80
                
            elif "Excel report generated successfully" in line:
                process_progress = 85
                process_status = "Excel report created successfully"
                
            elif "=== Step 6:" in line:
                process_status = "Creating consolidated summary report"
                process_progress = 90
                
            elif "Consolidated report generated successfully" in line:
                process_progress = 95
                process_status = "Consolidated report created successfully"
                
            elif "=== Analysis Complete ===" in line:
                process_status = "Analysis complete"
                process_progress = 100
            
            # Add the line to our output log
            process_output.append(line)
        
        # Custom stdout handler
        class TeeIO(io.StringIO):
            def write(self, s):
                super().write(s)
                if s.strip():  # Only process non-empty lines
                    update_progress(s.strip())
                return len(s)
        
        # Run the analysis with our custom output capture
        with redirect_stdout(TeeIO()):
            # Call the main pipeline function
            json_path, excel_path, consolidated_path = run_compliance_pipeline(skip_validation=skip_validation, clean_cache=clean_cache)
            
        process_status = "Completed"
        process_progress = 100
        
    except Exception as e:
        process_status = f"Error: {str(e)}"
        process_output.append(f"ERROR: {str(e)}")
    finally:
        process_running = False

def main():
    # Display Grant Thornton branding
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # In a production environment, replace this with an actual image
        st.markdown("""
        <div style="background-color: #5a287d; padding: 10px; border-radius: 5px; text-align: center;">
            <h3 style="color: white; margin: 0;">Grant Thornton</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <h1 style="color: #5a287d;">AI-Powered CPC Compliance Analysis</h1>
        <p style="color: #333333;">Grant Thornton solution for AIB life</p>
        """, unsafe_allow_html=True)
    
    # Add a divider
    st.markdown("<hr style='margin: 15px 0; border-color: #5a287d;'>", unsafe_allow_html=True)
    
    # Sidebar for configuration
    st.sidebar.markdown("<h3 style='color: #5a287d;'>Configuration</h3>", unsafe_allow_html=True)
    
    skip_validation = st.sidebar.checkbox("Skip Document Validation", value=False, 
                                         help="Skip the document validation step and analyze all documents")
    
    clean_cache = st.sidebar.checkbox("Clean Cache", value=False,
                                     help="Clear the cache and perform fresh analysis")
    
    # Add more configuration options
    st.sidebar.markdown("<h3 style='color: #5a287d;'>Advanced Options</h3>", unsafe_allow_html=True)
    show_debug = st.sidebar.checkbox("Show Debug Information", value=False,
                                   help="Show additional debug information in the output")
    
    # Display network access information
    st.sidebar.markdown("<h3 style='color: #5a287d;'>Network Access</h3>", unsafe_allow_html=True)
    local_ip = get_local_ip()
    st.sidebar.info(f"💻 **Local Network Access:** http://{local_ip}:8501")
    st.sidebar.markdown("""
    **To make this app publicly accessible:**
    
    1. **For local network access:**
       - Connect devices to the same network
       - Access using the local IP address above
    
    2. **For internet access (options):**
       - Use port forwarding on your router (port 8501)
       - Deploy to Streamlit Cloud: https://streamlit.io/cloud
       - Use a reverse proxy service
    
    Run with: `streamlit run frontend_app.py --server.address=0.0.0.0`
    """)
    
    # Add a divider
    st.sidebar.markdown("<hr style='margin: 15px 0; border-color: #5a287d;'>", unsafe_allow_html=True)
    
    # Add system information
    st.sidebar.markdown("<h3 style='color: #5a287d;'>About</h3>", unsafe_allow_html=True)
    st.sidebar.info("""
    **CPC Gap Analysis Tool v9**
    
    AI-powered compliance analysis system for financial services documents
    
    - Analyzes documents against CPC regulations
    - Uses Claude AI models for analysis
    - Generates detailed compliance reports
    """)
    
    # Document management section
    st.markdown("<h2 style='color: #5a287d;'>Document Management</h2>", unsafe_allow_html=True)
    
    # Create tabs for upload and manage
    doc_tab1, doc_tab2 = st.tabs(["📤 Upload Documents", "📋 Manage Documents"])
    
    with doc_tab1:
        st.write("Upload additional documents for compliance analysis")
        uploaded_files = st.file_uploader("Upload PDF documents", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            if st.button("Add Documents", use_container_width=True):
                for uploaded_file in uploaded_files:
                    file_path = save_uploaded_file(uploaded_file)
                    st.success(f"Added: {uploaded_file.name}")
    
    with doc_tab2:
        # Get document list
        documents = get_document_list()
        
        # Document count and search
        st.write(f"**{len(documents)} documents available for analysis**")
        
        if documents:
            # Add search functionality
            search_term = st.text_input("Search documents", placeholder="Enter filename to search")
            
            # Filter documents based on search term
            if search_term:
                filtered_docs = [doc for doc in documents if search_term.lower() in doc['name'].lower()]
            else:
                filtered_docs = documents
            
            # Pagination
            docs_per_page = 5
            total_pages = max(1, (len(filtered_docs) + docs_per_page - 1) // docs_per_page)
            
            col1, col2, col3 = st.columns([2, 3, 2])
            with col2:
                page = st.selectbox("Page", options=range(1, total_pages + 1), index=0)
            
            start_idx = (page - 1) * docs_per_page
            end_idx = min(start_idx + docs_per_page, len(filtered_docs))
            page_docs = filtered_docs[start_idx:end_idx]
            
            # Display documents with delete buttons
            for doc in page_docs:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.write(f"**{doc['name']}**")
                with col2:
                    st.write(f"Size: {doc['size']}")
                with col3:
                    st.write(f"Modified: {doc['date']}")
                with col4:
                    if st.button("🗑️", key=f"delete_{doc['name']}", help=f"Delete {doc['name']}"):
                        if delete_document(doc['name']):
                            st.rerun()  # Refresh the page to update the document list
            
            if not page_docs:
                st.info("No documents match your search criteria")
        else:
            st.info("No documents available. Upload documents using the Upload tab.")
    
    # Document stats section
    st.markdown("<h3 style='color: #5a287d;'>Document Statistics</h3>", unsafe_allow_html=True)
    
    # Count input documents
    input_dir = os.path.join(os.getcwd(), 'Input', 'Compliance Documents')
    input_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')] if os.path.exists(input_dir) else []
    
    # Display document counts
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents for Analysis", len(input_files))
    with col2:
        # Only show relevant documents if validation is complete and we have relevant docs
        if relevant_document_count > 0:
            st.metric("Relevant Documents", relevant_document_count)
        elif pipeline_stages[1]["status"] == "Complete":
            # If validation is complete but no relevant documents found
            st.metric("Relevant Documents", "0")
        elif pipeline_stages[1]["status"] == "In Progress":
            # If validation is in progress
            st.metric("Documents Being Validated", f"{pipeline_stages[1]['progress']}%")
        else:
            # Before validation starts
            st.metric("Documents Ready", len(input_files))
    
    # Run analysis section
    st.markdown("<h2 style='color: #5a287d;'>Run Analysis</h2>", unsafe_allow_html=True)
    
    # Button to start analysis
    if st.button("Run CPC Gap Analysis", use_container_width=True, type="primary", disabled=process_running):
        # Start the analysis in a separate thread
        thread = threading.Thread(target=run_analysis_thread, args=(skip_validation, clean_cache))
        thread.daemon = True
        thread.start()
    
    # Status and progress section
    st.markdown("<h2 style='color: #5a287d;'>Process Output</h2>", unsafe_allow_html=True)
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    completion_metric = st.empty()
    
    # Stage progress display
    st.markdown("<h2 style='color: #5a287d;'>Analysis Pipeline</h2>", unsafe_allow_html=True)
    stage_containers = [st.empty() for _ in range(len(pipeline_stages))]
    
    # Simple output area with progress bar and current activity
    output_container = st.container()
    log_expander = st.expander("View Activity Log")
    results_container = st.container()
    
    # Use session state to track if analysis is running
    if 'analysis_started' not in st.session_state:
        st.session_state.analysis_started = False
    
    # Update UI once initially, then use rerun for updates when process is running
    def update_ui():
        # Update status and progress bar
        with status_placeholder.container():
            st.subheader("Current Activity")
            st.info(f"**{process_status}**")
            progress_bar.progress(process_progress/100)  # Convert to 0-1 range for progress bar
            
            if process_progress == 100:
                st.success("Analysis completed successfully!")
        
        # Update completion metric
        with completion_metric.container():
            st.metric("Overall Completion", f"{process_progress}%")
            
        # Update stage progress displays
        for i, stage in enumerate(pipeline_stages):
            with stage_containers[i].container():
                # Create columns for stage info and progress bar
                col1, col2 = st.columns([3, 1])
                
                # Status color
                status_color = "gray"
                if stage["status"] == "Complete":
                    status_color = "green"
                elif stage["status"] == "In Progress":
                    status_color = "blue"
                elif stage["status"] == "Error":
                    status_color = "red"
                
                # Display stage name and progress
                with col1:
                    st.markdown(f"{stage['emoji']} **{stage['name']}** - {stage['status']}")
                with col2:
                    st.metric("Progress", f"{stage['progress']}%", label_visibility="collapsed")
        
        # Show simplified log in expander
        with log_expander:
            if process_output:
                # Create simplified log for user understanding
                simplified_log = []
                for line in process_output:
                    simple_msg = simplify_log_message(line)
                    if simple_msg:
                        simplified_log.append(simple_msg)
                
                # Display only unique messages to avoid repetition
                unique_messages = []
                for msg in simplified_log:
                    if msg not in unique_messages:
                        unique_messages.append(msg)
                
                # Show the last 10 unique messages
                for msg in unique_messages[-10:]:
                    st.write(msg)
            else:
                st.text("No activity yet...")
        
        # Show results when complete
        with results_container:
            if process_progress == 100:
                results_path = os.path.join(os.getcwd(), "output", "enhanced_document_analysis")
                st.header("Results")
                
                col1, col2 = st.columns(2)
                with col1:
                    if os.path.exists(os.path.join(results_path, "compliance_analysis_report.xlsx")):
                        excel_path = os.path.join(results_path, "compliance_analysis_report.xlsx")
                        st.download_button(
                            label="Download Detailed Report",
                            data=open(excel_path, "rb").read(),
                            file_name="compliance_analysis_report.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                
                with col2:
                    if os.path.exists(os.path.join(results_path, "consolidated_compliance_report.xlsx")):
                        consol_path = os.path.join(results_path, "consolidated_compliance_report.xlsx")
                        st.download_button(
                            label="Download Consolidated Report",
                            data=open(consol_path, "rb").read(),
                            file_name="consolidated_compliance_report.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
    
    # Initial UI update
    update_ui()
    
    # If process is running, set up auto-refresh
    if process_running:
        st.session_state.analysis_started = True
        time.sleep(0.2)  # Small delay to avoid excessive CPU usage
        st.experimental_rerun()  # Rerun the app to refresh the UI

if __name__ == "__main__":
    main()
