import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


df = pd.read_parquet("OC_sales_DE_pseudonymized.parquet")
print(df.head())


#NOTIZEN AUS DER ERSTEN Q&A

#stakeholder 
#operations - planning in the plant - throughput - revenue
#sales for better planning and predicting - customers are willing to pay more for specific delivery dates
#main goal is to improve the planning process

#predicting and optimizing the sequence of production

#assume one machine with one fillrate

#threshold as high as possible - lower limit not so easy to provide - aim for span of 5 days to customer - fill rate should allow for that above 80% percent - but also allow smaller batches to be faster

#assuming one central plant in germany - if challenge is too easy can add more sites


#oders mit so wenig machinen wie möglich nutzen - planungssicherheit  