import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style="dark")

@st.cache_data
def create_weekly_revenue_df(df): 
  weekly_revenue_df = df.resample(rule="W", on="order_purchase_timestamp").agg({
     "order_id" : "nunique",
     "payment_value" : "sum"
  })
  weekly_revenue_df = weekly_revenue_df.reset_index()
  return weekly_revenue_df

@st.cache_data
def create_sum_revenue_items_df(df):
    sum_revenue_items_df = df.groupby("product_category_name")['payment_value'].sum().sort_values(ascending=False).reset_index()
    sum_revenue_items_df.rename(columns={"payment_value" : "total_revenue"}, inplace=True)
    return sum_revenue_items_df

@st.cache_data
def create_payment_revenue_df(df):
   payment_revenue_df = df.groupby("payment_type")["payment_value"].sum().sort_values(ascending=False).reset_index()
   return payment_revenue_df

@st.cache_data
def create_rfm_df(df, recent_date):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_approved_at": "max",
        "order_id": "nunique",
        "payment_value": "sum"
    })

    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df

def load_main_data():
    df = pd.read_csv("dashboard/main_data.csv")
    datetime_columns = [
      "order_purchase_timestamp",
      "order_approved_at",
      "order_delivered_customer_date",
      "order_delivered_carrier_date",
      "order_estimated_delivery_date"
   ]
    df.sort_values(by="order_purchase_timestamp", inplace=True)
    for column in datetime_columns:
      df[column] = pd.to_datetime(df[column], errors="coerce")
    return df

df = load_main_data()

recent_date = df["order_purchase_timestamp"].max()
min_date = df["order_purchase_timestamp"].min()
max_date = df["order_purchase_timestamp"].max()

with st.sidebar:
   st.image("https://raw.githubusercontent.com/AqilzFracs/logo/refs/heads/main/logo_qshop.jpg")
   start_date, end_date = st.date_input(
        label='Time Span',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
  
main_df = df[(df["order_approved_at"] >= str(start_date)) & 
            (df["order_approved_at"] <= str(end_date))]

weekly_revenue_df = create_weekly_revenue_df(main_df)
sum_revenue_items_df = create_sum_revenue_items_df(main_df)
payment_revenue_df = create_payment_revenue_df(main_df)
rfm_df = create_rfm_df(main_df, recent_date)


st.title("Welcome to Qil Shop Dashboard!")
st.header("Weekly Revenue")

col1, col2 = st.columns(2)

with col1:
  total_orders = weekly_revenue_df.order_id.sum()
  st.metric("Total orders", value=total_orders)
with col2:
  total_revenue = format_currency(weekly_revenue_df.payment_value.sum(), "BRL", locale="pt_BR")
  st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16,8))
ax.plot(
  weekly_revenue_df["order_purchase_timestamp"],
  weekly_revenue_df["payment_value"],
  marker='o', 
  linewidth=2,
  color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)

# Product performance
st.subheader("Best & Worst Performing Product")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="total_revenue", y="product_category_name", data=sum_revenue_items_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)
for i in ax[0].patches:
    ax[0].text(i.get_width() + 0.2, i.get_y() + i.get_height()/2, 
               f'{int(i.get_width())}', ha='right', va='center', fontsize=12, color='black', weight='bold')

sns.barplot(x="total_revenue", y="product_category_name", data=sum_revenue_items_df.sort_values(by="total_revenue", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)
for i in ax[1].patches:
    ax[1].text(i.get_width() - 0.2, i.get_y() + i.get_height()/2, 
               f'{int(i.get_width())}', ha='left', va='center', fontsize=12, color='black', weight='bold')

st.pyplot(fig)

st.subheader("Revenue Based of Payment type")

fig, ax = plt.subplots(figsize=(16, 8))
sns.barplot(
    y="payment_value", 
    x="payment_type",
    data=payment_revenue_df.sort_values(by="payment_value", ascending=False),
    palette=colors,
    ax=ax
)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='x', labelsize=35)
ax.tick_params(axis='y', labelsize=30)
for bar in ax.patches:
    value = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,  # X-coordinate: center of the bar
        value,  # Y-coordinate: height of the bar
        f'{value:,.2f}',  # The text to display (formatted payment_value)
        ha='center',  # Horizontal alignment at center of the bar
        va='bottom',  # Text displayed just above the bar
        fontsize=25,  # Font size for the labels
        color='black'  # Text color
    )
st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)

rfm_df["sorted_customer_id"] = rfm_df["customer_id"].apply(lambda x: x[:5])
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y="recency", x="sorted_customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)

sns.barplot(y="frequency", x="sorted_customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)

sns.barplot(y="monetary", x="sorted_customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)

st.pyplot(fig)

st.caption('Copyright by AqilzFracs 2024')