# Presentation Notes

## Opening

This project asks how meme-stock attention moved across three places at once:
markets, Reddit discussion, and public search interest. The app focuses on GME,
AMC, BBBY, BB, and NOK from 2019 through mid-2023.

## Demo Script

1. Open the Streamlit app and start on **Overview**.
2. Explain that the dashboard uses shared filters so every tab reflects the same
   tickers and event window.
3. Use the default January 2021 squeeze window on **Timeline**. Point out the
   alignment between indexed prices, trading volume, and attention.
4. Move to **Reddit/Text**. Emphasize the text-analysis design: mention counts,
   top terms, and sentiment are deliberately interpretable.
5. Move to **Network**. Use the edge table and graph to show which tickers were
   discussed together.
6. Move to **Map**. Switch between `GameStop`, `AMC stock`, and
   `WallStreetBets`; explain that Google Trends values are relative, normalized
   search interest.
7. End on **Methods** and name the main limitations: Reddit coverage is focused
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
