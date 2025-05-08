# How to visualize your Data

## ⚠️ This is an absolute temporary solution
Disclaimer: Because this had high prio I just created a quick tool to visulize
your solutions. This is not even a real prototype, almost purely ChatGPT.
I already have made some improvements, but for that the datastructure of
the solution need to be changed. And until this is all done, you can use this
ugly beast.

## What do you need to do?
You need the `app.py` file. At the top you set your solution file. Then you
use `streamlit run algorithm/app.py --server.port 8999`. This should host
a website, that you can visit under `http://localhost:8999/` in your browser.
There you should see all the different solutions.
For that you need streamlit installed.

## Where is this going?
I have already started implementing the ability to see the total work hours and
also whether a day or shift is marked as free. Also the support for the different
qualifiaction. It is coming soon...
