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
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Click here to download processed data (.csv)</a>'
    return href

def get_txt_download_link(df, filename="processed_data.txt"):
    """
    Function to convert the processed DataFrame into a TXT download link.
    """
    txt = df.to_csv(index=False, sep='\t')
    b64 = base64.b64encode(txt.encode()).decode()
    href = f'<a href="data:file/text;base64,{b64}" download="{filename}">Click here to download processed data (.txt)</a>'
    return href

# --- Streamlit App ---

st.title("📄 Duplicate Data Remover Tool")
st.write("Upload a CSV, TXT, or XLSX file. This tool will remove duplicate rows and let you download the cleaned file.")

# 1. File Uploader
# --- CHANGE 1: Added 'xlsx' to the allowed types ---
uploaded_file = st.file_uploader("Choose your CSV, TXT, or XLSX file", type=["csv", "txt", "xlsx"])

if uploaded_file is not None:
    try:
        # Check the file extension
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # Read the file based on its extension
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
            
        elif file_extension == 'txt':
            df = pd.read_csv(uploaded_file, sep='\t')
            
        # --- CHANGE 2: Added logic to read .xlsx files ---
        elif file_extension == 'xlsx':
            # This requires the 'openpyxl' library
            df = pd.read_excel(uploaded_file)

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
            
            st.subheader("Preview of cleaned data (first 10 rows)")
            st.dataframe(df_cleaned.head(10))

            st.subheader("Download Links")
            
            csv_link = get_csv_download_link(df_cleaned, "cleaned_data.csv")
            st.markdown(csv_link, unsafe_allow_html=True)
            
            txt_link = get_txt_download_link(df_cleaned, "cleaned_data.txt")
            st.markdown(txt_link, unsafe_allow_html=True)
            
            st.session_state['cleaned_df'] = df_cleaned

    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
        st.error("Please ensure the file is in the correct format and not corrupted. If using XLSX, make sure you have 'openpyxl' installed.")
