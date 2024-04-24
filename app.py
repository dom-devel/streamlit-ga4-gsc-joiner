

import streamlit as st
import pandas as pd


def guess_column(columns, search_string):
    for col in columns:
        if search_string.lower() in col.lower():
            return col
    return None


def process_data(df, url_col, device_col, country_col, date_col, clicks_col, impressions_col, breakdown_columns, include_date):
    # Fill nulls in clicks and impressions columns with 0
    df[clicks_col] = df[clicks_col].fillna(0)
    df[impressions_col] = df[impressions_col].fillna(0)

    # Base groupby columns
    groupby_columns = [url_col, country_col, device_col]
    if include_date:
        groupby_columns.append(date_col)

    # Calculate total_clicks_by_page
    df['total_clicks_by_page'] = df.groupby(groupby_columns)[clicks_col].transform('sum')

    # Calculate percentage_breakdown based on clicks
    df['percentage_breakdown'] = df.apply(
        lambda row: row[clicks_col] / row['total_clicks_by_page'] if row['total_clicks_by_page'] > 0 else 0,
        axis=1
    )

    # Calculate total_x_per_page for each breakdown metric
    for col in breakdown_columns:
        total_col_name = f'total_{col}_per_page'
        df[total_col_name] = df.groupby(groupby_columns)[col].transform('sum')
        df[f'{col}_estimated'] = df['percentage_breakdown'] * df[col]

    # Add a row_number column based on impressions within each group
    df['row_number'] = df.groupby(groupby_columns)[impressions_col].rank(method='first', ascending=False)

    # Adjust percentage_breakdown where there are no clicks but other metrics > 0
    for _, group in df.groupby(groupby_columns):
        if group[clicks_col].sum() == 0 and any(group[col].sum() > 0 for col in breakdown_columns):
            df.loc[group.index, 'percentage_breakdown'] = (group['row_number'] == 1).astype(int)
            for col in breakdown_columns:
                df.loc[group.index, f'{col}_estimated'] = df.loc[group.index, 'percentage_breakdown'] * group[col]

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

        query_col = st.selectbox('Select the column for Query', df.columns,
                                   index=df.columns.tolist().index(guess_column(df.columns, 'query')))

        include_date = st.checkbox('Include Date column', value=True)
        date_col = None
        if include_date:
            date_col = st.selectbox('Select the column for Date', df.columns,
                                    index=df.columns.tolist().index(guess_column(df.columns, 'date')))

        clicks_col = st.selectbox('Select the column for Clicks', df.columns,
                                  index=df.columns.tolist().index(guess_column(df.columns, 'clicks')))
        impressions_col = st.selectbox('Select the column for Impressions', df.columns,
                                  index=df.columns.tolist().index(guess_column(df.columns, 'impressions')))

        st.markdown("""
        ### Breakdown Columns
        Select the columns you want to use for breakdown by query.
        The app will estimate the values for these columns based on the percentage breakdown.
        """)

        # Filter columns to exclude specific columns from being selected for breakdown
        excluded_columns = {url_col, device_col, country_col, date_col, clicks_col, impressions_col, query_col}
        breakdown_options = [col for col in df.columns if col not in excluded_columns]

        # Get the list of columns for breakdown by query
        breakdown_columns = st.multiselect('Select columns for breakdown by query', breakdown_options)

        if breakdown_columns:
            # Process the data
            processed_df = process_data(df, url_col, device_col, country_col, date_col, clicks_col,impressions_col,
                                        breakdown_columns, include_date)

            # Checkbox to decide grouping without date
            group_without_date = st.checkbox('Group data by summing metrics and exclude date', value=True)

            # Conditional grouping based on checkbox
            if group_without_date:
                # Define grouping columns excluding the date column
                group_columns = [url_col, country_col, device_col, query_col]  # Only dimension columns for grouping

                # Sum the metrics without grouping by them
                aggregation_functions = {clicks_col: 'sum'}  # Ensure clicks are summed
                for col in breakdown_columns:
                    aggregation_functions[f'{col}_estimated'] = 'sum'  # Sum estimated columns

                # Group by the defined columns and apply aggregation functions
                processed_df = processed_df.groupby(group_columns).agg(aggregation_functions).reset_index()

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