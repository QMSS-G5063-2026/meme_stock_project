# Presentation Notes

## Opening

This project asks how meme-stock attention moved across three places at once:
markets, Reddit discussion, and public search interest. The app focuses on GME,
AMC, BBBY, BB, and NOK from 2019 through mid-2023.

## Demo Script

1. Open the Streamlit app and start on **Overview**.
2. Explain that the dashboard uses shared filters so every tab reflects the same
   tickers and event window.
3. Use the default January 2021 squeeze window on **Timeline**. Choose `GME` as
   the focus stock, point out the alignment between indexed price, trading
   volume, and attention, then use direct labels such as `Elon Musk tweets
   'Gamestonk!!'` to identify the major event markers.
4. In **Event Stock View**, use the OHLC, cumulative-return, return, and
   volume/spike charts to explain how the selected event window moved the stock.
5. Move to **Reddit/Text**. Emphasize the text-analysis design: mention counts,
   top terms, and sentiment are deliberately interpretable.
6. Move to **Network**. Start with the strongest-pair metric and top
   co-mentions table, then use the graph to show which tickers were discussed
   together.
7. Move to **Map**. Switch between `GameStop`, `AMC stock`, and
   `WallStreetBets`; use the top-states table to name concrete examples and
   explain that Google Trends values are relative, normalized search interest.
8. End on **Methods** and name the main limitations: Reddit coverage is focused
   on the local archive window around the January 2021 event, and Google Trends
   reports normalized relative search interest.

## Key Takeaways

- The January 2021 squeeze is the clearest event window for connecting attention
  and volatility.
- Meme stocks were discussed as a connected basket, not only as isolated tickers.
- Google Trends adds a geographic layer to a story often shown only as a price
  chart.

## Audience Caveat

Market, Reddit/text/network, and Google Trends views are backed by processed
project/API outputs. Raw Reddit ZIP files are kept local because they are too
large for GitHub, and cached Google Trends exports are included so the app stays
deployable when live collection is rate-limited.

## Final Submission Check

- Add the public Streamlit Community Cloud URL to `README.md` once deployment is
  live.
- Verify Overview, Timeline, Reddit/Text, Network, Map, Presentation, and
  Methods from the public URL.
- Confirm that direct timeline event labels, Event Stock View, top co-mentions
  summary, and top-states table are visible in the deployed app.
