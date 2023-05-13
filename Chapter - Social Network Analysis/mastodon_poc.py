# -*- coding: utf-8 -*-
from mastodon import Mastodon
import pandas as pd

ACCESS_TOKEN = "YOUR-API-KEY"
BASE_URL = "https://defcon.social"
m = Mastodon(access_token=ACCESS_TOKEN, api_base_url=BASE_URL)

timeline_data = m.timeline(timeline="public")

df = pd.DataFrame(timeline_data)
df["id"] = df["id"].astype(dtype=str)
df["in_reply_to_id"] = df["in_reply_to_id"].astype(dtype=str)
df["in_reply_to_account_id"] = df["in_reply_to_account_id"].astype(dtype=str)

print(df.info())
df.to_csv("mastodon_timeline.csv")
