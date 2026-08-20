# ================================================================================= #
# funtion to remove dupliacate from the dataset 
# ================================================================================= #

import pandas as pd

def remove_duplicate(df: pd.DataFrame):

    before_count = len(df)

    df.drop_duplicates(inplace = True)

    after_count = len(df)

    duplicate_count = before_count - after_count

    return df, duplicate_count


