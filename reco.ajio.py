import streamlit as st
import pandas as pd
import base64
import io

def process_data(df):
    """
    You can put all your data processing logic here.
    For now, we are just dropping duplicate rows.
    """
    # Remove duplicate rows
    df_processed = df.drop_duplicates()
    
    # You can add more cleaning steps here, for example:
    # df_processed = df_processed.dropna() # Remove rows with empty values
    
    return df_processed

def get_csv_download_link(df, filename="processed_data.csv"):
    """
    Function to convert the processed DataFrame into a CSV download link.
    """
    # Convert DataFrame to CSV
    csv = df.to_csv(index=False)
    
    # Encode the CSV data
    b64 = base64.b64encode(csv.encode()).decode()
    
    # HTML for the download link
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Click here to download processed data (.csv)</a>'
    return href

def get_txt_download_link(df, filename="processed_data.txt"):
    """
    Function to convert the processed DataFrame into a TXT download link.
    """
    # Convert DataFrame to tab-separated text
    # You can change the separator (sep) if needed
    txt = df.to_csv(index=False, sep='\t')
    
    # Encode the data
    b64 = base64.b64encode(txt.encode()).decode()
    
    # HTML for the download link
    href = f'<a href="data:file/text;base64,{b64}" download="{filename}">Click here to download processed data (.txt)</a>'
    return href

# --- Streamlit App ---

st.title("📄 Duplicate Data Remover Tool")
st.write("Upload a CSV or TXT file, this tool will remove duplicate rows and let you download the cleaned file.")

# 1. File Uploader
# This checks the 'type' parameter to ensure only csv or txt files can be uploaded
uploaded_file = st.file_uploader("Choose your CSV or TXT file", type=["csv", "txt"])

if uploaded_file is not None:
    try:
        # Check the file extension
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # Read the file based on its extension
        if file_extension == 'csv':
            # Assuming the file is comma-separated
            df = pd.read_csv(uploaded_file)
        elif file_extension == 'txt':
            # Assuming the file is tab-separated
            # Change the separator (sep='\t') if your file uses something else (e.g., sep=';')
            df = pd.read_csv(uploaded_file, sep='\t')

        st.success("File uploaded successfully!")
        st.write("---")

        # 2. Process Data
        st.header("1. Data Processing")
        if st.button("Remove Duplicate Rows"):
            
            original_rows = len(df)
            st.write(f"Rows in original data: **{original_rows}**")

            # Call the processing function
            df_cleaned = process_data(df)
            
            cleaned_rows = len(df_cleaned)
            removed_rows = original_rows - cleaned_rows
            
            st.info(f"Rows in cleaned data: **{cleaned_rows}**")
            st.warning(f"Duplicate rows removed: **{removed_rows}**")
            
            st.write("---")

            # 3. Download Section
            st.header("2. Download Cleaned Data")
            
            # Show a preview
            st.subheader("Preview of cleaned data (first 10 rows)")
            st.dataframe(df_cleaned.head(10))

            # Download links
            st.subheader("Download Links")
            
            # CSV link
            csv_link = get_csv_download_link(df_cleaned, "cleaned_data.csv")
            st.markdown(csv_link, unsafe_allow_html=True)
            
            # TXT link
            txt_link = get_txt_download_link(df_cleaned, "cleaned_data.txt")
            st.markdown(txt_link, unsafe_allow_html=True)
            
            # Store cleaned data in session state (optional, but useful)
            st.session_state['cleaned_df'] = df_cleaned

    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
        st.error("Please ensure the file is in the correct format (CSV or TXT) and not corrupted.")
