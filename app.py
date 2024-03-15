

import streamlit as st
import pandas as pd


def guess_column(columns, search_string):
    for col in columns:
        if search_string.lower() in col.lower():
            return col
    return None


def process_data(df, url_col, device_col, country_col, date_col, clicks_col, breakdown_columns,
                 include_date):
    # Calculate total_clicks_by_page
    groupby_columns = [url_col, country_col, device_col]
    if include_date:
        groupby_columns.append(date_col)
    df['total_clicks_by_page'] = df.groupby(groupby_columns)[clicks_col].transform('sum')

    # Calculate percentage_breakdown
    df['percentage_breakdown'] = df[clicks_col] / df['total_clicks_by_page']

    # Calculate estimated columns for each breakdown column
    for col in breakdown_columns:
        df[f'{col}_estimated'] = df['percentage_breakdown'] * df[col]

    return df


def main():
    st.title('Breakdown GA4 metrics by query')

    st.markdown("""
           This app allows you to process joined GA4 and GSC data to estimate query level breakdown of things like sessions, conversions etc.:

           You can find the accompanying blog post here:

           In order to get this to work you will need to have a joined CSV file with the following columns:

           - Base data columns: URL, Device Category, Country, Date, Query, and Clicks
           - And then any metrics you want to breakdown from GA4 e.g. Sessions, Conversions etc.
           
           Upload that file here then:
           - Select the column you want to breakdown by query
           """)
    # File upload
    uploaded_file = st.file_uploader('Choose a CSV file', type='csv')

    if uploaded_file is not None:
        # Read CSV file
        df = pd.read_csv(uploaded_file)

        st.subheader('Uploaded CSV Data')
        st.write(df.head())

        st.markdown("""
        ### Column Selection
        Please select the appropriate columns for URL, Device Category, Country, Date (optional), Query, and Clicks.
        The app will attempt to guess the columns based on their names, but you can change the selection if needed.
        """)

        # Get the column names for URL, device, country, date, query, and clicks
        url_col = st.selectbox('Select the column for URL', df.columns,
                               index=df.columns.tolist().index(guess_column(df.columns, 'url')))
        device_col = st.selectbox('Select the column for Device Category', df.columns,
                                  index=df.columns.tolist().index(guess_column(df.columns, 'device')))
        country_col = st.selectbox('Select the column for Country', df.columns,
                                   index=df.columns.tolist().index(guess_column(df.columns, 'country')))

        include_date = st.checkbox('Include Date column', value=True)
        date_col = None
        if include_date:
            date_col = st.selectbox('Select the column for Date', df.columns,
                                    index=df.columns.tolist().index(guess_column(df.columns, 'date')))

        clicks_col = st.selectbox('Select the column for Clicks', df.columns,
                                  index=df.columns.tolist().index(guess_column(df.columns, 'clicks')))

        st.markdown("""
        ### Breakdown Columns
        Select the columns you want to use for breakdown by query.
        The app will estimate the values for these columns based on the percentage breakdown.
        """)

        # Get the list of columns for breakdown by query
        breakdown_columns = st.multiselect('Select columns for breakdown by query', df.columns)

        if breakdown_columns:
            # Process the data
            processed_df = process_data(df, url_col, device_col, country_col, date_col, clicks_col,
                                        breakdown_columns, include_date)

            st.subheader('Processed Data')
            st.write(processed_df.head())

            # Download the processed data as CSV
            csv = processed_df.to_csv(index=False)
            st.download_button(
                label='Download processed data as CSV',
                data=csv,
                file_name='processed_data.csv',
                mime='text/csv'
            )


if __name__ == '__main__':
    main()