# User review guide

1. Start the app using the README commands. The initial explorer shows the library totals, search modes, upload button, and a sample collection action.
2. Click **Try sample documents**. Three documents are indexed and “What is the vacation policy?” runs automatically. Inspect the employee handbook result and the source evidence below it.
3. Open **Search settings**. Set semantic weight to 0 and run the query in hybrid mode; compare with Keyword mode. Set it to 1 and compare with Meaning mode. Intermediate weights combine both rankings.
4. Upload your own text-based PDF, Office file, or supported text document. Expand **Advanced upload settings** to adjust chunking. Each file gets its own success or error message.
5. Search for a known exact phrase in Keyword mode. Try a related concept in Meaning mode. Small collections and unfamiliar paraphrases may have limited semantic recall; compare the raw scores and passages.
6. Restrict the search to a document and adjust the number of results or minimum rank score. Rank values are not confidence percentages.
7. Expand **Read full section**. Confirm the filename and passage number match your source content. **Copy references (JSON)** copies up to three passages when browser clipboard permissions allow it.
8. Open **My documents** and delete a document. Confirmation is required. Search again to verify its passages are gone.
9. Stop and restart the app. Indexed documents should remain. Try the layout on a narrow screen and navigate controls with the keyboard.
10. Use `/docs` to review and exercise API parameters. Run the documented tests before accepting changes.

## Acceptance record

The automated checks and browser results are recorded in `VALIDATION.md`. Screenshots show the initial explorer, retrieved results, and mobile layout. Search results depend on the uploaded corpus and are not a promise of answer accuracy.

Review decision points: whether local LSA meets your real retrieval needs; whether you need OCR or additional formats; whether you require a generative answer stage; and what authentication and hosting model is required before sharing the service.

The **How to use** button explains the three steps. Search mode guidance updates as you switch modes. **Reset settings** restores the Hybrid defaults, and **Done — go to search** closes uploads and focuses the search box. Technical ranking details remain available under **Search scores** on each result.
